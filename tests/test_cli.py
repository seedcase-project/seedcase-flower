"""Tests for the CLI commands."""

from pathlib import Path
from textwrap import dedent

import pytest

from seedcase_flower.cli import app, view
from seedcase_flower.internals import Uri
from seedcase_flower.styles import BuildStyle


@pytest.fixture
def mock_parse_uri(mocker):
    """Mock _parse_uri to isolate CLI tests from filesystem resolution."""
    return mocker.patch("seedcase_flower.cli._parse_uri")


@pytest.fixture
def mock_read_properties(mocker):
    """Mock _read_properties to isolate CLI tests from file I/O."""
    return mocker.patch("seedcase_flower.cli._read_properties")


# Testing CLI invocation ====


def test_build_with_mocked_internals(mock_parse_uri, mock_read_properties):
    """Isolate CLI behaviour by mocking internal helpers."""
    fake_uri = Uri(value="file:///datapackage.json", local=True)
    mock_parse_uri.return_value = fake_uri
    # Simulate running the app from the command line (but without calling sys.exit())
    app(["build", "datapackage.json"], result_action="return_value")

    # Checking that the correct values were passed to the internal functions
    mock_parse_uri.assert_called_once_with("datapackage.json")
    mock_read_properties.assert_called_once_with(fake_uri)


# Checking stdout ====


# TODO: Update this when verbose is added.
def test_build_verbose_prints_output(capsys, datapackage_path, datapackage):
    """--verbose should print output_dir, properties, template_dir, and style."""
    app(
        ["build", datapackage_path, "--verbose"],
        result_action="return_value",
    )
    expected = f"docs {datapackage} None BuildStyle.quarto_one_page\n"
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
    │ <build>    Build human-readable documentation from a datapackage.json file.            │
    │ --help     Display this message and exit.                                              │
    │ --version  Display application version.                                                │
    ╰────────────────────────────────────────────────────────────────────────────────────────╯
    """  # noqa
)

_BUILD_HELP_PAGE = dedent(
    """\
    Usage: seedcase-flower build [ARGS]

    Build human-readable documentation from a datapackage.json file.

    ╭─ Parameters ───────────────────────────────────────────────────────────────────────────╮
    │ --uri <URI>                    The path to a local datapackage.json file or its parent │
    │                                folder. Can also be an https: URL to a remote           │
    │                                datapackage.json or a github: / gh: URI pointing to a   │
    │                                repo with a datapackage.json in the repo root (in the   │
    │                                format gh:org/repo, which can also include reference to │
    │                                a tag or branch, such as gh:org/repo@main or            │
    │                                `gh:org/repo@1.0.1).                                    │
    │                                [default: datapackage.json]                             │
    │ --style <STYLE>                The style used to structure the output. If a template   │
    │                                directory is given, this parameter will be ignored.     │
    │                                [choices: quarto-one-page, quarto-resource-listing,     │
    │                                quarto-resource-tables]                                 │
    │                                [default: quarto-one-page]                              │
    │ --template-dir <TEMPLATE-DIR>  The directory that contains the Jinja template files    │
    │                                and sections.toml. When set, it will override any       │
    │                                built-in style given by the style parameter.            │
    │                                [default: None]                                         │
    │ --output-dir <OUTPUT-DIR>      The directory to save the generated files in.           │
    │                                [default: docs]                                         │
    │ --verbose                      If True, prints additional information to the console.  │
    │                                [default: False]                                        │
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


# It was not possible to include these color markup tags directly in the help string
# test above because printing them out explicitly in the rich console messes up the
# column widths in cyclopts
def test_build_help_page_applies_rich_markup(capsys):
    """build --help should apply bold-cyan to flags and dim to placeholders."""
    from rich.console import Console

    markup_console = Console(
        width=90,
        force_terminal=False,
        highlight=False,
        color_system=None,
        markup=False,
        legacy_windows=False,
    )
    with pytest.raises(SystemExit):
        app(["build", "--help"], console=markup_console)
    output = capsys.readouterr().out
    assert "[bold cyan]--uri[/bold cyan]" in output
    assert "[dim]<URI>[/dim]" in output
    assert "[bold cyan]--style[/bold cyan]" in output
    assert "[dim]<STYLE>[/dim]" in output
    assert "[bold cyan]--verbose[/bold cyan]" in output
    # Boolean flags must not produce a positional placeholder
    assert "[dim]<verbose>[/dim]" not in output


# view (placeholder) ====


def test_view() -> None:
    """view returns an empty string."""
    assert view() == ""
