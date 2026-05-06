"""Functions for the exposed CLI."""

from enum import Enum
from pathlib import Path
from typing import Any, Optional

from check_datapackage import check
from rich.console import Console, Group, RenderableType
from rich.rule import Rule
from rich.table import Table
from rich.text import Text
from seedcase_soil import (
    CONSOLE_THEME,
    Address,
    fmap,
    parse_source,
    print_if_verbose,
    read_properties,
    run_without_tracebacks,
    setup_cli,
)

from seedcase_flower.build_sections import build_sections
from seedcase_flower.config import Config
from seedcase_flower.internals import _number
from seedcase_flower.styles import Style
from seedcase_flower.write_sections import write_sections

app = setup_cli(
    name="seedcase-flower",
    help="Flower generates human-readable documentation from Data Packages.",
    config_name=".flower.toml",
)


class ViewMode(Enum):
    """Ways to display `view` output in the terminal."""

    tui = "tui"
    stdout = "stdout"


@app.command()
def build(
    source: str = "datapackage.json",
    /,  # End of positional-only args
    *,  # Start of keyword-only params
    style: Style = Style.quarto_one_page,
    template_dir: Optional[Path] = None,
    output_dir: Path = Path("docs"),
    verbose: bool = False,
) -> None:
    """Build human-readable documentation from a `datapackage.json` file.

    Args:
        source: The location of a `datapackage.json`, defaults to a file or folder
            path. Can also be an `https:` source to a remote `datapackage.json` or a
            `github:` / `gh:` pointing to a repo with a `datapackage.json`
            in the repo root (in the format `gh:org/repo`, which can also include
            reference to a tag or branch, such as `gh:org/repo@main` or
            `gh:org/repo@1.0.1`).
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
    address: Address = parse_source(source)
    properties: dict[str, Any] = read_properties(address)
    check(properties, error=True)
    print_if_verbose(
        verbose, f"Read Data Package {properties['name']!r} from {address.value!r}."
    )

    built_sections = build_sections(properties, config)
    print_if_verbose(
        verbose,
        (
            f"Created {_number('section', built_sections)} "
            f"using the {style.name!r} style."
        ),
    )

    output_files: list[Path] = write_sections(built_sections, output_dir)
    print_if_verbose(
        verbose, f"Created {_number('file', output_files)} in '{output_dir}/':"
    )
    print_if_verbose(
        verbose, "\n".join(fmap(output_files, lambda file: f"  - '{file}'"))
    )


@app.command(config=[])
def view(
    source: str = "datapackage.json",
    /,  # End of positional-only args
    *,  # Start of keyword-only params
    mode: ViewMode = ViewMode.tui,
) -> None:
    """Display the contents of a `datapackage.json` in a human-friendly way.

    Args:
        source: The location of a `datapackage.json`, defaults to a file or folder
            path. Can also be an `https:` source to a remote `datapackage.json` or a
            `github:` / `gh:` pointing to a repo with a `datapackage.json`
            in the repo root (in the format `gh:org/repo`, which can also include
            reference to a tag or branch, such as `gh:org/repo@main` or
            `gh:org/repo@1.0.1`).
        mode: The terminal display mode. Use `tui` for an interactive interface
            or `stdout` for plain output that can be piped to other tools.
    """
    address: Address = parse_source(source)
    properties: dict[str, Any] = read_properties(address)
    check(properties, error=True)
    if mode == ViewMode.tui:
        from seedcase_flower.tui import run_textual_viewer

        run_textual_viewer(properties)
        return

    console = Console(theme=CONSOLE_THEME)
    console.print(_format_view_properties(properties))


def _format_view_properties(properties: dict[str, Any]) -> RenderableType:
    """Format Data Package properties for plain terminal output."""
    renderables: list[RenderableType] = []
    title = _package_title(properties)
    if title:
        renderables.append(Text(title, style="markdown.h1"))
    if description := properties.get("description"):
        renderables.append(Text(description))
    if version := properties.get("version"):
        renderables.extend(_metadata_list("Version", [version]))
    if licenses := properties.get("licenses"):
        renderables.extend(_metadata_list("Licenses", _license_labels(licenses)))
    if contributors := properties.get("contributors"):
        renderables.extend(
            _metadata_list("Contributors", _contributor_labels(contributors))
        )
    if resources := properties.get("resources"):
        renderables.append(Text("Resources", style="yellow bold"))
        renderables.append(_resources_table(resources))

    for resource in properties.get("resources", []):
        renderables.extend([Text(""), Rule(style="dim"), Text("")])
        renderables.extend(_format_resource(resource))

    return Group(*renderables)


def _format_resource(resource: dict[str, Any]) -> list[RenderableType]:
    renderables: list[RenderableType] = []
    resource_name = resource.get("name", "")
    title = resource.get("title") or resource_name
    if title:
        renderables.append(Text(title, style="markdown.h1"))
    if description := _resource_description(resource):
        renderables.append(Text(description))

    schema = resource.get("schema") or {}
    if path := resource.get("path"):
        renderables.extend(_metadata_list("Path", [path]))
    if primary_key := schema.get("primaryKey"):
        renderables.extend(_metadata_list("Primary key", [_as_list_text(primary_key)]))
    if foreign_keys := schema.get("foreignKeys"):
        renderables.extend(
            _metadata_list("Foreign keys", _foreign_key_text(foreign_keys, resource))
        )
    if fields := schema.get("fields"):
        renderables.append(Text("Fields", style="yellow bold"))
        renderables.append(_fields_table(fields))
    return renderables


def _package_title(properties: dict[str, Any]) -> str:
    name = properties.get("name")
    title = properties.get("title")
    if name and title:
        return f"{name}: {title}"
    return name or title or ""


def _metadata_list(label: str, values: list[str]) -> list[RenderableType]:
    if not values:
        return []
    text = Text(label, style="yellow bold")
    for value in values:
        text.append(f"\n• {value}")
    return [text]


def _license_labels(licenses: list[dict[str, Any]]) -> list[str]:
    return [
        label
        for license in licenses
        if (label := license.get("title") or license.get("name"))
    ]


def _contributor_labels(contributors: list[dict[str, Any]]) -> list[str]:
    return [
        label
        for contributor in contributors
        if (label := _single_contributor_label(contributor))
    ]


def _single_contributor_label(contributor: dict[str, Any]) -> str:
    full_name = (
        f"{contributor.get('firstName', '')} {contributor.get('lastName', '')}"
    ).strip()
    label = (
        contributor.get("title")
        or full_name
        or contributor.get("organization")
        or contributor.get("email")
        or ""
    )
    roles = ", ".join(contributor.get("roles", []))
    return f"{label}{': ' + roles if roles else ''}" if label else ""


def _resource_description(resource: dict[str, Any]) -> str:
    description = resource.get("description", "")
    resource_name = resource.get("name", "")
    title = resource.get("title", "")
    labels = {_metadata_label(resource_name), _metadata_label(title)}
    return "" if _metadata_label(description) in labels else description


def _metadata_label(value: str) -> str:
    return value.strip().strip("`")


def _as_list_text(value: str | list[str]) -> str:
    return value if isinstance(value, str) else ", ".join(value)


def _foreign_key_text(
    foreign_keys: list[dict[str, Any]], resource: dict[str, Any]
) -> list[str]:
    lines = []
    for foreign_key in foreign_keys:
        reference = foreign_key.get("reference", {})
        reference_resource = reference.get("resource") or resource.get("name", "")
        lines.append(
            f"{_as_list_text(foreign_key.get('fields', []))} -> "
            f"{reference_resource}.{_as_list_text(reference.get('fields', []))}"
        )
    return lines


def _resources_table(resources: list[dict[str, Any]]) -> Table:
    table = Table(show_lines=False)
    table.add_column("Name", style="markdown.h1")
    table.add_column("Title")
    table.add_column("Description")
    for resource in resources:
        table.add_row(
            resource.get("name", ""),
            resource.get("title", ""),
            resource.get("description", ""),
        )
    return table


def _fields_table(fields: list[dict[str, Any]]) -> Table:
    table = Table(show_lines=False)
    table.add_column("Name", style="markdown.h1")
    table.add_column("Title")
    table.add_column("Type")
    table.add_column("Description")
    for field in fields:
        table.add_row(
            field.get("name", ""),
            field.get("title", ""),
            field.get("type", "any"),
            field.get("description", ""),
        )
    return table


def main() -> None:
    """Create an entry point to run the cli without tracebacks."""
    run_without_tracebacks(app)
