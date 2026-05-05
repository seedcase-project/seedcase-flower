"""Textual terminal app for browsing Data Package metadata."""

from dataclasses import dataclass
from typing import Any

from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import (
    ContentSwitcher,
    DataTable,
    Footer,
    Header,
    Label,
    ListItem,
    ListView,
    Static,
)

RICH_BLUE = "color(4) bold"
RICH_YELLOW = "color(3) bold"


@dataclass(frozen=True)
class ViewPage:
    """A Data Package page prepared for navigation in the Textual viewer."""

    label: str
    id: str
    blocks: list["ViewBlock"]


@dataclass(frozen=True)
class TextBlock:
    """A text fragment in a Textual viewer page."""

    content: str
    style: str = ""
    classes: str = "body-text"
    spans: tuple[tuple[int, int, str], ...] = ()


@dataclass(frozen=True)
class TableBlock:
    """Structured table data prepared for Textual's DataTable."""

    headers: list[str]
    rows: list[list[str]]
    caption: str = ""


type ViewBlock = TextBlock | TableBlock


def prepare_view_pages(properties: dict[str, Any]) -> list[ViewPage]:
    """Prepare Data Package properties for display in the Textual viewer."""
    pages = [
        ViewPage(
            label="Package",
            id="page-1",
            blocks=_package_blocks(properties),
        )
    ]
    pages.extend(
        ViewPage(
            label=resource.get("name", f"Resource {index}"),
            id=f"page-{index + 1}",
            blocks=_resource_blocks(resource),
        )
        for index, resource in enumerate(properties.get("resources", []), start=1)
    )
    return pages


def _package_blocks(properties: dict[str, Any]) -> list[ViewBlock]:
    blocks: list[ViewBlock] = []
    title = _package_title(properties)
    if title:
        blocks.append(TextBlock(title, style=RICH_BLUE, classes="title"))

    if description := properties.get("description"):
        blocks.append(TextBlock(description))
    if version := properties.get("version"):
        blocks.append(_labeled_list("Version", [version]))
    if licenses := properties.get("licenses"):
        blocks.append(
            TextBlock("Licenses", style=RICH_YELLOW, classes="compact-heading")
        )
        blocks.append(
            TextBlock("\n".join(_license_text(licenses)), classes="metadata-list")
        )
    if contributors := properties.get("contributors"):
        blocks.append(
            TextBlock("Contributors", style=RICH_YELLOW, classes="compact-heading")
        )
        blocks.append(
            TextBlock(
                "\n".join(_contributor_text(contributors)), classes="metadata-list"
            )
        )
    if resources := properties.get("resources"):
        blocks.append(TextBlock("Resources", style=RICH_YELLOW, classes="heading"))
        blocks.append(
            TableBlock(
                headers=["Name", "Title", "Description"],
                rows=[
                    [
                        resource.get("name", ""),
                        resource.get("title", ""),
                        resource.get("description", ""),
                    ]
                    for resource in resources
                ],
            )
        )
    return blocks


def _package_title(properties: dict[str, Any]) -> str:
    name = properties.get("name")
    title = properties.get("title")
    if name and title:
        return f"{name}: {title}"
    return name or title or ""


def _license_text(licenses: list[dict[str, Any]]) -> list[str]:
    return [
        f"• {label}"
        for license in licenses
        if (label := license.get("title") or license.get("name"))
    ]


def _contributor_text(contributors: list[dict[str, Any]]) -> list[str]:
    return [
        text
        for contributor in contributors
        if (text := _single_contributor_text(contributor))
    ]


def _single_contributor_text(contributor: dict[str, Any]) -> str:
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
    return f"• {label}{': ' + roles if roles else ''}" if label else ""


def _resource_blocks(resource: dict[str, Any]) -> list[ViewBlock]:
    blocks: list[ViewBlock] = []
    resource_name = resource.get("name", "")
    title = resource.get("title") or resource_name
    if title:
        blocks.append(TextBlock(title, style=RICH_BLUE, classes="title"))

    if description := _resource_description(resource):
        blocks.append(TextBlock(description))

    schema = resource.get("schema") or {}
    blocks.extend(_resource_metadata_blocks(resource, schema))

    if fields := schema.get("fields"):
        blocks.append(TextBlock("Fields", style=RICH_YELLOW, classes="heading"))
        blocks.append(
            TableBlock(
                headers=["Name", "Title", "Type", "Description"],
                rows=[
                    [
                        field.get("name", ""),
                        field.get("title", ""),
                        field.get("type", "any"),
                        field.get("description", ""),
                    ]
                    for field in fields
                ],
                caption=f"Fields in the {resource.get('name', 'resource')} resource.",
            )
        )
    return blocks


def _resource_description(resource: dict[str, Any]) -> str:
    description = resource.get("description", "")
    resource_name = resource.get("name", "")
    title = resource.get("title", "")
    labels = {_metadata_label(resource_name), _metadata_label(title)}
    return "" if _metadata_label(description) in labels else description


def _metadata_label(value: str) -> str:
    return value.strip().strip("`")


def _resource_metadata_blocks(
    resource: dict[str, Any], schema: dict[str, Any]
) -> list[TextBlock]:
    blocks = []
    if path := resource.get("path"):
        blocks.append(_labeled_list("Path", [path]))
    if primary_key := schema.get("primaryKey"):
        blocks.append(_labeled_list("Primary key", [_as_list_text(primary_key)]))
    if foreign_keys := schema.get("foreignKeys"):
        blocks.append(
            _labeled_list("Foreign keys", _foreign_key_text(foreign_keys, resource))
        )
    return blocks


