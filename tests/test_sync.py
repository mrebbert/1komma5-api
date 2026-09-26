"""Smoke tests for :mod:`onekommafive.sync`.

The sync facade delegates every method to the async client running on a
dedicated background event loop. The heavy behavioural tests live on the
async side (test_client.py, test_system.py, …); here we only verify that
each wrapper class exists, its methods dispatch to the async layer, and
the loop/thread lifecycle stays clean.
"""

from __future__ import annotations

from aioresponses import aioresponses

from onekommafive.sync import Client, EVCharger, System, Systems
from tests.fixtures import (
    FAKE_SYSTEM_ID,
    FAKE_TOKEN_SET,
    make_system_data,
    make_wallboxes_data,
)

_SYSTEMS_URL = "https://heartbeat.1komma5grad.com/api/v2/systems"


def _make_sync_client() -> Client:
    """Return a :class:`onekommafive.sync.Client` with a pre-loaded token set."""
    client = Client(username="user@example.com", password="password")
    client._async._token_set = FAKE_TOKEN_SET
    # Bypass JWT validation on the underlying async client.
    from unittest.mock import AsyncMock

    client._async._is_token_expiring = AsyncMock(return_value=False)
    return client


def test_client_context_manager_lifecycle() -> None:
    """__enter__/__exit__ must start and stop the internal loop cleanly."""
    with _make_sync_client() as client:
        assert isinstance(client, Client)
    # After __exit__, the runner's thread is joined and the loop closed.
    # Constructing a fresh client works the same way — no shared state.
    with _make_sync_client() as client2:
        assert client2 is not None


def test_systems_get_systems_delegates_to_async_layer() -> None:
    with aioresponses() as m:
        m.get(
            _SYSTEMS_URL,
            payload={"data": [make_system_data(FAKE_SYSTEM_ID)]},
            status=200,
        )
        with _make_sync_client() as client:
            systems = Systems(client).get_systems()
            assert len(systems) == 1
            assert isinstance(systems[0], System)
            assert systems[0].id() == FAKE_SYSTEM_ID


def test_system_get_wallboxes_returns_sync_wrappers() -> None:
    with aioresponses() as m:
        m.get(
            _SYSTEMS_URL,
            payload={"data": [make_system_data(FAKE_SYSTEM_ID)]},
            status=200,
        )
        m.get(
            f"https://heartbeat.1komma5grad.com/api/v1/sites/{FAKE_SYSTEM_ID}/assets/ev-chargers",
            payload=make_wallboxes_data(),
            status=200,
        )
        with _make_sync_client() as client:
            systems = Systems(client).get_systems()
            wallboxes = systems[0].get_wallboxes()
            assert len(wallboxes) >= 1


def test_sync_ev_charger_setter_smoke() -> None:
    """A single setter call proves the runner dispatches PATCH via the async layer."""
    from onekommafive.models import ChargingMode
    from tests.fixtures import make_ev_data

    ev_url = f"https://heartbeat.1komma5grad.com/api/v2/sites/{FAKE_SYSTEM_ID}/assets/evs/ev-1"
    with aioresponses() as m:
        m.get(
            _SYSTEMS_URL,
            payload={"data": [make_system_data(FAKE_SYSTEM_ID)]},
            status=200,
        )
        m.get(
            f"https://heartbeat.1komma5grad.com/api/v2/sites/{FAKE_SYSTEM_ID}/assets/evs",
            payload=[make_ev_data(ev_id="ev-1", charging_mode="SMART_CHARGE")],
            status=200,
        )
        m.patch(ev_url, payload={}, status=200)

        with _make_sync_client() as client:
            systems = Systems(client).get_systems()
            evs = systems[0].get_ev_chargers()
            assert isinstance(evs[0], EVCharger)
            evs[0].set_charging_mode(ChargingMode.SOLAR_CHARGE)
            assert evs[0].charging_mode() == ChargingMode.SOLAR_CHARGE


def test_ev_charger_read_only_accessors_pass_through() -> None:
    """Read-only accessors on EVCharger should not require the loop."""
    from tests.fixtures import make_ev_data

    with aioresponses() as m:
        m.get(
            _SYSTEMS_URL,
            payload={"data": [make_system_data(FAKE_SYSTEM_ID)]},
            status=200,
        )
        m.get(
            f"https://heartbeat.1komma5grad.com/api/v2/sites/{FAKE_SYSTEM_ID}/assets/evs",
            payload=[make_ev_data(ev_id="ev-1")],
            status=200,
        )
        with _make_sync_client() as client:
            evs = Systems(client).get_systems()[0].get_ev_chargers()
            ev = evs[0]
            # These never hit the network; they read from cached _data.
            assert ev.id() == "ev-1"
            assert isinstance(ev.name(), str | None)
            assert ev.charging_mode().value in {
                "SMART_CHARGE",
                "SOLAR_CHARGE",
                "QUICK_CHARGE",
            }
