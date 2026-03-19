"""Typed data models returned by the 1KOMMA5° API."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


@dataclass
class SystemInfo:
    """Static metadata for a 1KOMMA5° system (site).

    Populated from the ``GET /api/v4/systems/{id}`` response which is fetched
    once when the system is loaded.  Use :meth:`~onekommafive.System.info` to
    obtain an instance.
    """

    id: str
    """Unique system UUID."""

    name: str | None
    """Human-readable site name (``systemName`` in the API response)."""

    status: str | None
    """Operational status string, e.g. ``"ACTIVE"``."""

    address_line1: str | None
    """Street address, first line."""

    address_line2: str | None
    """Street address, second line (often ``None``)."""

    address_zip_code: str | None
    """Postal / ZIP code."""

    address_city: str | None
    """City name."""

    address_country: str | None
    """ISO 3166-1 alpha-2 country code, e.g. ``"DE"``."""

    address_latitude: float | None
    """Geographic latitude of the site."""

    address_longitude: float | None
    """Geographic longitude of the site."""

    customer_id: str | None
    """Internal customer identifier."""

    dynamic_pulse_compatible: bool
    """Whether the system supports Dynamic Pulse (dynamic tariff optimisation)."""

    energy_trader_active: bool | None
    """Whether the energy trading feature is active for this system (not available in API v4+)."""

    electricity_contract_active: bool | None
    """Whether an electricity contract is active for this system (not available in API v4+)."""

    created_at: str | None
    """ISO 8601 timestamp when the system was created."""

    updated_at: str | None
    """ISO 8601 timestamp of the last system update."""

    raw: dict[str, Any] = field(repr=False)
    """The complete raw API response."""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SystemInfo":
        """Construct a :class:`SystemInfo` from a raw API response dictionary."""
        return cls(
            id=data["id"],
            name=data.get("systemName"),
            status=data.get("status"),
            address_line1=data.get("addressLine1"),
            address_line2=data.get("addressLine2"),
            address_zip_code=data.get("addressZipCode"),
            address_city=data.get("addressCity"),
            address_country=data.get("addressCountry"),
            address_latitude=data.get("addressLatitude"),
            address_longitude=data.get("addressLongitude"),
            customer_id=data.get("customerId"),
            dynamic_pulse_compatible=bool(data.get("dynamicPulseCompatible", False)),
            energy_trader_active=bool(data["energyTraderActive"]) if "energyTraderActive" in data else None,
            electricity_contract_active=bool(data["electricityContractActive"]) if "electricityContractActive" in data else None,
            created_at=data.get("createdAt"),
            updated_at=data.get("updatedAt"),
            raw=data,
        )


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
    in **EUR/kWh** as provided by the API (v4).
    """

    # ------------------------------------------------------------------
    # Spot-only summary (energyMarket)
    # ------------------------------------------------------------------

    average_price: float
    """Average raw spot price over the requested period, in EUR/kWh."""

    highest_price: float
    """Highest hourly raw spot price in the period, in EUR/kWh."""

    lowest_price: float
    """Lowest hourly raw spot price in the period, in EUR/kWh."""

    # ------------------------------------------------------------------
    # Spot + grid costs summary (energyMarketWithGridCosts)
    # ------------------------------------------------------------------

    average_price_with_grid_costs: float
    """Average spot + grid cost price over the period, in EUR/kWh."""

    highest_price_with_grid_costs: float
    """Highest spot + grid cost price in the period, in EUR/kWh."""

    lowest_price_with_grid_costs: float
    """Lowest spot + grid cost price in the period, in EUR/kWh."""

    # ------------------------------------------------------------------
    # All-in summary incl. VAT (energyMarketWithGridCostsAndVat)
    # ------------------------------------------------------------------

    average_price_all_in: float
    """Average all-in price (spot + grid + VAT) over the period, in EUR/kWh."""

    highest_price_all_in: float
    """Highest all-in price (spot + grid + VAT) in the period, in EUR/kWh."""

    lowest_price_all_in: float
    """Lowest all-in price (spot + grid + VAT) in the period, in EUR/kWh."""

    # ------------------------------------------------------------------
    # Per-slot timeseries
    # ------------------------------------------------------------------

    prices: dict[str, float]
    """Raw spot prices keyed by ISO-8601 timestamp, in EUR/kWh."""

    prices_with_vat: dict[str, float]
    """Spot prices including VAT keyed by ISO-8601 timestamp, in EUR/kWh."""

    prices_with_grid_costs: dict[str, float]
    """Spot + grid cost prices keyed by ISO-8601 timestamp, in EUR/kWh."""

    prices_with_grid_costs_and_vat: dict[str, float]
    """All-in prices (spot + grid + VAT) keyed by ISO-8601 timestamp, in EUR/kWh."""

    grid_consumption: dict[str, float]
    """Actual grid energy consumed per slot, keyed by ISO-8601 timestamp, in kWh."""

    grid_feed_in: dict[str, float]
    """Actual grid energy fed in per slot, keyed by ISO-8601 timestamp, in kWh."""

    # ------------------------------------------------------------------
    # Grid cost constants
    # ------------------------------------------------------------------

    grid_costs_total: float
    """Total grid costs including VAT (constant component), in EUR/kWh."""

    vat: float
    """VAT multiplier applied to prices (e.g. ``0.19`` for 19 %)."""

    uses_fallback_grid_costs: bool
    """``True`` when the API fell back to default grid cost values."""

    grid_cost_energy_tax: float | None
    """Energy tax component of grid costs, in EUR/kWh (excl. VAT)."""

    grid_cost_purchasing: float | None
    """Purchasing cost component of grid costs, in EUR/kWh (excl. VAT)."""

    grid_cost_fixed_tariff: float | None
    """Fixed tariff component of grid costs, in EUR/kWh (excl. VAT)."""

    grid_cost_dynamic_markup: float | None
    """Dynamic markup component of grid costs, in EUR/kWh (excl. VAT)."""

    grid_cost_feed_in_remuneration_adj: float | None
    """Feed-in remuneration adjustment component of grid costs, in EUR/kWh (excl. VAT)."""

    raw: dict[str, Any] = field(repr=False)
    """The complete raw API response."""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MarketPrices":
        """Construct a :class:`MarketPrices` from a raw API response dictionary."""
        em = data["energyMarket"]
        emg = data.get("energyMarketWithGridCosts", {})
        emgv = data.get("energyMarketWithGridCostsAndVat", {})
        ts = data["timeseries"]
        gc = data.get("gridCostsComponents", {})

        def _price(node: dict, key: str) -> float:
            return float(node[key]["price"]["amount"])

        def _component(node: dict, key: str) -> float | None:
            entry = node.get(key)
            return float(entry["price"]["amount"]) if entry else None

        def _ts_field(key: str) -> dict[str, float]:
            return {t: float(v[key]) for t, v in ts.items() if key in v}

        return cls(
            average_price=_price(em, "averagePrice"),
            highest_price=_price(em, "highestPrice"),
            lowest_price=_price(em, "lowestPrice"),
            average_price_with_grid_costs=_price(emg, "averagePrice") if emg else float("nan"),
            highest_price_with_grid_costs=_price(emg, "highestPrice") if emg else float("nan"),
            lowest_price_with_grid_costs=_price(emg, "lowestPrice") if emg else float("nan"),
            average_price_all_in=_price(emgv, "averagePrice") if emgv else float("nan"),
            highest_price_all_in=_price(emgv, "highestPrice") if emgv else float("nan"),
            lowest_price_all_in=_price(emgv, "lowestPrice") if emgv else float("nan"),
            prices=_ts_field("marketPrice"),
            prices_with_vat=_ts_field("marketPriceWithVat"),
            prices_with_grid_costs=_ts_field("marketPriceWithGridCost"),
            prices_with_grid_costs_and_vat=_ts_field("marketPriceWithGridCostAndVat"),
            grid_consumption=_ts_field("gridConsumption"),
            grid_feed_in=_ts_field("gridFeedIn"),
            grid_costs_total=float(data["gridCostsTotal"]["price"]["amount"]),
            vat=float(data["vat"]),
            uses_fallback_grid_costs=bool(data["usesFallbackGridCosts"]),
            grid_cost_energy_tax=_component(gc, "energyTax"),
            grid_cost_purchasing=_component(gc, "purchasingCost"),
            grid_cost_fixed_tariff=_component(gc, "fixedTariff"),
            grid_cost_dynamic_markup=_component(gc, "dynamicMarkup"),
            grid_cost_feed_in_remuneration_adj=_component(gc, "feedInRemunerationAdjustment"),
            raw=data,
        )


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


