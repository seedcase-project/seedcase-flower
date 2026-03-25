"""Function for reading Data Package properties."""

import json
from pathlib import Path
from typing import Any
from urllib import parse, request
from urllib.error import HTTPError, URLError

from check_datapackage import check

from seedcase_flower.errors import (
    FileDoesNotExistError,
    HTTPDomainError,
    HTTPStatusError,
    JSONFormatError,
    NotJSONError,
)
from seedcase_flower.parse_source import Address

JSON_CONTENT_TYPES = ("application/json", "application/ld+json", "application/geo+json")


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
                content_type = open_url.headers.get("Content-Type", "")
                if not content_type.startswith(JSON_CONTENT_TYPES + ("text/plain",)):
                    main_type = content_type.split(";")[0].strip()
                    raise NotJSONError(address.value, main_type)
                datapackage = json.load(open_url)
        except HTTPError as e:
            raise HTTPStatusError(address.value, e.code, e.reason)
        except URLError as e:
            if "Name or service not known" in str(
                e.reason
            ) or "getaddrinfo failed" in str(e.reason):
                raise HTTPDomainError(address.value)
            raise JSONFormatError(address.value, str(e))
        except json.JSONDecodeError as e:
            raise JSONFormatError(address.value, str(e))
    check(datapackage, error=True)
    return datapackage
