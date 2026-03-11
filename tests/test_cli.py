"""Tests for the CLI commands."""

from io import StringIO
from pathlib import Path
from textwrap import dedent

import pytest
from rich.console import Console
from rich.markdown import Markdown

from seedcase_flower.build_sections import (
    BuiltSection,
    _get_template_dir,
    _load_sections_toml,
)
from seedcase_flower.cli import _CONSOLE_THEME, app
from seedcase_flower.config import Config
from seedcase_flower.parse_source import Address
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
def mock_build_sections(mocker):
    """Mock build_sections to isolate CLI tests from template rendering."""
    return mocker.patch("seedcase_flower.cli.build_sections")


@pytest.fixture
def mock_write_sections(mocker):
    """Mock write_sections to isolate CLI tests from file I/O."""
    return mocker.patch("seedcase_flower.cli.write_sections")


# Testing CLI invocation ====


def test_build_with_mocked_internals(
    mock_parse_source, mock_read_properties, mock_build_sections, mock_write_sections
):
    """Isolate CLI behaviour by mocking internal helpers."""
    fake_source = Address(value="file:///datapackage.json", local=True)
    mock_parse_source.return_value = fake_source
    # Simulate running the app from the command line (but without calling sys.exit())
    app(["build", "datapackage.json"], result_action="return_value")

    # Checking that the correct values were passed to the internal functions
    mock_parse_source.assert_called_once_with("datapackage.json")
    mock_read_properties.assert_called_once_with(fake_source)
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
        'source = "custom.json"\n'
        'style = "quarto_resource_listing"\n'
        'template_dir = "my-templates/"\n'
        'output_dir = "my-docs/"\n'
        "verbose = true\n"
    )

    monkeypatch.chdir(tmp_path)

    _, bound, _ = app.parse_args(["build"])
    assert bound.arguments["source"] == "custom.json"
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


# Help output ====

_HELP_PAGE = dedent(
    """\
    Usage: seedcase-flower COMMAND

    Flower generates human-readable documentation from Data Packages.

    ╭─ Commands ─────────────────────────────────────────────────────────────────────────────╮
    │ <build>               Build human-readable documentation from a datapackage.json file. │
    │ <view>                Display the contents of a datapackage.json in a human-friendly   │
    │                       way.                                                             │
    │ --help                Display this message and exit.                                   │
    │ --install-completion  Install shell completion for this application.                   │
    │ --version             Display application version.                                     │
    ╰────────────────────────────────────────────────────────────────────────────────────────╯
    """  # noqa
)


_BUILD_HELP_PAGE = dedent(
    """\
    Usage: seedcase-flower build [ARGS]

    Build human-readable documentation from a datapackage.json file.

    ╭─ Parameters ───────────────────────────────────────────────────────────────────────────╮
    │ --source <SOURCE>              The location of a datapackage.json, defaults to a file  │
    │                                or folder path. Can also be an https: source to a       │
    │                                remote datapackage.json or a github: / gh: pointing to  │
    │                                a repo with a datapackage.json in the repo root (in the │
    │                                format gh:org/repo, which can also include reference to │
    │                                a tag or branch, such as gh:org/repo@main or            │
    │                                gh:org/repo@1.0.1).                                     │
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

_VIEW_HELP_PAGE = dedent(
    """\
    Usage: seedcase-flower view [ARGS]

    Display the contents of a datapackage.json in a human-friendly way.

    ╭─ Parameters ───────────────────────────────────────────────────────────────────────────╮
    │ --source <SOURCE>  The location of a datapackage.json, defaults to a file or folder    │
    │                    path. Can also be an https: source to a remote datapackage.json or  │
    │                    a github: / gh: pointing to a repo with a datapackage.json in the   │
    │                    repo root (in the format gh:org/repo, which can also include        │
    │                    reference to a tag or branch, such as gh:org/repo@main or           │
    │                    gh:org/repo@1.0.1).                                                 │
    │                    [default: datapackage.json]                                         │
    │ --style <STYLE>    The style used to display the output in the terminal. Must be a     │
    │                    single-page style.                                                  │
    │                    [choices: quarto-one-page]                                          │
    │                    [default: quarto-one-page]                                          │
    ╰────────────────────────────────────────────────────────────────────────────────────────╯
    """  # noqa
)

_CHANGED_MSG = (
    "The `{cmd}` help output changed. Run `just generate-help-strings` "
    "and paste the updated string into the relevant test."
)


@pytest.fixture
def console():
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
    assert "[bold cyan]--source[/bold cyan]" in output
    assert "[dim]<SOURCE>[/dim]" in output
    assert "[bold cyan]--style[/bold cyan]" in output
    assert "[dim]<STYLE>[/dim]" in output
    assert "[bold cyan]--verbose[/bold cyan]" in output
    # Boolean flags must not produce a positional placeholder
    assert "[dim]<verbose>[/dim]" not in output


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
    mock_build_sections.assert_called_once_with(
        mock_read_properties.return_value,
        Config(style=Style.quarto_one_page),
    )
    assert mock_console.print.called


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


def test_styled_markdown_table_renders_box_and_header():
    """Markdown tables should render with a heavy-head box and column separators."""
    md = "| A | B |\n|---|---|\n| 1 | 2 |\n"
    out = StringIO()
    Console(file=out, theme=_CONSOLE_THEME, no_color=True).print(Markdown(md))
    output = out.getvalue()
    assert "┏" in output  # heavy outer box top
    assert "┡" in output  # heavy-to-light header separator
    assert "┴" in output  # bottom border with column joins
    assert "A" in output
    assert "B" in output


def test_view_help_page(capsys, console):
    """view --help should document source and style parameters."""
    with pytest.raises(SystemExit):
        app(["view", "--help"], console=console)
    assert capsys.readouterr().out == _VIEW_HELP_PAGE, _CHANGED_MSG.format(cmd="view")
