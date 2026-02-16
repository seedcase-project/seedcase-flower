"""These are integration tests for the CLI commands."""

import json

from pytest import fixture, mark

from seedcase_flower.cli import Style, build, view


# Create a file at tmp_path that is automatically cleaned up after tests finish
@fixture
def datapackage_path(tmp_path):
    data = {
        "name": "placeholder",
        "created": "2026-02-12T11:25:49+01:00",
        "description": "Placeholder",
        "id": "Placeholder",
        "licenses": [{"name": "Placeholder"}],
        "title": "Placeholder",
        "version": "0.0.0",
    }

    file_path = tmp_path / "datapackage.json"
    file_path.write_text(json.dumps(data))

    # Since `build` expects a str as the URI
    return str(file_path)


@mark.parametrize(
    "style, expected",
    [
        (None, ""),
        (Style.quarto_one_page, ""),
    ],
)
def test_build(
    datapackage_path: str,
    style: Style | None,
    expected: str,
) -> None:
    """Test the build CLI function."""
    result = build(datapackage_path, style=style)
    assert result == expected


def test_view() -> None:
    """Test the view CLI function."""
    result = view()
    assert result == ""
