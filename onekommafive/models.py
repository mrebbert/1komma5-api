"""Typed data models returned by the 1KOMMA5° API."""

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


@dataclass
class MarketPrices:
    """Electricity market price data for a time range.

    Returned by :meth:`~onekommafive.System.get_prices`.  All price values are
    in **ct/kWh** as provided by the API.
    """

    average_price: float
    """Average raw spot price over the requested period, in ct/kWh."""

    highest_price: float
    """Highest hourly raw spot price in the period, in ct/kWh."""

    lowest_price: float
    """Lowest hourly raw spot price in the period, in ct/kWh."""

    prices: dict[str, float]
    """Raw spot prices keyed by ISO-8601 timestamp, in ct/kWh."""

    prices_with_grid_costs: dict[str, float]
    """Spot prices including grid costs keyed by ISO-8601 timestamp, in ct/kWh."""

    grid_costs_total: float
    """Total grid costs (constant component), in ct/kWh."""

    vat: float
    """VAT multiplier applied to prices (e.g. ``0.19`` for 19 %)."""

    uses_fallback_grid_costs: bool
    """``True`` when the API fell back to default grid cost values."""

    raw: dict[str, Any] = field(repr=False)
    """The complete raw API response."""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MarketPrices":
        """Construct a :class:`MarketPrices` from a raw API response dictionary."""
        em = data["energyMarket"]
        emgc = data["energyMarketWithGridCosts"]
        return cls(
            average_price=float(em["averagePrice"]),
            highest_price=float(em["highestPrice"]),
            lowest_price=float(em["lowestPrice"]),
            prices={ts: float(v["price"]) for ts, v in em["data"].items()},
            prices_with_grid_costs={ts: float(v["price"]) for ts, v in emgc["data"].items()},
            grid_costs_total=float(data["gridCostsTotal"]["value"]),
            vat=float(data["vat"]),
            uses_fallback_grid_costs=bool(data["usesFallbackGridCosts"]),
            raw=data,
        )


@dataclass
class LiveOverview:
    """Real-time energy overview for a system.

    All power values are in **Watts**; all energy values are in **Wh**.
    Fields may be ``None`` when the relevant device is not installed.
    """

    pv_power: float | None
    """Current photovoltaic generation, in W."""

    battery_power: float | None
    """Battery charge (positive) or discharge (negative) power, in W."""

    battery_soc: float | None
    """Battery state-of-charge as a percentage (0–100)."""

    grid_power: float | None
    """Power imported from (positive) or exported to (negative) the grid, in W."""

    consumption_power: float | None
    """Total household consumption power, in W."""

    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LiveOverview":
        """Construct a :class:`LiveOverview` from a raw API response dictionary."""
        hero = data.get("liveHeroView", {})
        pv = hero.get("production", {}).get("value")
        consumption = hero.get("consumption", {}).get("value")
        grid_import = hero.get("gridConsumption", {}).get("value")
        grid_export = hero.get("gridFeedIn", {}).get("value")
        soc_frac = hero.get("totalStateOfCharge")

        # Positive = charging, negative = discharging; derived from power balance.
        if None not in (pv, consumption, grid_import, grid_export):
            battery_power: float | None = pv + grid_import - grid_export - consumption
        else:
            battery_power = None

        # Positive = importing from grid, negative = exporting to grid.
        if None not in (grid_import, grid_export):
            grid_power: float | None = grid_import - grid_export
        else:
            grid_power = None

        return cls(
            pv_power=pv,
            battery_power=battery_power,
            battery_soc=soc_frac * 100 if soc_frac is not None else None,
            grid_power=grid_power,
            consumption_power=consumption,
            raw=data,
        )


@dataclass
class EmsSettings:
    """Energy-management system (EMS) settings for a system."""

    auto_mode: bool
    """Whether the EMS is in automatic optimisation mode."""

    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EmsSettings":
        """Construct an :class:`EmsSettings` from a raw API response dictionary."""
        return cls(
            auto_mode=not data.get("overrideAutoSettings", False),
            raw=data,
        )
