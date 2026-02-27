"""Custom exception hierarchy for the 1KOMMA5° API client."""


class ApiError(Exception):
    """Base class for all errors raised by the 1KOMMA5° API client."""


class AuthenticationError(ApiError):
    """Raised when authentication fails.

    This covers invalid credentials, expired tokens that cannot be
    refreshed, or unexpected responses from the OAuth2 endpoint.
    """

    def __init__(self, message: str = "Authentication failed") -> None:
        self.message = message
        super().__init__(self.message)


class RequestError(ApiError):
    """Raised when an API request returns an unexpected HTTP status code.

    Inspect ``message`` for the raw response body returned by the server.
    """

    def __init__(self, message: str = "Request failed") -> None:
        self.message = message
        super().__init__(self.message)
