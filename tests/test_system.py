"""Tests for :mod:`onekommafive.system` – per-system API calls."""

from __future__ import annotations

import datetime

import responses as resp_lib
import pytest

from onekommafive.errors import RequestError
from onekommafive.ev_charger import EVCharger
from onekommafive.models import EmsSettings, EnergyData, LiveOverview, MarketPrices, SystemInfo
from onekommafive.system import System
from tests.fixtures import (
    FAKE_SYSTEM_ID,
    make_client,
    make_displayed_ev_charging_modes_data,
    make_ems_settings_data,
    make_energy_data,
    make_ev_data,
    make_live_overview_data,
    make_price_data,
    make_system_data,
)

_BASE = "https://heartbeat.1komma5grad.com"
_SYSTEM_BASE = f"{_BASE}/api/v1/systems/{FAKE_SYSTEM_ID}"
_SYSTEM_BASE_V2 = f"{_BASE}/api/v2/systems/{FAKE_SYSTEM_ID}"
_SYSTEM_BASE_V3 = f"{_BASE}/api/v3/systems/{FAKE_SYSTEM_ID}"
_SYSTEM_BASE_V4 = f"{_BASE}/api/v4/systems/{FAKE_SYSTEM_ID}"


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

    @resp_lib.activate
    def test_info_returns_system_info_instance(self) -> None:
        resp_lib.add(
            resp_lib.GET,
            f"{_BASE}/api/v4/systems/{FAKE_SYSTEM_ID}",
            json=make_system_data(FAKE_SYSTEM_ID),
            status=200,
        )
        info = _make_system().info()
        assert isinstance(info, SystemInfo)
        assert info.id == FAKE_SYSTEM_ID
        assert info.name == "My Home System"
        assert info.status == "ACTIVE"
        assert info.address_city == "Hamburg"
        assert info.energy_trader_active is True
        assert info.electricity_contract_active is True


# ---------------------------------------------------------------------------
# Live overview
# ---------------------------------------------------------------------------

class TestGetLiveOverview:
    """Tests for System.get_live_overview."""

    @resp_lib.activate
    def test_returns_live_overview_instance(self) -> None:
        resp_lib.add(
            resp_lib.GET,
            f"{_SYSTEM_BASE_V3}/live-overview",
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
            f"{_SYSTEM_BASE_V3}/live-overview",
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
            f"{_SYSTEM_BASE_V3}/live-overview",
            json={"error": "unavailable"},
            status=503,
        )
        with pytest.raises(RequestError, match="Failed to get live overview"):
            _make_system().get_live_overview()


# ---------------------------------------------------------------------------
# Displayed EV charging modes
# ---------------------------------------------------------------------------

_SITES_BASE = f"{_BASE}/api/v1/sites/{FAKE_SYSTEM_ID}"


