"""Tests for :mod:`onekommafive.system` – per-system API calls."""

from __future__ import annotations

import datetime

import responses as resp_lib
import pytest

from onekommafive.errors import RequestError
from onekommafive.ev_charger import EVCharger
from onekommafive.models import EmsSettings, LiveOverview, MarketPrices
from onekommafive.system import System
from tests.fixtures import (
    FAKE_SYSTEM_ID,
    make_client,
    make_ems_settings_data,
    make_ev_data,
    make_live_overview_data,
    make_price_data,
    make_system_data,
)

_BASE = "https://heartbeat.1komma5grad.com"
_SYSTEM_BASE = f"{_BASE}/api/v1/systems/{FAKE_SYSTEM_ID}"
_SYSTEM_BASE_V2 = f"{_BASE}/api/v2/systems/{FAKE_SYSTEM_ID}"


def _make_system() -> System:
    return System(make_client(), make_system_data(FAKE_SYSTEM_ID))


# ---------------------------------------------------------------------------
# Identity
# ---------------------------------------------------------------------------

class TestSystemIdentity:
    def test_id_returns_correct_value(self) -> None:
        system = _make_system()
        assert system.id() == FAKE_SYSTEM_ID

    def test_repr_contains_id(self) -> None:
        system = _make_system()
        assert FAKE_SYSTEM_ID in repr(system)


# ---------------------------------------------------------------------------
# Live overview
# ---------------------------------------------------------------------------

class TestGetLiveOverview:
    """Tests for System.get_live_overview."""

    @resp_lib.activate
    def test_returns_live_overview_instance(self) -> None:
        resp_lib.add(
            resp_lib.GET,
            f"{_SYSTEM_BASE}/live-overview",
            json=make_live_overview_data(),
            status=200,
        )
        overview = _make_system().get_live_overview()

        assert isinstance(overview, LiveOverview)
        assert overview.pv_power == 2500.0
        assert overview.battery_power == -500.0
        assert overview.battery_soc == 72.5
        assert overview.grid_power == 0.0
        assert overview.consumption_power == 3000.0

    @resp_lib.activate
    def test_handles_missing_optional_fields(self) -> None:
        """Systems without batteries should still return a valid LiveOverview."""
        resp_lib.add(
            resp_lib.GET,
            f"{_SYSTEM_BASE}/live-overview",
            json={"liveHeroView": {"production": {"value": 1000.0, "unit": "W"}}},
            status=200,
        )
        overview = _make_system().get_live_overview()

        assert overview.pv_power == 1000.0
        assert overview.battery_power is None
        assert overview.battery_soc is None

    @resp_lib.activate
    def test_raises_on_server_error(self) -> None:
        resp_lib.add(
            resp_lib.GET,
            f"{_SYSTEM_BASE}/live-overview",
            json={"error": "unavailable"},
            status=503,
        )
        with pytest.raises(RequestError, match="Failed to get live overview"):
            _make_system().get_live_overview()


# ---------------------------------------------------------------------------
# EV chargers
# ---------------------------------------------------------------------------

class TestGetEvChargers:
    """Tests for System.get_ev_chargers."""

    @resp_lib.activate
    def test_returns_list_of_ev_charger_instances(self) -> None:
        resp_lib.add(
            resp_lib.GET,
            f"{_SYSTEM_BASE}/devices/evs",
            json=[make_ev_data()],
            status=200,
        )
        chargers = _make_system().get_ev_chargers()

        assert len(chargers) == 1
        assert isinstance(chargers[0], EVCharger)

    @resp_lib.activate
    def test_returns_empty_list_when_no_ev_chargers(self) -> None:
        resp_lib.add(
            resp_lib.GET,
            f"{_SYSTEM_BASE}/devices/evs",
            json=[],
            status=200,
        )
        assert _make_system().get_ev_chargers() == []

    @resp_lib.activate
    def test_raises_on_server_error(self) -> None:
        resp_lib.add(
            resp_lib.GET,
            f"{_SYSTEM_BASE}/devices/evs",
            json={"error": "error"},
            status=500,
        )
        with pytest.raises(RequestError, match="Failed to get EV chargers"):
            _make_system().get_ev_chargers()


# ---------------------------------------------------------------------------
# EMS settings
# ---------------------------------------------------------------------------

class TestGetEmsSettings:
    """Tests for System.get_ems_settings."""

    @resp_lib.activate
    def test_returns_ems_settings_in_auto_mode(self) -> None:
        resp_lib.add(
            resp_lib.GET,
            f"{_SYSTEM_BASE}/ems/actions/get-settings",
            json=make_ems_settings_data(override=False),
            status=200,
        )
        settings = _make_system().get_ems_settings()

        assert isinstance(settings, EmsSettings)
        assert settings.auto_mode is True

    @resp_lib.activate
    def test_returns_ems_settings_in_manual_mode(self) -> None:
        resp_lib.add(
            resp_lib.GET,
            f"{_SYSTEM_BASE}/ems/actions/get-settings",
            json=make_ems_settings_data(override=True),
            status=200,
        )
        settings = _make_system().get_ems_settings()
        assert settings.auto_mode is False

    @resp_lib.activate
    def test_raises_on_server_error(self) -> None:
        resp_lib.add(
            resp_lib.GET,
            f"{_SYSTEM_BASE}/ems/actions/get-settings",
            json={"error": "error"},
            status=500,
        )
        with pytest.raises(RequestError, match="Failed to get EMS settings"):
            _make_system().get_ems_settings()


