"""Analytics / summary models — CO2, trading, and AI-summary endpoints."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ImpactOverview:
    """Lifetime CO2-savings figures for a site.

    Returned by :meth:`~onekommafive.System.get_impact_overview`
    (``GET /api/v2/systems/{id}/impact-overview``). The endpoint ignores
    any query parameters — values are always lifetime totals.
    """

    co2_savings_kg: float | None
    """CO2 saved by this site since installation, in kg."""

    co2_collective_savings_kg: float | None
    """Aggregated CO2 savings across the entire 1KOMMA5° customer base, in kg."""

    co2_global_savings_estimate_tons: float | None
    """Global renewable-energy CO2 savings estimate (marketing figure), in tons."""

    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ImpactOverview":
        def _val(node: dict | None) -> float | None:
            return node.get("value") if node else None
        return cls(
            co2_savings_kg=_val(data.get("co2Savings")),
            co2_collective_savings_kg=_val(data.get("co2CollectiveSavings")),
            co2_global_savings_estimate_tons=_val(data.get("co2GlobalSavingsEstimate")),
            raw=data,
        )


@dataclass
class EnergyTrader:
    """Lifetime energy-trading statistics for a site.

    Returned by :meth:`~onekommafive.System.get_energy_trader`
    (``GET /api/v2/energy-trader?siteId={id}``). Values accumulate over
    the site's entire trading history; no date range is supported.
    """

    status: str | None
    """Trading status, e.g. ``"ACTIVE"``."""

    green_energy_savings_eur: float | None
    """Lifetime savings attributed to green-energy sourcing, in EUR."""

    energy_trader_savings_eur: float | None
    """Lifetime savings attributed to dynamic trading, in EUR."""

    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EnergyTrader":
        et = data.get("energyTrader") or {}

        def _amount(node: dict | None) -> float | None:
            if not node:
                return None
            amt = node.get("amount")
            return float(amt) if amt is not None else None

        return cls(
            status=et.get("status"),
            green_energy_savings_eur=_amount(et.get("greenEnergySavings")),
            energy_trader_savings_eur=_amount(et.get("energyTraderSavings")),
            raw=data,
        )


@dataclass
class MonthlyTradingSavings:
    """Average monthly savings from Energy Trader activity.

    Returned by :meth:`~onekommafive.System.get_monthly_trading_savings`
    (``GET /api/v1/energy-trader-savings/{site_id}/month``).
    Complements :class:`EnergyTrader` (lifetime totals) with a monthly view.
    """

    average_past_variable_savings_eur: float | None
    """Average monthly savings from variable-pricing trading, in EUR."""

    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MonthlyTradingSavings":
        node = data.get("averagePastVariableSavings") or {}
        val = node.get("value")
        return cls(
            average_past_variable_savings_eur=float(val) if val is not None else None,
            raw=data,
        )


@dataclass
class HeartbeatAiSummary:
    """Aggregated Heartbeat-AI performance metrics for a resolution window.

    Returned by :meth:`~onekommafive.System.get_heartbeat_ai_summary`
    (``GET /api/v2/heartbeat-ai/summary?siteId=…&resolution=…``).

    Only ``resolution="1M"`` returns all metrics; ``"1W"`` and ``"1Y"``
    return only ``co2_saved_kg`` + ``production_kwh`` + ``car_travel_emission_km``,
    with the self-sufficiency and earnings fields set to ``None``.
    """

    resolution: str
    """The resolution requested (``"1W"``, ``"1M"``, or ``"1Y"``)."""

    self_sufficiency_percent: float | None
    """Site self-sufficiency ratio for the window (0–1)."""

    self_sufficiency_by_solar_kwh: float | None
    """Consumption covered directly by PV in the window, in kWh."""

    self_sufficiency_by_battery_kwh: float | None
    """Consumption covered by battery discharge in the window, in kWh."""

    earned_amount_eur: float | None
    """Earnings from grid feed-in in the window, in EUR."""

    sold_energy_kwh: float | None
    """Energy fed into the grid in the window, in kWh."""

    feed_in_price_eur_per_kwh: float | None
    """Feed-in tariff, in EUR/kWh."""

    co2_saved_kg: float | None
    """CO2 saved in the window, in kg."""

    production_kwh: float | None
    """PV production in the window, in kWh."""

    car_travel_emission_km: float | None
    """Equivalent car travel distance the saved CO2 would have caused, in km."""

    heartbeat_price_eur_per_kwh: float | None
    """Effective average Heartbeat electricity price for the window, in EUR/kWh."""

    peak_price_avoided_eur: float | None
    """Savings from avoiding peak-price grid consumption via battery
    discharge in the window, in EUR (from ``peakPriceAvoided.priceAvoided``).
    Top-level ``priceAvoided`` field is empirically always ``null``; the
    populated value sits nested here."""

    peak_battery_charging_cost_eur: float | None
    """Cost incurred to charge the battery for the peak-price-avoidance
    strategy in the window, in EUR (from ``peakPriceAvoided.batteryChargingCost``)."""

    peak_grid_charging_cost_eur: float | None
    """Cost of the grid consumption that would have occurred without the
    strategy in the window, in EUR (from ``peakPriceAvoided.gridChargingCost``).
    Net saving = :attr:`peak_price_avoided_eur` = grid - battery."""

    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_dict(cls, resolution: str, data: dict[str, Any]) -> "HeartbeatAiSummary":
        def _val(node: dict | None) -> float | None:
            return node.get("value") if node else None

        def _amount(node: dict | None) -> float | None:
            if not node:
                return None
            amt = node.get("amount")
            return float(amt) if amt is not None else None

        ss = data.get("selfSufficiency") or {}
        ee = data.get("energyEarned") or {}
        co2 = data.get("co2Saved") or {}
        hbp = data.get("heartbeatPrice") or {}
        ppa = data.get("peakPriceAvoided") or {}
        feed_in_price = (ee.get("feedInPrice") or {}).get("price")

        return cls(
            resolution=resolution,
            self_sufficiency_percent=ss.get("percentage"),
            self_sufficiency_by_solar_kwh=_val(ss.get("bySolar")),
            self_sufficiency_by_battery_kwh=_val(ss.get("byBattery")),
            earned_amount_eur=_amount(ee.get("earnedAmount")),
            sold_energy_kwh=_val(ee.get("soldEnergy")),
            feed_in_price_eur_per_kwh=_amount(feed_in_price),
            co2_saved_kg=co2.get("co2Saved"),
            production_kwh=_val(co2.get("production")),
            car_travel_emission_km=_val(co2.get("carTravelEmission")),
            heartbeat_price_eur_per_kwh=_amount(hbp.get("price")),
            peak_price_avoided_eur=_amount(ppa.get("priceAvoided")),
            peak_battery_charging_cost_eur=_amount(ppa.get("batteryChargingCost")),
            peak_grid_charging_cost_eur=_amount(ppa.get("gridChargingCost")),
            raw=data,
        )


@dataclass
class HeartbeatPriceWindow:
    """Financial breakdown for one aggregation window.

    Part of :class:`HeartbeatPrices`. Fields are grouped into three blocks:
    PV production, grid feed-in, grid consumption — plus site totals and
    a comparison-tariff reference.

    **VAT convention**: prices in this response are presented as displayed
    in the 1KOMMA5° app — most likely **gross** (VAT-inclusive), matching
    the German consumer convention. The :attr:`vat` field (typically
    ``0.19``) is included but the API does not document whether it has
    been applied or is informational. :attr:`comparison_tariff_eur_per_kwh`
    at ~0.27 EUR/kWh matches a typical German utility **gross** tariff,
    which is consistent with the gross interpretation. If your application
    is sensitive to gross/net semantics, verify against your electricity
    invoice.

    **Three distinct price semantics** (do not confuse):

    - :attr:`pv_valuation_price_eur_per_kwh` is Heartbeat's **internal
      accounting valuation** of the site's own PV production
      (empirically constant at 0.05 EUR/kWh). **Not** a market price.
    - :attr:`grid_feed_in_tariff_eur_per_kwh` is the **contractual
      feed-in tariff** the grid operator pays for exported energy.
    - :attr:`grid_consumption_price_eur_per_kwh` is the **effective
      per-kWh grid-purchase price** averaged over the window.
    - :attr:`heartbeat_price_eur_per_kwh` is the site's **effective
      all-in per-kWh price** for consumed energy (mix of PV, battery
      and grid, minus feed-in earnings, plus fixed costs).
    - :attr:`comparison_tariff_eur_per_kwh` is the static
      grid-supplier reference used for savings comparisons.
    """

    # PV production
    pv_produced_kwh: float | None
    """PV energy produced in the window, in kWh."""

    pv_production_cost_eur: float | None
    """Internal valuation of PV production (= produced × valuation price), in EUR."""

    pv_valuation_price_eur_per_kwh: float | None
    """Heartbeat's internal per-kWh valuation of own PV production, in EUR/kWh.
    Empirically constant at 0.05 EUR/kWh. **Not a market price.**"""

    # Grid feed-in
    grid_feed_in_kwh: float | None
    """Energy fed into the grid in the window, in kWh."""

    grid_feed_in_compensation_eur: float | None
    """Feed-in compensation received in the window, in EUR."""

    grid_feed_in_tariff_eur_per_kwh: float | None
    """Contractual feed-in tariff, in EUR/kWh."""

    # Grid consumption
    grid_consumed_kwh: float | None
    """Energy drawn from the grid in the window, in kWh."""

    grid_consumption_cost_eur: float | None
    """Cost of grid consumption in the window, in EUR."""

    grid_consumption_price_eur_per_kwh: float | None
    """Effective per-kWh grid-purchase price averaged over the window, in EUR/kWh."""

    # Site totals
    total_consumption_kwh: float | None
    """Total household consumption in the window (all sources), in kWh."""

    total_energy_cost_eur: float | None
    """Net total energy cost for the window, in EUR."""

    heartbeat_price_eur_per_kwh: float | None
    """Site's effective per-kWh price for consumed energy, in EUR/kWh.
    All-in: reflects the PV / battery / grid mix minus feed-in earnings
    plus fixed costs. See class docstring for VAT semantics."""

    comparison_tariff_eur_per_kwh: float | None
    """Static grid-supplier reference tariff for savings comparisons, in EUR/kWh."""

    grid_electricity_cost_eur: float | None
    """Grid-supplier fixed cost component in the window, in EUR."""

    energy_tax_reduction_eur: float | None
    """Applied energy-tax reduction in the window, in EUR (0 for German consumers)."""

    fixed_costs_and_savings_eur: float | None
    """Aggregated fixed cost / savings component in the window, in EUR."""

    # Metadata and quality flags
    vat: float
    """VAT rate applied by the API (e.g. ``0.19`` for 19%). Role undocumented — see class docstring."""

    should_report_implausible_pv_and_feed_in: bool
    """API flag: values in this window may be implausible."""

    should_report_overridden_pv_cost: bool
    """API flag: PV cost was overridden by manual configuration."""

    uses_feed_in_earnings_as_hb_price: bool
    """API flag: whether the Heartbeat price calculation uses feed-in earnings
    instead of the internal PV valuation."""

    feed_in_discrepancy: float | None
    """Numeric discrepancy metric between measured and expected feed-in."""

    # Regional / feature-flagged blocks (structure unknown; passed through as raw)
    peak_shaving_savings_raw: dict[str, Any] | None
    """Raw ``peakShavingSavings`` block (usually ``None``; structure unknown when populated)."""

    swedish_costs_and_savings_raw: dict[str, Any] | None
    """Raw ``swedishCostsAndSavings`` block (usually ``None``; structure unknown when populated)."""

    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HeartbeatPriceWindow":
        def _val(node: dict | None) -> float | None:
            return node.get("value") if node else None

        def _amount(node: dict | None) -> float | None:
            if not node:
                return None
            a = node.get("amount")
            return float(a) if a is not None else None

        def _rate(node: dict | None) -> float | None:
            """Extract per-unit rate from ``{price: {amount, currency}, unit}``."""
            return _amount((node or {}).get("price"))

        pv = data.get("pvProduction") or {}
        fi = data.get("gridFeedIn") or {}
        gc = data.get("gridConsumption") or {}
        return cls(
            pv_produced_kwh=_val(pv.get("energyProduced")),
            pv_production_cost_eur=_amount(pv.get("cost")),
            pv_valuation_price_eur_per_kwh=_rate(pv.get("price")),
            grid_feed_in_kwh=_val(fi.get("energyFedIn")),
            grid_feed_in_compensation_eur=_amount(fi.get("compensation")),
            grid_feed_in_tariff_eur_per_kwh=_rate(fi.get("price")),
            grid_consumed_kwh=_val(gc.get("energyConsumed")),
            grid_consumption_cost_eur=_amount(gc.get("cost")),
            grid_consumption_price_eur_per_kwh=_rate(gc.get("price")),
            total_consumption_kwh=_val(data.get("totalConsumption")),
            total_energy_cost_eur=_amount(data.get("totalEnergyCost")),
            heartbeat_price_eur_per_kwh=_rate(data.get("heartbeatPrice")),
            comparison_tariff_eur_per_kwh=_rate(data.get("comparisonTariff")),
            grid_electricity_cost_eur=_amount(data.get("gridElectricityCost")),
            energy_tax_reduction_eur=_amount(data.get("energyTaxReduction")),
            fixed_costs_and_savings_eur=_amount(data.get("fixedCostsAndSavings")),
            vat=float(data.get("vat", 0)),
            should_report_implausible_pv_and_feed_in=bool(data.get("shouldReportImplausiblePvAndFeedIn")),
            should_report_overridden_pv_cost=bool(data.get("shouldReportOverriddenPvCost")),
            uses_feed_in_earnings_as_hb_price=bool(data.get("usesFeedInEarningsAsHbPrice")),
            feed_in_discrepancy=data.get("feedInDiscrepancy"),
            peak_shaving_savings_raw=data.get("peakShavingSavings"),
            swedish_costs_and_savings_raw=data.get("swedishCostsAndSavings"),
            raw=data,
        )


@dataclass
class HeartbeatPrices:
    """Financial breakdown across five aggregation windows.

    Returned by :meth:`~onekommafive.System.get_heartbeat_prices`
    (``GET /api/v3/heartbeat-prices?siteId={id}``). Each window carries
    PV production, grid feed-in, grid consumption, site totals and the
    effective Heartbeat per-kWh price for a trailing period ending "now".

    Windows: :attr:`day`, :attr:`week`, :attr:`month`, :attr:`half_year`,
    :attr:`year`. All have the identical :class:`HeartbeatPriceWindow`
    shape.

    See :class:`HeartbeatPriceWindow` for the VAT convention and the
    three distinct price semantics.
    """

    day: HeartbeatPriceWindow
    week: HeartbeatPriceWindow
    month: HeartbeatPriceWindow
    half_year: HeartbeatPriceWindow
    """Trailing 6-month window (API field: ``halfYear``)."""

    year: HeartbeatPriceWindow

    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HeartbeatPrices":
        return cls(
            day=HeartbeatPriceWindow.from_dict(data.get("day") or {}),
            week=HeartbeatPriceWindow.from_dict(data.get("week") or {}),
            month=HeartbeatPriceWindow.from_dict(data.get("month") or {}),
            half_year=HeartbeatPriceWindow.from_dict(data.get("halfYear") or {}),
            year=HeartbeatPriceWindow.from_dict(data.get("year") or {}),
            raw=data,
        )
