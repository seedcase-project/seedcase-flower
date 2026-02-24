"""Helper functions for private use."""

import json
from enum import Enum
from pathlib import Path
from typing import Annotated, Any
from urllib import parse

from check_datapackage import check
from pydantic import AnyUrl, FileUrl, TypeAdapter, UrlConstraints

_AnnotatedHttps = Annotated[AnyUrl, UrlConstraints(allowed_schemes=["https"])]
_adapter = TypeAdapter(_AnnotatedHttps)


class HttpsUrl(str):
    """Type and class with validation for https URLs."""

    @classmethod
    def __get_pydantic_core_schema__(cls, source, handler):  # type: ignore[no-untyped-def]
        """Initialize adapter core schema."""
        return _adapter.core_schema

    def __new__(cls, value: str):  # type: ignore[no-untyped-def]
        """Setup validation."""
        validated = _adapter.validate_python(value)
        return str.__new__(cls, validated)


class BuildStyle(Enum):
    """Built-in styles for outputting to file."""

    quarto_one_page = "quarto_one_page"
    quarto_resource_listing = "quarto_resource_listing"
    quarto_resource_tables = "quarto_resource_tables"


def _resolve_uri(uri_or_path: str) -> HttpsUrl | FileUrl:
    split_uri = parse.urlsplit(uri_or_path)
    match split_uri.scheme:
        case "":
            return _check_path(uri_or_path)
        case "file":
            return _check_file_uri(split_uri)
        case "https":
            return _check_https_uri(split_uri)
        case "gh" | "github":
            return _check_github_uri(split_uri)
        case _:
            raise ValueError(
                "The URI must be either a path to an existing file/folder "
                "or have one of the following URI prefixes: "
                "`file:`, `https:`, `gh:`, `github:`"
            )


def _check_path(uri_or_path: str) -> FileUrl:
    path = Path(uri_or_path).resolve()
    if path.is_dir():
        path = path / "datapackage.json"
    if not path.exists():
        raise OSError(f"{path} does not exist.")
    return FileUrl(path.as_uri())


def _check_file_uri(split_uri: parse.SplitResult) -> FileUrl:
    return FileUrl(split_uri.geturl())


def _check_https_uri(split_uri: parse.SplitResult) -> HttpsUrl:
    return HttpsUrl(split_uri.geturl())


def _check_github_uri(split_uri: parse.SplitResult) -> HttpsUrl:
    return HttpsUrl(
        split_uri._replace(
            scheme="https",
            netloc="raw.githubusercontent.com",
            path=f"/{split_uri.path}/refs/heads/main/datapackage.json",
        ).geturl()
    )


# TODO Extend to also read properties from URLs
def _read_properties(uri: HttpsUrl | FileUrl) -> dict[str, Any]:
    with open(str(uri)) as properties_file:
        datapackage: dict[str, Any] = json.load(properties_file)
        check(datapackage)
        return datapackage
