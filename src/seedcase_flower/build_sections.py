"""Build sections from templates."""

import tomllib
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any, Optional, Union

from jinja2 import Environment, FileSystemLoader, select_autoescape
from jsonpath import findall
from pydantic import BaseModel, Field

from seedcase_flower.config import Config
from seedcase_flower.internals import _map
from seedcase_flower.section import Content, Mode, Section
from seedcase_flower.styles import Style


class SectionsFile(BaseModel, frozen=True):
    """Data model of the contents of the `sections.toml` file.

    Attributes:
        sections: The sections in the config file.
    """

    sections: list[Section] = Field(alias="section")


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


def _get_template_dir(style: Style) -> Path:
    styles_path = Path(str(files("seedcase_flower").joinpath("styles")))
    return styles_path / style.name


def _load_sections(template_dir: Path) -> list[Section]:
    if not template_dir.is_dir():
        raise NotADirectoryError(f"Template directory '{template_dir}' does not exist.")

    template_path = template_dir / "sections.toml"
    if not template_path.is_file():
        raise FileNotFoundError(
            f"Template directory '{template_dir}' does not contain a "
            "sections.toml file."
        )

    with open(template_path, mode="rb") as file:
        sections_file = tomllib.load(file)

    return SectionsFile.model_validate(sections_file).sections


def _build_content(
    content: Content, properties: dict[str, Any], template_dir: Path, env: Environment
) -> str:
    # TODO: handle Mode.many
    if content.mode == Mode.many:
        raise NotImplementedError()

    selected_properties = findall(content.jsonpath, properties)
    if len(selected_properties) > 1:
        raise ValueError(
            f"`Mode.one` expects at most one match. JSON path {content.jsonpath!r} "
            f"returned {len(selected_properties)} matches. Use a more specific "
            "JSON path or switch to `Mode.many`."
        )

    template_path = template_dir / content.template_path
    if not template_path.is_file():
        raise FileNotFoundError(
            f"Template file '{content.template_path}' does not exist in the template "
            f"directory '{template_dir}'."
        )

    template = env.get_template(template_path.name)
    return template.render(
        **{
            content.jinja_variable: selected_properties[0]
            if selected_properties
            else None
        }
    )


def _build_section(
    section: Section, properties: dict[str, Any], template_dir: Path, env: Environment
) -> BuiltSection:
    built_contents = _map(
        section.contents,
        lambda content: _build_content(content, properties, template_dir, env),
    )
    return BuiltSection(
        output_path=section.output_path,
        content="\n".join(built_contents),
    )


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


def build_sections(properties: dict[str, Any], config: Config) -> list[BuiltSection]:
    """Build all sections of a style configured in the `sections.toml` file.

    Args:
        properties: The Data Package metadata.
        config: The `Config` class, in particular with the `template_dir` filled in.

    Returns:
        A list of `BuiltSection` classes, to be used to write to files.
    """
    template_dir = config.template_dir or _get_template_dir(config.style)
    sections = _load_sections(template_dir)
    env = _create_jinja_env(template_dir)
    return _map(
        sections,
        lambda section: _build_section(section, properties, template_dir, env),
    )