@dataclass
class OptimizationEvent:
    """A single AI optimisation decision event.

    Returned as part of :class:`OptimizationEvents` by
    :meth:`~onekommafive.System.get_optimizations`.
    """

    id: str
    """Event UUID (shared across multiple events in the same optimisation run)."""

    timestamp: str
    """ISO-8601 timestamp when the decision was recorded."""

    decision: str
    """Optimisation decision, e.g. ``'BATTERY_NO_DISCHARGE'``, ``'BATTERY_CHARGE_FROM_GRID'``, ``'EV_CHARGE_FROM_GRID'``."""

    asset: str
    """Asset the decision applies to, e.g. ``'BATTERY'`` or ``'EV'``."""

    from_time: str
    """ISO-8601 start of the optimisation slot."""

    to_time: str
    """ISO-8601 end of the optimisation slot."""

    market_price: float | None
    """Market price at decision time, in EUR/MWh (may be ``None``)."""

    market_price_currency: str | None
    """Currency of the market price (typically ``'EUR'``)."""

    energy_sold: float | None
    """Energy sold in this slot (kWh), or ``None`` when not settled yet."""

    energy_bought: float | None
    """Energy bought in this slot (kWh), or ``None`` when not settled yet."""

    total_cost: float | None
    """Total cost for this slot (EUR), or ``None`` when not settled yet."""

    state_of_charge: int | None
    """State-of-charge at decision time as an integer percentage (0–100), or ``None``."""

    log: list[str]
    """List of ISO-8601 timestamps logged for this event (may be empty)."""

    raw: dict[str, Any] = field(repr=False)
    """The complete raw event dictionary."""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OptimizationEvent":
        """Construct an :class:`OptimizationEvent` from a raw API event dict."""
        d = data.get("data", {})
        mp = d.get("marketPrice") or {}
        return cls(
            id=data["id"],
            timestamp=data["timestamp"],
            decision=d.get("decision", ""),
            asset=d.get("asset", ""),
            from_time=d.get("from", ""),
            to_time=d.get("to", ""),
            market_price=float(mp["value"]) if mp.get("value") is not None else None,
            market_price_currency=mp.get("currency"),
            energy_sold=d.get("energySold"),
            energy_bought=d.get("energyBought"),
            total_cost=d.get("totalCost"),
            state_of_charge=d.get("stateOfCharge"),
            log=d.get("log", []),
            raw=data,
        )


