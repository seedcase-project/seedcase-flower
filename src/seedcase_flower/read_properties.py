"""Function for reading Data Package properties."""

import json
from pathlib import Path
from typing import Any
from urllib import parse, request
from urllib.error import HTTPError, URLError

from check_datapackage import check

from seedcase_flower.errors import FileLoadError
from seedcase_flower.parse_source import Address


def _get_url_error_message(error: URLError) -> str:
    """Convert URLError to a user-friendly error message."""
    error_msg = str(error.reason)
    if "Name or service not known" in error_msg or "getaddrinfo failed" in error_msg:
        return "Unable to connect to server (domain not found)"
    return f"Connection failed: {error.reason}"


def read_properties(address: Address) -> dict[str, Any]:
    """Read properties from a local or remote datapackage."""
    datapackage: dict[str, Any]
    if address.local:
        path = Path(parse.urlsplit(address.value).path)
        try:
            with open(path) as properties_file:
                datapackage = json.load(properties_file)
        except FileNotFoundError:
            raise FileLoadError(path, "File does not exist")
        except json.JSONDecodeError as e:
            raise FileLoadError(path, f"Invalid JSON format: {e}")
    else:
        try:
            with request.urlopen(address.value) as open_url:  # nosec B310
                datapackage = json.load(open_url)
        except HTTPError as e:
            raise FileLoadError(
                address.value, f"HTTP Error {e.code}: {e.reason}"
            ) from None
        except URLError as e:
            raise FileLoadError(address.value, _get_url_error_message(e)) from None
        except json.JSONDecodeError as e:
            raise FileLoadError(address.value, f"Invalid JSON format: {e}") from None
    check(datapackage, error=True)
    return datapackage
