import tomllib
from dataclasses import dataclass
from importlib.resources import files
from itertools import chain
from pathlib import Path
from typing import Any, Optional, Union, cast

from jinja2 import Environment, FileSystemLoader, Template, select_autoescape
from jsonpath import findall
from pydantic import BaseModel, Field

from seedcase_flower.config import Config
from seedcase_flower.internals import _filter, _flat_map, _map
from seedcase_flower.sections import Content, Many, One
from seedcase_flower.styles import BuildStyle, ViewStyle


class SectionsToml(BaseModel, frozen=True):
    """Data model of the contents of the `sections.toml` file.

    Attributes:
        one_sections: Sections in the config file generating one file.
        many_sections: Sections in the config file generating many files.
    """

    one_sections: list[One] = Field(alias="one", default=[])
    many_sections: list[Many] = Field(alias="many", default=[])


@dataclass(frozen=True)
class BuiltSection:
    """A section that has been built from a template.

    Attributes:
        content: The rendered template as a string.
        output_path: The path where the section should be written, relative
            to `Config.output_dir`. Sections displayed in the terminal don't
            have an `output_path`.
    """

    content: str
    output_path: Optional[Path] = None


def _get_template_dir(style: Union[BuildStyle, ViewStyle]) -> Path:
    styles_path = Path(str(files("seedcase_flower").joinpath("styles")))
    return styles_path / style.name


def _load_sections_toml(template_dir: Path) -> SectionsToml:
    if not template_dir.is_dir():
        raise NotADirectoryError(f"Template directory '{template_dir}' does not exist.")

    toml_path = template_dir / "sections.toml"
    if not toml_path.is_file():
        raise FileNotFoundError(
            f"Template directory '{template_dir}' does not contain a sections.toml "
            "file."
        )

    with open(toml_path, mode="rb") as file:
        toml_file = tomllib.load(file)

    return SectionsToml.model_validate(toml_file)


def _inline_code(value: Optional[str]) -> Optional[str]:
    return f"`{value}`" if value else None


def _inline_code_list(value: Union[str, list[str]]) -> str:
    # Some Data Package fields allow either a string or a list of strings
    if isinstance(value, str):
        value = [value]
    return ", ".join(_map(value, lambda item: f"`{item}`"))


def _create_jinja_env(template_dir: Path) -> Environment:
    env = Environment(
        loader=FileSystemLoader(template_dir),
        trim_blocks=True,
        autoescape=select_autoescape(
            enabled_extensions=(
                "html.jinja",
                "xml.jinja",
            ),
            default=False,
        ),
    )
    # Render a list of strings as comma-separated inline code
    env.filters["_inline_code_list"] = _inline_code_list
    # Render a single value as inline code
    env.filters["_inline_code"] = _inline_code
    return env


def _get_template(
    template_dir: Path, content_template_path: Path, env: Environment
) -> Template:
    template_path = template_dir / content_template_path
    if not template_path.is_file():
        raise FileNotFoundError(
            f"Template file '{template_path}' does not exist in the template directory."
        )
    return env.get_template(template_path.name)


def _build_content_one(
    content: Content, properties: dict[str, Any], template_dir: Path, env: Environment
) -> str:
    selected_properties = findall(content.jsonpath, properties)
    if len(selected_properties) > 1:
        raise ValueError(
            "A `one` section expects at most one match. JSON path "
            f"{content.jsonpath!r} returned {len(selected_properties)} "
            "matches. Use a more specific JSON path or switch to a `many` section."
        )

    template = _get_template(template_dir, content.template_path, env)
    return template.render(
        **{
            content.jinja_variable: selected_properties[0]
            if selected_properties
            else None
        }
    )


def _select_properties_one(jsonpath: str, properties: dict[str, Any]) -> list[Any]:
    selected_properties = findall(jsonpath, properties)
    if len(selected_properties) > 1:
        raise ValueError(
            f"`one` expects at most one match. JSON path {jsonpath!r} "
            f"returned {len(selected_properties)} matches. Use a more specific "
            "JSON path or switch to `many`."
        )

    return selected_properties


def _select_properties_many(
    jsonpath: str, properties: dict[str, Any]
) -> list[dict[str, Any]]:
    selected_properties = findall(jsonpath, properties)

    # Flatten list of matches if all matches are lists (e.g. JSON path `$.resources`)
    if all(_map(selected_properties, lambda match: isinstance(match, list))):
        selected_properties = list(
            chain.from_iterable(cast(list[list[Any]], selected_properties))
        )

    if _filter(
        selected_properties,
        lambda match: not isinstance(match, dict) or "name" not in match,
    ):
        raise ValueError(
            "In a `many` section, each item must have a 'name' property to be used as "
            f"the output file name. JSON path {jsonpath!r} returned at "
            "least one match without a 'name' property."
        )

    return cast(list[dict[str, Any]], selected_properties)


def _build_one(
    one: One, properties: dict[str, Any], template_dir: Path, env: Environment
) -> BuiltSection:
    built_contents = _map(
        one.contents,
        lambda content: _build_content_one(content, properties, template_dir, env),
    )
    return BuiltSection(
        output_path=one.output_path,
        content="\n".join(built_contents),
    )


def _build_many(
    many: Many, properties: dict[str, Any], template_dir: Path, env: Environment
) -> list[BuiltSection]:
    selected_properties = _select_properties_many(many.content.jsonpath, properties)
    template = _get_template(template_dir, many.content.template_path, env)

    return _map(
        selected_properties,
        lambda match: BuiltSection(
            output_path=_get_output_path_for_match(match, many.output_path),
            content=template.render(**{many.content.jinja_variable: match}),
        ),
    )


def _get_output_path_for_match(
    match: dict[str, Any], output_path: Optional[Path]
) -> Optional[Path]:
    if not output_path:
        return None

    name: str = match["name"]
    # TODO: refine
    if "{" in output_path.name:
        return output_path.parent / name
    return output_path / name


def build_sections(properties: dict[str, Any], config: Config) -> list[BuiltSection]:
    """Builds the output files based on the provided properties and configuration.

    Args:
        properties: The Data Package properties.
        config: The configuration.

    Returns:
        A list of built output files.
    """
    template_dir = config.template_dir or _get_template_dir(config.style)
    sections_toml = _load_sections_toml(template_dir)
    env = _create_jinja_env(template_dir)
    return _map(
        sections_toml.one_sections,
        lambda one: _build_one(one, properties, template_dir, env),
    ) + _flat_map(
        sections_toml.many_sections,
        lambda many: _build_many(many, properties, template_dir, env),
    )
