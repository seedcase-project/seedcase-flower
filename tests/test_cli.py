"""These are integration tests for the CLI commands."""

from pytest import mark

from seedcase_flower.cli import BuildStyle, build, view


@mark.parametrize(
    "style, expected",
    [
        (None, "Setting style from config (or default if no file found)"),
        (BuildStyle.quarto_one_page, "Style supported!"),
    ],
)
def test_build(style: BuildStyle | None, expected: str) -> None:
    """Test the build CLI function."""
    result = build(style=style)
    assert result == expected


def test_view() -> None:
    """Test the view CLI function."""
    result = view()
    assert result == ""
