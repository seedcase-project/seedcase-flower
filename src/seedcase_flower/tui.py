"""Textual terminal app for browsing Data Package metadata."""

from dataclasses import dataclass
from typing import Any

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
    classes: str = "body-text"


@dataclass(frozen=True)
class TableBlock:
    """Structured table data prepared for Textual's DataTable."""

    headers: list[str]
    rows: list[list[str]]


type ViewBlock = TextBlock | TableBlock


def prepare_view_pages(properties: dict[str, Any]) -> list[ViewPage]:
    """Prepare Data Package properties for display in the Textual viewer."""
    pages = [ViewPage(label="Package", id="page-1", blocks=_package_blocks(properties))]
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
    if title := _package_title(properties):
        blocks.append(TextBlock(title, classes="title"))
    if description := properties.get("description"):
        blocks.append(TextBlock(description))
    if resources := properties.get("resources"):
        blocks.append(TextBlock("Resources", classes="heading"))
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


def _resource_blocks(resource: dict[str, Any]) -> list[ViewBlock]:
    blocks: list[ViewBlock] = []
    if title := resource.get("title") or resource.get("name"):
        blocks.append(TextBlock(title, classes="title"))
    if description := resource.get("description"):
        blocks.append(TextBlock(description))
    schema = resource.get("schema") or {}
    if path := resource.get("path"):
        blocks.append(TextBlock(f"Path: {path}"))
    if primary_key := schema.get("primaryKey"):
        blocks.append(TextBlock(f"Primary key: {_as_list_text(primary_key)}"))
    if fields := schema.get("fields"):
        blocks.append(TextBlock("Fields", classes="heading"))
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
            )
        )
    return blocks


def _package_title(properties: dict[str, Any]) -> str:
    name = properties.get("name")
    title = properties.get("title")
    if name and title:
        return f"{name}: {title}"
    return name or title or ""


def _as_list_text(value: str | list[str]) -> str:
    return value if isinstance(value, str) else ", ".join(value)


class FlowerViewApp(App[None]):
    """Interactive terminal viewer for Data Package metadata."""

    CSS = """
    Screen {
        layout: vertical;
    }

    #body {
        height: 1fr;
    }

    #toc {
        width: 32;
        min-width: 24;
        height: 100%;
        border-right: solid $foreground;
    }

    #content-switcher {
        width: 1fr;
        height: 100%;
        padding: 0 1;
    }

    .content-page {
        width: 1fr;
        height: 100%;
    }

    .body-text {
        margin: 0 0 1 0;
    }

    .title {
        margin: 0 0 1 0;
        text-style: bold;
    }

    .heading {
        margin: 1 0 0 0;
        text-style: bold;
    }

    .field-table {
        width: 1fr;
        height: 1fr;
        min-height: 8;
    }
    """
    BINDINGS = [("q", "quit", "Quit")]
    TITLE = "Flower"

    def __init__(self, pages: list[ViewPage]) -> None:
        """Initialize the app with pages to display."""
        super().__init__()
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
                yield Static(block.content, classes=block.classes)
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
