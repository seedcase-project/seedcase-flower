"""Tests for the Textual viewer helpers."""

import asyncio
import inspect

from seedcase_flower.tui import (
    FlowerViewApp,
    PageView,
    TableBlock,
    TextBlock,
    ViewPage,
    prepare_view_pages,
)


def test_flower_view_app_has_vim_navigation_bindings():
    assert ("j", "toc_down", "Down") in FlowerViewApp.BINDINGS
    assert ("k", "toc_up", "Up") in FlowerViewApp.BINDINGS


def test_flower_view_app_pre_mounts_pages():
    assert "ContentSwitcher" in inspect.getsource(FlowerViewApp.compose)
    assert "#content-switcher" in FlowerViewApp.CSS
    assert ".content-page" in FlowerViewApp.CSS


def test_flower_view_app_uses_native_datatables_for_tables():
    assert "DataTable" in inspect.getsource(PageView.compose)
    assert "field-table" in FlowerViewApp.CSS
    assert "table-caption" in FlowerViewApp.CSS


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
    assert ".title" in FlowerViewApp.CSS
    assert ".compact-list" in FlowerViewApp.CSS
    assert "margin: 0 0 1 0" in FlowerViewApp.CSS


def test_prepare_view_pages_builds_package_page_from_properties():
    pages = prepare_view_pages(
        {
            "name": "test-package",
            "title": "Test Package",
            "version": "1.0.0",
            "description": "A test package.",
            "licenses": [{"name": "MIT"}],
            "contributors": [{"title": "Ada", "roles": ["author"]}],
            "resources": [
                {
                    "name": "species_catalog",
                    "title": "Species Catalog",
                    "description": "Species metadata.",
                }
            ],
        }
    )

    assert pages[0].label == "Package"
    assert pages[0].id == "page-1"
    assert pages[0].blocks == [
        TextBlock("test-package: Test Package", style="color(4) bold", classes="title"),
        TextBlock(
            "Licenses: MIT\nVersion: 1.0.0",
            spans=((10, 13, "color(3) bold"), (23, 28, "color(3) bold")),
        ),
        TextBlock("A test package."),
        TextBlock("Contributors", style="color(3) bold", classes="heading"),
        TextBlock("• Ada: author"),
        TextBlock("Resources", style="color(3) bold", classes="heading"),
        TableBlock(
            headers=["Name", "Title", "Description"],
            rows=[["species_catalog", "Species Catalog", "Species metadata."]],
        ),
    ]


def test_prepare_view_pages_builds_resource_page_from_properties():
    pages = prepare_view_pages(
        {
            "name": "test-package",
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
                            },
                            {
                                "name": "species",
                                "title": "Species",
                                "type": "string",
                                "description": "Scientific name.",
                            },
                        ],
                    },
                }
            ],
        }
    )

    assert pages[1].label == "species_catalog"
    assert pages[1].id == "page-2"
    assert pages[1].blocks == [
        TextBlock("Species Catalog", style="color(4) bold", classes="title"),
        TextBlock("Species metadata."),
        TextBlock(
            "• Path: data/species.csv\n• Primary key: id",
            classes="compact-list",
            spans=((8, 24, "color(3) bold"), (40, 42, "color(3) bold")),
        ),
        TableBlock(
            headers=["Name", "Title", "Type", "Description"],
            rows=[
                ["id", "Identifier", "integer", "Stable identifier."],
                ["species", "Species", "string", "Scientific name."],
            ],
            caption="Fields in the species_catalog resource.",
        ),
    ]


def test_prepare_view_pages_handles_foreign_keys():
    pages = prepare_view_pages(
        {
            "name": "test-package",
            "resources": [
                {
                    "name": "plots",
                    "schema": {
                        "foreignKeys": [
                            {
                                "fields": ["species_id"],
                                "reference": {
                                    "resource": "species",
                                    "fields": ["id"],
                                },
                            }
                        ]
                    },
                }
            ],
        }
    )

    assert (
        TextBlock(
            "• Foreign keys:\n  ◦ species_id -> species.id",
            classes="compact-list",
            spans=((20, 44, "color(3) bold"),),
        )
        in pages[1].blocks
    )


def test_prepare_view_pages_omits_resource_name_from_main_content():
    pages = prepare_view_pages(
        {
            "name": "test-package",
            "resources": [
                {
                    "name": "species_catalog",
                    "title": "species_catalog",
                    "description": "`species_catalog`",
                    "schema": {"fields": []},
                }
            ],
        }
    )

    assert pages[1].label == "species_catalog"
    assert pages[1].blocks == []


def test_flower_view_app_switches_between_pre_mounted_pages():
    async def run_test() -> None:
        app = FlowerViewApp(
            [
                ViewPage(
                    label="Package",
                    id="page-1",
                    blocks=[TextBlock("Package")],
                ),
                ViewPage(
                    label="species_catalog",
                    id="page-2",
                    blocks=[TextBlock("Species")],
                ),
            ]
        )

        async with app.run_test():
            await app._show_page(1)

            assert app.sub_title == "species_catalog"
            assert app.query_one("#content-switcher").current == "page-2"

    asyncio.run(run_test())


def test_flower_view_app_does_not_update_page_on_switch():
    async def run_test() -> None:
        app = FlowerViewApp(
            [
                ViewPage(
                    label="Package",
                    id="page-1",
                    blocks=[TextBlock("Package")],
                ),
                ViewPage(
                    label="species_catalog",
                    id="page-2",
                    blocks=[TextBlock("Species")],
                ),
            ]
        )

        async with app.run_test():
            page = app.query_one("#page-2")
            page.remove = None  # type: ignore[method-assign]
            await app._show_page(1)

            assert app.query_one("#content-switcher").current == "page-2"

    asyncio.run(run_test())
