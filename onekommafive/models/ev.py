"""EV / wallbox related models."""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ChargingMode(StrEnum):
    """Charging strategy for an EV charger.

    The vendor decides which modes a site offers (see
    :meth:`~onekommafive.System.get_displayed_ev_charging_modes`), so the
    members below are the values seen so far, not a closed set. A value the
    library does not know yet still converts: ``ChargingMode("NEW_MODE")``
    returns a member whose ``value`` is ``"NEW_MODE"``. Only the empty string
    raises ``ValueError``.
    """

    SMART_CHARGE = "SMART_CHARGE"
    """Charge according to the energy-management system's optimisation."""

    QUICK_CHARGE = "QUICK_CHARGE"
    """Charge as fast as possible regardless of grid price."""

    SOLAR_CHARGE = "SOLAR_CHARGE"
    """Charge only when surplus solar power is available."""

    PROGRAM_CHARGE = "PROGRAM_CHARGE"
    """Offered instead of ``SMART_CHARGE`` by sites in an early registration stage."""

    @classmethod
    def _missing_(cls, value: object) -> "ChargingMode | None":
        """Create (and cache) a member for a value the enum does not list."""
        if not isinstance(value, str) or not value:
            return None
        member = str.__new__(cls, value)
        member._name_ = value
        member._value_ = value
        return cls._value2member_map_.setdefault(value, member)  # type: ignore[return-value]


@dataclass
class Wallbox:
    """Physical wallbox hardware assigned to a system.

    Returned by :meth:`~onekommafive.System.get_wallboxes`
    (``GET /api/v1/sites/{id}/assets/ev-chargers``).

    Distinct from :class:`~onekommafive.EVCharger`, which represents the
    **vehicle-side** charging profile (charging mode, target SoC, departure
    schedule) bound to a wallbox via :attr:`assigned_ev_id`.
    """

    id: str | None
    """Canonical wallbox identifier."""

    gridx_hardware_id: str | None
    """Legacy GridX hardware UUID. Always ``None``; kept for
    backwards-compatible presence-check callers."""

    name: str | None
    """Human-readable wallbox name, e.g. ``"Wallbox"``."""

    assigned_ev_id: str | None
    """UUID of the EV/vehicle profile currently paired with this wallbox
    (matches the ``id`` returned by :meth:`~onekommafive.System.get_ev_chargers`)."""

    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Wallbox":
        return cls(
            id=data.get("id"),
            gridx_hardware_id=data.get("gridxHardwareId"),
            name=data.get("name"),
            assigned_ev_id=data.get("assignedEvId"),
            raw=data,
        )