# ---------------------------------------------------------------------------
# Set EMS mode
# ---------------------------------------------------------------------------

class TestSetEmsMode:
    """Tests for System.set_ems_mode."""

    @resp_lib.activate
    def test_sets_auto_mode(self) -> None:
        resp_lib.add(
            resp_lib.POST,
            f"{_SYSTEM_BASE}/ems/actions/set-manual-override",
            json={},
            status=201,
        )
        _make_system().set_ems_mode(auto=True)  # must not raise

        body = resp_lib.calls[0].request.body
        import json
        payload = json.loads(body)
        assert payload["overrideAutoSettings"] is False

    @resp_lib.activate
    def test_sets_manual_override(self) -> None:
        resp_lib.add(
            resp_lib.POST,
            f"{_SYSTEM_BASE}/ems/actions/set-manual-override",
            json={},
            status=201,
        )
        _make_system().set_ems_mode(auto=False)

        import json
        payload = json.loads(resp_lib.calls[0].request.body)
        assert payload["overrideAutoSettings"] is True

    @resp_lib.activate
    def test_raises_on_unexpected_status(self) -> None:
        resp_lib.add(
            resp_lib.POST,
            f"{_SYSTEM_BASE}/ems/actions/set-manual-override",
            json={},
            status=200,  # API expects 201
        )
        with pytest.raises(RequestError, match="Failed to set EMS mode"):
            _make_system().set_ems_mode(auto=True)


# ---------------------------------------------------------------------------
# Market prices
# ---------------------------------------------------------------------------

class TestGetPrices:
    """Tests for System.get_prices."""

    @resp_lib.activate
    def test_returns_market_prices_instance(self) -> None:
        resp_lib.add(
            resp_lib.GET,
            f"{_SYSTEM_BASE_V2}/charts/market-prices",
            json=make_price_data(),
            status=200,
        )
        result = _make_system().get_prices(
            datetime.datetime(2024, 6, 1),
            datetime.datetime(2024, 6, 2),
        )

        assert isinstance(result, MarketPrices)
        assert result.average_price == 8.5
        assert result.highest_price == 13.0
        assert result.lowest_price == 1.5
        assert result.grid_costs_total == 16.37
        assert result.vat == 0.19
        assert result.uses_fallback_grid_costs is False

    @resp_lib.activate
    def test_prices_dict_keyed_by_timestamp(self) -> None:
        resp_lib.add(
            resp_lib.GET,
            f"{_SYSTEM_BASE_V2}/charts/market-prices",
            json=make_price_data(),
            status=200,
        )
        result = _make_system().get_prices(
            datetime.datetime(2024, 6, 1),
            datetime.datetime(2024, 6, 2),
        )

        assert result.prices["2024-06-01T00:00Z"] == 8.0
        assert result.prices["2024-06-01T01:00Z"] == 9.0
        assert result.prices_with_grid_costs["2024-06-01T00:00Z"] == 24.4

    @resp_lib.activate
    def test_omits_resolution_param_by_default(self) -> None:
        resp_lib.add(
            resp_lib.GET,
            f"{_SYSTEM_BASE_V2}/charts/market-prices",
            json=make_price_data(),
            status=200,
        )
        _make_system().get_prices(
            start=datetime.datetime(2024, 6, 1),
            end=datetime.datetime(2024, 6, 3),
        )

        qs = resp_lib.calls[0].request.url
        assert "from=2024-06-01" in qs
        assert "to=2024-06-03" in qs
        assert "resolution" not in qs

    @resp_lib.activate
    def test_passes_resolution_when_specified(self) -> None:
        resp_lib.add(
            resp_lib.GET,
            f"{_SYSTEM_BASE_V2}/charts/market-prices",
            json=make_price_data(),
            status=200,
        )
        _make_system().get_prices(
            start=datetime.datetime(2024, 6, 1),
            end=datetime.datetime(2024, 6, 2),
            resolution="1h",
        )

        qs = resp_lib.calls[0].request.url
        assert "resolution=1h" in qs

    @resp_lib.activate
    def test_raises_on_server_error(self) -> None:
        resp_lib.add(
            resp_lib.GET,
            f"{_SYSTEM_BASE_V2}/charts/market-prices",
            json={"error": "error"},
            status=500,
        )
        with pytest.raises(RequestError, match="Failed to get prices"):
            _make_system().get_prices(
                datetime.datetime(2024, 6, 1),
                datetime.datetime(2024, 6, 2),
            )
