"""Tests for the CLI commands."""

import json
from pathlib import Path
from textwrap import dedent

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


# Testing CLI invocation ====


def test_build_with_mocked_internals(mock_resolve_uri, mock_read_properties):
    """Isolate CLI behaviour by mocking internal helpers."""
    fake_path = Path("datapackage.json")
    mock_resolve_uri.return_value = fake_path
    # Simulate running the app from the command line (but without calling sys.exit())
    app(["build", "datapackage.json"], result_action="return_value")

    # Checking that the correct values were passed to the internal functions
    mock_resolve_uri.assert_called_once_with("datapackage.json")
    mock_read_properties.assert_called_once_with(fake_path)


# Checking stdout ====


# TODO: Update this when verbose is added.
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


# File-based config ====


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


# Help output ====

_HELP_PAGE = dedent(
    """\
    Usage: seedcase-flower COMMAND

    Flower generates human-readable documentation from Data Packages.

    ╭─ Commands ─────────────────────────────────────────────────────────────────────────────╮
    │ build        Build human-readable documentation from a datapackage.json file.          │
    │ --help (-h)  Display this message and exit.                                            │
    │ --version    Display application version.                                              │
    ╰────────────────────────────────────────────────────────────────────────────────────────╯
    """  # noqa
)

_BUILD_HELP_PAGE = dedent(
    """\
    Usage: seedcase-flower build [ARGS]

    Build human-readable documentation from a datapackage.json file.

    ╭─ Parameters ───────────────────────────────────────────────────────────────────────────╮
    │ URI --uri                    The path to a local datapackage.json file or its parent   │
    │                              folder. Can also be an https: URL to a remote             │
    │                              datapackage.json or a github: / gh: URI pointing to a     │
    │                              repo with a datapackage.json in the repo root (in the     │
    │                              format gh:org/repo). [default: datapackage.json]          │
    │ STYLE --style                The style used to structure the output. If a template     │
    │                              directory is given, this parameter will be ignored.       │
    │                              [choices: quarto-one-page, quarto-resource-listing,       │
    │                              quarto-resource-tables] [default: quarto-one-page]        │
    │ TEMPLATE-DIR --template-dir  The directory that contains the Jinja template files and  │
    │                              sections.toml. When set, it will override any built-in    │
    │                              style given by the style parameter.                       │
    │ OUTPUT-DIR --output-dir      The directory to save the generated files in. [default:   │
    │                              docs]                                                     │
    │ VERBOSE --verbose            If True, prints additional information to the console.    │
    │                              [default: False]                                          │
    ╰────────────────────────────────────────────────────────────────────────────────────────╯
    """  # noqa
)

_CHANGED_MSG = (
    "The `{cmd}` help output changed. Run `just generate-help-strings` "
    "and paste the updated string into the relevant test."
)


@pytest.fixture
def console():
    from rich.console import Console

    return Console(
        width=90,
        force_terminal=True,
        highlight=False,
        color_system=None,
        legacy_windows=False,
    )


def test_help_page(capsys, console):
    """Top-level --help should match expected output."""
    with pytest.raises(SystemExit):
        app(["--help"], console=console)
    assert capsys.readouterr().out == _HELP_PAGE, _CHANGED_MSG.format(cmd="general")


def test_build_help_page(capsys, console):
    """build --help should document all parameters with defaults and choices."""
    with pytest.raises(SystemExit):
        app(["build", "--help"], console=console)
    assert capsys.readouterr().out == _BUILD_HELP_PAGE, _CHANGED_MSG.format(cmd="build")


# view (placeholder) ====


def test_view() -> None:
    """view returns an empty string."""
    assert view() == ""
