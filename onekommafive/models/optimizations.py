"""AI optimisation event models (``/api/v1/heartbeat-ai/optimizations``)."""

from dataclasses import dataclass, field
from typing import Any


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
    """Optimisation decision, e.g. ``'BATTERY_NO_DISCHARGE'``,
    ``'BATTERY_CHARGE_FROM_GRID'``, ``'EV_CHARGE_FROM_GRID'``."""

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
