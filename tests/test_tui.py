"""Tests for the Textual viewer helpers."""

import asyncio
import inspect
from pathlib import Path

from seedcase_flower.build_sections import BuiltSection
from seedcase_flower.tui import (
    FlowerViewApp,
    MarkdownBlock,
    PageView,
    TableBlock,
    ViewPage,
    prepare_view_pages,
)


def test_flower_view_app_has_vim_navigation_bindings():
    assert ("j", "toc_down", "Down") in FlowerViewApp.BINDINGS
    assert ("k", "toc_up", "Up") in FlowerViewApp.BINDINGS


def test_flower_view_app_pre_mounts_markdown_pages():
    assert "ContentSwitcher" in inspect.getsource(FlowerViewApp.compose)
    assert "#content-switcher" in FlowerViewApp.CSS
    assert ".content-page" in FlowerViewApp.CSS


def test_flower_view_app_styles_markdown_headings_like_terminal_output():
    assert "MarkdownH1" in FlowerViewApp.CSS
    assert "content-align: left middle" in FlowerViewApp.CSS
    assert "color: ansi_blue" in FlowerViewApp.CSS
    assert "MarkdownH2" in FlowerViewApp.CSS
    assert "color: ansi_yellow" in FlowerViewApp.CSS
    assert "MarkdownHeader" in FlowerViewApp.CSS
    assert "margin: 1 0 0 0" in FlowerViewApp.CSS
    assert "margin: 0 0 1 0" in FlowerViewApp.CSS


def test_flower_view_app_themes_chrome_and_full_width_toc_rows():
    assert "Header, Footer" in FlowerViewApp.CSS
    assert "FooterLabel, FooterKey" in FlowerViewApp.CSS
    assert "#toc" in FlowerViewApp.CSS
    assert "#toc:focus" in FlowerViewApp.CSS
    assert "background: #292E42" in FlowerViewApp.CSS
    assert "background-tint: ansi_default 0%" in FlowerViewApp.CSS
    assert "color: ansi_default" in FlowerViewApp.CSS
    assert "ListItem" in FlowerViewApp.CSS
    assert "width: 100%" in FlowerViewApp.CSS


def test_flower_view_app_maps_markdown_colors_to_ansi_terminal_styles():
    assert "background: ansi_default" in FlowerViewApp.CSS
    assert "MarkdownBlock > .code_inline" in FlowerViewApp.CSS
    assert "color: ansi_yellow" in FlowerViewApp.CSS
    assert "MarkdownFence" in FlowerViewApp.CSS
    assert "color: ansi_cyan" in FlowerViewApp.CSS
    assert "background: ansi_black" in FlowerViewApp.CSS
    assert "MarkdownBlockQuote" in FlowerViewApp.CSS
    assert "border-left: outer ansi_magenta" in FlowerViewApp.CSS
    assert "MarkdownBullet" in FlowerViewApp.CSS
    assert "MarkdownTableContent" in FlowerViewApp.CSS
    assert "keyline: thin ansi_white" in FlowerViewApp.CSS
    assert "MarkdownTableContent > .header" in FlowerViewApp.CSS


def test_flower_view_app_uses_native_datatables_for_tables():
    assert "DataTable" in inspect.getsource(PageView.compose)
    assert "field-table" in FlowerViewApp.CSS
    assert "table-caption" in FlowerViewApp.CSS


def test_prepare_view_pages_uses_package_label_for_index():
    pages = prepare_view_pages(
        [BuiltSection(content="# Test Package", output_path=Path("index.qmd"))]
    )

    assert pages[0].label == "Package"
    assert pages[0].content == "# Test Package"
    assert pages[0].id == "page-1"
    assert pages[0].blocks == [MarkdownBlock("# Test Package")]


def test_prepare_view_pages_uses_resource_front_matter_for_label_and_content():
    pages = prepare_view_pages(
        [
            BuiltSection(
                content=(
                    "---\n"
                    'title: "Species Catalog"\n'
                    'subtitle: "`species_catalog`"\n'
                    'description: "Resource description"\n'
                    "---\n\n"
                    "- Path: `data/species.csv`"
                ),
                output_path=Path("resources/species_catalog.qmd"),
            )
        ]
    )

    assert pages[0].label == "species_catalog"
    assert pages[0].id == "page-1"
    assert "title:" not in pages[0].content
    assert "description:" not in pages[0].content
    assert "# Species Catalog" in pages[0].content
    assert "## `species_catalog`" in pages[0].content
    assert "- Path: `data/species.csv`" in pages[0].content
    assert pages[0].blocks == [
        MarkdownBlock(
            "# Species Catalog\n\n## `species_catalog`\n\n- Path: `data/species.csv`"
        )
    ]


def test_prepare_view_pages_extracts_markdown_tables_into_table_blocks():
    pages = prepare_view_pages(
        [
            BuiltSection(
                content=(
                    "# Resource\n\n"
                    "| Name | Type |\n"
                    "|------|------|\n"
                    "| `id` | integer |\n"
                    "| `name` | string |\n\n"
                    ": Fields in the resource."
                ),
                output_path=Path("resources/data.qmd"),
            )
        ]
    )

    assert pages[0].blocks == [
        MarkdownBlock("# Resource"),
        TableBlock(
            headers=["Name", "Type"],
            rows=[["`id`", "integer"], ["`name`", "string"]],
            caption="Fields in the resource.",
        ),
    ]


def test_prepare_view_pages_falls_back_to_output_stem():
    pages = prepare_view_pages(
        [
            BuiltSection(
                content="Resource details",
                output_path=Path("resources/growth-records.qmd"),
            )
        ]
    )

    assert pages[0].label == "Growth Records"


def test_flower_view_app_switches_between_pre_mounted_pages():
    async def run_test() -> None:
        app = FlowerViewApp(
            [
                ViewPage(
                    label="Package",
                    content="# Package",
                    id="page-1",
                    blocks=[MarkdownBlock("# Package")],
                ),
                ViewPage(
                    label="species_catalog",
                    content="# Species",
                    id="page-2",
                    blocks=[MarkdownBlock("# Species")],
                ),
            ]
        )

        async with app.run_test():
            await app._show_page(1)

            assert app.sub_title == "species_catalog"
            assert app.query_one("#content-switcher").current == "page-2"

    asyncio.run(run_test())


def test_flower_view_app_does_not_update_markdown_on_page_switch():
    async def run_test() -> None:
        app = FlowerViewApp(
            [
                ViewPage(
                    label="Package",
                    content="# Package",
                    id="page-1",
                    blocks=[MarkdownBlock("# Package")],
                ),
                ViewPage(
                    label="species_catalog",
                    content="# Species",
                    id="page-2",
                    blocks=[MarkdownBlock("# Species")],
                ),
            ]
        )

        async with app.run_test():
            markdown = app.query_one("#page-2")
            markdown.update = None  # type: ignore[method-assign]
            await app._show_page(1)

            assert app.query_one("#content-switcher").current == "page-2"

    asyncio.run(run_test())
