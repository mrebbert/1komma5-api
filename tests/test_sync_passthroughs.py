"""Parametrized passthrough coverage for :mod:`onekommafive.sync`.

The heavy behaviour lives on the async side; here we only prove that each
sync wrapper method dispatches to its async counterpart through the
:class:`onekommafive.sync._LoopRunner`. All async methods are stubbed
with :class:`unittest.mock.AsyncMock`, so no real I/O runs.
"""

from __future__ import annotations

import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, sentinel

import pytest

from onekommafive.sync import Client, EVCharger, System, Systems
from tests.fixtures import FAKE_TOKEN_SET


def _make_sync_client() -> Client:
    client = Client(username="user@example.com", password="password")
    client._async._token_set = FAKE_TOKEN_SET
    client._async._is_token_expiring = AsyncMock(return_value=False)
    return client


CLIENT_METHODS = [
    ("get_token", (), "token"),
    ("get_user", (), sentinel.user),
    ("get_supported_versions", (), sentinel.versions),
    ("logout", (), None),
]


@pytest.mark.parametrize(("method", "args", "expected"), CLIENT_METHODS)
def test_client_delegates_to_async(
    method: str, args: tuple[Any, ...], expected: Any,
) -> None:
    with _make_sync_client() as client:
        setattr(client._async, method, AsyncMock(return_value=expected))
        result = getattr(client, method)(*args)
        assert result == expected or result is None
        getattr(client._async, method).assert_awaited_once_with(*args)


def test_client_identity_api_property() -> None:
    with _make_sync_client() as client:
        assert client.IDENTITY_API == client._async.IDENTITY_API


def test_systems_get_system_delegates() -> None:
    with _make_sync_client() as client:
        stub = MagicMock()
        stub.id.return_value = "sys-1"
        client._async.__class__  # ensure attribute access
        systems = Systems(client)
        systems._async.get_system = AsyncMock(return_value=stub)
        result = systems.get_system("sys-1")
        assert isinstance(result, System)
        systems._async.get_system.assert_awaited_once_with("sys-1")


DT_START = datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC)
DT_END = datetime.datetime(2026, 1, 2, tzinfo=datetime.UTC)
DATE_FROM = datetime.date(2026, 1, 1)
DATE_TO = datetime.date(2026, 1, 2)

SYSTEM_METHODS: list[tuple[str, tuple[Any, ...]]] = [
    ("info", ()),
    ("get_details", ()),
    ("get_status_and_assets", ()),
    ("get_device_gateways", ()),
    ("get_active_features", ("cust-1",)),
    ("get_live_overview", ()),
    ("get_displayed_ev_charging_modes", ()),
    ("get_energy_today", ("1h",)),
    ("get_energy_savings", (DATE_FROM, DATE_TO)),
    ("get_energy_historical", (DATE_FROM, DATE_TO, "1h")),
    ("get_ems_settings", ()),
    ("set_ems_mode", (True,)),
    ("get_prices", (DT_START, DT_END, "1h")),
    ("get_weather", ()),
    ("get_price_customizations", ()),
    ("get_comparison_price", ()),
    ("get_price_guarantee", ("cust-1",)),
    ("get_wallboxes", ()),
    ("get_smart_meter", ()),
    ("get_impact_overview", ()),
    ("get_energy_trader", ()),
    ("get_heartbeat_prices", ()),
    ("get_monthly_trading_savings", ()),
    ("get_heartbeat_ai_summary", ("1M",)),
    ("get_optimizations", (DT_START, DT_END)),
    ("get_self_sufficiency_events", (DT_START, DT_END)),
    ("get_site_details", ()),
    ("get_customer", ("cust-1",)),
    ("get_subscriptions", ("cust-1",)),
    ("get_notifications", ()),
    ("get_notification_settings", ()),
]


@pytest.mark.parametrize(("method", "args"), SYSTEM_METHODS)
def test_system_delegates_to_async(method: str, args: tuple[Any, ...]) -> None:
    with _make_sync_client() as client:
        async_system = MagicMock()
        async_system.id.return_value = "sys-1"
        setattr(async_system, method, AsyncMock(return_value=sentinel.result))
        wrapper = System.__new__(System)
        wrapper._runner = client._runner
        wrapper._async = async_system
        result = getattr(wrapper, method)(*args)
        assert result is sentinel.result or result is None
        getattr(async_system, method).assert_awaited_once_with(*args)


