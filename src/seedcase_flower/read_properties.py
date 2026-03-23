"""Function for reading Data Package properties."""

import json
from pathlib import Path
from typing import Any
from urllib import parse, request
from urllib.error import HTTPError, URLError

from check_datapackage import check

from seedcase_flower.errors import (
    FileDoesNotExistError,
    HTTP404Error,
    HTTPDomainError,
    JSONFormatError,
)
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
            raise FileDoesNotExistError(str(path))
        except json.JSONDecodeError as e:
            raise JSONFormatError(str(path), str(e))
    else:
        try:
            with request.urlopen(address.value) as open_url:  # nosec B310
                datapackage = json.load(open_url)
        except HTTPError as e:
            raise HTTP404Error(address.value, e.code, e.reason) from None
        except URLError as e:
            if "Name or service not known" in str(
                e.reason
            ) or "getaddrinfo failed" in str(e.reason):
                raise HTTPDomainError(address.value) from None
            raise JSONFormatError(address.value, str(e)) from None
        except json.JSONDecodeError as e:
            raise JSONFormatError(address.value, str(e)) from None
    check(datapackage, error=True)
    return datapackage
