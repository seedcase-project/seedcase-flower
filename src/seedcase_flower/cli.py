"""Functions for the exposed CLI."""

from enum import Enum
from pathlib import Path
from typing import Any, Optional

from seedcase_flower.internals import _read_properties, _resolve_uri
import cyclopts

app = cyclopts.App(
    help="Flower generates human-readable documentation from Data Packages."
)


class BuildStyle(Enum):
    """Built-in styles for outputting to file."""

    quarto_one_page = "quarto_one_page"
    quarto_resource_listing = "quarto_resource_listing"
    quarto_resource_tables = "quarto_resource_tables"


@app.command()
def build(
    uri: str = "datapackage.json",
    style: Optional[BuildStyle] = None,
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
    # Match works well when paired with enums for strictness and checking.
    match style:
        case None:
            cli_message = "Setting style from config (or default if no file found)"
            # TODO implement loading the style from the config
            # TODO It seems appropriate to set the default value inside `load_config` if
            # no file found since this will be a repeating pattern
            # config: Config = load_config(style, path)

        # cyclopts guarantees that any value other than None is a `BuildStyle`
        case _:
            cli_message = "Style supported!"  # Placeholder
            # TODO implement setting the style in the config class
            # config: Config = Config(style=BuildStyle(style))

    path: Path = _resolve_uri(uri)
    properties: dict[str, Any] = _read_properties(path)

    if verbose:
        print(output_dir, properties, template_dir)  # Placeholder for unused args
    return cli_message


def view() -> str:
    """Display the contents of a `datapackage.json` in a human-friendly way."""
    return ""


if __name__ == "__main__":
    app()
