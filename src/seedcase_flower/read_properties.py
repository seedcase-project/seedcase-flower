"""Function for reading Data Package properties."""

import json
from pathlib import Path
from typing import Any
from urllib import parse, request

from check_datapackage import check

from seedcase_flower.internals import Address


def read_properties(address: Address) -> dict[str, Any]:
    """Read properties from a local or remote datapackage."""
    datapackage: dict[str, Any]
    if address.local:
        path = Path(parse.urlsplit(address.value).path)
        with open(path) as properties_file:
            datapackage = json.load(properties_file)
    else:
        with request.urlopen(address.value) as open_url:  # nosec B310
            datapackage = json.load(open_url)
    check(datapackage, error=True)
    return datapackage