class TestGetDisplayedEvChargingModes:
    """Tests for System.get_displayed_ev_charging_modes."""

    @resp_lib.activate
    def test_returns_enabled_charging_modes(self) -> None:
        from onekommafive.models import ChargingMode

        resp_lib.add(
            resp_lib.GET,
            f"{_SITES_BASE}/assets/evs/displayed-ev-charging-modes",
            json=make_displayed_ev_charging_modes_data(),
            status=200,
        )
        modes = _make_system().get_displayed_ev_charging_modes()

        assert ChargingMode.SMART_CHARGE in modes
        assert ChargingMode.SOLAR_CHARGE in modes
        assert ChargingMode.QUICK_CHARGE not in modes  # disabled=True in fixture

    @resp_lib.activate
    def test_raises_on_server_error(self) -> None:
        resp_lib.add(
            resp_lib.GET,
            f"{_SITES_BASE}/assets/evs/displayed-ev-charging-modes",
            json={"error": "error"},
            status=500,
        )
        with pytest.raises(RequestError, match="Failed to get displayed EV charging modes"):
            _make_system().get_displayed_ev_charging_modes()


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
            f"{_SYSTEM_BASE_V4}/charts/market-prices",
            json=make_price_data(),
            status=200,
        )
        result = _make_system().get_prices(
            datetime.datetime(2024, 6, 1),
            datetime.datetime(2024, 6, 2),
        )

        assert isinstance(result, MarketPrices)
        assert result.average_price == pytest.approx(0.085)
        assert result.highest_price == pytest.approx(0.13)
        assert result.lowest_price == pytest.approx(0.015)
        assert result.grid_costs_total == pytest.approx(0.1637)
        assert result.vat == pytest.approx(0.19)
        assert result.uses_fallback_grid_costs is False

    @resp_lib.activate
    def test_prices_dict_keyed_by_timestamp(self) -> None:
        resp_lib.add(
            resp_lib.GET,
            f"{_SYSTEM_BASE_V4}/charts/market-prices",
            json=make_price_data(),
            status=200,
        )
        result = _make_system().get_prices(
            datetime.datetime(2024, 6, 1),
            datetime.datetime(2024, 6, 2),
        )

        assert result.prices["2024-06-01T00:00Z"] == pytest.approx(0.08)
        assert result.prices["2024-06-01T01:00Z"] == pytest.approx(0.09)
        assert result.prices_with_grid_costs["2024-06-01T00:00Z"] == pytest.approx(0.244)

    @resp_lib.activate
    def test_uses_zoned_datetime_format_and_default_resolution(self) -> None:
        resp_lib.add(
            resp_lib.GET,
            f"{_SYSTEM_BASE_V4}/charts/market-prices",
            json=make_price_data(),
            status=200,
        )
        _make_system().get_prices(
            start=datetime.datetime(2024, 6, 1),
            end=datetime.datetime(2024, 6, 3),
        )

        qs = resp_lib.calls[0].request.url
        assert "from=2024-06-01T" in qs
        assert "to=2024-06-03T" in qs
        assert "resolution=1h" in qs

    @resp_lib.activate
    def test_passes_resolution_when_specified(self) -> None:
        resp_lib.add(
            resp_lib.GET,
            f"{_SYSTEM_BASE_V4}/charts/market-prices",
            json=make_price_data(),
            status=200,
        )
        _make_system().get_prices(
            start=datetime.datetime(2024, 6, 1),
            end=datetime.datetime(2024, 6, 2),
            resolution="15m",
        )

        qs = resp_lib.calls[0].request.url
        assert "resolution=15m" in qs

    @resp_lib.activate
    def test_raises_on_server_error(self) -> None:
        resp_lib.add(
            resp_lib.GET,
            f"{_SYSTEM_BASE_V4}/charts/market-prices",
            json={"error": "error"},
            status=500,
        )
        with pytest.raises(RequestError, match="Failed to get prices"):
            _make_system().get_prices(
                datetime.datetime(2024, 6, 1),
                datetime.datetime(2024, 6, 2),
            )


# ---------------------------------------------------------------------------
# Energy today
# ---------------------------------------------------------------------------

