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


def _resolve_uri(uri_or_path: str) -> Uri:
    split_uri = parse.urlsplit(uri_or_path)
    match split_uri.scheme:
        case "":
            return _resolve_path(uri_or_path)
        case "file":
            return _resolve_file_uri(split_uri)
        case "https":
            return _resolve_https_uri(split_uri)
        case "gh" | "github":
            return _resolve_github_uri(split_uri)
        case _:
            raise ValueError(
                "The URI must be either a path to an existing file/folder "
                "or have one of the following URI prefixes: "
                "`file:`, `https:`, `gh:`, `github:`"
            )


def _resolve_path(uri_or_path: str) -> Uri:
    path = Path(uri_or_path).resolve()
    if path.is_dir():
        path = path / "datapackage.json"
    if not path.exists():
        raise OSError(f"{path} does not exist.")
    return Uri(value=str(path), local=True)


def _resolve_file_uri(split_uri: parse.SplitResult) -> Uri:
    return _resolve_path(parse.unquote(split_uri.path))


def _resolve_https_uri(split_uri: parse.SplitResult) -> Uri:
    return Uri(value=split_uri.geturl(), local=False)


def _resolve_github_uri(split_uri: parse.SplitResult) -> Uri:
    github_path = "/".join(
        part for part in (split_uri.netloc, split_uri.path.lstrip("/")) if part
    )
    return Uri(
        value=split_uri._replace(
            scheme="https",
            netloc="raw.githubusercontent.com",
            path=f"/{github_path}/refs/heads/main/datapackage.json",
        ).geturl(),
        local=False,
    )


# TODO Extend to also read properties from URLs
def _read_properties(uri: Uri) -> dict[str, Any]:
    if not uri.local:
        raise NotImplementedError(
            "Reading properties from remote URIs is not implemented yet."
        )
    with open(uri.value) as properties_file:
        datapackage: dict[str, Any] = json.load(properties_file)
        return datapackage
