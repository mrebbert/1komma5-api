"""Site status and asset inventory models (``/api/v2/sites/{id}/status-and-assets``)."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Asset:
    """One hardware asset (inverter, heat pump, meter, EV charger, …) at a site.

    Returned as part of :class:`SiteStatus` by
    :meth:`~onekommafive.System.get_status_and_assets`.

    The ``connection_status`` and ``network_address`` fields are flattened from
    the nested ``connectionStatus.status`` / ``network.address`` objects in the
    raw response.
    """

    id: str
    """Asset UUID."""

    type: str
    """Asset type, e.g. ``"HYBRID"``, ``"HEAT_PUMP"``, ``"METER"``, ``"EV_CHARGER"``."""

    emp_type: str | None
    """Energy management provider type, e.g. ``"GRIDX"``."""

    name: str | None
    """Human-readable display name (typically only set for EV chargers / wallboxes)."""

    connection_status: str | None
    """Flattened from ``connectionStatus.status`` — e.g. ``"CONNECTED"``."""

    manufacturer: str | None
    """Hardware manufacturer, e.g. ``"Sungrow"``."""

    model: str | None
    """Hardware model identifier, e.g. ``"SH6.0RT-V112"``."""

    serial_number: str | None
    """Hardware serial number (API field: ``serialnumber``, lowercase ``n``)."""

    firmware: str | None
    """Firmware version string (often ``None`` for meters)."""

    network_address: str | None
    """Flattened from ``network.address`` — usually a local IPv4 address."""

    heat_pump_meter_type: str | None
    """Heat-pump meter classification, e.g. ``"HOUSEHOLD"`` (only on ``HEAT_PUMP`` assets)."""

    raw: dict[str, Any] = field(repr=False)
    """The complete raw API asset dictionary."""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Asset":
        """Construct an :class:`Asset` from a raw API asset dictionary."""
        return cls(
            id=data["id"],
            type=data.get("type", ""),
            emp_type=data.get("empType"),
            name=data.get("name"),
            connection_status=(data.get("connectionStatus") or {}).get("status"),
            manufacturer=data.get("manufacturer"),
            model=data.get("model"),
            serial_number=data.get("serialnumber"),
            firmware=data.get("firmware"),
            network_address=(data.get("network") or {}).get("address"),
            heat_pump_meter_type=data.get("heatPumpMeterType"),
            raw=data,
        )


@dataclass
class SiteStatus:
    """Overall connection status and asset inventory for a site.

    Returned by :meth:`~onekommafive.System.get_status_and_assets`
    (``GET /api/v2/sites/{id}/status-and-assets``).
    """

    status: str | None
    """Overall site connection status, e.g. ``"CONNECTED"``."""

    assets: list[Asset]
    """All hardware assets installed at the site (inverter, meter, heat pump, EV charger, …)."""

    raw: dict[str, Any] = field(repr=False)
    """The complete raw API response."""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SiteStatus":
        """Construct a :class:`SiteStatus` from a raw API response dictionary."""
        return cls(
            status=data.get("status"),
            assets=[Asset.from_dict(a) for a in data.get("assets") or []],
            raw=data,
        )
