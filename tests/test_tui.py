"""Tests for the Textual viewer helpers."""

import asyncio
import inspect

from textual.widgets import ContentSwitcher

from seedcase_flower.tui import (
    FlowerViewApp,
    PageView,
    TableBlock,
    TextBlock,
    ViewPage,
    prepare_view_pages,
)


def test_prepare_view_pages_builds_package_and_resource_pages():
    pages = prepare_view_pages(
        {
            "name": "test-package",
            "title": "Test Package",
            "description": "A test package.",
            "resources": [
                {
                    "name": "species_catalog",
                    "title": "Species Catalog",
                    "description": "Species metadata.",
                    "path": "data/species.csv",
                    "schema": {
                        "primaryKey": "id",
                        "fields": [
                            {
                                "name": "id",
                                "title": "Identifier",
                                "type": "integer",
                                "description": "Stable identifier.",
                            }
                        ],
                    },
                }
            ],
        }
    )

    assert pages == [
        ViewPage(
            label="Package",
            id="page-1",
            blocks=[
                TextBlock("test-package: Test Package", classes="title"),
                TextBlock("A test package."),
                TextBlock("Resources", classes="heading"),
                TableBlock(
                    headers=["Name", "Title", "Description"],
                    rows=[["species_catalog", "Species Catalog", "Species metadata."]],
                ),
            ],
        ),
        ViewPage(
            label="species_catalog",
            id="page-2",
            blocks=[
                TextBlock("Species Catalog", classes="title"),
                TextBlock("Species metadata."),
                TextBlock("Path: data/species.csv"),
                TextBlock("Primary key: id"),
                TextBlock("Fields", classes="heading"),
                TableBlock(
                    headers=["Name", "Title", "Type", "Description"],
                    rows=[["id", "Identifier", "integer", "Stable identifier."]],
                ),
            ],
        ),
    ]


def test_flower_view_app_uses_content_switcher_and_datatables():
    assert "ContentSwitcher" in inspect.getsource(FlowerViewApp.compose)
    assert "DataTable" in inspect.getsource(PageView.compose)
    assert "field-table" in FlowerViewApp.CSS


def test_flower_view_app_switches_between_pages():
    async def run_test() -> None:
        app = FlowerViewApp(
            [
                ViewPage("Package", "page-1", [TextBlock("Package")]),
                ViewPage("species_catalog", "page-2", [TextBlock("Species")]),
            ]
        )

        async with app.run_test():
            await app._show_page(1)

            assert app.sub_title == "species_catalog"
            assert (
                app.query_one("#content-switcher", ContentSwitcher).current == "page-2"
            )

    asyncio.run(run_test())
