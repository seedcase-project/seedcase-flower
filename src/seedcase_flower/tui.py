"""Textual terminal app for browsing built Data Package sections."""

from dataclasses import dataclass
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import (
    ContentSwitcher,
    Footer,
    Header,
    Label,
    ListItem,
    ListView,
    Markdown,
)

from seedcase_flower.build_sections import BuiltSection


@dataclass(frozen=True)
class ViewPage:
    """A built section prepared for navigation in the Textual viewer."""

    label: str
    content: str
    id: str


def prepare_view_pages(built_sections: list[BuiltSection]) -> list[ViewPage]:
    """Prepare built sections for display in the Textual viewer."""
    return [
        ViewPage(
            label=_section_label(section, index),
            content=_section_content(section.content),
            id=f"page-{index}",
        )
        for index, section in enumerate(built_sections, start=1)
    ]


def _section_label(section: BuiltSection, index: int) -> str:
    front_matter, _ = _split_front_matter(section.content)
    title = _front_matter_value(front_matter, "title")
    subtitle = _front_matter_value(front_matter, "subtitle").strip("`")
    if subtitle:
        return subtitle
    if title:
        return title
    if section.output_path:
        return _output_path_label(section.output_path)
    return f"Section {index}"


def _output_path_label(output_path: Path) -> str:
    if output_path.name == "index.qmd":
        return "Package"
    return output_path.stem.replace("_", " ").replace("-", " ").title()


def _section_content(content: str) -> str:
    front_matter, body = _split_front_matter(content)
    if not front_matter:
        return body

    headings = []
    title = _front_matter_value(front_matter, "title")
    subtitle = _front_matter_value(front_matter, "subtitle")
    if title:
        headings.append(f"# {title}")
    if subtitle:
        headings.append(f"## {subtitle}")

    if not headings:
        return body.lstrip()
    return "\n\n".join([*headings, body.lstrip()])


def _split_front_matter(content: str) -> tuple[list[str], str]:
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return [], content

    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return lines[1:index], "\n".join(lines[index + 1 :])

    return [], content


def _front_matter_value(front_matter: list[str], key: str) -> str:
    prefix = f"{key}:"
    for line in front_matter:
        if line.startswith(prefix):
            return line.removeprefix(prefix).strip().strip("\"'")
    return ""


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

    Markdown {
        background: ansi_default;
        color: ansi_default;
    }

    MarkdownBlock > .code_inline {
        color: ansi_yellow;
        background: ansi_default;
        text-style: bold;
    }

    MarkdownBlock > .strong {
        text-style: bold;
    }

    MarkdownBlock > .em {
        text-style: italic;
    }

    MarkdownBlockQuote {
        background: ansi_default;
        border-left: outer ansi_magenta;
        color: ansi_magenta;
    }

    MarkdownBullet {
        color: ansi_cyan;
    }

    MarkdownFence {
        color: ansi_cyan;
        background: ansi_black;
    }

    MarkdownHeader {
        margin: 1 0 0 0;
    }

    MarkdownH1 {
        content-align: left middle;
        color: ansi_blue;
        text-style: bold;
        margin: 0;
    }

    MarkdownH2 {
        color: ansi_yellow;
        text-style: bold;
        margin: 0 0 1 0;
    }

    MarkdownH3 {
        color: ansi_blue;
    }

    MarkdownH4 {
        color: ansi_magenta;
        text-style: italic;
    }

    MarkdownH5 {
        text-style: italic;
    }

    MarkdownH6 {
        text-opacity: 60%;
    }

    MarkdownHorizontalRule {
        border-bottom: solid ansi_white;
    }

    MarkdownTableContent {
        keyline: thin ansi_white;
    }

    MarkdownTableContent > .header {
        color: ansi_blue;
    }

    MarkdownTableContent > .markdown-table--header {
        color: ansi_blue;
        text-style: bold;
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
                    yield Markdown(page.content, id=page.id, classes="content-page")
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


def run_textual_viewer(built_sections: list[BuiltSection]) -> None:
    """Run the interactive Textual viewer for built sections."""
    FlowerViewApp(prepare_view_pages(built_sections)).run()
