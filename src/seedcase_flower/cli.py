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
        uri: The URI to a datapackage.json file. Defaults to
            `datapackage.json` in the current working directory.
        style: The style of output to use. If None, Flower will look for a
            config file in the same directory as the `datapackage.json` file.
            If a config file is not found, it will use the default style
            (`quarto-one-page`). A custom style is only configurable from
            the config file (or via the `Config` Python class).
        template_dir: The directory that contains the custom styling Jinja
            template files as well as the `sections.toml` file. Defaults to None
            as the default style is a built-in style that uses built-in templates.
        output_dir: The directory to output the generated files to.
            Defaults to `docs/` within the current working directory.
        verbose: If True, outputs messages to the console.

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
