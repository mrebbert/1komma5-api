"""User profile model (``/api/v1/users/me``)."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConnectedSystem:
    """One entry in :attr:`User.connected_systems` — summary of a site the user has access to."""

    system_id: str
    """System UUID."""

    name: str | None
    """Site display name (API field: ``systemName``)."""

    address_name: str | None
    address_line1: str | None
    address_line2: str | None
    address_zip_code: str | None
    address_city: str | None
    address_country: str | None
    technical_contact_id: str | None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConnectedSystem":
        return cls(
            system_id=data["systemId"],
            name=data.get("systemName"),
            address_name=data.get("addressName"),
            address_line1=data.get("addressLine1"),
            address_line2=data.get("addressLine2"),
            address_zip_code=data.get("addressZipCode"),
            address_city=data.get("addressCity"),
            address_country=data.get("addressCountry"),
            technical_contact_id=data.get("technicalContactId"),
        )


@dataclass
class User:
    """Authenticated user profile returned by the identity service."""

    id: str
    email: str

    first_name: str | None
    last_name: str | None
    phone: str | None
    status: str | None
    external_id: str | None
    """Third-party identity, typically ``"auth0|..."``."""

    connected_systems: list[ConnectedSystem]
    """All systems the user is authorised for (summary view)."""

    created_at: str | None

    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "User":
        """Construct a :class:`User` from a raw API response dictionary."""
        return cls(
            id=data["id"],
            email=data["email"],
            first_name=data.get("firstName"),
            last_name=data.get("lastName"),
            phone=data.get("phone"),
            status=data.get("status"),
            external_id=data.get("externalId"),
            connected_systems=[
                ConnectedSystem.from_dict(s) for s in data.get("connectedSystems") or []
            ],
            created_at=data.get("createdAt"),
            raw=data,
        )