class TestGetEnergyToday:
    @resp_lib.activate
    def test_returns_energy_data_instance(self) -> None:
        resp_lib.add(resp_lib.GET, f"{_SYSTEM_BASE_V2}/energy-today", json=make_energy_data(), status=200)
        result = _make_system().get_energy_today()
        assert isinstance(result, EnergyData)

    @resp_lib.activate
    def test_scalar_totals_parsed(self) -> None:
        resp_lib.add(resp_lib.GET, f"{_SYSTEM_BASE_V2}/energy-today", json=make_energy_data(), status=200)
        result = _make_system().get_energy_today()
        assert result.energy_produced_kwh == pytest.approx(30.76)
        assert result.self_sufficiency == pytest.approx(0.61)
        assert result.grid_supply_kwh == pytest.approx(10.33)
        assert result.grid_feed_in_kwh == pytest.approx(6.76)
        assert result.battery_charge_kwh == pytest.approx(22.42)
        assert result.battery_discharge_kwh == pytest.approx(14.58)
        assert result.consumption_total_kwh == pytest.approx(26.50)
        assert result.savings_eur == pytest.approx(6.48)
        assert result.updated_at == "2026-03-08T14:00:00Z"

    @resp_lib.activate
    def test_consumers_and_consumers_total_parsed(self) -> None:
        resp_lib.add(resp_lib.GET, f"{_SYSTEM_BASE_V2}/energy-today", json=make_energy_data(), status=200)
        result = _make_system().get_energy_today()
        # direct from PV
        assert result.consumption_household_kwh == pytest.approx(2.5)
        assert result.consumption_heat_pump_kwh == pytest.approx(8.0)
        assert result.consumption_ac_kwh is None
        # total (from all sources)
        assert result.consumption_household_total_kwh == pytest.approx(13.5)
        assert result.consumption_ev_total_kwh == pytest.approx(5.0)
        assert result.consumption_heat_pump_total_kwh == pytest.approx(12.0)
        assert result.consumption_ac_total_kwh is None

    @resp_lib.activate
    def test_timeseries_nested_under_data_key(self) -> None:
        resp_lib.add(resp_lib.GET, f"{_SYSTEM_BASE_V2}/energy-today", json=make_energy_data(), status=200)
        result = _make_system().get_energy_today()
        assert len(result.timeseries) == 2
        slot = result.timeseries["2026-03-08T12:00Z"]
        assert slot.production == pytest.approx(5.008)
        assert slot.grid_supply == pytest.approx(0.334)
        assert slot.grid_feed_in == pytest.approx(0.053)
        assert slot.battery_soc == pytest.approx(0.536)
        assert slot.battery_charge == pytest.approx(4.688)
        assert slot.consumption_household == pytest.approx(0.267)
        assert slot.consumption_household_total == pytest.approx(0.602)
        assert slot.consumption_ac is None
        assert slot.consumption_ac_total is None

    @resp_lib.activate
    def test_default_resolution_is_1h(self) -> None:
        resp_lib.add(resp_lib.GET, f"{_SYSTEM_BASE_V2}/energy-today", json=make_energy_data(), status=200)
        _make_system().get_energy_today()
        assert "resolution=1h" in resp_lib.calls[0].request.url

    @resp_lib.activate
    def test_passes_resolution_15m(self) -> None:
        resp_lib.add(resp_lib.GET, f"{_SYSTEM_BASE_V2}/energy-today", json=make_energy_data(), status=200)
        _make_system().get_energy_today(resolution="15m")
        assert "resolution=15m" in resp_lib.calls[0].request.url

    @resp_lib.activate
    def test_raises_on_server_error(self) -> None:
        resp_lib.add(resp_lib.GET, f"{_SYSTEM_BASE_V2}/energy-today", json={}, status=500)
        with pytest.raises(RequestError, match="Failed to get energy today"):
            _make_system().get_energy_today()


# ---------------------------------------------------------------------------
# Energy historical
# ---------------------------------------------------------------------------

class TestGetEnergyHistorical:
    @resp_lib.activate
    def test_returns_energy_data_instance(self) -> None:
        resp_lib.add(resp_lib.GET, f"{_SYSTEM_BASE_V3}/energy-historical", json=make_energy_data(), status=200)
        result = _make_system().get_energy_historical(
            from_date=datetime.date(2026, 3, 8), to_date=datetime.date(2026, 3, 8)
        )
        assert isinstance(result, EnergyData)
        assert result.energy_produced_kwh == pytest.approx(30.76)

    @resp_lib.activate
    def test_passes_date_and_resolution_params(self) -> None:
        resp_lib.add(resp_lib.GET, f"{_SYSTEM_BASE_V3}/energy-historical", json=make_energy_data(), status=200)
        _make_system().get_energy_historical(
            from_date=datetime.date(2026, 3, 1), to_date=datetime.date(2026, 3, 2)
        )
        url = resp_lib.calls[0].request.url
        assert "from=2026-03-01" in url
        assert "to=2026-03-02" in url
        assert "resolution=1h" in url

    @resp_lib.activate
    def test_passes_resolution_15m(self) -> None:
        resp_lib.add(resp_lib.GET, f"{_SYSTEM_BASE_V3}/energy-historical", json=make_energy_data(), status=200)
        _make_system().get_energy_historical(
            from_date=datetime.date(2026, 3, 8), to_date=datetime.date(2026, 3, 8), resolution="15m"
        )
        assert "resolution=15m" in resp_lib.calls[0].request.url

    @resp_lib.activate
    def test_timeseries_parsed(self) -> None:
        resp_lib.add(resp_lib.GET, f"{_SYSTEM_BASE_V3}/energy-historical", json=make_energy_data(), status=200)
        result = _make_system().get_energy_historical(
            from_date=datetime.date(2026, 3, 8), to_date=datetime.date(2026, 3, 8)
        )
        assert len(result.timeseries) == 2

    @resp_lib.activate
    def test_raises_on_server_error(self) -> None:
        resp_lib.add(resp_lib.GET, f"{_SYSTEM_BASE_V3}/energy-historical", json={}, status=500)
        with pytest.raises(RequestError, match="Failed to get historical energy data"):
            _make_system().get_energy_historical(
                from_date=datetime.date(2026, 3, 8), to_date=datetime.date(2026, 3, 8)
            )
