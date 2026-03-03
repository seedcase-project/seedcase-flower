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
class Address:
    """A source parsed into an actual address."""

    value: str
    local: bool


def _parse_source(source: str) -> Address:
    split_source = parse.urlsplit(source)
    if split_source.scheme == "":
        split_source = split_source._replace(scheme="file")
    match split_source.scheme:
        case "file":
            return _convert_to_path(split_source)
        case "https":
            return _convert_to_https(split_source)
        case "gh" | "github":
            return _convert_to_github(split_source)
        case _:
            raise ValueError(
                "The source must be either a path to an existing file or "
                "folder or have one of the following prefixes: `https:`, "
                "`gh:`, `github:`"
            )


def _convert_to_path(source: parse.SplitResult) -> Address:
    path = Path(source.path).resolve()
    if path.is_dir():
        path /= "datapackage.json"
    source = source._replace(path=path.as_posix())
    return Address(value=source.geturl(), local=True)


def _convert_to_https(source: parse.SplitResult) -> Address:
    return Address(value=source.geturl(), local=False)


def _convert_to_github(source: parse.SplitResult) -> Address:
    return Address(
        value=source._replace(
            scheme="https",
            netloc="raw.githubusercontent.com",
            path=f"/{source.path}/refs/heads/main/datapackage.json",
        ).geturl(),
        local=False,
    )


# TODO Extend to also read properties from URLs
def _read_properties(address: Address) -> dict[str, Any]:
    if address.local:
        path = Path(parse.urlsplit(address.value).path)
        with open(path) as properties_file:
            return json.load(properties_file)  # type: ignore # TODO fix in read_prop PR
    else:
        # TODO read from remote file
        return {"placeholder": address.value}
