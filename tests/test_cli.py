"""These are integration tests for the CLI commands."""

from pathlib import Path

from seedcase_flower.cli import build, view


def test_build() -> None:
    """Test the build CLI function."""
    result = build()
    assert result == Path(".")


def test_view() -> None:
    """Test the view CLI function."""
    result = view()
    assert result == ""
