"""Tests for the CLI commands."""

from pathlib import Path

import pytest
from check_datapackage.check import DataPackageError
from seedcase_soil import Address

from seedcase_flower.build_sections import (
    BuiltSection,
    _get_template_dir,
    _load_sections_toml,
)
from seedcase_flower.cli import app
from seedcase_flower.config import Config
from seedcase_flower.styles import Style, ViewStyle


@pytest.fixture
def mock_parse_source(mocker):
    """Mock _parse_source to isolate CLI tests from filesystem resolution."""
    return mocker.patch("seedcase_flower.cli.parse_source")


@pytest.fixture
def mock_read_properties(mocker):
    """Mock read_properties to isolate CLI tests from file I/O."""
    return mocker.patch("seedcase_flower.cli.read_properties")


@pytest.fixture
def mock_check(mocker):
    """Mock datapackage check to isolate CLI tests from schema checks."""
    return mocker.patch("seedcase_flower.cli.check")


@pytest.fixture
def mock_build_sections(mocker):
    """Mock build_sections to isolate CLI tests from template rendering."""
    return mocker.patch("seedcase_flower.cli.build_sections")


@pytest.fixture
def mock_write_sections(mocker):
    """Mock write_sections to isolate CLI tests from file I/O."""
    return mocker.patch("seedcase_flower.cli.write_sections")


# Testing CLI invocation ====


def test_build_with_mocked_internals(
    mock_parse_source,
    mock_read_properties,
    mock_check,
    mock_build_sections,
    mock_write_sections,
):
    """Isolate CLI behaviour by mocking internal helpers."""
    fake_source = Address(value="file:///datapackage.json", local=True)
    mock_parse_source.return_value = fake_source
    # Simulate running the app from the command line (but without calling sys.exit())
    app(["build", "datapackage.json"], result_action="return_value")

    # Checking that the correct values were passed to the internal functions
    mock_parse_source.assert_called_once_with("datapackage.json")
    mock_read_properties.assert_called_once_with(fake_source)
    mock_check.assert_called_once_with(mock_read_properties.return_value, error=True)
    mock_build_sections.assert_called_once_with(
        mock_read_properties.return_value, Config()
    )
    mock_write_sections.assert_called_once_with(
        mock_build_sections.return_value, Path("docs")
    )


# Checking stdout ====


def test_build_verbose_prints_output(
    capsys, datapackage_path, datapackage, tmp_path, monkeypatch
):
    """--verbose should print package name, package path, style, output dir, and created
    file paths."""
    monkeypatch.chdir(tmp_path)
    app(
        ["build", datapackage_path, "--verbose"],
        result_action="return_value",
    )

    out = capsys.readouterr().out.replace("\n", "")  # To not break long path

    for content in [
        datapackage["name"],
        datapackage_path,
        Style.quarto_one_page.name,
        "docs/",
        "docs/index.qmd",
    ]:
        assert content in out, f"Expected {content!r} to be a substring in {out!r}."


def test_build_no_verbose_produces_no_output(
    capsys, datapackage_path, tmp_path, monkeypatch
):
    """Without --verbose, build should produce no stdout."""
    monkeypatch.chdir(tmp_path)
    app(["build", datapackage_path], result_action="return_value")
    assert capsys.readouterr().out == ""


# File-based config ====


def test_build_reads_source_from_flower_toml(tmp_path, monkeypatch):
    """Build args specified in .flower.toml should overwrite the default values."""
    toml_path = tmp_path / ".flower.toml"
    toml_path.write_text(
        'style = "quarto_resource_listing"\n'
        'template_dir = "my-templates/"\n'
        'output_dir = "my-docs/"\n'
        "verbose = true\n"
    )

    monkeypatch.chdir(tmp_path)

    _, bound, _ = app.parse_args(["build"])
    assert bound.arguments["style"] == Style.quarto_resource_listing
    assert bound.arguments["template_dir"] == Path("my-templates/")
    assert bound.arguments["output_dir"] == Path("my-docs/")
    assert bound.arguments["verbose"] is True


