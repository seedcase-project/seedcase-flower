"""Build sections from templates."""

import tomllib
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any, Optional, Union, cast

from jinja2 import (
    Environment,
    FileSystemLoader,
    Template,
    TemplateNotFound,
    select_autoescape,
)
from jsonpath import findall, finditer
from pydantic import BaseModel, Field
from seedcase_soil import flat_fmap, fmap

from seedcase_flower.config import Config
from seedcase_flower.sections import Content, Many, ManyContent, One
from seedcase_flower.styles import Style


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


def _get_styles_dir() -> Path:
    return Path(str(files("seedcase_flower").joinpath("styles")))


def _get_template_dir(style: Style) -> Path:
    return _get_styles_dir() / style.name


def _get_shared_dir() -> Path:
    return _get_styles_dir() / "shared"


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
    return ", ".join(fmap(value, lambda item: f"`{item}`"))


def _inline_code_values(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(fmap(value, lambda item: f"`{item}`"))
    return f"`{value}`"


def _within_character_limit(values: list[str], character_limit: int) -> bool:
    return len(", ".join(values)) <= character_limit


def _last_index_within_character_limit(values: list[str], character_limit: int) -> int:
    valid_indexes = filter(
        lambda i: _within_character_limit(values[:i], character_limit),
        range(1, len(values) + 1),
    )
    return max(valid_indexes, default=1)


def _split_allowed_values(
    value: Any, visible_characters: int = 150, hidden_characters: int = 50
) -> dict[str, Any]:
    if not isinstance(value, list):
        return {"visible": [str(value)], "hidden": []}
    raw_values = list(map(str, value))
    full_values = ", ".join(raw_values)
    if len(full_values) <= visible_characters:
        return {"visible": raw_values, "hidden": []}

    visible_count = _last_index_within_character_limit(raw_values, visible_characters)
    hidden_values = raw_values[visible_count:]
    hidden = ", ".join(hidden_values)
    if len(hidden) < hidden_characters:
        return {"visible": raw_values, "hidden": []}

    return {"visible": raw_values[:visible_count], "hidden": hidden_values}


def _join_values(value: list[str]) -> str:
    return ", ".join(value)


def _bracket_list(value: Union[str, list[str]]) -> str:
    if isinstance(value, str):
        return value
    if len(value) == 1:
        return value[0]
    return f"[{', '.join(value)}]"


def _replace_newlines(cell: str) -> str:
    return cell.replace("\n", " ")


def _replace_newlines_in_row(row: list[str]) -> list[str]:
    return fmap(row, _replace_newlines)


def _max_column_width(rows: list[list[str]], col: int) -> int:
    return max(map(lambda row: len(row[col]), rows), default=0)


def _cell_width(header_row: list[str], data_rows: list[list[str]], col: int) -> int:
    return max(len(header_row[col]), _max_column_width(data_rows, col))


def _column_widths(header_row: list[str], data_rows: list[list[str]]) -> list[int]:
    return fmap(range(len(header_row)), lambda i: _cell_width(header_row, data_rows, i))


def _format_row(row: list[str], widths: list[int]) -> str:
    return "| " + " | ".join(map(str.ljust, row, widths)) + " |"


def _separator_row(widths: list[int]) -> str:
    return "|" + "|".join(map(lambda w: "-" * (w + 2), widths)) + "|"


def _adjust_column_widths(header_row: list[str], data_rows: list[list[str]]) -> str:
    if not header_row:
        return ""

    header_row = _replace_newlines_in_row(header_row)
    data_rows = fmap(data_rows, _replace_newlines_in_row)
    widths = _column_widths(header_row, data_rows)

    return "\n".join(
        [
            _format_row(header_row, widths),
            _separator_row(widths),
            *map(lambda row: _format_row(row, widths), data_rows),
        ]
    )


def _create_jinja_env(search_paths: list[Path]) -> Environment:
    env = Environment(
        loader=FileSystemLoader(search_paths),
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
    # Render a possible value or list of possible values as inline code
    env.filters["_inline_code_values"] = _inline_code_values
    # Split possible values into visible and hidden values for templates to render
    env.globals["_split_allowed_values"] = _split_allowed_values
    # Render a list of strings as comma-separated text
    env.filters["_join_values"] = _join_values
    # Render a single value as inline code
    env.filters["_inline_code"] = _inline_code
    # Render a list of strings as bracketed list
    env.filters["_bracket_list"] = _bracket_list
    # Render a markdown table with adjusted column widths
    env.globals["_adjust_column_widths"] = _adjust_column_widths
    return env


def _get_template(content_template_path: Path, env: Environment) -> Template:
    try:
        # as_posix() ensures consistent separators; Jinja expects POSIX-style paths.
        template = env.get_template(content_template_path.as_posix())
    except TemplateNotFound:
        raise FileNotFoundError(
            f"Template file '{content_template_path}' does not exist in the "
            f"search path: {cast(FileSystemLoader, env.loader).searchpath}"
        )
    return template


def _build_content_one(
    content: Content, properties: dict[str, Any], env: Environment
) -> str:
    selected_properties = findall(content.jsonpath, properties)
    if len(selected_properties) > 1:
        raise ValueError(
            "A `one` section expects at most one match. JSON path "
            f"{content.jsonpath!r} returned {len(selected_properties)} "
            "matches. Use a more specific JSON path or switch to a `many` section."
        )

    template = _get_template(content.template_path, env)
    return template.render(
        **{
            content.jinja_variable: selected_properties[0]
            if selected_properties
            else None
        }
    )


def _build_one(one: One, properties: dict[str, Any], env: Environment) -> BuiltSection:
    built_contents = fmap(
        one.contents,
        lambda content: _build_content_one(content, properties, env),
    )
    return BuiltSection(
        output_path=one.output_path,
        content="\n".join(built_contents),
    )


@dataclass(frozen=True)
class ManyMatch:
    """A metadata item displayed in a `many` section.

    Attributes:
        resource_name: The name of the resource containing the metadata item.
        properties: The metadata item.
    """

    resource_name: str
    properties: dict[str, Any]


def _get_many_matches(jsonpath: str, properties: dict[str, Any]) -> list[ManyMatch]:
    return fmap(
        finditer(jsonpath, properties),
        lambda match: ManyMatch(
            resource_name=properties["resources"][match.parts[1]]["name"],
            properties=cast(dict[str, Any], match.value),
        ),
    )


def _build_many(
    many: Many, properties: dict[str, Any], env: Environment
) -> list[BuiltSection]:
    template = _get_template(many.template_path, env)
    matches = _get_many_matches(many.content.jsonpath, properties)

    return fmap(
        matches,
        lambda match: BuiltSection(
            output_path=_get_output_path_for_match(match, many),
            content=template.render(**{many.jinja_variable: match.properties}),
        ),
    )


def _get_output_path_for_match(match: ManyMatch, many: Many) -> Optional[Path]:
    if not many.output_path:
        return None

    return Path(
        many.output_path.as_posix()
        .replace(ManyContent.resources.placeholder, match.resource_name)
        .replace(ManyContent.fields.placeholder, match.properties["name"])
    )


def build_sections(properties: dict[str, Any], config: Config) -> list[BuiltSection]:
    """Builds the output files based on the provided properties and configuration.

    Args:
        properties: The Data Package properties.
        config: The configuration.

    Returns:
        A list of built output files.
    """
    if config.template_dir is None:
        template_dir = _get_template_dir(config.style)
        # Search style dir first, then shared dir.
        search_paths = [template_dir, _get_shared_dir()]
    else:
        # Only search the custom dir.
        template_dir = config.template_dir
        search_paths = [template_dir]
    sections_toml = _load_sections_toml(template_dir)
    env = _create_jinja_env(search_paths)
    return fmap(
        sections_toml.one_sections,
        lambda one: _build_one(one, properties, env),
    ) + flat_fmap(
        sections_toml.many_sections,
        lambda many: _build_many(many, properties, env),
    )
