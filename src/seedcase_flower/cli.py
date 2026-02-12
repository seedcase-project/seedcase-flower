"""Module containing functions for the exposed CLI."""
from enum import Enum
from pathlib import Path

import cyclopts

app = cyclopts.App()

# Allows for strict checking of built-in styles, as this is a sum type.
# The specific terminal style needs to also exist in the Style enum.
class BuildStyle(Enum):
    """Built-in styles for outputting to file."""
    quarto_one_page = 'quarto_one_page'
    quarto_resource_listing = 'quarto_resource_listing'
    quarto_resource_tables = 'quarto_resource_tables'

# TODO To keep track of path and built content for each section.
# @dataclass(frozen=True)
# class BuiltSection:
#     output_path: Path
#     built_content: str

@app.command
def build(
    uri: str = "datapackage.json",
    style: BuildStyle | None = None,
    output_dir: Path = Path(),
    verbose: bool = False
    ) -> None:
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
    # Output maybe str? Path?
    # Use `match` inside for strictness on URI types?
    # path: str = resolve_uri(uri)


    # Match works well when paired with enums for strictness and checking.
    match style:
        case _ if style in BuildStyle:
            print("Style supported!")  # Placeholder
            # TODO implement setting the style in the config
            # config: Config = Config(style=BuildStyle(style))

        case None:
            print('Setting style from config (or default if no file found)')
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
    properties: PackageProperties = read_properties(path)

    # # One item per section, rendered from template.
    # # Internally uses Jinja2 to render templates with metadata.
    # output: list[BuiltSection] = build_sections(
    #     properties,
    #     config
    # )

    # output_files: list[Path] = write_sections(output, output_dir)

    # if verbose:
    #     cli_message(output_files) #?
    print(uri, output_dir, verbose)  # Placeholder


def view() -> str:
    """Display the contents of a `datapackage.json` in a human-friendly way."""
    return ""


if __name__ == "__main__":
    app()
