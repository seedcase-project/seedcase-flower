"""Functions for the exposed CLI."""

from pathlib import Path
from typing import Any, Optional

from cyclopts import App, Parameter, config

# from seedcase_flower.config import Config as FlowerConfig
from seedcase_flower.internals import BuildStyle, Uri, _parse_source, _read_properties

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
            root_keys="tool.seedcase-flower",
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
        source: The path to a local `datapackage.json` file or its parent folder.
            Can also be an `https:` URL to a remote `datapackage.json` or a
            `github:` / `gh:` URI pointing to a repo with a `datapackage.json`
            in the repo root (in the format `gh:org/repo`).
        style: The style used to structure the output. If a template directory
            is given, this parameter will be ignored.
        template_dir: The directory that contains the Jinja template
            files and `sections.toml`. When set, it will override any
            built-in style given by the `style` parameter.
        output_dir: The directory to save the generated files in.
        verbose: If True, prints additional information to the console.
    """
    uri: Uri = _parse_source(source)
    properties: dict[str, Any] = _read_properties(uri)

    # One item per section, rendered from template.
    # Internally uses Jinja2 to render templates with metadata, which
    # are loaded within `build_sections()`. The Jinja2 templates and
    # and the `sections.toml` file are loaded from the template directory,
    # given by the `template_dir` arg or by the built-in styles (which points
    # to a Flower internal template directory).
    # config = FlowerConfig(
    #   style=style,
    #   template_dir=template_dir,
    #   output_dir=output_dir
    # )
    # output: list[BuiltSection] = build_sections(
    #     properties,
    #     config
    # )
    # output_files: list[Path] = write_sections(output, output_dir)

    if verbose:
        print(
            output_dir, properties, template_dir, style
        )  # Placeholder for unused args


def view() -> str:
    """Display the contents of a `datapackage.json` in a human-friendly way."""
    return ""
