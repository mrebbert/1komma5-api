"""Synchronous facade over the async :mod:`onekommafive` API.

Every method delegates to the async :class:`~onekommafive.Client`
implementation running on a dedicated background event loop. Meant for
scripts, notebooks, and other callers who don't want to introduce
``asyncio`` into their code.

The wrappers keep the same method names and return types as the async
versions, minus the ``async``/``await``. Read-only accessors on
:class:`~onekommafive.EVCharger` (``charging_mode()``, ``target_soc()`` …)
were already synchronous and pass through unchanged.

Example::

    from onekommafive.sync import Client, Systems

    with Client("user@example.com", "s3cr3t") as client:
        systems = Systems(client).get_systems()
        info = systems[0].info()
        systems[0].get_ev_chargers()[0].set_charging_mode(mode)
"""

from __future__ import annotations

import asyncio
import atexit
import contextlib
import datetime
import threading
from collections.abc import Coroutine
from pathlib import Path
from typing import TYPE_CHECKING, Any, Self, TypeVar

from . import client as _client_module
from . import ev_charger as _ev_module
from . import system as _system_module
from . import systems as _systems_module

if TYPE_CHECKING:
    from types import TracebackType

    import aiohttp

    from .models import (
        ChargingMode,
        ComparisonPrice,
        Customer,
        DeviceGateway,
        EmsSettings,
        EnergyData,
        EnergyTrader,
        HeartbeatAiSummary,
        HeartbeatPrices,
        HeartbeatSavings,
        ImpactOverview,
        LiveOverview,
        MarketPrices,
        MonthlyTradingSavings,
        NotificationSettings,
        NotificationsList,
        OptimizationEvents,
        PriceCustomizations,
        PriceGuarantee,
        SelfSufficiencyEvents,
        SiteDetails,
        SiteStatus,
        SmartMeter,
        SubscriptionsList,
        SupportedVersions,
        SystemDetails,
        SystemInfo,
        User,
        Wallbox,
        WeatherData,
    )

T = TypeVar("T")


class _LoopRunner:
    """A persistent event loop running in a daemon thread.

    Purpose: let synchronous code call coroutines from any thread —
    including from a thread that itself has a running loop (Jupyter,
    unittest, etc.) — without the ``asyncio.run()`` restrictions.
    """

    def __init__(self) -> None:
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=self._loop.run_forever, name="onekommafive-sync-loop", daemon=True,
        )
        self._thread.start()

    def run(self, coro: Coroutine[Any, Any, T]) -> T:
        """Schedule *coro* on the internal loop and block until it completes."""
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result()

    def close(self) -> None:
        """Stop the loop and join the background thread."""
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join()
        self._loop.close()


class Client:
    """Synchronous wrapper around :class:`onekommafive.Client`."""

    HEARTBEAT_API: str = _client_module.HEARTBEAT_API

    # Strong references to every live SyncClient — prevents premature GC
    # so scripts that forget to call ``close()`` still get a clean
    # aiohttp-session shutdown at interpreter exit via the atexit hook
    # registered below.
    _live: set[Client] = set()

    def __init__(
        self,
        username: str,
        password: str,
        *,
        session: aiohttp.ClientSession | None = None,
        token_cache: Path | str | None = None,
    ) -> None:
        self._runner = _LoopRunner()
        self._async = _client_module.Client(
            username, password, session=session, token_cache=token_cache,
        )
        self._closed = False
        Client._live.add(self)

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        """Close the underlying aiohttp session and stop the internal loop.

        Idempotent: safe to call more than once.
        """
        if self._closed:
            return
        self._closed = True
        try:
            self._runner.run(self._async.close())
        finally:
            self._runner.close()
        Client._live.discard(self)

    # ------------------------------------------------------------------
    # Public interface (delegates to async client)
    # ------------------------------------------------------------------

    def get_token(self) -> str:
        return self._runner.run(self._async.get_token())

    def get_user(self) -> User:
        return self._runner.run(self._async.get_user())

    def get_supported_versions(self) -> SupportedVersions:
        return self._runner.run(self._async.get_supported_versions())

    def logout(self) -> None:
        self._runner.run(self._async.logout())

    # ------------------------------------------------------------------
    # Class-attribute passthrough (for API host constants)
    # ------------------------------------------------------------------

    @property
    def IDENTITY_API(self) -> str:  # noqa: N802 — matches async Client
        return self._async.IDENTITY_API

    # Internal handle used by wrappers below.
    @property
    def _inner(self) -> _client_module.Client:
        return self._async


