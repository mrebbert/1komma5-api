"""Custom exception hierarchy for the 1KOMMA5° API client."""


class ApiError(Exception):
    """Base class for all errors raised by the 1KOMMA5° API client."""

    def __init__(self, message: str = "") -> None:
        super().__init__(message)
        self.message = message


class AuthenticationError(ApiError):
    """Raised when authentication fails."""


class RequestError(ApiError):
    """Raised when an API request returns an unexpected HTTP status code."""
