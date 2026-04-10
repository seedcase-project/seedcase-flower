"""Shared fixtures for tests."""

import pytest
from seedcase_soil import example_datapackage, write_example_datapackage


@pytest.fixture
def datapackage():
    """Return a valid datapackage dict with resources."""
    return example_datapackage()


@pytest.fixture
def datapackage_path(tmp_path):
    """Create a temporary datapackage.json file and return its path as a string."""
    return str(write_example_datapackage(tmp_path))