def test_view_ignores_flower_toml(tmp_path, monkeypatch):
    """View should ignore any .flower.toml config and always use defaults."""
    toml_path = tmp_path / ".flower.toml"
    toml_path.write_text(
        'source = "custom.json\n'  # a comment to prevent ruff from wrapping this
        'style = "quarto_one_page"\n'
    )
    monkeypatch.chdir(tmp_path)

    _, bound, _ = app.parse_args(["view"])
    assert "source" not in bound.arguments
    assert "style" not in bound.arguments


# view ====


def test_view_styles_are_one_page():
    """Every ViewStyle member must map to a single-section (one-page) style."""
    for member in ViewStyle:
        style = Style[member.name]
        sections = _load_sections_toml(_get_template_dir(style))
        assert not sections.many_sections, (
            f"ViewStyle.{member.name} includes `Many` sections, "
            "but view styles must be single-page (exactly 1 `One` section)."
        )
        assert len(sections.one_sections) == 1, (
            f"ViewStyle.{member.name} has {len(sections.one_sections)} sections, "
            "but view styles must be single-page (exactly 1 `One` section)."
        )


def test_view_with_mocked_internals(mocker):
    """view should parse source, build sections, and render via Console."""
    mock_parse_source = mocker.patch("seedcase_flower.cli.parse_source")
    mock_read_properties = mocker.patch("seedcase_flower.cli.read_properties")
    mock_check = mocker.patch("seedcase_flower.cli.check")
    mock_build_sections = mocker.patch("seedcase_flower.cli.build_sections")
    mock_console_cls = mocker.patch("seedcase_flower.cli.Console")
    mock_console = mock_console_cls.return_value

    mock_build_sections.return_value = [
        BuiltSection(content="# Test", output_path=None)
    ]

    fake_source = Address(value="file:///datapackage.json", local=True)
    mock_parse_source.return_value = fake_source

    app(["view", "datapackage.json"], result_action="return_value")

    mock_parse_source.assert_called_once_with("datapackage.json")
    mock_read_properties.assert_called_once_with(fake_source)
    mock_check.assert_called_once_with(mock_read_properties.return_value, error=True)
    mock_build_sections.assert_called_once_with(
        mock_read_properties.return_value,
        Config(style=Style.quarto_one_page),
    )
    assert mock_console.print.called


def test_build_raises_on_invalid_datapackage(tmp_path):
    """build should check datapackage content and fail for malformed metadata."""
    json_file = tmp_path / "datapackage.json"
    json_file.write_text('{"name": "malformed-package", "resources": []}')

    with pytest.raises(DataPackageError, match="should be non-empty"):
        app(["build", str(json_file)], result_action="return_value")


def test_view_raises_on_invalid_datapackage(tmp_path):
    """view should check datapackage content and fail for malformed metadata."""
    json_file = tmp_path / "datapackage.json"
    json_file.write_text('{"name": "malformed-package", "resources": []}')

    with pytest.raises(DataPackageError, match="should be non-empty"):
        app(["view", str(json_file)], result_action="return_value")


# The color codes cannot easily be tested so we look at substrings
# instead of the exact full output
def test_view_renders_datapackage(capsys, datapackage_path):
    """view should render all key datapackage fields to the terminal."""
    app(["view", datapackage_path], result_action="return_value")
    output = capsys.readouterr().out

    # Package metadata
    assert "test-package" in output
    assert "Test Package" in output
    assert "MIT" in output
    assert "1.0.0" in output
    assert "A test datapackage" in output

    # Resource structure
    assert "Resources" in output
    assert "data" in output
    assert "data.csv" in output

    # Schema fields table
    assert "id" in output
    assert "integer" in output
    assert "name" in output
    assert "string" in output
