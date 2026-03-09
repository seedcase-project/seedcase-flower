"""Shared fixtures for tests."""

import json

import pytest


@pytest.fixture
def datapackage():
    """Return a valid datapackage dict with resources."""
    return {
        "name": "test-package",
        "title": "Test Package",
        "description": "A test datapackage",
        "version": "1.0.0",
        "licenses": [{"name": "MIT"}],
        "resources": [
            {
                "name": "data",
                "path": "data.csv",
                "schema": {
                    "fields": [
                        {"name": "id", "type": "integer"},
                        {"name": "name", "type": "string"},
                    ]
                },
            },
            {
                "name": "data2",
                "path": "data2.csv",
                "schema": {
                    "fields": [
                        {"name": "id", "type": "integer"},
                        {"name": "age", "type": "integer"},
                    ]
                },
            },
        ],
    }


@pytest.fixture
def datapackage_path(tmp_path, datapackage):
    """Create a temporary datapackage.json file and return its path as a string."""
    file_path = tmp_path / "datapackage.json"
    file_path.write_text(json.dumps(datapackage))
    return str(file_path)
