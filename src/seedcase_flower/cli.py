"""Module containing only the functions for the exposed CLI."""

from pathlib import Path


def build() -> Path:
    """Build human-friendly documentation from a `datapackage.json` file."""
    # mypy doesn't like returning None (design is to return None)
    return Path(".")


def view() -> str:
    """Display the contents of a `datapackage.json` in a human-friendly way."""
    return ""
