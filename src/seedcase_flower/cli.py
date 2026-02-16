"""Functions for the exposed CLI."""

from enum import Enum
from pathlib import Path
from typing import Any, Optional

from cyclopts import App, Parameter, config

from seedcase_flower.internals import _read_properties, _resolve_uri

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
            root_keys="flower",
            search_parents=True,
            use_commands_as_keys=False,
        ),
    ],
)


class BuildStyle(Enum):
    """Built-in styles for outputting to file."""

    quarto_one_page = "quarto_one_page"
    quarto_resource_listing = "quarto_resource_listing"
    quarto_resource_tables = "quarto_resource_tables"


@app.command()
def build(
    uri: str = "datapackage.json",
    style: Optional[BuildStyle] = BuildStyle.quarto_one_page,
    template_dir: Optional[Path] = None,
    output_dir: Path = Path("docs"),
    verbose: bool = False,
) -> str:
    """Build human-readable documentation from a `datapackage.json` file.

    Args:
        uri: The URI to a datapackage.json file.
        style: The style used to structure the output.
        template_dir: The directory that contains the Jinja template
            files and `sections.toml`. When set, it will override any
            built-in style specified via the `style` parameter.
        output_dir: The directory to save the generated files in.
        verbose: If True, outputs additional information to the console.

    Returns:
        Outputs a message of the files created if verbose is True, otherwise
            outputs nothing.
    """
    path: Path = _resolve_uri(uri)
    properties: dict[str, Any] = _read_properties(path)

    if verbose:
        print(output_dir, properties, template_dir)  # Placeholder for unused args
    return ""


def view() -> str:
    """Display the contents of a `datapackage.json` in a human-friendly way."""
    return ""


if __name__ == "__main__":
    app()
