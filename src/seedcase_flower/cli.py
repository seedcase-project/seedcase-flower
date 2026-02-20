"""Functions for the exposed CLI."""

from pathlib import Path
from typing import Any, Optional

from cyclopts import App, Parameter, config
from cyclopts.help import (
    ColumnSpec,
    DefaultFormatter,
    DescriptionRenderer,
    NameRenderer,
    PlainFormatter,
)

# from seedcase_flower.config import Config as FlowerConfig
from seedcase_flower.internals import BuildStyle, _read_properties, _resolve_uri


# Define custom column renderers
def names_renderer(entry):
    """Combine parameter names and shorts."""
    # if entry.names:
    #     names = " ".join(name for name in entry.names if name.startswith("-"))
    # else:
    #     names = ""
    from cyclopts.annotations import get_hint_name

    names = []
    if entry.names:
        for name in sorted(entry.names):
            if not name.startswith("-"):
                # breakpoint()
                # if isinstance(entry.type, bool):
                if get_hint_name(entry.type) == "bool":
                    name = ""
                else:
                    name = f"[dim]<{name}>[/dim]"
            else:
                name = f"[bold red]{name}[/bold red]"
            names.append(name)

        # hint = f"[dim]{get_hint_name(entry.type)}[/dim]"
        # names.append(hint)
        # names.append(get_hint_name(entry.type))

    # names = " ".join(sorted(entry.names)) if entry.names else ""
    # names = " ".join(entry.names) if entry.names else ""
    # shorts = " ".join(entry.shorts) if entry.shorts else ""
    # return f"{names} {shorts}".strip()
    return f"{' '.join(names)}".strip()
    # return f"{entry}"


app = App(
    help="Flower generates human-readable documentation from Data Packages.",
    # help_formatter=PlainFormatter(),
    help_formatter=DefaultFormatter(
        column_specs=(
            ColumnSpec(
                renderer=names_renderer,
            ),
            # ColumnSpec(renderer=NameRenderer()),
            ColumnSpec(renderer=DescriptionRenderer(newline_metadata=True)),
        )
    ),
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
    properties: dict[str, Any] = _read_properties(path)

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
