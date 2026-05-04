"""Tests for the Textual viewer helpers."""

from pathlib import Path

from seedcase_flower.build_sections import BuiltSection
from seedcase_flower.tui import prepare_view_pages


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

    assert pages[0].label == "species_catalog: Species Catalog"
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
