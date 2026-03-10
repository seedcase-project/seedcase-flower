"""Tests for parsing the source for the Data Package."""

import pytest

from seedcase_flower.parse_source import Address, parse_source

# parse_source: plain path (no scheme) ====


def test_parse_source_plain_file_path_is_local(tmp_path):
    """A plain file path with no scheme should return a local Address."""
    result = parse_source(str(tmp_path / "datapackage.json"))
    assert result.local is True


def test_parse_source_plain_file_path_has_file_scheme(tmp_path):
    """A plain file path should be normalised to a file path."""
    result = parse_source(str(tmp_path / "datapackage.json"))
    assert result.value.startswith("file://")


def test_parse_source_directory_path_appends_datapackage_json(tmp_path):
    """Passing a directory path should append datapackage.json to the source."""
    result = parse_source(str(tmp_path))
    assert result.value.endswith("datapackage.json")


def test_parse_source_directory_path_is_local(tmp_path):
    """Passing a directory path should return a local Address."""
    result = parse_source(str(tmp_path))
    assert result.local is True


# parse_source: file:// scheme ====


def test_parse_source_file_scheme_is_local(tmp_path):
    """A file path should return a local Address."""
    result = parse_source(f"file://{tmp_path / 'datapackage.json'}")
    assert result.local is True


def test_parse_source_file_scheme_preserves_path(tmp_path):
    """A file path pointing to a file should preserve the path."""
    file = tmp_path / "datapackage.json"
    result = parse_source(f"file://{file}")
    assert str(file) in result.value


# parse_source: https:// scheme ====


def test_parse_source_https_is_not_local():
    """An https:// should return a non-local Address."""
    result = parse_source("https://example.com/datapackage.json")
    assert result.local is False


def test_parse_source_https_preserves_url():
    """An https:// should be returned unchanged."""
    url = "https://example.com/datapackage.json"
    result = parse_source(url)
    assert result.value == url


# parse_source: gh:// / github:// scheme ====


@pytest.mark.parametrize("scheme", ["gh", "github"])
def test_parse_source_github_scheme_converts_to_raw_githubusercontent(scheme):
    """GitHub sources should be converted to a raw.githubusercontent.com URL."""
    result = parse_source(f"{scheme}://owner/repo")
    assert result.value.startswith("https://raw.githubusercontent.com/")


@pytest.mark.parametrize("scheme", ["gh", "github"])
def test_parse_source_github_scheme_is_not_local(scheme):
    """GitHub sources should return a non-local Address."""
    result = parse_source(f"{scheme}://owner/repo")
    assert result.local is False


@pytest.mark.parametrize("scheme", ["gh", "github"])
def test_parse_source_github_scheme_appends_datapackage_json(scheme):
    """GitHub sources should point to the datapackage.json on the main branch."""
    result = parse_source(f"{scheme}://owner/repo")
    assert result.value.endswith("datapackage.json")


@pytest.mark.parametrize("scheme", ["gh", "github"])
def test_parse_source_github_scheme_uses_main_by_default(scheme):
    """GitHub sources without @ref should use main."""
    result = parse_source(f"{scheme}:owner/repo")
    assert result.value == (
        "https://raw.githubusercontent.com/owner/repo/main/datapackage.json"
    )


@pytest.mark.parametrize("scheme", ["gh", "github"])
def test_parse_source_github_scheme_with_tag(scheme):
    """GitHub sources with @tag should use the tag as the ref."""
    result = parse_source(f"{scheme}:owner/repo@v1.0.0")
    assert result.value == (
        "https://raw.githubusercontent.com/owner/repo/v1.0.0/datapackage.json"
    )


@pytest.mark.parametrize("scheme", ["gh", "github"])
def test_parse_source_github_scheme_with_branch(scheme):
    """GitHub sources with @branch should use the branch as the ref."""
    result = parse_source(f"{scheme}:owner/repo@develop")
    assert result.value == (
        "https://raw.githubusercontent.com/owner/repo/develop/datapackage.json"
    )


# parse_source: unsupported scheme ====


def test_parse_source_unsupported_scheme_raises_value_error():
    """An unsupported source scheme should raise a ValueError."""
    with pytest.raises(ValueError, match="source must be either"):
        parse_source("ftp://example.com/datapackage.json")


def test_parse_source_returns_address_instance(tmp_path):
    """parse_source should always return a address instance."""
    result = parse_source(str(tmp_path / "datapackage.json"))
    assert isinstance(result, Address)
