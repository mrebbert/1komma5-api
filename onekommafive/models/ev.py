"""EV / wallbox related models."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ChargingMode(Enum):
    """Charging strategy for an EV charger."""

    SMART_CHARGE = "SMART_CHARGE"
    """Charge according to the energy-management system's optimisation."""

    QUICK_CHARGE = "QUICK_CHARGE"
    """Charge as fast as possible regardless of grid price."""

    SOLAR_CHARGE = "SOLAR_CHARGE"
    """Charge only when surplus solar power is available."""


@dataclass
class Wallbox:
    """Physical wallbox hardware assigned to a system.

    Returned by :meth:`~onekommafive.System.get_wallboxes`
    (``GET /api/v1/systems/{id}/devices/ev-chargers``).

    Distinct from :class:`~onekommafive.EVCharger`, which represents the
    **vehicle-side** charging profile (charging mode, target SoC, departure
    schedule) bound to a wallbox via :attr:`assigned_ev_id`.
    """

    gridx_hardware_id: str | None
    """Internal GridX hardware UUID for the wallbox."""

    name: str | None
    """Human-readable wallbox name, e.g. ``"Wallbox"``."""

    assigned_ev_id: str | None
    """UUID of the EV/vehicle profile currently paired with this wallbox
    (matches the ``id`` returned by :meth:`~onekommafive.System.get_ev_chargers`)."""

    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Wallbox":
        return cls(
            gridx_hardware_id=data.get("gridxHardwareId"),
            name=data.get("name"),
            assigned_ev_id=data.get("assignedEvId"),
            raw=data,
        )
