"""Tests for the Textual viewer helpers."""

from pathlib import Path

from seedcase_flower.build_sections import BuiltSection
from seedcase_flower.tui import FlowerViewApp, prepare_view_pages


def test_flower_view_app_has_vim_navigation_bindings():
    assert ("j", "toc_down", "Down") in FlowerViewApp.BINDINGS
    assert ("k", "toc_up", "Up") in FlowerViewApp.BINDINGS


def test_flower_view_app_styles_markdown_headings_like_terminal_output():
    assert "MarkdownH1" in FlowerViewApp.CSS
    assert "content-align: left middle" in FlowerViewApp.CSS
    assert "color: ansi_blue" in FlowerViewApp.CSS
    assert "MarkdownH2" in FlowerViewApp.CSS
    assert "color: ansi_yellow" in FlowerViewApp.CSS
    assert "MarkdownHeader" in FlowerViewApp.CSS
    assert "margin: 1 0 0 0" in FlowerViewApp.CSS


def test_flower_view_app_themes_chrome_like_main_panel():
    assert "Header, Footer" in FlowerViewApp.CSS
    assert "#toc" in FlowerViewApp.CSS
    assert "background: ansi_default" in FlowerViewApp.CSS
    assert "color: ansi_default" in FlowerViewApp.CSS


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


def test_prepare_view_pages_uses_package_label_for_index():
    pages = prepare_view_pages(
        [BuiltSection(content="# Test Package", output_path=Path("index.qmd"))]
    )

    assert pages[0].label == "Package"
    assert pages[0].content == "# Test Package"


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
    assert "title:" not in pages[0].content
    assert "description:" not in pages[0].content
    assert "# Species Catalog" in pages[0].content
    assert "## `species_catalog`" in pages[0].content
    assert "- Path: `data/species.csv`" in pages[0].content


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
