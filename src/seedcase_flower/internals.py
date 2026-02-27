"""Helper functions for private use."""

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any
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


def _parse_source(source: str) -> Uri:
    split_source = parse.urlsplit(source)
    if split_source.scheme == "":
        split_source = split_source._replace(scheme="file")
    match split_source.scheme:
        case "file":
            return _convert_to_file_uri(split_source)
        case "https":
            return _convert_to_https_uri(split_source)
        case "gh" | "github":
            return _convert_to_github_uri(split_source)
        case _:
            raise ValueError(
                "The source must be either a path to an existing file/folder "
                "or a URI with one of the following URI prefixes: "
                "`file:`, `https:`, `gh:`, `github:`"
            )


def _convert_to_file_uri(split_file_source: parse.SplitResult) -> Uri:
    path = Path(split_file_source.path).resolve()
    if path.is_dir():
        path /= "datapackage.json"
    split_file_source = split_file_source._replace(path=path.as_posix())
    return Uri(value=split_file_source.geturl(), local=True)


def _convert_to_https_uri(split_https_source: parse.SplitResult) -> Uri:
    return Uri(value=split_https_source.geturl(), local=False)


def _convert_to_github_uri(split_gh_source: parse.SplitResult) -> Uri:
    github_path = "/".join(
        part
        for part in (split_gh_source.netloc, split_gh_source.path.lstrip("/"))
        if part
    )
    return Uri(
        value=split_gh_source._replace(
            scheme="https",
            netloc="raw.githubusercontent.com",
            path=f"/{github_path}/refs/heads/main/datapackage.json",
        ).geturl(),
        local=False,
    )


# TODO Extend to also read properties from URLs
def _read_properties(uri: Uri) -> dict[str, Any]:
    with open(uri.value) as properties_file:
        datapackage: dict[str, Any] = json.load(properties_file)
        return datapackage
