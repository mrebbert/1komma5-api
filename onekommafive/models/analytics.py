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
            raw=data,
        )
