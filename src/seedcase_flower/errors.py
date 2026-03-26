"""Custom exception handling for seedcase-flower."""


class FlowerError(Exception):
    """Base class for all seedcase-flower exceptions."""

    def __init__(self, resolved_address: str, reason: str = "") -> None:
        """Initialize FlowerError with resolved_address and optional reason."""
        message = f"Could not load '{resolved_address}'.\n"
        if reason:
            message += f"{reason}"
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
            f"A JSON formatting issue was found: {json_error}",
        )


class HTTPStatusError(FlowerError):
    """Error when an HTTP request returns an error status code."""

    def __init__(self, resolved_address: str, code: int, reason: str) -> None:
        """Initialize HTTPStatusError with resolved_address, status code, and reason."""
        super().__init__(resolved_address, f"Error code {code}: {reason}")


class HTTPDomainError(FlowerError):
    """Error when unable to connect to server due to domain not being found."""

    def __init__(self, resolved_address: str) -> None:
        """Initialize HTTPDomainError with resolved_address."""
        super().__init__(
            resolved_address,
            "Couldn't connect to the server because the domain wasn't found.",
        )


class NotJSONError(FlowerError):
    """Error when a URL does not return JSON content."""

    def __init__(self, resolved_address: str, content_type: str) -> None:
        """Initialize NotJSONError with resolved_address and actual content type."""
        super().__init__(
            resolved_address,
            f"Expected JSON but received '{content_type}'.",
        )