def test_system_id_and_repr_do_not_touch_loop() -> None:
    async_system = MagicMock()
    async_system.id.return_value = "sys-abc"
    wrapper = System.__new__(System)
    wrapper._runner = MagicMock()
    wrapper._async = async_system
    assert wrapper.id() == "sys-abc"
    assert repr(wrapper) == "System(id='sys-abc')"
    wrapper._runner.run.assert_not_called()


def test_system_get_ev_chargers_wraps_each() -> None:
    with _make_sync_client() as client:
        async_charger = MagicMock()
        async_charger.id.return_value = "ev-1"
        async_system = MagicMock()
        async_system.get_ev_chargers = AsyncMock(return_value=[async_charger])
        wrapper = System.__new__(System)
        wrapper._runner = client._runner
        wrapper._async = async_system
        chargers = wrapper.get_ev_chargers()
        assert len(chargers) == 1
        assert isinstance(chargers[0], EVCharger)


EV_ACCESSORS = [
    "id",
    "name",
    "manufacturer",
    "model",
    "capacity_wh",
    "min_charging_current_a",
    "safety_range_km",
    "assigned_charger_id",
    "manual_soc_timestamp",
    "updated_at",
    "charging_mode",
    "charging_mode_updated_at",
    "default_soc",
    "target_soc",
    "primary_schedule_days",
    "primary_schedule_departure_time",
    "primary_schedule_departure_soc",
    "secondary_schedule_departure_time",
    "secondary_schedule_departure_soc",
    "current_soc",
]


@pytest.mark.parametrize("method", EV_ACCESSORS)
def test_ev_accessor_passthrough(method: str) -> None:
    async_charger = MagicMock()
    getattr(async_charger, method).return_value = sentinel.value
    wrapper = EVCharger(runner=MagicMock(), async_charger=async_charger)
    assert getattr(wrapper, method)() is sentinel.value
    wrapper._runner.run.assert_not_called()


EV_SETTERS = [
    ("set_charging_mode", (MagicMock(),)),
    ("set_current_soc", (0.42,)),
    ("set_target_soc", (0.9,)),
    ("set_primary_departure_time", ("07:30",)),
    ("assign_charger", ("charger-1",)),
]


@pytest.mark.parametrize(("method", "args"), EV_SETTERS)
def test_ev_setter_dispatches_to_loop(method: str, args: tuple[Any, ...]) -> None:
    with _make_sync_client() as client:
        async_charger = MagicMock()
        setattr(async_charger, method, AsyncMock(return_value=None))
        wrapper = EVCharger(runner=client._runner, async_charger=async_charger)
        result = getattr(wrapper, method)(*args)
        assert result is None
        getattr(async_charger, method).assert_awaited_once_with(*args)


def test_ev_repr_delegates_without_loop() -> None:
    async_charger = MagicMock()
    async_charger.__repr__ = MagicMock(return_value="EVCharger(id='ev-1')")
    wrapper = EVCharger(runner=MagicMock(), async_charger=async_charger)
    assert repr(wrapper) == "EVCharger(id='ev-1')"


def test_client_close_is_idempotent() -> None:
    client = _make_sync_client()
    client.close()
    client.close()
    assert client._closed is True


def test_system_direct_construction_works() -> None:
    with _make_sync_client() as client:
        system = System(client, {"id": "sys-direct"})
        assert system.id() == "sys-direct"


def test_close_leftover_clients_closes_live_clients() -> None:
    """The atexit hook must close every SyncClient still in :attr:`Client._live`."""
    from onekommafive.sync import _close_leftover_clients

    client = _make_sync_client()
    assert client in Client._live
    _close_leftover_clients()
    assert client._closed is True
    assert client not in Client._live


def test_close_leftover_clients_swallows_close_errors() -> None:
    """One raising close() must not skip the others."""
    from onekommafive.sync import _close_leftover_clients

    good = _make_sync_client()
    bad = _make_sync_client()
    bad.close = MagicMock(side_effect=RuntimeError("boom"))  # type: ignore[method-assign]
    Client._live.add(bad)
    _close_leftover_clients()
    assert good._closed is True
    Client._live.discard(bad)
