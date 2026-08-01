"""API meta / compatibility models (``/api/v1/supported-versions``)."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class VersionInfo:
    """Target and minimum-supported version for one client channel."""

    target_version: str | None
    """The API's currently expected client version."""

    minimum_supported_version: str | None
    """Clients below this version may be rejected by future endpoint deploys."""

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "VersionInfo":
        data = data or {}
        return cls(
            target_version=data.get("targetVersion"),
            minimum_supported_version=data.get("minimumSupportedVersion"),
        )


@dataclass
class SupportedVersions:
    """API compatibility matrix reported by ``GET /api/v1/supported-versions``.

    Retrieved via :meth:`~onekommafive.Client.get_supported_versions`.
    Not system-scoped — one response per API deployment.
    """

    b2b: VersionInfo
    """Business-facing (installer/partner) client channel."""

    b2c: VersionInfo
    """Consumer-facing (end-user) client channel."""

    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SupportedVersions":
        return cls(
            b2b=VersionInfo.from_dict(data.get("b2b")),
            b2c=VersionInfo.from_dict(data.get("b2c")),
            raw=data,
        )
