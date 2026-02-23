"""Helper functions for private use."""

import json
from enum import Enum
from pathlib import Path
from typing import Any

from check_datapackage import check


class BuildStyle(Enum):
    """Built-in styles for outputting to file."""

    quarto_one_page = "quarto_one_page"
    quarto_resource_listing = "quarto_resource_listing"
    quarto_resource_tables = "quarto_resource_tables"


# Output maybe str? Path?
# Use `match` inside for strictness on URI types? Or use a library for URI parsing?
# TODO Extend to parse strings and return either URL or Path
def _resolve_uri(uri: str) -> Path:
    return Path(uri)


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
