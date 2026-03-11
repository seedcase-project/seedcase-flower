"""Tests for the read_properties function."""

import json
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError

import pytest
from check_datapackage.check import DataPackageError

from seedcase_flower.parse_source import Address, parse_source
from seedcase_flower.read_properties import read_properties

# read_properties: local file ====


def test_read_properties_local_filepath(datapackage_path, datapackage):
    """Reading a local datapackage.json file should return its contents."""
    address = Address(value=str(datapackage_path), local=True)
    result = read_properties(address)

    assert result == datapackage


def test_read_properties_local_dirpath(datapackage_path, datapackage):
    """Passing a path to a directory containing a datapackage.json should work."""
    address = parse_source(str(Path(datapackage_path).parent))
    result = read_properties(address)

    assert result == datapackage


def test_read_properties_raises_on_invalid_datapackage(tmp_path):
    """An invalid datapackage should raise a ValueError."""
    invalid_datapackage = {"name": "invalid-package", "resources": []}
    json_file = tmp_path / "datapackage.json"
    json_file.write_text(json.dumps(invalid_datapackage))

    address = Address(value=str(json_file), local=True)

    with pytest.raises(DataPackageError, match="should be non-empty"):
        read_properties(address)


def test_read_properties_raises_on_file_not_found():
    """A non-existent file should raise FileNotFound."""
    address = Address(value="file:///nonexistent/path/datapackage.json", local=True)

    from seedcase_flower.errors import FileNotFound

    with pytest.raises(FileNotFound):
        read_properties(address)


def test_read_properties_raises_on_malformed_json(tmp_path):
    """A file with malformed JSON should raise JSONDecodeError."""
    json_file = tmp_path / "datapackage.json"
    json_file.write_text("{ invalid json }")

    address = Address(value=str(json_file), local=True)

    with pytest.raises(json.JSONDecodeError):
        read_properties(address)


# read_properties: remote file ====


@pytest.mark.usefixtures("mocker")
def test_read_properties_remote_url(mocker, datapackage):
    """Reading a remote datapackage.json URL should return its contents."""
    mock_urlopen = mocker.patch("seedcase_flower.read_properties.request.urlopen")
    mock_response = mock_urlopen.return_value.__enter__.return_value
    mock_response.read.return_value = json.dumps(datapackage).encode()

    address = Address(value="https://example.com/datapackage.json", local=False)
    result = read_properties(address)

    assert result == datapackage
    mock_urlopen.assert_called_once_with("https://example.com/datapackage.json")


@pytest.mark.usefixtures("mocker")
def test_read_properties_raises_on_remote_invalid_json(mocker):
    """A remote URL returning invalid JSON should raise JSONDecodeError."""
    mock_urlopen = mocker.patch("seedcase_flower.read_properties.request.urlopen")
    mock_response = mock_urlopen.return_value.__enter__.return_value
    mock_response.read.return_value = b"{ invalid json }"

    address = Address(value="https://example.com/datapackage.json", local=False)

    with pytest.raises(json.JSONDecodeError):
        read_properties(address)


@pytest.mark.usefixtures("mocker")
def test_read_properties_raises_on_remote_404(mocker):
    """A remote URL returning 404 should raise FileNotFound."""
    mocker.patch(
        "seedcase_flower.read_properties.request.urlopen",
        side_effect=HTTPError(
            "https://example.com/datapackage.json", 404, "Not Found", Message(), None
        ),
    )

    address = Address(value="https://example.com/datapackage.json", local=False)

    from seedcase_flower.errors import FileNotFound

    with pytest.raises(FileNotFound):
        read_properties(address)
