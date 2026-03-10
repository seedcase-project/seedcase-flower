"""Helper functions for internal use."""

from itertools import repeat
from typing import Callable, Iterable, Optional, TypeVar

from cyclopts.annotations import get_hint_name
from cyclopts.help import HelpEntry
from jinja2 import Environment, FileSystemLoader, select_autoescape
from jsonpath import findall
from pydantic import BaseModel, Field

from seedcase_flower.config import Config
from seedcase_flower.section import Content, Mode, Section
from seedcase_flower.styles import Style


@dataclass(frozen=True)
class Address:
    """A source parsed into an actual address."""

    value: str
    local: bool


def _parse_source(source: str) -> Address:
    split_source = parse.urlsplit(source)
    if split_source.scheme == "":
        split_source = split_source._replace(scheme="file")
    match split_source.scheme:
        case "file":
            return _convert_to_path(split_source)
        case "https":
            return _convert_to_https(split_source)
        case "gh" | "github":
            return _convert_to_github(split_source)
        case _:
            raise ValueError(
                "The source must be either a path to an existing file or "
                "folder or have one of the following prefixes: `https:`, "
                "`gh:`, `github:`"
            )


def _convert_to_path(source: parse.SplitResult) -> Address:
    path = Path(source.path).resolve()
    if path.is_dir():
        path /= "datapackage.json"
    source = source._replace(path=path.as_posix())
    return Address(value=source.geturl(), local=True)


def _convert_to_https(source: parse.SplitResult) -> Address:
    return Address(value=source.geturl(), local=False)


def _convert_to_github(source: parse.SplitResult) -> Address:
    full_path = f"{source.netloc}{source.path}"
    if "@" in full_path:
        owner_repo, ref = full_path.rsplit("@", 1)
    else:
        owner_repo, ref = full_path, "main"
    return Address(
        value=source._replace(
            scheme="https",
            netloc="raw.githubusercontent.com",
            path=f"/{owner_repo}/{ref}/datapackage.json",
        ).geturl(),
        local=False,
    )


def _format_param_help(entry: HelpEntry) -> str:
    """Re-structure the parameter help into a more readable format."""
    # Sort to put the flag first (eg `--source SOURCE` instead of the default
    # `SOURCE --source`)
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


In = TypeVar("In")
Out = TypeVar("Out")


def _map(x: Iterable[In], fn: Callable[[In], Out]) -> list[Out]:
    return list(map(fn, x))


def _filter(x: Iterable[In], fn: Callable[[In], bool]) -> list[In]:
    return list(filter(fn, x))
