"""Module containing only the functions for the exposed CLI."""

from pathlib import Path


def build() -> Path:
    """Build the flower dataset."""
    # mypy doesn't like returning None (design is to return None)
    return Path(".")


def view() -> str:
    """View the flower dataset."""
    return ""
