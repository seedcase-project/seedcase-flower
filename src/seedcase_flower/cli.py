"""Functions for the exposed CLI."""

from enum import Enum
from typing import Optional
from pathlib import Path

from seedcase_flower.internals import _read_properties, _resolve_uri


class BuildStyle(Enum):
    """Built-in styles for outputting to file."""

    quarto_one_page = "quarto_one_page"
    quarto_resource_listing = "quarto_resource_listing"
    quarto_resource_tables = "quarto_resource_tables"


def build(
    uri: str = "datapackage.json",
    style: Optional[BuildStyle] = None,
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
            (`quarto-one-page`). The `custom` style is only configurable from
            the config file (or via the `Config` Python class).
        output_dir: The directory to output the generated files to.
            Defaults to the current working directory.
        verbose: If True, outputs messages to the console.

    Returns:
        Outputs a message of the files created if verbose is True, otherwise
            outputs nothing.
    """
    # Match works well when paired with enums for strictness and checking.
    match style:
        case _ if style in BuildStyle:
            cli_message = "Style supported!"  # Placeholder
            # TODO implement setting the style in the config class
            # config: Config = Config(style=BuildStyle(style))

        case None:
            cli_message = "Setting style from config (or default if no file found)"
            # TODO implement loading the style from the config
            # TODO It seems appropriate to set the default value inside `load_config` if
            # no file found since this will be a repeating pattern
            # config: Config = load_config(style, path)

        case _:
            cli_message = (  # Placeholder
                "Style not supported for `build`. Should be one of "
                f"{BuildStyle._member_names_}"
            )
            # TODO Raise error

    path: Path = _resolve_uri(uri)
    properties: dict = _read_properties(path)

    print(output_dir, verbose, properties)  # Placeholder to ensure no unused args
    return cli_message


def view() -> str:
    """Display the contents of a `datapackage.json` in a human-friendly way."""
    return ""
