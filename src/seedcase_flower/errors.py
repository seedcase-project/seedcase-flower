"""Custom exception handling for seedcase-flower."""

from check_datapackage import setup_suppressed_tracebacks


class FlowerError(Exception):
    """Base class for all seedcase-flower exceptions."""

    def __init__(self, resolved_address: str, reason: str = "") -> None:
        """Initialize FlowerError with resolved_address and optional reason."""
        message = f"Could not load '{resolved_address}'."
        if reason:
            message += f" {reason}"
        super().__init__(message)


class FileDoesNotExistError(FlowerError):
    """Error when a local path does not point to an existing file."""

    def __init__(self, resolved_address: str) -> None:
        """Initialize FileDoesNotExistError with resolved_address."""
        super().__init__(
            resolved_address,
            "The file cannot be found; maybe there is a typo in the path?",
        )


class JSONFormatError(FlowerError):
    """Error when a file has invalid JSON format."""

    def __init__(self, resolved_address: str, json_error: str) -> None:
        """Initialize JSONFormatError with resolved_address and JSON error details."""
        super().__init__(
            resolved_address,
            f"When trying to load the JSON file, a formatting issue was found: {json_error}",
        )


class HTTP404Error(FlowerError):
    """Error when an HTTP request returns a 404 or other error status."""

    def __init__(self, resolved_address: str, code: int, reason: str) -> None:
        """Initialize HTTP404Error with resolved_address, status code, and reason."""
        super().__init__(resolved_address, f"HTTP Error {code}: {reason}")


class HTTPDomainError(FlowerError):
    """Error when unable to connect to server due to domain not being found."""

    def __init__(self, resolved_address: str) -> None:
        """Initialize HTTPDomainError with resolved_address."""
        super().__init__(
            resolved_address,
            "Couldn't connect to the server because the domain wasn't found.",
        )


# Set up traceback suppression for all custom exceptions
setup_suppressed_tracebacks(FlowerError)
