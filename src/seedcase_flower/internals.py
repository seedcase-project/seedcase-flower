"""Helper functions for private use."""

import json
from pathlib import Path


# TODO Extend to parse strings and return either URL or Path
def _resolve_uri(uri) -> Path:
    return Path(uri)


# TODO Extend to also read properties from URLs
def _read_properties(path: Path) -> dict:
    with open(path) as properties_file:
        return json.load(properties_file)
