"""Functions for the exposed CLI."""

from pathlib import Path
from typing import Any, Optional

from cyclopts import App, Parameter, config
from cyclopts.help import ColumnSpec, DefaultFormatter, DescriptionRenderer
from rich import box
from rich.console import Console
from rich.markdown import Markdown
from rich.theme import Theme

from seedcase_flower import errors
from seedcase_flower.build_sections import build_sections
from seedcase_flower.config import Config
from seedcase_flower.internals import (
    _format_param_help,
    _map,
    _number,
    _pretty_print,
)
from seedcase_flower.parse_source import Address, parse_source
from seedcase_flower.read_properties import read_properties
from seedcase_flower.styles import Style, ViewStyle
from seedcase_flower.write_sections import write_sections

# To style markdown tables with a box (pipes) surrounding each column
# instead of only a horizontal line after the table header
box.SIMPLE = box.HEAVY_HEAD

_CONSOLE_THEME = Theme(
    {
        "markdown.h1": "bold yellow",
        "markdown.h2": "bold yellow",
        "markdown.h3": "italic yellow",
        "markdown.code": "blue",
        "markdown.link": "underline cyan",
        "markdown.link_url": "underline cyan",
        "markdown.table.header": "yellow",
        "markdown.table.border": "white",
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
app.register_install_completion_command()


@app.command()
def build(
    source: str = "datapackage.json",
    style: Style = Style.quarto_one_page,
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
    address: Address = parse_source(source)
    properties: dict[str, Any] = read_properties(address)
    _pretty_print(
        verbose, f"Read Data Package {properties['name']!r} from {address.value!r}."
    )

    built_sections = build_sections(properties, config)
    _pretty_print(
        verbose,
        (
            f"Created {_number('section', built_sections)} "
            f"using the {style.name!r} style."
        ),
    )

    output_files: list[Path] = write_sections(built_sections, output_dir)
    _pretty_print(
        verbose, f"Created {_number('file', output_files)} in '{output_dir}/':"
    )
    _pretty_print(verbose, "\n".join(_map(output_files, lambda file: f"  - '{file}'")))


@app.command(config=[])
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
        style: The style used to display the output in the terminal. Must be a
            single-page style.
    """
    address: Address = parse_source(source)
    properties: dict[str, Any] = read_properties(address)
    built_sections = build_sections(properties, Config(style=Style[style.name]))
    console = Console(theme=_CONSOLE_THEME)
    print()  # One line separation between the command and the datapackage title
    console.print(Markdown(built_sections[0].content))
