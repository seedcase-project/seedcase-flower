"""Functions for the exposed CLI."""

from pathlib import Path
from typing import Any, Optional

from cyclopts import App, Parameter, config
from cyclopts.help import ColumnSpec, DefaultFormatter, DescriptionRenderer
from rich.console import Console
from rich.markdown import Markdown, box
from rich.theme import Theme

from seedcase_flower.config import Config
from seedcase_flower.internals import (
    Address,
    _build_sections,
    _format_param_help,
    _get_template_dir,
    _parse_source,
)
from seedcase_flower.read_properties import read_properties
from seedcase_flower.styles import BuildStyle, ViewStyle
from seedcase_flower.write_sections import write_sections

box.SIMPLE = box.HEAVY_HEAD

_CONSOLE_THEME = Theme(
    {
        "markdown.code": "bold cyan",
        "markdown.table.header": "bold magenta",
        "markdown.table.border": "magenta",
    }
)

app = App(
    name="seedcase-flower",
    help="Flower generates human-readable documentation from Data Packages.",
    help_formatter=DefaultFormatter(
        column_specs=(
            ColumnSpec(renderer=_format_param_help),
            ColumnSpec(renderer=DescriptionRenderer(newline_metadata=True)),
        )
    ),
    default_parameter=Parameter(negative=(), show_default=True),
    config=[
        config.Toml(
            ".flower.toml",
            search_parents=True,
            use_commands_as_keys=False,
        ),
        config.Toml(
            "pyproject.toml",
            root_keys=["tool", "seedcase-flower"],
            search_parents=True,
            use_commands_as_keys=False,
        ),
    ],
)


@app.command()
def build(
    source: str = "datapackage.json",
    style: BuildStyle = BuildStyle.quarto_one_page,
    template_dir: Optional[Path] = None,
    output_dir: Path = Path("docs"),
    verbose: bool = False,
) -> None:
    """Build human-readable documentation from a `datapackage.json` file.

    Args:
        source: The location of a `datapackage.json`, defaults to a file or folder
            path. Can also be an `https:` source to a remote `datapackage.json` or a
            `github:` / `gh:` pointing to a repo with a `datapackage.json`
            in the repo root (in the format `gh:org/repo`, which can also include
            reference to a tag or branch, such as `gh:org/repo@main` or
            `gh:org/repo@1.0.1`).
        style: The style used to structure the output. If a template directory
            is given, this parameter will be ignored.
        template_dir: The directory that contains the Jinja template
            files and `sections.toml`. When set, it will override any
            built-in style given by the `style` parameter.
        output_dir: The directory to save the generated files in.
        verbose: If True, prints additional information to the console.
    """
    config = Config(
        style=style,
        template_dir=template_dir,
        output_dir=output_dir,
    )
    address: Address = _parse_source(source)
    properties: dict[str, Any] = read_properties(address)
    built_sections = _build_sections(properties, config)
    output_files: list[Path] = write_sections(built_sections, output_dir)  # noqa: F841

    if verbose:
        print(
            output_dir, properties, template_dir, style
        )  # Placeholder for unused args


@app.command()
def view(
    source: str = "datapackage.json",
    style: ViewStyle = ViewStyle.quarto_one_page,
) -> None:
    """Display the contents of a `datapackage.json` in a human-friendly way.

    Args:
        source: The location of a `datapackage.json`, defaults to a file or folder
            path. Can also be an `https:` source to a remote `datapackage.json` or a
            `github:` / `gh:` pointing to a repo with a `datapackage.json`
            in the repo root (in the format `gh:org/repo`, which can also include
            reference to a tag or branch, such as `gh:org/repo@main` or
            `gh:org/repo@1.0.1`).
        style: The terminal style used to display the output. Must be one of the
            built-in terminal styles.
    """
    address: Address = _parse_source(source)
    properties: dict[str, Any] = read_properties(address)
    built_sections = _build_sections(
        properties, Config(template_dir=_get_template_dir(style))
    )
    console = Console(theme=_CONSOLE_THEME)
    for section in built_sections:
        if style == ViewStyle.quarto_one_page:
            console.print(_StyledMarkdown(section.content))
        else:
            print(section.content)
