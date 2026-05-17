"""Market price models (``/api/v4/systems/{id}/charts/market-prices``)."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MarketPrices:
    """Electricity market price data for a time range.

    Returned by :meth:`~onekommafive.System.get_prices`.  All price values are
    in **EUR/kWh** as provided by the API (v4).

    The summary fields ``*_with_grid_costs`` and ``*_all_in`` are set to
    ``float("nan")`` when the API does not deliver the corresponding block
    (``energyMarketWithGridCosts`` / ``energyMarketWithGridCostsAndVat``).
    Use ``math.isnan(value)`` to check for missing summaries.
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
