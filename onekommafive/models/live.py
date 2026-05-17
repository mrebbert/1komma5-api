"""Live energy overview model (``/api/v3/systems/{id}/live-overview``)."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class LiveOverview:
    """Real-time energy overview for a system.

    All power values are in **Watts**.
    Fields may be ``None`` when the relevant device is not installed or the
    field is absent from the API response.
    """

    timestamp: str | None
    """ISO-8601 timestamp of the reading."""

    status: str | None
    """System connection status, e.g. ``'ONLINE'``."""

    pv_power: float | None
    """Current photovoltaic generation, in W."""

    battery_power: float | None
    """Battery charge (positive) or discharge (negative) power, in W."""

    battery_soc: float | None
    """Battery state-of-charge as a percentage (0–100)."""

    grid_power: float | None
    """Power imported from (positive) or exported to (negative) the grid, in W."""

    grid_consumption_power: float | None
    """Raw grid import power (always ≥ 0), in W (``gridConsumption`` in the API)."""

    grid_feed_in_power: float | None
    """Raw grid export / feed-in power (always ≥ 0), in W (``gridFeedIn`` in the API)."""

    consumption_power: float | None
    """Total site consumption power (all loads combined), in W."""

    household_power: float | None
    """Base household consumption excluding smart devices (EV chargers, heat pumps, ACs), in W."""

    self_sufficiency: float | None
    """Self-sufficiency ratio (0.0–1.0)."""

    ev_chargers_power: float | None
    """Aggregated EV charger power, in W."""

    heat_pumps_power: float | None
    """Aggregated heat pump power, in W."""

    acs_power: float | None
    """Aggregated air-conditioner power, in W."""

    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LiveOverview":
        """Construct a :class:`LiveOverview` from a raw API response dictionary."""
        hero = data.get("liveHeroView", {})
        cards = data.get("summaryCards", {})

        pv = hero.get("production", {}).get("value")
        consumption = hero.get("consumption", {}).get("value")
        grid_import = hero.get("gridConsumption", {}).get("value")
        grid_export = hero.get("gridFeedIn", {}).get("value")
        soc_frac = hero.get("totalStateOfCharge")

        # Battery: prefer direct summaryCards measurement (sign: negative = charging).
        # Fall back to power-balance derivation when summaryCards is absent.
        raw_battery = (cards.get("battery", {}).get("power") or {}).get("value")
        if raw_battery is not None:
            # Flip sign: API uses negative-for-charging; we use positive-for-charging.
            battery_power: float | None = -raw_battery
        elif None not in (pv, consumption, grid_import, grid_export):
            battery_power = pv + grid_import - grid_export - consumption
        else:
            battery_power = None

        # Grid: prefer direct summaryCards measurement (positive = importing from grid).
        raw_grid = (cards.get("grid", {}).get("power") or {}).get("value")
        if raw_grid is not None:
            grid_power: float | None = raw_grid
        elif None not in (grid_import, grid_export):
            grid_power = grid_import - grid_export
        else:
            grid_power = None

        def _power(node: dict | None) -> float | None:
            return (node or {}).get("power", {}).get("value") if node else None

        return cls(
            timestamp=data.get("timestamp"),
            status=data.get("status"),
            pv_power=pv,
            battery_power=battery_power,
            battery_soc=soc_frac * 100 if soc_frac is not None else None,
            grid_power=grid_power,
            grid_consumption_power=grid_import,
            grid_feed_in_power=grid_export,
            consumption_power=consumption,
            household_power=_power(cards.get("household")),
            self_sufficiency=hero.get("selfSufficiency"),
            ev_chargers_power=_power(hero.get("evChargersAggregated")),
            heat_pumps_power=_power(hero.get("heatPumpsAggregated")),
            acs_power=_power(hero.get("acsAggregated")),
            raw=data,
        )
