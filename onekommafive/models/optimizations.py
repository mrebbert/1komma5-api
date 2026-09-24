"""AI optimisation event models (``/api/v1/heartbeat-ai/optimizations``)."""

import datetime as _dt
from dataclasses import dataclass, field
from typing import Any

_SLOT_MINUTES = 15


def _parse_iso(ts: str) -> _dt.datetime:
    return _dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))


def _plus_slot(ts: str) -> str:
    """Return ``ts`` shifted forward by one 15-min slot, as ISO-8601 UTC."""
    dt = _parse_iso(ts) + _dt.timedelta(minutes=_SLOT_MINUTES)
    return dt.astimezone(_dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


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
    """Reference price the AI compared against for this decision,
    in EUR/MWh (may be ``None``).

    **Semantic caveat**: empirically much lower than the spot purchase
    price returned by ``/charts/market-prices`` for the same timestamp
    (factor ~4-5). Likely the **feed-in / trader-side price** from the
    Dynamic-Pulse regime rather than the grid-purchase price, but the
    API does not document which of the two it is."""

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
    """Start-timestamps of additional 15-min slots the API rolled into this
    event because they carried the **same** ``decision`` within the same
    hour bucket (``:00``–``:59:59`` UTC).

    Empirically:

    - ``log[0]`` equals ``to_time`` exactly; the list grows in 15-min
      steps and never crosses an hour boundary, so ``len(log)`` is 0–3.
    - ``from_time``/``to_time`` still describe **only the first slot**;
      the numeric fields (``market_price``, ``state_of_charge``) are the
      values at that first slot, not aggregates.

    Use :attr:`slot_count` and :attr:`end_time` if you want to know how
    much time this event actually covers. Ignoring ``log`` undercounts
    consecutive same-decision slots by up to a factor of four.
    """

    raw: dict[str, Any] = field(repr=False)
    """The complete raw event dictionary."""

    @property
    def slot_count(self) -> int:
        """Number of 15-min slots this event covers (``1 + len(log)``)."""
        return 1 + len(self.log)

    @property
    def end_time(self) -> str:
        """ISO-8601 end of the last slot covered by this event.

        Equals ``to_time`` when ``log`` is empty, otherwise
        ``log[-1] + 15 min``.
        """
        return _plus_slot(self.log[-1]) if self.log else self.to_time

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
class SelfSufficiencyEvents:
    """AI events explaining the site's self-sufficiency outcomes.

    Returned by :meth:`~onekommafive.System.get_self_sufficiency_events`
    (``GET /api/v1/heartbeat-ai/self-sufficiency``).

    Payload structure is identical to :class:`OptimizationEvents` — same
    :class:`OptimizationEvent` shape — but the two endpoints return
    **different subsets** of AI activity. In practice ``optimizations``
    tends to be sparse while ``self-sufficiency`` yields the granular
    battery discharge/charge decisions. Use both if you need full
    coverage of the AI's decision trace.
    """

    events: list[OptimizationEvent]
    """All self-sufficiency events in the response."""

    raw: dict[str, Any] = field(repr=False)
    """The complete raw API response."""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SelfSufficiencyEvents":
        return cls(
            events=[OptimizationEvent.from_dict(e) for e in data.get("events", [])],
            raw=data,
        )
