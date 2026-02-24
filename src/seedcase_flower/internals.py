"""Helper functions for private use."""

import json
from enum import Enum
from pathlib import Path
from typing import Annotated, Any
from urllib import parse, request

from check_datapackage import check
from pydantic import AnyUrl, FileUrl, TypeAdapter, UrlConstraints

_AnnotatedHttps = Annotated[AnyUrl, UrlConstraints(allowed_schemes=["https"])]
_adapter = TypeAdapter(_AnnotatedHttps)


class HttpsUrl(str):
    """Type and class with validation for https URLs."""

    @classmethod
    def __get_pydantic_core_schema__(cls, source, handler):
        """Initialize adapter core schema."""
        return _adapter.core_schema

    def __new__(cls, value: str):
        """Setup validation."""
        validated = _adapter.validate_python(value)
        return str.__new__(cls, validated)


class BuildStyle(Enum):
    """Built-in styles for outputting to file."""

    quarto_one_page = "quarto_one_page"
    quarto_resource_listing = "quarto_resource_listing"
    quarto_resource_tables = "quarto_resource_tables"


def _resolve_uri(path_or_url: str) -> HttpsUrl | FileUrl:
    split_url = parse.urlsplit(path_or_url)
    if split_url.scheme == "https":
        uri = _check_https_uri(split_url)
    elif split_url.scheme in ["gh", "github"]:
        uri = _check_github_uri(split_url)
    elif split_url.scheme == "":
        uri = _check_path(path_or_url)
    else:
        raise ValueError(
            "The URI must be either a path to an existing file/folder "
            "or have one of the following URI prefixes: "
            "`file://`, `https://`, `gh:`, `github:`"
        )
    return uri


def _check_https_uri(split_url: parse.SplitResult) -> HttpsUrl:
    return HttpsUrl(split_url.geturl())


def _check_github_uri(split_url: parse.SplitResult) -> HttpsUrl:
    return HttpsUrl(
        split_url._replace(
            scheme="https",
            netloc="raw.githubusercontent.com",
            path=f"/{split_url.path}/refs/heads/main/datapackage.json",
        ).geturl()
    )


def _check_path(path_or_url: str) -> FileUrl:
    path = Path(path_or_url).resolve()
    if path.is_dir():
        path = path / "datapackage.json"
    if not path.exists():
        raise OSError(f"{path} does not exist.")
    return FileUrl(path.as_uri())


# TODO Extend to also read properties from URLs
def _read_properties(path: Path) -> dict[str, Any]:
    with open(path) as properties_file:
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
