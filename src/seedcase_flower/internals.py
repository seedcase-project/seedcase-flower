"""Helper functions for private use."""

import json
from enum import Enum
from pathlib import Path
from typing import Any


class BuildStyle(Enum):
    """Built-in styles for outputting to file."""

    quarto_one_page = "quarto_one_page"
    quarto_resource_listing = "quarto_resource_listing"
    quarto_resource_tables = "quarto_resource_tables"


# TODO Extend to parse strings and return either URL or Path
def _resolve_uri(uri: str) -> Path:
    return Path(uri)


# TODO Extend to also read properties from URLs
def _read_properties(path: Path) -> dict[str, Any]:
    with open(path) as properties_file:
        datapackage: dict[str, Any] = json.load(properties_file)
        return datapackage
