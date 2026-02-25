"""Tests for the CLI commands."""

import json
from pathlib import Path

import pytest

from seedcase_flower.cli import app, view
from seedcase_flower.internals import BuildStyle

_DATAPACKAGE_DATA = {
    "name": "placeholder",
    "created": "2026-02-12T11:25:49+01:00",
    "description": "Placeholder",
    "id": "Placeholder",
    "licenses": [{"name": "Placeholder"}],
    "title": "Placeholder",
    "version": "0.0.0",
}


@pytest.fixture
def datapackage_path(tmp_path):
    """Create a temporary datapackage.json and return its path as a string."""
    file_path = tmp_path / "datapackage.json"
    file_path.write_text(json.dumps(_DATAPACKAGE_DATA))
    return str(file_path)


@pytest.fixture
def mock_resolve_uri(mocker):
    """Mock _resolve_uri to isolate CLI tests from filesystem resolution."""
    return mocker.patch("seedcase_flower.cli._resolve_uri")


@pytest.fixture
def mock_read_properties(mocker):
    """Mock _read_properties to isolate CLI tests from file I/O."""
    return mocker.patch("seedcase_flower.cli._read_properties")


# === Testing CLI invocation ===


def test_build_with_mocked_internals(mock_resolve_uri, mock_read_properties):
    """Isolate CLI behaviour by mocking internal helpers."""
    fake_path = Path("datapackage.json")
    mock_resolve_uri.return_value = fake_path
    # Simulate running the app from the command line (but without calling sys.exit())
    app(["build", "datapackage.json"], result_action="return_value")

    # Checking that the correct values were passed to the internal functions
    mock_resolve_uri.assert_called_once_with("datapackage.json")
    mock_read_properties.assert_called_once_with(fake_path)


# === Checking stdout ===


def test_build_verbose_prints_output(capsys, datapackage_path):
    """--verbose should print output_dir, properties, template_dir, and style."""
    app(
        ["build", datapackage_path, "--verbose"],
        result_action="return_value",
    )
    expected = f"docs {_DATAPACKAGE_DATA} None BuildStyle.quarto_one_page\n"
    assert capsys.readouterr().out == expected


def test_build_no_verbose_produces_no_output(capsys, datapackage_path):
    """Without --verbose, build should produce no stdout."""
    app(["build", datapackage_path], result_action="return_value")
    assert capsys.readouterr().out == ""


# === File-based config ===


def test_build_reads_uri_from_flower_toml(tmp_path, monkeypatch):
    """Build args specified in .flower.toml should overwrite the default values."""
    toml_path = tmp_path / ".flower.toml"
    toml_path.write_text(
        'uri = "custom.json"\n'
        'style = "quarto_resource_listing"\n'
        'template_dir = "my-templates/"\n'
        'output_dir = "my-docs/"\n'
        "verbose = true\n"
    )

    monkeypatch.chdir(tmp_path)

    _, bound, _ = app.parse_args(["build"])
    assert bound.arguments["uri"] == "custom.json"
    assert bound.arguments["style"] == BuildStyle.quarto_resource_listing
    assert bound.arguments["template_dir"] == Path("my-templates/")
    assert bound.arguments["output_dir"] == Path("my-docs/")
    assert bound.arguments["verbose"] is True


# TODO === view placeholder ===


def test_view() -> None:
    """view returns an empty string."""
    assert view() == ""
