"""Textual terminal app for browsing Data Package metadata."""

from dataclasses import dataclass
from typing import Any

from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.timer import Timer
from textual.widgets import (
    ContentSwitcher,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    Static,
)

RICH_BLUE = "color(4) bold"
RICH_YELLOW = "color(3) bold"
HIGHLIGHT_DEBOUNCE_SECONDS = 0.1


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

    #table-search {
        display: none;
        height: 3;
        background: #292E42;
        color: ansi_yellow;
        text-style: bold;
        border: solid ansi_yellow;
    }
    """
    BINDINGS = [
        ("/", "search_table", "Search table"),
        ("s", "sort_table", "Sort table"),
        ("escape", "clear_search", "Clear search"),
        ("j", "toc_down", "Down"),
        ("k", "toc_up", "Up"),
        ("q", "quit", "Quit"),
    ]
    TITLE = "Flower"

    def __init__(self, pages: list[ViewPage]) -> None:
        """Initialize the app with pages to display."""
        super().__init__(ansi_color=True)
        self.pages = pages
        self._pending_page_index: int | None = None
        self._highlight_timer: Timer | None = None

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
        yield Input(placeholder="Search all tables", id="table-search")
        yield Footer()

    def on_mount(self) -> None:
        """Focus page navigation when the app starts."""
        self.query_one("#toc", ListView).focus()

    async def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        """Show the highlighted page in the content pane."""
        index = event.list_view.index
        if index is not None:
            self._pending_page_index = index
            if self._highlight_timer is not None:
                self._highlight_timer.stop()
            self._highlight_timer = self.set_timer(
                HIGHLIGHT_DEBOUNCE_SECONDS,
                self._show_pending_page,
            )

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Show the selected page in the content pane."""
        if self._highlight_timer is not None:
            self._highlight_timer.stop()
        self._pending_page_index = None
        await self._show_page(event.index)

    def action_toc_down(self) -> None:
        """Move down in the page navigation."""
        self._move_toc(1)

    def action_toc_up(self) -> None:
        """Move up in the page navigation."""
        self._move_toc(-1)

    def _move_toc(self, step: int) -> None:
        """Move to the next visible table-of-contents item."""
        toc = self.query_one("#toc", ListView)
        visible_indices = self._visible_toc_indices()
        if not visible_indices:
            return

        current = toc.index
        if current is None or current not in visible_indices:
            toc.index = visible_indices[0 if step > 0 else -1]
            return

        current_position = visible_indices.index(current)
        next_position = max(
            0,
            min(len(visible_indices) - 1, current_position + step),
        )
        toc.index = visible_indices[next_position]

    def action_search_table(self) -> None:
        """Focus the table search input."""
        search = self.query_one("#table-search", Input)
        search.display = True
        search.focus()

    def action_sort_table(self) -> None:
        """Sort the current page table by the next column."""
        if table := self._current_table():
            table.sort_next_column()

    def action_clear_search(self) -> None:
        """Clear table filtering and hide the search input."""
        search = self.query_one("#table-search", Input)
        search.value = ""
        search.display = False
        self._filter_all_tables("")
        self.query_one("#toc", ListView).focus()

    async def on_input_changed(self, event: Input.Changed) -> None:
        """Filter the current page table while typing in the search input."""
        if event.input.id == "table-search":
            visible_pages = self._filter_all_tables(event.value)
            if visible_pages and self._current_page_index() not in visible_pages:
                self.query_one("#toc", ListView).index = visible_pages[0]
                await self._show_page(visible_pages[0])

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Return focus to navigation after submitting table search."""
        if event.input.id == "table-search":
            self.query_one("#toc", ListView).focus()

    async def _show_pending_page(self) -> None:
        """Show the latest highlighted page after a short navigation debounce."""
        if self._pending_page_index is not None:
            await self._show_page(self._pending_page_index)
            self._pending_page_index = None
        self._highlight_timer = None

    async def _show_page(self, index: int) -> None:
        page = self.pages[index]
        self.sub_title = page.label
        self.query_one("#content-switcher", ContentSwitcher).current = page.id
        search = self.query_one("#table-search", Input)
        if table := self._current_table():
            table.filter_rows(search.value)

    def _filter_all_tables(self, query: str) -> list[int]:
        """Filter all mounted tables and return visible page indices."""
        for table in self.query(SearchableDataTable):
            table.filter_rows(query)

        visible_pages = []
        toc = self.query_one("#toc", ListView)
        for index, item in enumerate(toc.children):
            page = self.query_one(f"#{self.pages[index].id}", PageView)
            tables = page.query(SearchableDataTable)
            is_visible = (
                not query or index == 0 or any(table.row_count > 0 for table in tables)
            )
            item.display = is_visible
            if is_visible:
                visible_pages.append(index)
        return visible_pages

    def _visible_toc_indices(self) -> list[int]:
        """Return indices for visible table-of-contents items."""
        toc = self.query_one("#toc", ListView)
        return [
            index
            for index, item in enumerate(toc.children)
            if item.display is not False
        ]

    def _current_page_index(self) -> int | None:
        """Return the index of the currently visible page."""
        current = self.query_one("#content-switcher", ContentSwitcher).current
        for index, page in enumerate(self.pages):
            if page.id == current:
                return index
        return None

    def _current_table(self) -> "SearchableDataTable | None":
        """Return the first table on the currently visible page."""
        switcher = self.query_one("#content-switcher", ContentSwitcher)
        if not switcher.current:
            return None
        page = self.query_one(f"#{switcher.current}", PageView)
        tables = page.query(SearchableDataTable)
        return tables.first() if tables else None


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
                table = SearchableDataTable(block)
                yield table
                if block.caption:
                    yield Label(block.caption, classes="table-caption")


class SearchableDataTable(DataTable[str]):
    """DataTable with simple current-page sorting and row filtering."""

    def __init__(self, block: TableBlock) -> None:
        """Initialize a table from prepared table data."""
        super().__init__(
            show_row_labels=False,
            zebra_stripes=True,
            cursor_type="row",
            classes="field-table",
        )
        self.headers = block.headers
        self.all_rows = block.rows
        self._sort_column_index: int | None = None
        self._sort_reverse = False

    def on_mount(self) -> None:
        """Populate the table once it has app context for measuring columns."""
        for header in self.headers:
            self.add_column(header, key=header)
        self.filter_rows("")

    def filter_rows(self, query: str) -> None:
        """Show only rows that contain the query text."""
        normalized_query = query.casefold()
        rows = [
            row
            for row in self.all_rows
            if not normalized_query
            or normalized_query in " ".join(str(cell) for cell in row).casefold()
        ]
        self.clear()
        self.add_rows(rows)
        if self._sort_column_index is not None:
            self._sort_by_column(self._sort_column_index)

    def sort_next_column(self) -> None:
        """Sort rows by columns, toggling direction before moving on."""
        if not self.headers:
            return
        if self._sort_column_index is None:
            self._sort_column_index = 0
            self._sort_reverse = False
        elif not self._sort_reverse:
            self._sort_reverse = True
        else:
            self._sort_column_index = (self._sort_column_index + 1) % len(self.headers)
            self._sort_reverse = False
        self._sort_by_column(self._sort_column_index)

    def _sort_by_column(self, column_index: int) -> None:
        """Sort rows case-insensitively by one column."""
        self._refresh_sort_indicators()
        self.sort(
            self.headers[column_index],
            key=lambda value: str(value).casefold(),
            reverse=self._sort_reverse,
        )

    def _refresh_sort_indicators(self) -> None:
        """Show the active sort column and direction in table headers."""
        for column_index, header in enumerate(self.headers):
            label = Text(header)
            if column_index == self._sort_column_index:
                label.append(" ")
                label.append("↓" if self._sort_reverse else "↑", style=RICH_YELLOW)
            column = self.columns[header]
            column.label = label
            label_width = len(label.plain)
            column.content_width = max(column.content_width, label_width)
            if column.auto_width:
                column.width = max(column.width, label_width)
            self.refresh_column(column_index)
