"""Helper functions for private use."""

import json
import tomllib
from dataclasses import dataclass
from enum import Enum
from importlib.resources import files
from pathlib import Path
from typing import Any, Callable, Iterable, Optional, TypeVar, Union

from jinja2 import Environment, FileSystemLoader
from jsonpath import findall
from pydantic import BaseModel, Field

from seedcase_flower.config import Config
from seedcase_flower.section import Content, RelativePath, Section


class BuildStyle(Enum):
    """Built-in styles for outputting to file."""

    quarto_one_page = "quarto_one_page"
    quarto_resource_listing = "quarto_resource_listing"
    quarto_resource_tables = "quarto_resource_tables"


class ViewStyle(Enum):
    """Built-in styles for outputting to the terminal."""

    terminal_default = "terminal_default"


# Output maybe str? Path?
# Use `match` inside for strictness on URI types? Or use a library for URI parsing?
# TODO Extend to parse strings and return either URL or Path
def _resolve_uri(uri: str) -> Path:
    return Path(uri)


# TODO Extend to also read properties from URLs
def _read_properties(path: Path) -> dict[str, Any]:
    with open(path) as properties_file:
        datapackage: dict[str, Any] = json.load(properties_file)
        return datapackage


In = TypeVar("In")
Out = TypeVar("Out")


def _map(x: Iterable[In], fn: Callable[[In], Out]) -> list[Out]:
    return list(map(fn, x))


class SectionsFile(BaseModel, frozen=True):
    """Class modelling the `sections.toml` file.

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
    output_path: Optional[RelativePath] = None


def _get_template_dir_for_style(style: Union[BuildStyle, ViewStyle]) -> Path:
    STYLES_PATH = Path(str(files("seedcase_flower").joinpath("styles")))
    return STYLES_PATH / style.name


def _load_sections(template_dir: Path) -> list[Section]:
    with open(template_dir / "sections.toml", mode="rb") as file:
        sections_file = tomllib.load(file)

    return SectionsFile.model_validate(sections_file).sections


def _build_content(
    content: Content, properties: dict[str, Any], template_dir: Path, env: Environment
) -> str:
    selected_properties = findall(content.jsonpath, properties)
    template = env.get_template((template_dir / content.template_path).name)
    # Mode.one
    # TODO: handle Mode.many
    return template.render(
        **{
            # TODO: handle all possible selected properties
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
        content="".join(built_contents),
    )


def _inline_code(value: Optional[str]) -> Optional[str]:
    return f"`{value}`" if value else None


def _inline_code_list(value: str | list[str]) -> str:
    if isinstance(value, str):
        value = [value]
    return ", ".join(_map(value, lambda item: f"`{item}`"))


def _create_jinja_env(template_dir: Path) -> Environment:
    env = Environment(
        loader=FileSystemLoader(template_dir),
        trim_blocks=True,
    )
    env.filters["_inline_code_list"] = _inline_code_list
    env.filters["_inline_code"] = _inline_code
    return env


def _build_sections(properties: dict[str, Any], config: Config) -> list[BuiltSection]:
    template_dir = config.template_dir or _get_template_dir_for_style(config.style)
    sections = _load_sections(template_dir)
    env = _create_jinja_env(template_dir)
    return _map(
        sections,
        lambda section: _build_section(section, properties, template_dir, env),
    )