def _labeled_list(label: str, values: list[str]) -> TextBlock:
    lines = [label] + [f"• {value}" for value in values]
    return TextBlock(
        "\n".join(lines),
        classes="metadata-list",
        spans=((0, len(label), RICH_YELLOW),),
    )


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
            f"{_as_list_text(foreign_key.get('fields', []))} → "
            f"{reference_resource}.{_as_list_text(reference.get('fields', []))}"
        )
    return lines


class FlowerViewApp(App[None]):
    """Interactive terminal viewer for Data Package documentation sections."""

    CSS = """
    Screen {
        layout: vertical;
        background: ansi_default;
        color: ansi_default;
    }

    Header, Footer {
        background: #292E42;
        background-tint: ansi_default 0%;
        color: ansi_default;
    }

    FooterLabel, FooterKey {
        background: #292E42;
        background-tint: ansi_default 0%;
        color: ansi_default;
    }

    #body {
        height: 1fr;
        background: ansi_default;
    }

    #toc {
        width: 32;
        min-width: 24;
        height: 100%;
        background: #292E42;
        background-tint: ansi_default 0%;
        color: ansi_default;
        border-right: solid ansi_white;
    }

    #toc:focus {
        background-tint: ansi_default 0%;
    }

    #content-switcher {
        width: 1fr;
        height: 100%;
        padding: 0 1;
        background: ansi_default;
    }

    .content-page {
        width: 1fr;
        height: 100%;
    }

    ListItem {
        width: 100%;
    }

    ListItem > Label {
        width: 100%;
        padding: 0 1;
        color: ansi_default;
    }

    #toc > ListItem.-highlight {
        background: ansi_yellow;
        color: #1A1B26;
    }

    #toc > ListItem.-highlight > Label {
        background: ansi_yellow;
        color: #1A1B26;
    }

    #toc:focus > ListItem.-highlight {
        background: ansi_yellow;
        color: #1A1B26;
    }

    #toc:focus > ListItem.-highlight > Label {
        background: ansi_yellow;
        color: #1A1B26;
    }

    PageView {
        width: 1fr;
        height: 100%;
        background: ansi_default;
    }

    .body-text {
        margin: 0 0 1 0;
        color: ansi_default;
    }

    .metadata-list {
        margin: 0;
        color: ansi_default;
    }

    .title {
        margin: 0 0 1 0;
        color: ansi_blue;
        text-style: bold;
    }

    .subtitle {
        margin: 0 0 1 0;
    }

    .heading {
        margin: 1 0 0 0;
        color: ansi_yellow;
        text-style: bold;
    }

    .compact-heading {
        margin: 0;
        color: ansi_yellow;
        text-style: bold;
    }

    .field-table {
        width: 1fr;
        height: 1fr;
        min-height: 8;
        background: ansi_default;
        color: ansi_default;
    }

    .field-table > .datatable--header {
        background: ansi_default;
        color: ansi_blue;
        text-style: bold;
    }

    .field-table > .datatable--cursor {
        background: #292E42;
        color: ansi_default;
    }

    .table-caption {
        color: ansi_default;
        text-style: italic;
        margin: 0 0 1 0;
    }
    """
    BINDINGS = [
        ("j", "toc_down", "Down"),
        ("k", "toc_up", "Up"),
        ("q", "quit", "Quit"),
    ]
    TITLE = "Flower"

    def __init__(self, pages: list[ViewPage]) -> None:
        """Initialize the app with pages to display."""
        super().__init__(ansi_color=True)
        self.pages = pages

    def compose(self) -> ComposeResult:
        """Compose the page navigation and content widgets."""
        initial_page = self.pages[0]
        self.sub_title = initial_page.label
        yield Header()
        with Horizontal(id="body"):
            yield ListView(
                *[ListItem(Label(page.label)) for page in self.pages], id="toc"
            )
            with ContentSwitcher(id="content-switcher", initial=initial_page.id):
                for page in self.pages:
                    yield PageView(page.blocks, id=page.id, classes="content-page")
        yield Footer()

    def on_mount(self) -> None:
        """Focus page navigation when the app starts."""
        self.query_one("#toc", ListView).focus()

    async def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        """Show the highlighted page in the content pane."""
        index = event.list_view.index
        if index is not None:
            await self._show_page(index)

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Show the selected page in the content pane."""
        await self._show_page(event.index)

    def action_toc_down(self) -> None:
        """Move down in the page navigation."""
        self.query_one("#toc", ListView).action_cursor_down()

    def action_toc_up(self) -> None:
        """Move up in the page navigation."""
        self.query_one("#toc", ListView).action_cursor_up()

    async def _show_page(self, index: int) -> None:
        page = self.pages[index]
        self.sub_title = page.label
        self.query_one("#content-switcher", ContentSwitcher).current = page.id


def run_textual_viewer(properties: dict[str, Any]) -> None:
    """Run the interactive Textual viewer for Data Package properties."""
    FlowerViewApp(prepare_view_pages(properties)).run()


class PageView(VerticalScroll):
    """A cached Textual page composed from text and native tables."""

    def __init__(self, blocks: list[ViewBlock], **kwargs: object) -> None:
        """Initialize the page with prepared content blocks."""
        super().__init__(**kwargs)
        self.blocks = blocks

    def compose(self) -> ComposeResult:
        """Compose text fragments and DataTables for the page."""
        for block in self.blocks:
            if isinstance(block, TextBlock):
                text = Text(block.content, style=block.style)
                for start, end, style in block.spans:
                    text.stylize(style, start, end)
                yield Static(text, classes=block.classes)
            else:
                table = DataTable(
                    show_row_labels=False,
                    zebra_stripes=True,
                    cursor_type="row",
                    classes="field-table",
                )
                table.add_columns(*block.headers)
                table.add_rows(block.rows)
                yield table
                if block.caption:
                    yield Label(block.caption, classes="table-caption")
