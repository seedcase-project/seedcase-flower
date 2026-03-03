"""Tests for internal helper functions."""

import json
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError

import pytest
from check_datapackage.check import DataPackageError

from seedcase_flower.internals import Uri, _parse_uri, _read_properties

# _parse_uri: plain path (no scheme) ====


def test_parse_uri_plain_file_path_is_local(tmp_path):
    """A plain file path with no scheme should return a local Uri."""
    result = _parse_uri(str(tmp_path / "datapackage.json"))
    assert result.local is True


def test_parse_uri_plain_file_path_has_file_scheme(tmp_path):
    """A plain file path should be normalised to a file:// URI."""
    result = _parse_uri(str(tmp_path / "datapackage.json"))
    assert result.value.startswith("file://")


def test_parse_uri_directory_path_appends_datapackage_json(tmp_path):
    """Passing a directory path should append datapackage.json to the URI."""
    result = _parse_uri(str(tmp_path))
    assert result.value.endswith("datapackage.json")


def test_parse_uri_directory_path_is_local(tmp_path):
    """Passing a directory path should return a local Uri."""
    result = _parse_uri(str(tmp_path))
    assert result.local is True


# _parse_uri: file:// scheme ====


def test_parse_uri_file_scheme_is_local(tmp_path):
    """A file:// URI should return a local Uri."""
    result = _parse_uri(f"file://{tmp_path / 'datapackage.json'}")
    assert result.local is True


def test_parse_uri_file_scheme_preserves_path(tmp_path):
    """A file:// URI pointing to a file should preserve the path."""
    file = tmp_path / "datapackage.json"
    result = _parse_uri(f"file://{file}")
    assert str(file) in result.value


# _parse_uri: https:// scheme ====


def test_parse_uri_https_is_not_local():
    """An https:// URI should return a non-local Uri."""
    result = _parse_uri("https://example.com/datapackage.json")
    assert result.local is False


def test_parse_uri_https_preserves_url():
    """An https:// URI should be returned unchanged."""
    url = "https://example.com/datapackage.json"
    result = _parse_uri(url)
    assert result.value == url


# _parse_uri: gh:// / github:// scheme ====


@pytest.mark.parametrize("scheme", ["gh", "github"])
def test_parse_uri_github_scheme_converts_to_raw_githubusercontent(scheme):
    """GitHub  URIs should be converted to a raw.githubusercontent.com URL."""
    result = _parse_uri(f"{scheme}://owner/repo")
    assert result.value.startswith("https://raw.githubusercontent.com/")


@pytest.mark.parametrize("scheme", ["gh", "github"])
def test_parse_uri_github_scheme_is_not_local(scheme):
    """GitHub URIs should return a non-local Uri."""
    result = _parse_uri(f"{scheme}://owner/repo")
    assert result.local is False


@pytest.mark.parametrize("scheme", ["gh", "github"])
def test_parse_uri_github_scheme_appends_datapackage_json(scheme):
    """GitHub URIs should point to the datapackage.json on the main branch."""
    result = _parse_uri(f"{scheme}://owner/repo")
    assert result.value.endswith("datapackage.json")


# _parse_uri: unsupported scheme ====


def test_parse_uri_unsupported_scheme_raises_value_error():
    """An unsupported URI scheme should raise a ValueError."""
    with pytest.raises(ValueError, match="uri must be either"):
        _parse_uri("ftp://example.com/datapackage.json")


def test_parse_uri_returns_uri_instance(tmp_path):
    """_parse_uri should always return a Uri instance."""
    result = _parse_uri(str(tmp_path / "datapackage.json"))
    assert isinstance(result, Uri)


# _read_properties: local file ====


def test_read_properties_local_filepath(datapackage_path, datapackage):
    """Reading a local datapackage.json file should return its contents."""
    uri = Uri(value=str(datapackage_path), local=True)
    result = _read_properties(uri)

    assert result == datapackage


def test_read_properties_local_dirpath(datapackage_path, datapackage):
    """Passing a path to a directory containing a datapackage.json should work."""
    uri = _parse_uri(str(Path(datapackage_path).parent))
    result = _read_properties(uri)

    assert result == datapackage


def test_read_properties_raises_on_invalid_datapackage(tmp_path):
    """An invalid datapackage should raise a ValueError."""
    invalid_datapackage = {"name": "invalid-package", "resources": []}
    json_file = tmp_path / "datapackage.json"
    json_file.write_text(json.dumps(invalid_datapackage))

    uri = Uri(value=str(json_file), local=True)

    with pytest.raises(DataPackageError, match="should be non-empty"):
        _read_properties(uri)


def test_read_properties_raises_on_file_not_found():
    """A non-existent file should raise FileNotFoundError."""
    uri = Uri(value="file:///nonexistent/path/datapackage.json", local=True)

    with pytest.raises(FileNotFoundError):
        _read_properties(uri)


def test_read_properties_raises_on_malformed_json(tmp_path):
    """A file with malformed JSON should raise JSONDecodeError."""
    json_file = tmp_path / "datapackage.json"
    json_file.write_text("{ invalid json }")

    uri = Uri(value=str(json_file), local=True)

    with pytest.raises(json.JSONDecodeError):
        _read_properties(uri)


# _read_properties: remote file ====


@pytest.mark.usefixtures("mocker")
def test_read_properties_remote_url(mocker, datapackage):
    """Reading a remote datapackage.json URL should return its contents."""
    mock_urlopen = mocker.patch("seedcase_flower.internals.request.urlopen")
    mock_response = mock_urlopen.return_value.__enter__.return_value
    mock_response.read.return_value = json.dumps(datapackage).encode()

    uri = Uri(value="https://example.com/datapackage.json", local=False)
    result = _read_properties(uri)

    assert result == datapackage
    mock_urlopen.assert_called_once_with("https://example.com/datapackage.json")


@pytest.mark.usefixtures("mocker")
def test_read_properties_raises_on_remote_invalid_json(mocker):
    """A remote URL returning invalid JSON should raise JSONDecodeError."""
    mock_urlopen = mocker.patch("seedcase_flower.internals.request.urlopen")
    mock_response = mock_urlopen.return_value.__enter__.return_value
    mock_response.read.return_value = b"{ invalid json }"

    uri = Uri(value="https://example.com/datapackage.json", local=False)

    with pytest.raises(json.JSONDecodeError):
        _read_properties(uri)


@pytest.mark.usefixtures("mocker")
def test_read_properties_raises_on_remote_404(mocker):
    """A remote URL returning 404 should raise HTTPError."""
    mocker.patch(
        "seedcase_flower.internals.request.urlopen",
        side_effect=HTTPError(
            "https://example.com/datapackage.json", 404, "Not Found", Message(), None
        ),
    )

    uri = Uri(value="https://example.com/datapackage.json", local=False)

    with pytest.raises(HTTPError):
        _read_properties(uri)
