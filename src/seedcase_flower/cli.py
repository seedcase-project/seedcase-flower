"""Functions for the exposed CLI."""

import tomllib
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any, Optional

from cyclopts import App, Parameter, config
from jinja2 import Environment, FileSystemLoader
from jsonpath import findall
from pydantic import BaseModel, Field

from seedcase_flower.config import Config
from seedcase_flower.internals import (
    BuildStyle,
    ViewStyle,
    _read_properties,
    _resolve_uri,
)
from seedcase_flower.section import RelativePath, Section

app = App(
    help="Flower generates human-readable documentation from Data Packages.",
    default_parameter=Parameter(negative=()),
    config=[
        config.Toml(
            ".flower.toml",
            search_parents=True,
            use_commands_as_keys=False,
        ),
        config.Toml(
            "pyproject.toml",
            root_keys="tool.seedcase-flower",
            search_parents=True,
            use_commands_as_keys=False,
        ),
    ],
)


class SectionsFile(BaseModel, frozen=True):
    """The structure of the `sections.toml` file."""

    sections: list[Section] = Field(alias="section")


@dataclass(frozen=True)
class BuiltSection:
    """A built section."""

    content: str
    output_path: Optional[RelativePath] = None


def _get_template_dir_for_style(style: BuildStyle | ViewStyle) -> Path:
    """Get the template directory for a given style."""
    STYLES_PATH = Path(str(files("seedcase_flower").joinpath("styles")))
    return STYLES_PATH / style.name


def _load_sections(template_dir: Path) -> list[Section]:
    with open(template_dir / "sections.toml", mode="rb") as file:
        sections = tomllib.load(file)

    return SectionsFile.model_validate(sections).sections


def _inline_code(value: str | None) -> str:
    return f"`{value}`" if value else "N/A"


def _inline_code_list(value: str | list[str]) -> str:
    if isinstance(value, str):
        value = [value]
    return ", ".join(list(map(_inline_code, value)))


def _build_section(
    section: Section, properties: dict[str, Any], template_dir: Path
) -> str:
    env = Environment(loader=FileSystemLoader(template_dir))
    env.filters["_inline_code_list"] = _inline_code_list
    env.filters["_inline_code"] = _inline_code
    section_output = ""
    for content in section.contents:
        selected_properties = findall(content.jsonpath, properties)
        template = env.get_template((template_dir / content.template_path).name)
        # Mode.one
        # TODO: handle Mode.many
        section_output += template.render(
            **{
                # TODO: handle all possible selected properties
                content.jinja_variable: selected_properties[0]
                if selected_properties
                else None
            }
        )
    return section_output


def _build_sections(properties: dict[str, Any], config: Config) -> list[BuiltSection]:
    template_dir = config.template_dir or _get_template_dir_for_style(config.style)
    sections = _load_sections(template_dir)
    return [
        BuiltSection(
            output_path=section.output_path,
            content=_build_section(section, properties, template_dir),
        )
        for section in sections
    ]


def _write_sections(built_sections: list[BuiltSection], output_dir: Path) -> None:
    for built_section in built_sections:
        if built_section.output_path:
            output_path = output_dir / built_section.output_path
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(built_section.content)
        else:
            print("What is a section with no output path doing here?")


@app.command()
def build(
    uri: str = "datapackage.json",
    style: BuildStyle = BuildStyle.quarto_one_page,
    template_dir: Optional[Path] = None,
    output_dir: Path = Path("docs"),
    verbose: bool = False,
) -> None:
    """Build human-readable documentation from a `datapackage.json` file.

    Args:
        uri: The URI to a datapackage.json file.
        style: The style used to structure the output. If a template directory
            is given, this parameter will be ignored.
        template_dir: The directory that contains the Jinja template
            files and `sections.toml`. When set, it will override any
            built-in style given by the `style` parameter.
        output_dir: The directory to save the generated files in.
        verbose: If True, prints additional information to the console.
    """
    path: Path = _resolve_uri(uri)
    properties: dict[str, Any] = _read_properties(path)

    if verbose:
        print(output_dir, properties, template_dir)  # Placeholder for unused args

    config = Config(
        style=style,
        template_dir=template_dir,
        output_dir=output_dir,
    )
    built_sections = _build_sections(properties, config)
    _write_sections(built_sections, output_dir)


def view() -> str:
    """Display the contents of a `datapackage.json` in a human-friendly way."""
    return ""
