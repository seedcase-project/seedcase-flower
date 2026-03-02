"""Functions for the exposed CLI."""

from pathlib import Path
from typing import Any, Optional

from cyclopts import App, Parameter, config

from seedcase_flower.config import Config
from seedcase_flower.internals import (
    _build_sections,
    _read_properties,
    _resolve_uri,
)
from seedcase_flower.styles import BuildStyle

app = App(
    name="seedcase-flower",
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
            root_keys=["tool", "seedcase-flower"],
            search_parents=True,
            use_commands_as_keys=False,
        ),
    ],
)


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
    config = Config(
        style=style,
        template_dir=template_dir,
        output_dir=output_dir,
    )

    properties: dict[str, Any] = _read_properties(path)
    built_sections = _build_sections(properties, config)  # noqa: F841
    # TODO: write built sections
    # output_files: list[Path] = write_sections(built_sections, output_dir)

    if verbose:
        print(
            output_dir, properties, template_dir, style
        )  # Placeholder for unused args


def view() -> str:
    """Display the contents of a `datapackage.json` in a human-friendly way."""
    return ""
