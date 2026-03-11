"""Custom exception handling for seedcase-flower."""

from pathlib import Path

from check_datapackage import setup_no_traceback_hooks


class FlowerError(Exception):
    """Base exception for seedcase-flower errors."""


class FileLoadError(FlowerError):
    """Error when a file cannot be loaded (local or remote)."""

    def __init__(self, path: str | Path, reason: str = "") -> None:
        """Initialize FileLoadError with path and optional reason."""
        message = f"Could not load '{path}'."
        if reason:
            message += f" {reason}"
        super().__init__(message)


setup_no_traceback_hooks(FlowerError)
