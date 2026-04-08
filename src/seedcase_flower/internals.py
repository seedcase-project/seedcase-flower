"""Helper functions for internal use."""

from itertools import chain
from typing import Any, Callable, Iterable, TypeVar

In = TypeVar("In")
Out = TypeVar("Out")


def _map(x: Iterable[In], fn: Callable[[In], Out]) -> list[Out]:
    return list(map(fn, x))


def _filter(x: Iterable[In], fn: Callable[[In], bool]) -> list[In]:
    return list(filter(fn, x))


def _flat_map(items: Iterable[In], fn: Callable[[In], Iterable[Out]]) -> list[Out]:
    """Maps and flattens the items by one level."""
    return list(chain.from_iterable(map(fn, items)))


def _number(value: str, items: list[Any]) -> str:
    suffix = "" if len(items) == 1 else "s"
    return f"{len(items)} {value}{suffix}"
