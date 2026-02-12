"""These are integration tests for the CLI commands."""

from pytest import mark
from seedcase_flower.cli import build, view


@mark.parametrize(
    "style, expected",
    [
        (None, "Setting style from config (or default if no file found)"),
        ("quarto_one_page", "Style supported!"),
        ("unsupported_style", "Style not supported for `build`. Should be one of"),
    ],
)
def test_build(style, expected) -> None:
    """Test the build CLI function."""
    result = build(style=style)
    assert result.startswith(expected)


def test_view() -> None:
    """Test the view CLI function."""
    result = view()
    assert result == ""
