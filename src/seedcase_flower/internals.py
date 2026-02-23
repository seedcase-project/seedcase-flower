"""Helper functions for private use."""

import json
from enum import Enum
from itertools import repeat
from pathlib import Path
from typing import Any

from cyclopts.annotations import get_hint_name
from cyclopts.help import HelpEntry


class BuildStyle(Enum):
    """Built-in styles for outputting to file."""

    quarto_one_page = "quarto_one_page"
    quarto_resource_listing = "quarto_resource_listing"
    quarto_resource_tables = "quarto_resource_tables"


# Output maybe str? Path?
# Use `match` inside for strictness on URI types? Or use a library for URI parsing?
# TODO Extend to parse strings and return either URL or Path
def _resolve_uri(uri: str) -> Path:
    return Path(uri)


# TODO Extend to also read properties from URLs
def _read_properties(path: Path) -> dict[str, Any]:
    with open(path) as properties_file:
        datapackage: dict[str, Any] = json.load(properties_file)
        return datapackage


def _format_param_help(entry: HelpEntry) -> str:
    """Re-structure the parameter help into a more readable format."""
    if entry.names:
        names = map(_add_highlight_syntax, sorted(entry.names), repeat(entry.type))
    return f"{' '.join(names)}".strip()


def _add_highlight_syntax(name: str, entry_type: type | None) -> str:
    """Add markup character to highlight in colors, etc where desired."""
    if not name.startswith("-"):
        # Don't output redundant value placeholder for boolean flags
        if get_hint_name(entry_type) == "bool":
            name = ""
        else:
            # Matching the `dim` used by default in cyclopts for `choices` and
            # `defaults` in the description
            name = f"[dim]<{name}>[/dim]"
    else:
        name = f"[bold cyan]{name}[/bold cyan]"
    return name