@atexit.register
def _close_leftover_clients() -> None:
    """Interpreter-shutdown safety net for scripts that forget ``close()``.

    Iterates over a snapshot of :attr:`Client._live` so ``close()`` can
    mutate the set safely.
    """
    for client in list(Client._live):
        # Best-effort during shutdown; a raising close() on one client
        # must not skip the others.
        with contextlib.suppress(Exception):
            client.close()


class Systems:
    """Synchronous wrapper around :class:`onekommafive.Systems`."""

    def __init__(self, client: Client) -> None:
        self._runner = client._runner
        self._async = _systems_module.Systems(client._inner)

    def get_systems(self) -> list[System]:
        async_systems = self._runner.run(self._async.get_systems())
        return [System._wrap(self._runner, s) for s in async_systems]

    def get_system(self, system_id: str) -> System:
        async_system = self._runner.run(self._async.get_system(system_id))
        return System._wrap(self._runner, async_system)


class System:
    """Synchronous wrapper around :class:`onekommafive.System`."""

    def __init__(self, client: Client, data: dict[str, Any]) -> None:
        self._runner = client._runner
        self._async = _system_module.System(client._inner, data)

    @classmethod
    def _wrap(cls, runner: _LoopRunner, async_system: _system_module.System) -> System:
        """Construct a sync wrapper around an already-built async System."""
        instance = cls.__new__(cls)
        instance._runner = runner
        instance._async = async_system
        return instance

    # Sync passthrough — no I/O
    def id(self) -> str:
        return self._async.id()

    def __repr__(self) -> str:
        return f"System(id={self.id()!r})"

    # ------------------------------------------------------------------
    # Delegated async methods
    # ------------------------------------------------------------------

    def info(self) -> SystemInfo:
        return self._runner.run(self._async.info())

    def get_details(self) -> SystemDetails:
        return self._runner.run(self._async.get_details())

    def get_status_and_assets(self) -> SiteStatus:
        return self._runner.run(self._async.get_status_and_assets())

    def get_device_gateways(self) -> list[DeviceGateway]:
        return self._runner.run(self._async.get_device_gateways())

    def get_active_features(self, customer_id: str) -> list[str]:
        return self._runner.run(self._async.get_active_features(customer_id))

    def get_live_overview(self) -> LiveOverview:
        return self._runner.run(self._async.get_live_overview())

    def get_displayed_ev_charging_modes(self) -> list[ChargingMode]:
        return self._runner.run(self._async.get_displayed_ev_charging_modes())

    def get_ev_chargers(self) -> list[EVCharger]:
        async_chargers = self._runner.run(self._async.get_ev_chargers())
        return [EVCharger._wrap(self._runner, c) for c in async_chargers]

    def get_energy_today(self, resolution: str = "1h") -> EnergyData:
        return self._runner.run(self._async.get_energy_today(resolution))

    def get_energy_savings(
        self,
        from_date: datetime.date | None = None,
        to_date: datetime.date | None = None,
    ) -> HeartbeatSavings:
        return self._runner.run(self._async.get_energy_savings(from_date, to_date))

    def get_energy_historical(
        self,
        from_date: datetime.date,
        to_date: datetime.date,
        resolution: str = "1h",
    ) -> EnergyData:
        return self._runner.run(
            self._async.get_energy_historical(from_date, to_date, resolution)
        )

    def get_ems_settings(self) -> EmsSettings:
        return self._runner.run(self._async.get_ems_settings())

    def set_ems_mode(self, auto: bool) -> None:
        self._runner.run(self._async.set_ems_mode(auto))

    def get_prices(
        self,
        start: datetime.datetime,
        end: datetime.datetime,
        resolution: str = "1h",
    ) -> MarketPrices:
        return self._runner.run(self._async.get_prices(start, end, resolution))

    def get_weather(self) -> WeatherData:
        return self._runner.run(self._async.get_weather())

    def get_price_customizations(self) -> PriceCustomizations:
        return self._runner.run(self._async.get_price_customizations())

    def get_comparison_price(self) -> ComparisonPrice:
        return self._runner.run(self._async.get_comparison_price())

    def get_price_guarantee(self, customer_id: str) -> PriceGuarantee:
        return self._runner.run(self._async.get_price_guarantee(customer_id))

    def get_wallboxes(self) -> list[Wallbox]:
        return self._runner.run(self._async.get_wallboxes())

    def get_smart_meter(self) -> SmartMeter:
        return self._runner.run(self._async.get_smart_meter())

    def get_impact_overview(self) -> ImpactOverview:
        return self._runner.run(self._async.get_impact_overview())

    def get_energy_trader(self) -> EnergyTrader:
        return self._runner.run(self._async.get_energy_trader())

    def get_heartbeat_prices(self) -> HeartbeatPrices:
        return self._runner.run(self._async.get_heartbeat_prices())

    def get_monthly_trading_savings(self) -> MonthlyTradingSavings:
        return self._runner.run(self._async.get_monthly_trading_savings())

    def get_heartbeat_ai_summary(self, resolution: str = "1M") -> HeartbeatAiSummary:
        return self._runner.run(self._async.get_heartbeat_ai_summary(resolution))

    def get_optimizations(
        self, start: datetime.datetime, end: datetime.datetime,
    ) -> OptimizationEvents:
        return self._runner.run(self._async.get_optimizations(start, end))

    def get_self_sufficiency_events(
        self, start: datetime.datetime, end: datetime.datetime,
    ) -> SelfSufficiencyEvents:
        return self._runner.run(self._async.get_self_sufficiency_events(start, end))

    def get_site_details(self) -> SiteDetails:
        return self._runner.run(self._async.get_site_details())

    def get_customer(self, customer_id: str) -> Customer:
        return self._runner.run(self._async.get_customer(customer_id))

    def get_subscriptions(self, customer_id: str) -> SubscriptionsList:
        return self._runner.run(self._async.get_subscriptions(customer_id))

    def get_notifications(self) -> NotificationsList:
        return self._runner.run(self._async.get_notifications())

    def get_notification_settings(self) -> NotificationSettings:
        return self._runner.run(self._async.get_notification_settings())


