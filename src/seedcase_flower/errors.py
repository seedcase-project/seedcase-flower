"""Custom exception handling for seedcase-flower."""

import sys
from pathlib import Path
from types import TracebackType
from typing import Any

from rich import print as rprint

from check_datapackage import check


def _pretty_print_exception(
    exc_type: type[BaseException],
    exc_value: BaseException,
) -> None:
    rprint(f"\n[red]{exc_type.__name__}[/red]: {exc_value}")


def no_traceback_hook(
    exc_type: type[BaseException],
    exc_value: BaseException,
    exc_traceback: TracebackType | None,
) -> None:
    if issubclass(exc_type, FlowerError):
        _pretty_print_exception(exc_type, exc_value)
    else:
        sys.__excepthook__(exc_type, exc_value, exc_traceback)


sys.excepthook = no_traceback_hook


def _is_running_from_ipython() -> bool:
    """Checks whether running in IPython interactive console or not."""
    try:
        from IPython import get_ipython
    except ImportError:
        return False
    else:
        return get_ipython() is not None


if _is_running_from_ipython():

    def no_traceback_in_ipython(
        self: Any,
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_traceback: TracebackType | None,
        tb_offset: None = None,
    ) -> None:
        """Hide tracebacks and correctly display rich markup in IPython."""
        if issubclass(exc_type, FlowerError):
            _pretty_print_exception(exc_type, exc_value)
        else:
            self.showtraceback(
                (exc_type, exc_value, exc_traceback), tb_offset=tb_offset
            )

    get_ipython().set_custom_exc((Exception,), no_traceback_in_ipython)


class FlowerError(Exception):
    """Base exception for seedcase-flower errors that hides traceback."""


class FileNotFound(FlowerError):
    """Error when a file is not found."""

    def __init__(self, path: Path | str) -> None:
        super().__init__(f"The file '{path}' does not exist.")
