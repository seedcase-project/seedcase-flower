"""Functions for the exposed CLI."""

from pathlib import Path
from typing import Any, Optional

from cyclopts import App, Parameter, config
from cyclopts.help import ColumnSpec, DefaultFormatter, DescriptionRenderer

from seedcase_flower.config import Config
from seedcase_flower.internals import (
    Uri,
    _build_sections,
    _format_param_help,
    _parse_uri,
    _read_properties,
)
from seedcase_flower.styles import BuildStyle

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
        uri: The path to a local `datapackage.json` file or its parent folder.
            Can also be an `https:` URL to a remote `datapackage.json` or a
            `github:` / `gh:` URI pointing to a repo with a `datapackage.json`
            in the repo root (in the format `gh:org/repo`, which can also include
            reference to a tag or branch, such as `gh:org/repo@main` or
            `gh:org/repo@1.0.1).
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

    uri: Uri = _parse_uri(uri)  # type: ignore # TODO fix in read_prop PR
    properties: dict[str, Any] = _read_properties(uri)  # type: ignore # TODO fix in read_prop PR
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
