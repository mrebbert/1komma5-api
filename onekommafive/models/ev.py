"""EV charger related enums."""

from enum import Enum


class ChargingMode(Enum):
    """Charging strategy for an EV charger."""

    SMART_CHARGE = "SMART_CHARGE"
    """Charge according to the energy-management system's optimisation."""

    QUICK_CHARGE = "QUICK_CHARGE"
    """Charge as fast as possible regardless of grid price."""

    SOLAR_CHARGE = "SOLAR_CHARGE"
    """Charge only when surplus solar power is available."""
