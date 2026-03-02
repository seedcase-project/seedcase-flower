"""Tests for internal helper functions."""

import pytest

from seedcase_flower.internals import Uri, _parse_uri

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


def test_parse_uri_gh_scheme_converts_to_raw_githubusercontent():
    """A gh:// URI should be converted to a raw.githubusercontent.com URL."""
    result = _parse_uri("gh://owner/repo")
    assert "raw.githubusercontent.com" in result.value


def test_parse_uri_gh_scheme_is_not_local():
    """A gh:// URI should return a non-local Uri."""
    result = _parse_uri("gh://owner/repo")
    assert result.local is False


def test_parse_uri_gh_scheme_appends_datapackage_json():
    """A gh:// URI should point to the datapackage.json on the main branch."""
    result = _parse_uri("gh://owner/repo")
    assert result.value.endswith("datapackage.json")


def test_parse_uri_github_scheme_converts_to_raw_githubusercontent():
    """A github:// URI should be converted to a raw.githubusercontent.com URL."""
    result = _parse_uri("github://owner/repo")
    assert "raw.githubusercontent.com" in result.value


def test_parse_uri_github_scheme_is_not_local():
    """A github:// URI should return a non-local Uri."""
    result = _parse_uri("github://owner/repo")
    assert result.local is False


def test_parse_uri_github_scheme_appends_datapackage_json():
    """A github:// URI should point to the datapackage.json on the main branch."""
    result = _parse_uri("github://owner/repo")
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
