"""Tests for :mod:`onekommafive.systems` – system collection retrieval."""

from __future__ import annotations

import responses as resp_lib
import pytest

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

    @resp_lib.activate
    def test_returns_list_of_system_objects(self) -> None:
        resp_lib.add(
            resp_lib.GET,
            _SYSTEMS_URL,
            json={"data": [make_system_data(FAKE_SYSTEM_ID)]},
            status=200,
        )
        systems = Systems(make_client()).get_systems()

        assert len(systems) == 1
        assert isinstance(systems[0], System)
        assert systems[0].id() == FAKE_SYSTEM_ID

    @resp_lib.activate
    def test_filters_out_null_uuid_systems(self) -> None:
        """Placeholder systems with the nil UUID must be excluded from results."""
        resp_lib.add(
            resp_lib.GET,
            _SYSTEMS_URL,
            json={
                "data": [
                    make_system_data(FAKE_SYSTEM_ID),
                    make_system_data(NULL_SYSTEM_ID),
                ]
            },
            status=200,
        )
        systems = Systems(make_client()).get_systems()

        assert len(systems) == 1
        assert systems[0].id() == FAKE_SYSTEM_ID

    @resp_lib.activate
    def test_returns_empty_list_when_no_active_systems(self) -> None:
        resp_lib.add(
            resp_lib.GET,
            _SYSTEMS_URL,
            json={"data": [make_system_data(NULL_SYSTEM_ID)]},
            status=200,
        )
        systems = Systems(make_client()).get_systems()
        assert systems == []

    @resp_lib.activate
    def test_handles_multiple_active_systems(self) -> None:
        resp_lib.add(
            resp_lib.GET,
            _SYSTEMS_URL,
            json={
                "data": [
                    make_system_data(FAKE_SYSTEM_ID),
                    make_system_data(FAKE_SYSTEM_ID_2),
                ]
            },
            status=200,
        )
        systems = Systems(make_client()).get_systems()
        assert len(systems) == 2

    @resp_lib.activate
    def test_raises_on_server_error(self) -> None:
        resp_lib.add(resp_lib.GET, _SYSTEMS_URL, json={"error": "server error"}, status=500)
        with pytest.raises(RequestError, match="Failed to get systems"):
            Systems(make_client()).get_systems()


class TestGetSystem:
    """Tests for Systems.get_system."""

    @resp_lib.activate
    def test_returns_system_by_id(self) -> None:
        resp_lib.add(
            resp_lib.GET,
            f"{_SYSTEMS_URL}/{FAKE_SYSTEM_ID}",
            json=make_system_data(FAKE_SYSTEM_ID),
            status=200,
        )
        system = Systems(make_client()).get_system(FAKE_SYSTEM_ID)

        assert isinstance(system, System)
        assert system.id() == FAKE_SYSTEM_ID

    @resp_lib.activate
    def test_raises_on_not_found(self) -> None:
        resp_lib.add(
            resp_lib.GET,
            f"{_SYSTEMS_URL}/{FAKE_SYSTEM_ID}",
            json={"error": "not found"},
            status=404,
        )
        with pytest.raises(RequestError, match="Failed to get system"):
            Systems(make_client()).get_system(FAKE_SYSTEM_ID)
