"""Functions for parsing the source for a Data Package."""

from dataclasses import dataclass
from pathlib import Path
from urllib import parse


@dataclass(frozen=True)
class Address:
    """A source parsed into an actual address."""

    value: str
    local: bool


def parse_source(source: str) -> Address:
    """Parse the source of a Data Package into a formal `Address`.

    Args:
        source: The string representation for the location of a Data Package
            metadata, either as a path, `https`, or `gh`/`github` repository.

    Returns:
        A formal `Address` class.

    Raises:
        ValueError: If the `source` contains something other than what
            Flower can accept.

    Examples:
        ```{python}
        import seedcase_flower as fl
        print(fl.parse_source("./datapackage.json"))
        print(fl.parse_source("https://raw.githubusercontent.com/seedcase-project/seedcase-flower/refs/heads/main/docs/includes/datapackage.json"))
        ```
    """
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