class EVCharger:
    """Synchronous wrapper around :class:`onekommafive.EVCharger`.

    Read-only accessors pass through unchanged (they never did I/O in the
    async version either). Only setters are dispatched via the loop.

    Not intended for direct construction; obtain instances via
    :meth:`System.get_ev_chargers`.
    """

    def __init__(self, runner: _LoopRunner, async_charger: _ev_module.EVCharger) -> None:
        self._runner = runner
        self._async = async_charger

    @classmethod
    def _wrap(cls, runner: _LoopRunner, async_charger: _ev_module.EVCharger) -> EVCharger:
        return cls(runner, async_charger)

    # ------------------------------------------------------------------
    # Sync passthrough (read-only, no I/O)
    # ------------------------------------------------------------------

    def id(self) -> str:
        return self._async.id()

    def name(self) -> str | None:
        return self._async.name()

    def manufacturer(self) -> str | None:
        return self._async.manufacturer()

    def model(self) -> str | None:
        return self._async.model()

    def capacity_wh(self) -> float | None:
        return self._async.capacity_wh()

    def min_charging_current_a(self) -> float | None:
        return self._async.min_charging_current_a()

    def safety_range_km(self) -> float | None:
        return self._async.safety_range_km()

    def assigned_charger_id(self) -> str | None:
        return self._async.assigned_charger_id()

    def manual_soc_timestamp(self) -> str | None:
        return self._async.manual_soc_timestamp()

    def updated_at(self) -> str | None:
        return self._async.updated_at()

    def charging_mode(self) -> ChargingMode:
        return self._async.charging_mode()

    def charging_mode_updated_at(self) -> str | None:
        return self._async.charging_mode_updated_at()

    def default_soc(self) -> float | None:
        return self._async.default_soc()

    def target_soc(self) -> float | None:
        return self._async.target_soc()

    def primary_schedule_days(self) -> list[str]:
        return self._async.primary_schedule_days()

    def primary_schedule_departure_time(self) -> str | None:
        return self._async.primary_schedule_departure_time()

    def primary_schedule_departure_soc(self) -> float | None:
        return self._async.primary_schedule_departure_soc()

    def secondary_schedule_departure_time(self) -> str | None:
        return self._async.secondary_schedule_departure_time()

    def secondary_schedule_departure_soc(self) -> float | None:
        return self._async.secondary_schedule_departure_soc()

    def current_soc(self) -> float | None:
        return self._async.current_soc()

    def __repr__(self) -> str:
        return repr(self._async)

    # ------------------------------------------------------------------
    # Mutating operations (dispatched to the loop)
    # ------------------------------------------------------------------

    def set_charging_mode(self, mode: ChargingMode) -> None:
        self._runner.run(self._async.set_charging_mode(mode))

    def set_current_soc(self, soc: float) -> None:
        self._runner.run(self._async.set_current_soc(soc))

    def set_target_soc(self, soc: float) -> None:
        self._runner.run(self._async.set_target_soc(soc))

    def set_primary_departure_time(self, time: str) -> None:
        self._runner.run(self._async.set_primary_departure_time(time))

    def assign_charger(self, charger_id: str) -> None:
        self._runner.run(self._async.assign_charger(charger_id))


__all__ = ["Client", "EVCharger", "System", "Systems"]