@dataclass
class OptimizationEvents:
    """AI optimisation decisions for a system over a time period.

    Returned by :meth:`~onekommafive.System.get_optimizations`.
    Events are ordered newest-first as delivered by the API.
    """

    events: list[OptimizationEvent]
    """All optimisation events in the response (newest-first)."""

    raw: dict[str, Any] = field(repr=False)
    """The complete raw API response."""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OptimizationEvents":
        """Construct an :class:`OptimizationEvents` from a raw API response dict."""
        return cls(
            events=[OptimizationEvent.from_dict(e) for e in data.get("events", [])],
            raw=data,
        )


@dataclass
class EmsManualDevice:
    """One device entry in the EMS manual settings.

    The ``type`` field determines which optional fields are populated:

    * ``EV_CHARGER`` — ``id``, ``charger_name``, ``assigned_ev_id``,
      ``assigned_ev_name``, ``active_charging_mode``
    * ``BATTERY`` — ``enable_forecast_charging``
    * ``HEAT_PUMP`` — ``id``, ``use_solar_surplus``,
      ``max_solar_surplus_usage_kw``
    """

    type: str
    """Device type: ``'EV_CHARGER'``, ``'BATTERY'``, or ``'HEAT_PUMP'``."""

    id: str | None
    """Device UUID (EV charger and heat pump only)."""

    charger_name: str | None
    """Human-readable wallbox name (EV charger only)."""

    assigned_ev_id: str | None
    """UUID of the EV assigned to this charger (EV charger only)."""

    assigned_ev_name: str | None
    """Name of the EV assigned to this charger (EV charger only)."""

    active_charging_mode: str | None
    """Active charging mode value (EV charger only)."""

    enable_forecast_charging: bool | None
    """Whether forecast-based charging is enabled (battery only)."""

    use_solar_surplus: bool | None
    """Whether solar surplus is used to power the heat pump (heat pump only)."""

    max_solar_surplus_usage_kw: float | None
    """Maximum solar surplus power used by the heat pump, in kW (heat pump only)."""

    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EmsManualDevice":
        surplus = data.get("maxSolarSurplusUsage")
        return cls(
            type=data.get("type", ""),
            id=data.get("id"),
            charger_name=data.get("chargerName"),
            assigned_ev_id=data.get("assignedEvId"),
            assigned_ev_name=data.get("assignedEvName"),
            active_charging_mode=data.get("activeChargingMode"),
            enable_forecast_charging=data.get("enableForecastCharging"),
            use_solar_surplus=data.get("useSolarSurplus"),
            max_solar_surplus_usage_kw=float(surplus["value"]) if surplus else None,
            raw=data,
        )


@dataclass
class EmsSettings:
    """Energy-management system (EMS) settings for a system."""

    auto_mode: bool
    """Whether the EMS is in automatic optimisation mode (``overrideAutoSettings`` is ``False``)."""

    system_id: str | None
    """UUID of the system these settings belong to."""

    created_at: str | None
    """ISO-8601 timestamp when this settings record was created."""

    updated_at: str | None
    """ISO-8601 timestamp of the last settings update."""

    consent_given: bool
    """Whether the user has given consent for EMS operation."""

    time_of_use_enabled: bool
    """Whether Time-of-Use optimisation is active."""

    manual_devices: list[EmsManualDevice]
    """Ordered list of devices configured in manual override mode."""

    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EmsSettings":
        """Construct an :class:`EmsSettings` from a raw API response dictionary."""
        manual_raw = data.get("manualSettings") or {}
        devices = [
            EmsManualDevice.from_dict(manual_raw[k])
            for k in sorted(manual_raw.keys(), key=lambda x: int(x) if x.isdigit() else x)
        ]
        return cls(
            auto_mode=not data.get("overrideAutoSettings", False),
            system_id=data.get("systemId"),
            created_at=data.get("createdAt"),
            updated_at=data.get("updatedAt"),
            consent_given=bool(data.get("consentGiven", False)),
            time_of_use_enabled=bool(data.get("timeOfUseEnabled", False)),
            manual_devices=devices,
            raw=data,
        )
