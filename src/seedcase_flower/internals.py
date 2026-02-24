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


def read_properties(path: Path) -> dict:
    """Read in the properties from the `datapackage.json` file.

    Reads the `datapackage.json` file, checks that it is correct, and then
    outputs a `PackageProperties` object.

    Args:
        path: The path to the `datapackage.json` file. Use `PackagePath().properties()`
            to help get the correct path. If no path is provided, this function looks
            for the `datapackage.json` file in the current working directory.

    Returns:
        A `PackageProperties` object with the properties from the
            `datapackage.json` file.

    Examples:
        ```{python}
        import seedcase_sprout as sp

        with sp.ExamplePackage():
            sp.read_properties()
        ```

    Raises:
        FileNotFound: If the `datapackage.json` file doesn't exist.
        JSONDecodeError: If the `datapackage.json` file couldn't be read.
    """
    _check_is_file(path)  # or _check_is_URL
    package_properties = _read_json(path)
    check(properties=package_properties, error=True)
    return package_properties


def _read_json(path: Path) -> dict[str, Any]:
    """Reads the contents of a JSON file into an object.

    Args:
        path: The path to the file to load.

    Returns:
        The contents of the file as an object.

    Raises:
        JSONDecodeError: If the contents of the file cannot be de-serialised as JSON.
        TypeError: If the object in the file is not a dictionary.
    """
    loaded_object = json.loads(path.read_text())
    if not isinstance(loaded_object, dict):
        raise TypeError(
            f"Expected {path} to contain a JSON dictionary object "
            f"but found {type(loaded_object)}."
        )
    return loaded_object


def _check_is_file(path: Path) -> Path:
    """Checks whether the file given by the path exists and is a file.

    Args:
        path: The path to check.

    Returns:
        A path to the file if the path refers to a file.

    Raises:
        FileNotFound: If the file in the path doesn't exist or isn't a file.
    """
    if not path.is_file():
        raise FileNotFoundError(f"{path} is not a file.")

    return path
