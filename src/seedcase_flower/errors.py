"""Custom exception handling for seedcase-flower."""

from pathlib import Path

from check_datapackage import setup_suppressed_tracebacks


class FileLoadError(Exception):
    """Base error when a file cannot be loaded (local or remote)."""

    def __init__(self, path: str | Path, reason: str = "") -> None:
        """Initialize FileLoadError with path and optional reason."""
        message = f"Could not load '{path}'."
        if reason:
            message += f" {reason}"
        super().__init__(message)


class FileDoesNotExistError(FileLoadError):
    """Error when a local file does not exist."""

    def __init__(self, path: str | Path) -> None:
        """Initialize FileDoesNotExistError with path."""
        super().__init__(path, "File does not exist")


class JSONFormatError(FileLoadError):
    """Error when a file has invalid JSON format."""

    def __init__(self, path: str | Path, json_error: str) -> None:
        """Initialize JSONFormatError with path and JSON error details."""
        super().__init__(path, f"Invalid JSON format: {json_error}")


class HTTP404Error(FileLoadError):
    """Error when an HTTP request returns a 404 or other error status."""

    def __init__(self, url: str, code: int, reason: str) -> None:
        """Initialize HTTP404Error with URL, status code, and reason."""
        super().__init__(url, f"HTTP Error {code}: {reason}")


class HTTPDomainError(FileLoadError):
    """Error when unable to connect to server (domain not found)."""

    def __init__(self, url: str) -> None:
        """Initialize HTTPDomainError with URL."""
        super().__init__(url, "Unable to connect to server (domain not found)")


# Set up traceback suppression for all custom exceptions
setup_no_traceback_hooks(FileLoadError)
