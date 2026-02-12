"""Module containing functions for the exposed CLI."""

from enum import Enum
from pathlib import Path

from seedcase_sprout import PackageProperties, read_properties


# Allows for strict checking of built-in styles, as this is a sum type.
class BuildStyle(Enum):
    """Built-in styles for outputting to file."""

    quarto_one_page = "quarto_one_page"
    quarto_resource_listing = "quarto_resource_listing"
    quarto_resource_tables = "quarto_resource_tables"


def build(
    uri: str = "datapackage.json",
    style: BuildStyle | None = None,
    output_dir: Path = Path(),
    verbose: bool = False,
) -> Path:
    """Build human-readable documentation from a `datapackage.json` file.

    Args:
        uri: The URI to a datapackage.json file. Defaults to
            `datapackage.json` in the current working directory.
        style: The style of output to use. Either one of the built-in styles in
            `Style` or None. If None, it will look for a config file in
            the same directory as the `datapackage.json` file. If a config file is
            not found, it will use the default style (`Style.quarto_one_page`).
            The `Style.custom` option is only available to use in the config
            file (or directly via `Config`).
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
            print("Style supported!")  # Placeholder
            # TODO implement setting the style in the config class
            # config: Config = Config(style=BuildStyle(style))

        case None:
            print("Setting style from config (or default if no file found)")
            # TODO implement loading the style from the config
            # TODO It seems appropriate to set the default value inside `load_config` if
            # no file found since this will be a repeating pattern
            # config: Config = load_config(style, path)

        case _:
            print(  # Placeholder
                "Style not supported for `view`. Should be one of "
                f"{BuildStyle._member_names_}"
            )
            # TODO Raise error

    # Able to read from URI, e.g. `https` or `file` or `gh`
    # Output maybe str? Path?
    # Use `match` inside for strictness on URI types?
    # TODO implement resolve_uri
    # path: str = resolve_uri(uri)

    # TODO temp workaround since sprout only handles reading file paths currently
    path: Path = Path(uri)
    properties: PackageProperties = read_properties(path)

    print(output_dir, verbose, properties)  # Placeholder to ensure no unused args
    return Path()


def view() -> str:
    """Display the contents of a `datapackage.json` in a human-friendly way."""
    return ""
