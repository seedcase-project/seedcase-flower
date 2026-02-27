"""Helper functions for private use."""

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Iterable, Optional, TypeVar, cast


class BuildStyle(Enum):
    """Built-in styles for outputting to file."""

    quarto_one_page = "quarto_one_page"
    quarto_resource_listing = "quarto_resource_listing"
    quarto_resource_tables = "quarto_resource_tables"


# Output maybe str? Path?
# Use `match` inside for strictness on URI types? Or use a library for URI parsing?
# TODO Extend to parse strings and return either URL or Path
def _resolve_uri(uri: str) -> Path:
    return Path(uri)


# TODO Extend to also read properties from URLs
def _read_properties(path: Path) -> dict[str, Any]:
    with open(path) as properties_file:
        datapackage: dict[str, Any] = json.load(properties_file)
        return datapackage


In = TypeVar("In")
Out = TypeVar("Out")


def _filter(x: Iterable[In], fn: Callable[[In], bool]) -> list[In]:
    return list(filter(fn, x))


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


def _write_sections(built_sections: list[BuiltSection], output_dir: Path) -> None:
    if _filter(built_sections, lambda section: section.output_path is None):
        raise ValueError(
            "At least one section in `sections.toml` is missing an output path. "
            "When using the `build` command, all sections must have an output path."
        )

    for built_section in built_sections:
        output_path = output_dir / cast(Path, built_section.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(built_section.content)
