"""Tests for the Textual viewer helpers."""

import asyncio
import inspect

from seedcase_flower.tui import (
    FlowerViewApp,
    PageView,
    SearchableDataTable,
    TableBlock,
    TextBlock,
    ViewPage,
    prepare_view_pages,
)


def test_flower_view_app_has_vim_navigation_bindings():
    assert ("j", "toc_down", "Down") in FlowerViewApp.BINDINGS
    assert ("k", "toc_up", "Up") in FlowerViewApp.BINDINGS
    assert ("/", "search_table", "Search table") in FlowerViewApp.BINDINGS
    assert ("s", "sort_table", "Sort table") in FlowerViewApp.BINDINGS
    assert ("escape", "clear_search", "Clear search") in FlowerViewApp.BINDINGS


def test_flower_view_app_pre_mounts_pages():
    assert "ContentSwitcher" in inspect.getsource(FlowerViewApp.compose)
    assert "#content-switcher" in FlowerViewApp.CSS
    assert ".content-page" in FlowerViewApp.CSS


def test_flower_view_app_uses_native_datatables_for_tables():
    assert "DataTable" in inspect.getsource(PageView.compose)
    assert "SearchableDataTable" in inspect.getsource(PageView.compose)
    assert "field-table" in FlowerViewApp.CSS
    assert "table-caption" in FlowerViewApp.CSS
    assert "#table-search" in FlowerViewApp.CSS
    assert "color: ansi_yellow" in FlowerViewApp.CSS
    assert "border: solid ansi_yellow" in FlowerViewApp.CSS


def test_flower_view_app_themes_chrome_and_full_width_toc_rows():
    assert "Header, Footer" in FlowerViewApp.CSS
    assert "FooterLabel, FooterKey" in FlowerViewApp.CSS
    assert "#toc" in FlowerViewApp.CSS
    assert "#toc:focus" in FlowerViewApp.CSS
    assert "background: #292E42" in FlowerViewApp.CSS
    assert "background-tint: ansi_default 0%" in FlowerViewApp.CSS
    assert "color: ansi_default" in FlowerViewApp.CSS
    assert "ListItem" in FlowerViewApp.CSS
    assert "#toc > ListItem.-highlight" in FlowerViewApp.CSS
    assert "background: ansi_yellow" in FlowerViewApp.CSS
    assert "color: #1A1B26" in FlowerViewApp.CSS
    assert "color: $footer-key-foreground" not in FlowerViewApp.CSS
    assert "width: 100%" in FlowerViewApp.CSS
    assert ".title" in FlowerViewApp.CSS
    assert ".compact-list" not in FlowerViewApp.CSS
    assert ".metadata-list" in FlowerViewApp.CSS
    assert ".compact-heading" in FlowerViewApp.CSS
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
        TextBlock("A test package."),
        TextBlock(
            "Version\n• 1.0.0",
            classes="metadata-list",
            spans=((0, 7, "color(3) bold"),),
        ),
        TextBlock("Licenses", style="color(3) bold", classes="compact-heading"),
        TextBlock("• MIT", classes="metadata-list"),
        TextBlock("Contributors", style="color(3) bold", classes="compact-heading"),
        TextBlock("• Ada: author", classes="metadata-list"),
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
            "Path\n• data/species.csv",
            classes="metadata-list",
            spans=((0, 4, "color(3) bold"),),
        ),
        TextBlock(
            "Primary key\n• id",
            classes="metadata-list",
            spans=((0, 11, "color(3) bold"),),
        ),
        TextBlock("Fields", style="color(3) bold", classes="heading"),
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

    assert pages[1].blocks[0] == TextBlock(
        "plots", style="color(4) bold", classes="title"
    )
    assert (
        TextBlock(
            "Foreign keys\n• species_id → species.id",
            classes="metadata-list",
            spans=((0, 12, "color(3) bold"),),
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
    assert pages[1].blocks == [
        TextBlock("species_catalog", style="color(4) bold", classes="title")
    ]


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


def test_flower_view_app_debounces_highlight_navigation():
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
                ViewPage(
                    label="location_catalog",
                    id="page-3",
                    blocks=[TextBlock("Locations")],
                ),
            ]
        )

        async with app.run_test() as pilot:
            app.action_toc_down()
            app.action_toc_down()

            assert app.query_one("#content-switcher").current == "page-1"

            await pilot.pause(0.15)

            assert app.sub_title == "location_catalog"
            assert app.query_one("#content-switcher").current == "page-3"

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


def test_flower_view_app_filters_current_page_table():
    async def run_test() -> None:
        app = FlowerViewApp(
            [
                ViewPage(
                    label="Package",
                    id="page-1",
                    blocks=[
                        TableBlock(
                            headers=["Name", "Type"],
                            rows=[
                                ["species", "string"],
                                ["plot_id", "integer"],
                            ],
                        )
                    ],
                )
            ]
        )

        async with app.run_test() as pilot:
            table = app.query_one(SearchableDataTable)

            app.action_search_table()
            assert app.query_one("#table-search").placeholder == "Search all tables"
            await pilot.press("s", "p")

            assert table.row_count == 1
            assert table.get_row_at(0) == ["species", "string"]

            app.action_clear_search()

            assert table.row_count == 2

    asyncio.run(run_test())


def test_flower_view_app_filters_sidebar_to_matching_resource_tables():
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
                    blocks=[
                        TableBlock(
                            headers=["Name"],
                            rows=[["species"]],
                        )
                    ],
                ),
                ViewPage(
                    label="location_catalog",
                    id="page-3",
                    blocks=[
                        TableBlock(
                            headers=["Name"],
                            rows=[["location"]],
                        )
                    ],
                ),
            ]
        )

        async with app.run_test() as pilot:
            app.action_search_table()
            await pilot.press("s", "p")

            toc_items = app.query_one("#toc").children
            assert toc_items[0].display is True
            assert toc_items[1].display is True
            assert toc_items[2].display is False

            toc = app.query_one("#toc")
            app.action_toc_down()
            assert toc.index == 1

            app.action_toc_down()
            assert toc.index == 1

            app.action_toc_up()
            assert toc.index == 0

            app.action_clear_search()

            assert all(item.display is True for item in toc_items)

    asyncio.run(run_test())


def test_flower_view_app_sorts_current_page_table():
    async def run_test() -> None:
        app = FlowerViewApp(
            [
                ViewPage(
                    label="Package",
                    id="page-1",
                    blocks=[
                        TableBlock(
                            headers=["Name", "Type"],
                            rows=[
                                ["species", "string"],
                                ["plot_id", "integer"],
                            ],
                        )
                    ],
                )
            ]
        )

        async with app.run_test():
            table = app.query_one(SearchableDataTable)
            initial_width = table.columns["Name"].width

            app.action_sort_table()

            assert table.get_row_at(0) == ["plot_id", "integer"]
            assert table.columns["Name"].label.plain == "Name ↑"
            assert table.columns["Name"].width >= initial_width
            assert str(table.columns["Name"].label.spans[0].style) == "color(3) bold"

            app.action_sort_table()
            assert table.get_row_at(0) == ["species", "string"]
            assert table.columns["Name"].label.plain == "Name ↓"

            app.action_sort_table()
            assert table.get_row_at(0) == ["plot_id", "integer"]
            assert table.columns["Name"].label.plain == "Name"
            assert table.columns["Type"].label.plain == "Type ↑"

    asyncio.run(run_test())
