"""Tests for :mod:`onekommafive.systems` – system collection retrieval."""

from __future__ import annotations

import pytest
from aioresponses import aioresponses

from onekommafive.errors import RequestError
from onekommafive.system import System
from onekommafive.systems import Systems
from tests.fixtures import (
    FAKE_SYSTEM_ID,
    FAKE_SYSTEM_ID_2,
    NULL_SYSTEM_ID,
    make_client,
    make_system_data,
)

_SYSTEMS_URL = "https://heartbeat.1komma5grad.com/api/v2/systems"


class TestGetSystems:
    """Tests for Systems.get_systems."""

    async def test_returns_list_of_system_objects(self) -> None:
        with aioresponses() as m:
            m.get(
                _SYSTEMS_URL,
                payload={"data": [make_system_data(FAKE_SYSTEM_ID)]},
                status=200,
            )
            client = make_client()
            systems = await Systems(client).get_systems()

            assert len(systems) == 1
            assert isinstance(systems[0], System)
            assert systems[0].id() == FAKE_SYSTEM_ID
            await client.close()

    async def test_filters_out_null_uuid_systems(self) -> None:
        """Placeholder systems with the nil UUID must be excluded from results."""
        with aioresponses() as m:
            m.get(
                _SYSTEMS_URL,
                payload={
                    "data": [
                        make_system_data(FAKE_SYSTEM_ID),
                        make_system_data(NULL_SYSTEM_ID),
                    ]
                },
                status=200,
            )
            client = make_client()
            systems = await Systems(client).get_systems()

            assert len(systems) == 1
            assert systems[0].id() == FAKE_SYSTEM_ID
            await client.close()

    async def test_returns_empty_list_when_no_active_systems(self) -> None:
        with aioresponses() as m:
            m.get(
                _SYSTEMS_URL,
                payload={"data": [make_system_data(NULL_SYSTEM_ID)]},
                status=200,
            )
            client = make_client()
            systems = await Systems(client).get_systems()
            assert systems == []
            await client.close()

    async def test_handles_multiple_active_systems(self) -> None:
        with aioresponses() as m:
            m.get(
                _SYSTEMS_URL,
                payload={
                    "data": [
                        make_system_data(FAKE_SYSTEM_ID),
                        make_system_data(FAKE_SYSTEM_ID_2),
                    ]
                },
                status=200,
            )
            client = make_client()
            systems = await Systems(client).get_systems()
            assert len(systems) == 2
            await client.close()

    async def test_raises_on_server_error(self) -> None:
        with aioresponses() as m:
            m.get(_SYSTEMS_URL, payload={"error": "server error"}, status=500)
            client = make_client()
            with pytest.raises(RequestError, match="Failed to get systems"):
                await Systems(client).get_systems()
            await client.close()


class TestGetSystem:
    """Tests for Systems.get_system."""

    async def test_returns_system_by_id(self) -> None:
        with aioresponses() as m:
            m.get(
                f"{_SYSTEMS_URL}/{FAKE_SYSTEM_ID}",
                payload=make_system_data(FAKE_SYSTEM_ID),
                status=200,
            )
            client = make_client()
            system = await Systems(client).get_system(FAKE_SYSTEM_ID)

            assert isinstance(system, System)
            assert system.id() == FAKE_SYSTEM_ID
            await client.close()

    async def test_raises_on_not_found(self) -> None:
        with aioresponses() as m:
            m.get(
                f"{_SYSTEMS_URL}/{FAKE_SYSTEM_ID}",
                payload={"error": "not found"},
                status=404,
            )
            client = make_client()
            with pytest.raises(RequestError, match="Failed to get system"):
                await Systems(client).get_system(FAKE_SYSTEM_ID)
            await client.close()
