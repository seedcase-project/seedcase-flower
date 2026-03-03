"""Helper functions for private use."""

import json
import tomllib
from dataclasses import dataclass
from importlib.resources import files
from itertools import repeat
from pathlib import Path
from typing import Any, Callable, Iterable, Optional, TypeVar, Union
from urllib import parse

from cyclopts.annotations import get_hint_name
from cyclopts.help import HelpEntry
from jinja2 import Environment, FileSystemLoader, select_autoescape
from jsonpath import findall
from pydantic import BaseModel, Field

from seedcase_flower.config import Config
from seedcase_flower.section import Content, Mode, Section
from seedcase_flower.styles import BuildStyle, ViewStyle


@dataclass(frozen=True)
class Uri:
    """A parsed URI with its normalised value and locality flag."""

    value: str
    local: bool


def _parse_uri(uri: str) -> Uri:
    split_uri = parse.urlsplit(uri)
    if split_uri.scheme == "":
        split_uri = split_uri._replace(scheme="file")
    match split_uri.scheme:
        case "file":
            return _convert_to_file_uri(split_uri)
        case "https":
            return _convert_to_https_uri(split_uri)
        case "gh" | "github":
            return _convert_to_github_uri(split_uri)
        case _:
            raise ValueError(
                "The uri must be either a path to an existing file/folder "
                "or a URI with one of the following URI prefixes: "
                "`file:`, `https:`, `gh:`, `github:`"
            )


def _convert_to_file_uri(split_file_uri: parse.SplitResult) -> Uri:
    path = Path(split_file_uri.path).resolve()
    if path.is_dir():
        path /= "datapackage.json"
    split_file_uri = split_file_uri._replace(path=path.as_posix())
    return Uri(value=split_file_uri.geturl(), local=True)


def _convert_to_https_uri(split_https_uri: parse.SplitResult) -> Uri:
    return Uri(value=split_https_uri.geturl(), local=False)


def _convert_to_github_uri(split_gh_uri: parse.SplitResult) -> Uri:
    return Uri(
        value=split_gh_uri._replace(
            scheme="https",
            netloc="raw.githubusercontent.com",
            path=f"/{split_gh_uri.path}/refs/heads/main/datapackage.json",
        ).geturl(),
        local=False,
    )


def _format_param_help(entry: HelpEntry) -> str:
    """Re-structure the parameter help into a more readable format."""
    # Sort to put the flag first (eg `--uri URI` instead of the default `URI --uri`)
    names = map(_add_highlight_syntax, sorted(entry.names), repeat(entry.type))
    return f"{' '.join(names)}".strip()


def _add_highlight_syntax(name: str, entry_type: Optional[type]) -> str:
    """Add markup character to highlight in colors, etc where desired."""
    formatted_name = f"[bold cyan]{name}[/bold cyan]"
    if not name.startswith("-"):
        # Matching the `dim` used by default in cyclopts for `choices` and
        # `defaults` in the description
        formatted_name = f"[dim]<{name}>[/dim]"

        # Don't output redundant value placeholder for boolean flags
        if get_hint_name(entry_type) == "bool":
            formatted_name = ""
    return formatted_name


def _read_properties(uri: Uri) -> dict[str, Any]:
    if uri.local:
        path = Path(parse.urlsplit(uri.value).path)
        with open(path) as properties_file:
            return json.load(properties_file)  # type: ignore # TODO fix in read_prop PR
    else:
        # TODO read from remote file
        return {"placeholder": uri.value}


In = TypeVar("In")
Out = TypeVar("Out")


def _map(x: Iterable[In], fn: Callable[[In], Out]) -> list[Out]:
    return list(map(fn, x))


def _filter(x: Iterable[In], fn: Callable[[In], bool]) -> list[In]:
    return list(filter(fn, x))


class SectionsFile(BaseModel, frozen=True):
    """Data model of the contents of the `sections.toml` file.

    Attributes:
        sections: The sections in the config file.
    """

    sections: list[Section] = Field(alias="section")


@dataclass(frozen=True)
class BuiltSection:
    """A section that has been built from a template.

    Attributes:
        content: The rendered template as a string.
        output_path: The path where the section should be written, relative
            to `Config.output_dir`. Sections displayed in the terminal don't
            have an `output_path`.
    """

    content: str
    output_path: Optional[Path] = None


def _get_template_dir(style: Union[BuildStyle, ViewStyle]) -> Path:
    styles_path = Path(str(files("seedcase_flower").joinpath("styles")))
    return styles_path / style.name


def _load_sections(template_dir: Path) -> list[Section]:
    if not template_dir.is_dir():
        raise NotADirectoryError(f"Template directory '{template_dir}' does not exist.")

    template_path = template_dir / "sections.toml"
    if not template_path.is_file():
        raise FileNotFoundError(
            f"Template directory '{template_dir}' does not contain a "
            "sections.toml file."
        )

    with open(template_path, mode="rb") as file:
        sections_file = tomllib.load(file)

    return SectionsFile.model_validate(sections_file).sections


def _build_content(
    content: Content, properties: dict[str, Any], template_dir: Path, env: Environment
) -> str:
    # TODO: handle Mode.many
    if content.mode == Mode.many:
        raise NotImplementedError()

    selected_properties = findall(content.jsonpath, properties)
    if len(selected_properties) > 1:
        raise ValueError(
            f"`Mode.one` expects at most one match. JSON path {content.jsonpath!r} "
            f"returned {len(selected_properties)} matches. Use a more specific "
            "JSON path or switch to `Mode.many`."
        )

    template_path = template_dir / content.template_path
    if not template_path.is_file():
        raise FileNotFoundError(
            f"Template file '{content.template_path}' does not exist in the template "
            f"directory '{template_dir}'."
        )

    template = env.get_template(template_path.name)
    return template.render(
        **{
            content.jinja_variable: selected_properties[0]
            if selected_properties
            else None
        }
    )


def _build_section(
    section: Section, properties: dict[str, Any], template_dir: Path, env: Environment
) -> BuiltSection:
    built_contents = _map(
        section.contents,
        lambda content: _build_content(content, properties, template_dir, env),
    )
    return BuiltSection(
        output_path=section.output_path,
        content="\n".join(built_contents),
    )


def _inline_code(value: Optional[str]) -> Optional[str]:
    return f"`{value}`" if value else None


def _inline_code_list(value: Union[str, list[str]]) -> str:
    # Some Data Package fields allow either a string or a list of strings
    if isinstance(value, str):
        value = [value]
    return ", ".join(_map(value, lambda item: f"`{item}`"))


def _create_jinja_env(template_dir: Path) -> Environment:
    env = Environment(
        loader=FileSystemLoader(template_dir),
        trim_blocks=True,
        autoescape=select_autoescape(
            enabled_extensions=(
                "html.jinja",
                "xml.jinja",
            ),
            default=False,
        ),
    )
    # Render a list of strings as comma-separated inline code
    env.filters["_inline_code_list"] = _inline_code_list
    # Render a single value as inline code
    env.filters["_inline_code"] = _inline_code
    return env


def _build_sections(properties: dict[str, Any], config: Config) -> list[BuiltSection]:
    template_dir = config.template_dir or _get_template_dir(config.style)
    sections = _load_sections(template_dir)
    env = _create_jinja_env(template_dir)
    return _map(
        sections,
        lambda section: _build_section(section, properties, template_dir, env),
    )
