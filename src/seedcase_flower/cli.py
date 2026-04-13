"""Functions for the exposed CLI."""

from pathlib import Path
from typing import Any, Optional

from check_datapackage import check
from rich.console import Console
from rich.markdown import Markdown
from seedcase_soil import (
    CONSOLE_THEME,
    Address,
    parse_source,
    print_if_verbose,
    read_properties,
    run_without_tracebacks,
    setup_cli,
)

from seedcase_flower.build_sections import build_sections
from seedcase_flower.config import Config
from seedcase_flower.internals import (
    _map,
    _number,
)
from seedcase_flower.styles import Style, ViewStyle
from seedcase_flower.write_sections import write_sections

app = setup_cli(
    name="seedcase-flower",
    help="Flower generates human-readable documentation from Data Packages.",
    config_name=".flower.toml",
)


@app.command()
def build(
    source: str = "datapackage.json",
    /,  # End of positional-only args
    *,  # Start of keyword-only params
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
    check(properties, error=True)
    print_if_verbose(
        verbose, f"Read Data Package {properties['name']!r} from {address.value!r}."
    )

    built_sections = build_sections(properties, config)
    print_if_verbose(
        verbose,
        (
            f"Created {_number('section', built_sections)} "
            f"using the {style.name!r} style."
        ),
    )

    output_files: list[Path] = write_sections(built_sections, output_dir)
    print_if_verbose(
        verbose, f"Created {_number('file', output_files)} in '{output_dir}/':"
    )
    print_if_verbose(
        verbose, "\n".join(_map(output_files, lambda file: f"  - '{file}'"))
    )


@app.command(config=[])
def view(
    source: str = "datapackage.json",
    /,  # End of positional-only args
    *,  # Start of keyword-only params
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
    check(properties, error=True)
    built_sections = build_sections(properties, Config(style=Style[style.name]))
    console = Console(theme=CONSOLE_THEME)
    # TODO move back console theme? will it be used in CDP?
    print()  # One line separation between the command and the datapackage title
    console.print(Markdown(built_sections[0].content))


def main() -> None:
    """Create an entry point to run the cli without tracebacks."""
    run_without_tracebacks(app)
