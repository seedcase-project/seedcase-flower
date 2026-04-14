"""Helper functions for internal use."""

from typing import Any

__all__ = ["_number"]


def _number(value: str, items: list[Any]) -> str:
    suffix = "" if len(items) == 1 else "s"
    return f"{len(items)} {value}{suffix}"
