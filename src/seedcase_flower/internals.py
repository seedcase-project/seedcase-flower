"""Helper functions for private use."""

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Iterable, Optional, TypeVar
from urllib import parse


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


# TODO Extend to also read properties from URLs
def _read_properties(uri: Uri) -> dict[str, Any]:
    if uri.local:
        path = Path(parse.urlsplit(uri.value).path)
        with open(path) as properties_file:
            return json.load(properties_file)  # type: ignore # TODO fix in read_prop PR
    else:
        # TODO read from remote file
        return {"placeholder": uri.value}


In = TypeVar("In")
Out = TypeVar("Out")


def _map(x: Iterable[In], fn: Callable[[In], Out]) -> list[Out]:
    return list(map(fn, x))


def _filter(x: Iterable[In], fn: Callable[[In], bool]) -> list[In]:
    return list(filter(fn, x))


@dataclass(frozen=True)
class BuiltSection:
    """A section that has been built from a template.

    Attributes:
        content: The rendered template as a string.
        output_path: The path where the section should be written, relative
            to `Config.output_dir`. Sections displayed in the terminal don't
            have an `output_path`.
    """

    content: str
    output_path: Optional[Path] = None
