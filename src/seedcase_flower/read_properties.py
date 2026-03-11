"""Function for reading Data Package properties."""

import json
from pathlib import Path
from typing import Any
from urllib import parse, request
from urllib.error import HTTPError, URLError

from check_datapackage import check

from seedcase_flower.errors import FileLoadError
from seedcase_flower.parse_source import Address


def read_properties(address: Address) -> dict[str, Any]:
    """Read properties from a local or remote datapackage."""
    datapackage: dict[str, Any]
    if address.local:
        path = Path(parse.urlsplit(address.value).path)
        try:
            with open(path) as properties_file:
                datapackage = json.load(properties_file)
        except FileNotFoundError:
            raise FileLoadError(path, "The file does not exist")
        except json.JSONDecodeError as e:
            raise FileLoadError(path, f"Invalid JSON: {e}")
    else:
        try:
            with request.urlopen(address.value) as open_url:  # nosec B310
                datapackage = json.load(open_url)
        except (HTTPError, URLError) as e:
            raise FileLoadError(address.value, str(e)) from None
        except json.JSONDecodeError as e:
            raise FileLoadError(address.value, f"Invalid JSON: {e}")
    check(datapackage, error=True)
    return datapackage
