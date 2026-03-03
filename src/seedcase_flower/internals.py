"""Helper functions for private use."""

import json
from dataclasses import dataclass
from enum import Enum
from itertools import repeat
from pathlib import Path
from typing import Any
from urllib import parse

from cyclopts.annotations import get_hint_name
from cyclopts.help import HelpEntry


class BuildStyle(Enum):
    """Built-in styles for outputting to file."""

    quarto_one_page = "quarto_one_page"
    quarto_resource_listing = "quarto_resource_listing"
    quarto_resource_tables = "quarto_resource_tables"


@dataclass(frozen=True)
class Uri:
    """A parsed URI with its normalised value and locality flag."""

    value: str
    local: bool


def _parse_uri(uri: str) -> Uri:
    split_uri = parse.urlsplit(uri)
    if split_uri.scheme == "":
        split_uri = split_uri._replace(scheme="file")
    match split_uri.scheme:
        case "file":
            return _convert_to_file_uri(split_uri)
        case "https":
            return _convert_to_https_uri(split_uri)
        case "gh" | "github":
            return _convert_to_github_uri(split_uri)
        case _:
            raise ValueError(
                "The uri must be either a path to an existing file/folder "
                "or a URI with one of the following URI prefixes: "
                "`file:`, `https:`, `gh:`, `github:`"
            )


def _convert_to_file_uri(split_file_uri: parse.SplitResult) -> Uri:
    path = Path(split_file_uri.path).resolve()
    if path.is_dir():
        path /= "datapackage.json"
    split_file_uri = split_file_uri._replace(path=path.as_posix())
    return Uri(value=split_file_uri.geturl(), local=True)


def _convert_to_https_uri(split_https_uri: parse.SplitResult) -> Uri:
    return Uri(value=split_https_uri.geturl(), local=False)


def _convert_to_github_uri(split_gh_uri: parse.SplitResult) -> Uri:
    return Uri(
        value=split_gh_uri._replace(
            scheme="https",
            netloc="raw.githubusercontent.com",
            path=f"/{split_gh_uri.path}/refs/heads/main/datapackage.json",
        ).geturl(),
        local=False,
    )


def _format_param_help(entry: HelpEntry) -> str:
    """Re-structure the parameter help into a more readable format."""
    # Sort to put the flag first (eg `--uri URI` instead of the default `URI --uri`)
    names = map(_add_highlight_syntax, sorted(entry.names), repeat(entry.type))
    return f"{' '.join(names)}".strip()


def _add_highlight_syntax(name: str, entry_type: Optional[type]) -> str:
    """Add markup character to highlight in colors, etc where desired."""
    formatted_name = f"[bold cyan]{name}[/bold cyan]"
    if not name.startswith("-"):
        # Matching the `dim` used by default in cyclopts for `choices` and
        # `defaults` in the description
        formatted_name = f"[dim]<{name}>[/dim]"

        # Don't output redundant value placeholder for boolean flags
        if get_hint_name(entry_type) == "bool":
            formatted_name = ""
    return formatted_name


def _read_properties(uri: Uri) -> dict[str, Any]:
    if uri.local:
        path = Path(parse.urlsplit(uri.value).path)
        with open(path) as properties_file:
            return json.load(properties_file)  # type: ignore # TODO fix in read_prop PR
    else:
        # TODO read from remote file
        return {"placeholder": uri.value}
