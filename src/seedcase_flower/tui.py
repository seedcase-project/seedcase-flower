"""Textual terminal app for browsing built Data Package sections."""

from dataclasses import dataclass
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Footer, Header, Label, ListItem, ListView, Markdown

from seedcase_flower.build_sections import BuiltSection


@dataclass(frozen=True)
class ViewPage:
    """A built section prepared for navigation in the Textual viewer."""

    label: str
    content: str


def prepare_view_pages(built_sections: list[BuiltSection]) -> list[ViewPage]:
    """Prepare built sections for display in the Textual viewer."""
    return [
        ViewPage(
            label=_section_label(section, index),
            content=_section_content(section.content),
        )
        for index, section in enumerate(built_sections, start=1)
    ]


def _section_label(section: BuiltSection, index: int) -> str:
    front_matter, _ = _split_front_matter(section.content)
    title = _front_matter_value(front_matter, "title")
    subtitle = _front_matter_value(front_matter, "subtitle").strip("`")
    if title and subtitle:
        return f"{subtitle}: {title}"
    if title or subtitle:
        return title or subtitle
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
    }

    #body {
        height: 1fr;
    }

    #toc {
        width: 32;
        min-width: 24;
        height: 100%;
        border-right: solid $primary;
    }

    #content {
        width: 1fr;
        height: 100%;
        padding: 0 1;
    }

    ListItem > Label {
        padding: 0 1;
    }
    """
    BINDINGS = [("q", "quit", "Quit")]
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
            yield Markdown(initial_page.content, id="content")
        yield Footer()

    def on_mount(self) -> None:
        """Focus page navigation when the app starts."""
        self.query_one("#toc", ListView).focus()

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Show the selected page in the content pane."""
        page = self.pages[event.index]
        self.sub_title = page.label
        await self.query_one("#content", Markdown).update(page.content)


def run_textual_viewer(built_sections: list[BuiltSection]) -> None:
    """Run the interactive Textual viewer for built sections."""
    FlowerViewApp(prepare_view_pages(built_sections)).run()
