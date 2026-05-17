"""Energy data models (``/api/v2/systems/{id}/energy-today`` and ``/api/v3/.../energy-historical``)."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class EnergySlot:
    """One timestamped slot in an energy timeseries.

    All power values are in **kW**; ``battery_soc`` is a fraction (0–1).
    ``*_total`` fields reflect consumption from **all** sources (PV + battery + grid).
    Plain fields reflect the share covered **directly by PV** only.
    Fields may be ``None`` when the device is not installed.
    """

    production: float | None
    """PV generation, in kW."""

    consumption_household: float | None
    """Household load covered directly by PV, in kW."""

    consumption_household_total: float | None
    """Total household load (PV + battery + grid), in kW."""

    consumption_ev: float | None
    """EV load covered directly by PV, in kW."""

    consumption_ev_total: float | None
    """Total EV charging power from all sources (``evCharge``), in kW."""

    consumption_heat_pump: float | None
    """Heat-pump load covered directly by PV, in kW."""

    consumption_heat_pump_total: float | None
    """Total heat-pump power from all sources, in kW."""

    consumption_ac: float | None
    """AC load covered directly by PV, in kW (``None`` when no AC installed)."""

    consumption_ac_total: float | None
    """Total AC power from all sources, in kW (``None`` when no AC installed)."""

    consumption_battery: float | None
    """Battery charging power sourced from PV, in kW."""

    consumption_direct: float | None
    """Total direct consumption from PV (all devices combined), in kW."""

    grid_supply: float | None
    """Grid import power, in kW."""

    grid_feed_in: float | None
    """Grid export / feed-in power, in kW."""

    battery_soc: float | None
    """Battery state-of-charge as a fraction (0–1)."""

    battery_charge: float | None
    """Battery charge power, in kW."""

    battery_discharge: float | None
    """Battery discharge power, in kW."""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EnergySlot":
        c = data.get("consumption", {})
        return cls(
            production=data.get("production"),
            consumption_household=c.get("household"),
            consumption_household_total=c.get("householdTotal"),
            consumption_ev=c.get("ev"),
            consumption_ev_total=c.get("evCharge"),
            consumption_heat_pump=c.get("heatPump"),
            consumption_heat_pump_total=c.get("heatPumpTotal"),
            consumption_ac=c.get("ac"),
            consumption_ac_total=c.get("acTotal"),
            consumption_battery=c.get("battery"),
            consumption_direct=c.get("direct"),
            grid_supply=data.get("gridSupply"),
            grid_feed_in=data.get("gridFeedIn"),
            battery_soc=data.get("batteryStateOfCharge"),
            battery_charge=data.get("batteryCharge"),
            battery_discharge=data.get("batteryDischarge"),
        )


@dataclass
class EnergyData:
    """Aggregated energy data for a system over a time period.

    Returned by :meth:`~onekommafive.System.get_energy_today` and
    :meth:`~onekommafive.System.get_energy_historical`.
    Scalar totals are in **kWh**; savings in **EUR**.

    ``consumption_*_kwh`` fields reflect the share sourced **directly from PV**.
    ``consumption_*_total_kwh`` fields reflect consumption from **all** sources.
    """

    updated_at: str | None
    """ISO-8601 timestamp of the last data update."""

    energy_produced_kwh: float | None
    """Total PV energy produced in the period, in kWh."""

    self_sufficiency: float | None
    """Self-sufficiency ratio for the period (0–1)."""

    grid_feed_in_kwh: float | None
    """Total energy fed into the grid, in kWh."""

    grid_supply_kwh: float | None
    """Total energy drawn from the grid, in kWh."""

    battery_charge_kwh: float | None
    """Total energy charged into the battery, in kWh."""

    battery_discharge_kwh: float | None
    """Total energy discharged from the battery, in kWh."""

    consumption_direct_kwh: float | None
    """Total direct consumption from PV (without storage/grid), in kWh."""

    consumption_total_kwh: float | None
    """Total site consumption from all sources, in kWh."""

    consumption_ev_kwh: float | None
    """EV charging energy sourced directly from PV, in kWh."""

    consumption_ev_total_kwh: float | None
    """Total EV charging energy from all sources, in kWh."""

    consumption_heat_pump_kwh: float | None
    """Heat-pump energy sourced directly from PV, in kWh."""

    consumption_heat_pump_total_kwh: float | None
    """Total heat-pump energy from all sources, in kWh."""

    consumption_ac_kwh: float | None
    """AC energy sourced directly from PV, in kWh (``None`` when no AC)."""

    consumption_ac_total_kwh: float | None
    """Total AC energy from all sources, in kWh (``None`` when no AC)."""

    consumption_household_kwh: float | None
    """Household energy sourced directly from PV, in kWh."""

    consumption_household_total_kwh: float | None
    """Total household energy from all sources, in kWh."""

    consumption_battery_kwh: float | None
    """Energy charged into battery from PV, in kWh."""

    savings_eur: float | None
    """Estimated savings from self-consumption, in EUR."""

    timeseries: dict[str, "EnergySlot"]
    """Per-slot data keyed by ISO-8601 timestamp."""

    raw: dict[str, Any] = field(repr=False)
    """The complete raw API response."""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EnergyData":
        """Construct an :class:`EnergyData` from a raw API response dictionary."""

        def _kwh(node: dict | None) -> float | None:
            if node is None:
                return None
            return float(node["value"]) if "value" in node else None

        grid = data.get("grid", {}) or {}
        battery = data.get("battery", {}) or {}
        consumption = data.get("consumption", {}) or {}
        consumers = consumption.get("consumers", {}) or {}
        consumers_total = consumption.get("consumersTotal", {}) or {}
        savings = data.get("heartbeatSavings")

        # Timeseries is nested under .data in both v2 and v3 responses
        ts_container = data.get("timestampedProductionAndConsumption", {}) or {}
        ts_raw = ts_container.get("data", {}) or {}
        timeseries = {k: EnergySlot.from_dict(v) for k, v in ts_raw.items()}

        return cls(
            updated_at=data.get("updatedAt"),
            energy_produced_kwh=_kwh(data.get("energyProduced")),
            self_sufficiency=data.get("selfSufficiencyPercent"),
            grid_feed_in_kwh=_kwh(grid.get("feedIn")),
            grid_supply_kwh=_kwh(grid.get("supply")),
            battery_charge_kwh=_kwh(battery.get("charge")),
            battery_discharge_kwh=_kwh(battery.get("discharge")),
            consumption_direct_kwh=_kwh(consumption.get("direct")),
            consumption_total_kwh=_kwh(consumption.get("total")),
            consumption_ev_kwh=_kwh(consumers.get("ev")),
            consumption_ev_total_kwh=_kwh(consumers_total.get("ev")),
            consumption_heat_pump_kwh=_kwh(consumers.get("heatPump")),
            consumption_heat_pump_total_kwh=_kwh(consumers_total.get("heatPump")),
            consumption_ac_kwh=_kwh(consumers.get("ac")),
            consumption_ac_total_kwh=_kwh(consumers_total.get("ac")),
            consumption_household_kwh=_kwh(consumers.get("household")),
            consumption_household_total_kwh=_kwh(consumers_total.get("household")),
            consumption_battery_kwh=_kwh(consumers.get("battery")),
            savings_eur=float(savings["value"]) if savings and "value" in savings else None,
            timeseries=timeseries,
            raw=data,
        )
