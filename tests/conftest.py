"""Shared fixtures for tests."""

import pytest
from seedcase_soil import (
    Example,
    read_properties,
    write_properties,
)


@pytest.fixture
def datapackage():
    """Return a datapackage dict with resources."""
    return read_properties(Example.simple.address)


@pytest.fixture
def datapackage_path(tmp_path, datapackage):
    """Create a temporary datapackage.json file and return its path as a string."""
    file_path = tmp_path / "datapackage.json"
    write_properties(datapackage, file_path)
    return str(file_path)
