"""User profile model (``/api/v1/users/me``)."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class User:
    """Authenticated user profile returned by the identity service."""

    id: str
    email: str
    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "User":
        """Construct a :class:`User` from a raw API response dictionary."""
        return cls(
            id=data["id"],
            email=data["email"],
            raw=data,
        )
