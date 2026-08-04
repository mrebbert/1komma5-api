"""Tests for :mod:`onekommafive.system` – per-system API calls."""

from __future__ import annotations

import datetime

import pytest
import responses as resp_lib

from onekommafive.errors import RequestError
from onekommafive.ev_charger import EVCharger
from onekommafive.models import (
    ComparisonPrice,
    Customer,
    EmsSettings,
    EnergyData,
    EnergyTrader,
    HeartbeatAiSummary,
    HeartbeatPrices,
    HeartbeatPriceWindow,
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
    SystemDetails,
    SystemInfo,
    Wallbox,
    WeatherData,
)
from onekommafive.system import System
from tests.fixtures import (
    FAKE_SYSTEM_ID,
    FAKE_USER_ID,
    make_active_features_data,
    make_client,
    make_comparison_price_data,
    make_customer_data,
    make_displayed_ev_charging_modes_data,
    make_ems_settings_data,
    make_energy_data,
    make_energy_savings_data,
    make_energy_trader_data,
    make_ev_data,
    make_heartbeat_ai_summary_data,
    make_heartbeat_prices_data,
    make_impact_overview_data,
    make_live_overview_data,
    make_monthly_trading_savings_data,
    make_notification_settings_data,
    make_notifications_data,
    make_optimizations_data,
    make_price_customizations_data,
    make_price_data,
    make_price_guarantee_data,
    make_self_sufficiency_events_data,
    make_site_details_data,
    make_smart_meter_data,
    make_status_and_assets_data,
    make_subscriptions_data,
    make_system_data,
    make_system_details_data,
    make_user_data,
    make_wallboxes_data,
    make_weather_data,
)

_BASE = "https://heartbeat.1komma5grad.com"
_IDENTITY_BASE = "https://customer-identity.1komma5grad.com"
_SYSTEM_BASE = f"{_BASE}/api/v1/systems/{FAKE_SYSTEM_ID}"
_SYSTEM_BASE_V2 = f"{_BASE}/api/v2/systems/{FAKE_SYSTEM_ID}"
_SYSTEM_BASE_V3 = f"{_BASE}/api/v3/systems/{FAKE_SYSTEM_ID}"
_SYSTEM_BASE_V4 = f"{_BASE}/api/v4/systems/{FAKE_SYSTEM_ID}"
_SITE_BASE_V2 = f"{_BASE}/api/v2/sites/{FAKE_SYSTEM_ID}"
_OPTIMIZATIONS_URL = f"{_BASE}/api/v1/heartbeat-ai/optimizations"
_SELF_SUFFICIENCY_URL = f"{_BASE}/api/v1/heartbeat-ai/self-sufficiency"
_USERS_ME_URL = f"{_IDENTITY_BASE}/api/v1/users/me"


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
# System details (v1)
# ---------------------------------------------------------------------------

class TestGetSystemDetails:
    """Tests for System.get_details."""

    @resp_lib.activate
    def test_returns_system_details_instance(self) -> None:
        resp_lib.add(
            resp_lib.GET,
            f"{_SYSTEM_BASE}/details",
            json=make_system_details_data(FAKE_SYSTEM_ID),
            status=200,
        )
        details = _make_system().get_details()
        assert isinstance(details, SystemDetails)
        assert details.id == FAKE_SYSTEM_ID
        assert details.name == "My Home System"
        assert details.status == "ACTIVE"
        assert details.emp_type == "GRIDX"
        assert details.address_city == "Hamburg"
        assert details.address_country == "DE"
        assert details.technical_contact_name == "Example Installer"
        assert details.customer is not None
        assert details.customer.email == "user@example.com"
        assert details.customer.first_name == "John"
        assert details.energy_trader_active is True
        assert details.electricity_contract_active is True
        assert details.has_third_party_smart_meter is None  # API returned null
        assert details.earliest_measurement == "2025-01-24"
        assert len(details.device_gateways) == 1
        gw = details.device_gateways[0]
        assert gw.id == "gw-0001-0000-0000-0000-000000000001"
        assert gw.serial_number == "I000-000-000-000-000-X-X"
        assert gw.installation_date == "2025-01-24"

    @resp_lib.activate
    def test_handles_minimal_response(self) -> None:
        """Systems with most optional fields missing should still parse."""
        resp_lib.add(
            resp_lib.GET,
            f"{_SYSTEM_BASE}/details",
            json={"id": FAKE_SYSTEM_ID},
            status=200,
        )
        details = _make_system().get_details()
        assert details.id == FAKE_SYSTEM_ID
        assert details.name is None
        assert details.customer is None
        assert details.device_gateways == []
        assert details.energy_trader_active is None
        assert details.electricity_contract_active is None
        assert details.has_third_party_smart_meter is None
        assert details.dynamic_pulse_compatible is False

    @resp_lib.activate
    def test_raises_on_server_error(self) -> None:
        resp_lib.add(
            resp_lib.GET,
            f"{_SYSTEM_BASE}/details",
            json={"error": "error"},
            status=500,
        )
        with pytest.raises(RequestError, match="Failed to get system details"):
            _make_system().get_details()


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


# ---------------------------------------------------------------------------
# Status and assets (v2)
# ---------------------------------------------------------------------------

class TestGetStatusAndAssets:
    """Tests for System.get_status_and_assets."""

    @resp_lib.activate
    def test_returns_site_status_instance(self) -> None:
        resp_lib.add(
            resp_lib.GET,
            f"{_SITE_BASE_V2}/status-and-assets",
            json=make_status_and_assets_data(),
            status=200,
        )
        result = _make_system().get_status_and_assets()
        assert isinstance(result, SiteStatus)
        assert result.status == "CONNECTED"
        assert len(result.assets) == 4

    @resp_lib.activate
    def test_flattens_connection_and_network(self) -> None:
        resp_lib.add(
            resp_lib.GET,
            f"{_SITE_BASE_V2}/status-and-assets",
            json=make_status_and_assets_data(),
            status=200,
        )
        result = _make_system().get_status_and_assets()
        types = {a.type for a in result.assets}
        assert types == {"HYBRID", "HEAT_PUMP", "METER", "EV_CHARGER"}
        for asset in result.assets:
            assert asset.connection_status == "CONNECTED"
            assert asset.network_address is not None
            assert asset.emp_type == "GRIDX"

    @resp_lib.activate
    def test_extracts_optional_fields(self) -> None:
        resp_lib.add(
            resp_lib.GET,
            f"{_SITE_BASE_V2}/status-and-assets",
            json=make_status_and_assets_data(),
            status=200,
        )
        assets = {a.type: a for a in _make_system().get_status_and_assets().assets}
        # EV charger has a name; others don't
        assert assets["EV_CHARGER"].name == "Wallbox"
        assert assets["HYBRID"].name is None
        # Heat pump has heat_pump_meter_type; others don't
        assert assets["HEAT_PUMP"].heat_pump_meter_type == "HOUSEHOLD"
        assert assets["METER"].heat_pump_meter_type is None
        # serial_number uses lowercase 'n' API field
        assert assets["EV_CHARGER"].serial_number == "00000"

    @resp_lib.activate
    def test_raises_on_server_error(self) -> None:
        resp_lib.add(
            resp_lib.GET,
            f"{_SITE_BASE_V2}/status-and-assets",
            json={"error": "error"},
            status=500,
        )
        with pytest.raises(RequestError, match="Failed to get site status and assets"):
            _make_system().get_status_and_assets()


# ---------------------------------------------------------------------------
# Active features (customer-identity v1)
# ---------------------------------------------------------------------------

class TestGetActiveFeatures:
    """Tests for System.get_active_features."""

    _CUSTOMER_ID = "cust-0001"

    def _url(self) -> str:
        return f"{_IDENTITY_BASE}/api/v1/customers/{self._CUSTOMER_ID}/sites/{FAKE_SYSTEM_ID}/active-features"

    @resp_lib.activate
    def test_returns_list_of_feature_codes(self) -> None:
        resp_lib.add(resp_lib.GET, self._url(), json=make_active_features_data(), status=200)
        features = _make_system().get_active_features(self._CUSTOMER_ID)
        assert features == ["DYNAMIC_TARIFF", "TIME_OF_USE_OPTIMIZATION", "SMART_CHARGING"]

    @resp_lib.activate
    def test_returns_empty_list_when_no_features(self) -> None:
        resp_lib.add(resp_lib.GET, self._url(), json={"features": []}, status=200)
        assert _make_system().get_active_features(self._CUSTOMER_ID) == []

    @resp_lib.activate
    def test_handles_missing_features_key(self) -> None:
        resp_lib.add(resp_lib.GET, self._url(), json={}, status=200)
        assert _make_system().get_active_features(self._CUSTOMER_ID) == []

    @resp_lib.activate
    def test_raises_on_server_error(self) -> None:
        resp_lib.add(resp_lib.GET, self._url(), json={"error": "error"}, status=500)
        with pytest.raises(RequestError, match="Failed to get active features"):
            _make_system().get_active_features(self._CUSTOMER_ID)


# ---------------------------------------------------------------------------
# Energy savings (v1)
# ---------------------------------------------------------------------------

class TestGetEnergySavings:
    _URL = f"{_SYSTEM_BASE}/energy-savings"

    @resp_lib.activate
    def test_returns_savings_instance(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json=make_energy_savings_data(), status=200)
        result = _make_system().get_energy_savings()
        assert isinstance(result, HeartbeatSavings)
        assert result.savings_eur == pytest.approx(39.39)

    @resp_lib.activate
    def test_omits_query_params_when_dates_missing(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json=make_energy_savings_data(), status=200)
        _make_system().get_energy_savings()
        url = resp_lib.calls[0].request.url
        assert "from=" not in url
        assert "to=" not in url

    @resp_lib.activate
    def test_passes_date_params(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json=make_energy_savings_data(value=175.42), status=200)
        _make_system().get_energy_savings(
            from_date=datetime.date(2026, 7, 1),
            to_date=datetime.date(2026, 7, 31),
        )
        url = resp_lib.calls[0].request.url
        assert "from=2026-07-01" in url
        assert "to=2026-07-31" in url

    @resp_lib.activate
    def test_missing_field_yields_none(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json={}, status=200)
        assert _make_system().get_energy_savings().savings_eur is None

    @resp_lib.activate
    def test_null_field_yields_none(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json=make_energy_savings_data(value=None), status=200)
        assert _make_system().get_energy_savings().savings_eur is None

    @resp_lib.activate
    def test_raises_on_server_error(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json={}, status=500)
        with pytest.raises(RequestError, match="Failed to get energy savings"):
            _make_system().get_energy_savings()


# ---------------------------------------------------------------------------
# Weather (v1)
# ---------------------------------------------------------------------------

class TestGetWeather:
    _URL = f"{_SYSTEM_BASE}/weather"

    @resp_lib.activate
    def test_returns_weather_data_instance(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json=make_weather_data(), status=200)
        result = _make_system().get_weather()
        assert isinstance(result, WeatherData)
        assert result.today.temperature_celsius == pytest.approx(22.5)
        assert result.today.weather_symbol_id == 2
        assert result.today.weather_description == "Heiter"
        assert len(result.forecasts) == 2
        assert result.forecasts[0].period_start == "2026-06-01T09:00:00Z"
        assert result.forecasts[1].wind_speed == pytest.approx(4.1)

    @resp_lib.activate
    def test_missing_symbol_id_yields_placeholder_description(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json=make_weather_data(), status=200)
        result = _make_system().get_weather()
        assert result.tomorrow.weather_symbol_id is None
        assert result.tomorrow.weather_description == "—"

    @resp_lib.activate
    def test_raises_on_server_error(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json={}, status=500)
        with pytest.raises(RequestError, match="Failed to get weather"):
            _make_system().get_weather()


# ---------------------------------------------------------------------------
# Price customizations (v2)
# ---------------------------------------------------------------------------

class TestGetPriceCustomizations:
    _URL = f"{_BASE}/api/v2/systems/{FAKE_SYSTEM_ID}/price-customizations"

    @resp_lib.activate
    def test_returns_all_prices(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json=make_price_customizations_data(), status=200)
        result = _make_system().get_price_customizations()
        assert isinstance(result, PriceCustomizations)
        assert result.grid_energy_price_eur_per_kwh == pytest.approx(0.3039)
        assert result.comparison_energy_price_eur_per_kwh == pytest.approx(0.274)
        assert result.monthly_base_price_eur == pytest.approx(13.9)

    @resp_lib.activate
    def test_handles_missing_fields(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json={}, status=200)
        result = _make_system().get_price_customizations()
        assert result.grid_energy_price_eur_per_kwh is None
        assert result.monthly_base_price_eur is None

    @resp_lib.activate
    def test_raises_on_server_error(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json={}, status=500)
        with pytest.raises(RequestError, match="Failed to get price customizations"):
            _make_system().get_price_customizations()


# ---------------------------------------------------------------------------
# Comparison price (v2)
# ---------------------------------------------------------------------------

class TestGetComparisonPrice:
    _URL = f"{_BASE}/api/v2/comparison-price"

    @resp_lib.activate
    def test_returns_price_and_siteid_query(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json=make_comparison_price_data(), status=200)
        result = _make_system().get_comparison_price()
        assert isinstance(result, ComparisonPrice)
        assert result.price_eur_per_kwh == pytest.approx(0.274)
        assert f"siteId={FAKE_SYSTEM_ID}" in resp_lib.calls[0].request.url

    @resp_lib.activate
    def test_handles_missing_wrapper(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json={}, status=200)
        assert _make_system().get_comparison_price().price_eur_per_kwh is None

    @resp_lib.activate
    def test_raises_on_server_error(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json={}, status=500)
        with pytest.raises(RequestError, match="Failed to get comparison price"):
            _make_system().get_comparison_price()


# ---------------------------------------------------------------------------
# Price guarantee (customer-identity v1)
# ---------------------------------------------------------------------------

class TestGetPriceGuarantee:
    _CUSTOMER_ID = "cust-0001"
    _URL = f"{_IDENTITY_BASE}/api/v1/customers/{_CUSTOMER_ID}/price-guarantee"

    @resp_lib.activate
    def test_returns_guarantee_and_systemid_query(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json=make_price_guarantee_data(), status=200)
        result = _make_system().get_price_guarantee(self._CUSTOMER_ID)
        assert isinstance(result, PriceGuarantee)
        assert result.value == pytest.approx(12)
        assert result.unit == "ct/kWh"
        assert result.version == "DE_PRICE_GUARANTEE_V2"
        assert f"systemId={FAKE_SYSTEM_ID}" in resp_lib.calls[0].request.url

    @resp_lib.activate
    def test_handles_null_value(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json=make_price_guarantee_data(value=None), status=200)
        result = _make_system().get_price_guarantee(self._CUSTOMER_ID)
        assert result.value is None
        assert result.unit is None

    @resp_lib.activate
    def test_raises_on_server_error(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json={}, status=500)
        with pytest.raises(RequestError, match="Failed to get price guarantee"):
            _make_system().get_price_guarantee(self._CUSTOMER_ID)


# ---------------------------------------------------------------------------
# Wallboxes (v1)
# ---------------------------------------------------------------------------

class TestGetWallboxes:
    _URL = f"{_SYSTEM_BASE}/devices/ev-chargers"

    @resp_lib.activate
    def test_returns_list_of_wallboxes(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json=make_wallboxes_data(), status=200)
        boxes = _make_system().get_wallboxes()
        assert len(boxes) == 1
        assert isinstance(boxes[0], Wallbox)
        assert boxes[0].name == "Wallbox"
        assert boxes[0].gridx_hardware_id == "wb-0001-0000-0000-0000-000000000001"
        assert boxes[0].assigned_ev_id == "ev-1111-1111-1111-111111111111"

    @resp_lib.activate
    def test_returns_empty_list_when_none(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json=[], status=200)
        assert _make_system().get_wallboxes() == []

    @resp_lib.activate
    def test_raises_on_server_error(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json={}, status=500)
        with pytest.raises(RequestError, match="Failed to get wallboxes"):
            _make_system().get_wallboxes()


# ---------------------------------------------------------------------------
# Smart meter (v1)
# ---------------------------------------------------------------------------

class TestGetSmartMeter:
    _URL = f"{_BASE}/api/v1/sites/{FAKE_SYSTEM_ID}/smart-meter"

    @resp_lib.activate
    def test_returns_flattened_fields(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json=make_smart_meter_data(), status=200)
        result = _make_system().get_smart_meter()
        assert isinstance(result, SmartMeter)
        assert result.site_id == FAKE_SYSTEM_ID
        assert result.control_area_eic == "10YDE-RWENET---I"
        assert result.dso_bdew_code == "9900000000009"
        assert result.concession_fee_eur_per_kwh == pytest.approx(0.0159)

    @resp_lib.activate
    def test_handles_missing_arrays(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json={"siteId": FAKE_SYSTEM_ID}, status=200)
        result = _make_system().get_smart_meter()
        assert result.dso_bdew_code is None
        assert result.concession_fee_eur_per_kwh is None

    @resp_lib.activate
    def test_raises_on_server_error(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json={}, status=500)
        with pytest.raises(RequestError, match="Failed to get smart meter"):
            _make_system().get_smart_meter()


# ---------------------------------------------------------------------------
# Monthly trading savings (v1)
# ---------------------------------------------------------------------------

class TestGetMonthlyTradingSavings:
    _URL = f"{_BASE}/api/v1/energy-trader-savings/{FAKE_SYSTEM_ID}/month"

    @resp_lib.activate
    def test_returns_value(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json=make_monthly_trading_savings_data(), status=200)
        result = _make_system().get_monthly_trading_savings()
        assert isinstance(result, MonthlyTradingSavings)
        assert result.average_past_variable_savings_eur == pytest.approx(12.83)

    @resp_lib.activate
    def test_handles_missing_field(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json={}, status=200)
        assert _make_system().get_monthly_trading_savings().average_past_variable_savings_eur is None

    @resp_lib.activate
    def test_raises_on_server_error(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json={}, status=500)
        with pytest.raises(RequestError, match="Failed to get monthly trading savings"):
            _make_system().get_monthly_trading_savings()


# ---------------------------------------------------------------------------
# Self-sufficiency events (v1)
# ---------------------------------------------------------------------------

class TestGetSelfSufficiencyEvents:
    @resp_lib.activate
    def test_returns_events(self) -> None:
        resp_lib.add(resp_lib.GET, _SELF_SUFFICIENCY_URL,
                     json=make_self_sufficiency_events_data(), status=200)
        result = _make_system().get_self_sufficiency_events(
            datetime.datetime(2026, 8, 1, 5),
            datetime.datetime(2026, 8, 1, 6),
        )
        assert isinstance(result, SelfSufficiencyEvents)
        assert len(result.events) == 1
        assert result.events[0].decision == "BATTERY_DISCHARGE"
        assert result.events[0].state_of_charge == 56

    @resp_lib.activate
    def test_query_params(self) -> None:
        resp_lib.add(resp_lib.GET, _SELF_SUFFICIENCY_URL,
                     json=make_self_sufficiency_events_data(), status=200)
        _make_system().get_self_sufficiency_events(
            datetime.datetime(2026, 8, 1, 5, 30),
            datetime.datetime(2026, 8, 1, 6, 45),
        )
        url = resp_lib.calls[0].request.url
        assert f"siteId={FAKE_SYSTEM_ID}" in url
        assert "from=2026-08-01T05%3A30%3A00.000Z" in url
        assert "to=2026-08-01T06%3A45%3A00.999Z" in url

    @resp_lib.activate
    def test_raises_on_server_error(self) -> None:
        resp_lib.add(resp_lib.GET, _SELF_SUFFICIENCY_URL, json={}, status=500)
        with pytest.raises(RequestError, match="Failed to get self-sufficiency events"):
            _make_system().get_self_sufficiency_events(
                datetime.datetime(2026, 8, 1, 5),
                datetime.datetime(2026, 8, 1, 6),
            )


# ---------------------------------------------------------------------------
# Site details (v2)
# ---------------------------------------------------------------------------

class TestGetSiteDetails:
    _URL = f"{_BASE}/api/v2/sites/{FAKE_SYSTEM_ID}/details"

    @resp_lib.activate
    def test_returns_extended_fields(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json=make_site_details_data(), status=200)
        result = _make_system().get_site_details()
        assert isinstance(result, SiteDetails)
        assert result.id == FAKE_SYSTEM_ID
        assert result.name == "My Home Site"
        assert result.bidding_zone == "DE_LU"
        assert result.ems_mode == "TOU"
        assert result.ems_state == "OPERATIONAL"
        assert result.ems_state_reasons == []
        assert result.emp_details["serialNumber"] == "I000-000-000-000-000-X-X"

    @resp_lib.activate
    def test_returns_newly_mapped_fields(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json=make_site_details_data(), status=200)
        result = _make_system().get_site_details()
        assert result.earliest_measurement == "2025-01-24"
        assert result.energy_trader_active is True
        assert result.electricity_contract_active is True
        assert result.impacted_by_enwg is False
        assert result.emp_reference_id == "emp-ref-0001"
        assert result.customer is not None
        assert result.customer.first_name == "John"
        assert result.customer.email == "user@example.com"
        assert result.grid_connection_point_phases == 3
        assert result.max_current_per_phase_ampere == pytest.approx(63.0)

    @resp_lib.activate
    def test_handles_missing_optional_fields(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json={"id": FAKE_SYSTEM_ID}, status=200)
        result = _make_system().get_site_details()
        assert result.bidding_zone is None
        assert result.ems_mode is None
        assert result.ems_state_reasons == []
        assert result.emp_details is None
        assert result.customer is None
        assert result.energy_trader_active is None
        assert result.electricity_contract_active is None
        assert result.impacted_by_enwg is None
        assert result.earliest_measurement is None
        assert result.emp_reference_id is None
        assert result.grid_connection_point_phases is None
        assert result.max_current_per_phase_ampere is None

    @resp_lib.activate
    def test_raises_on_server_error(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json={}, status=500)
        with pytest.raises(RequestError, match="Failed to get site details"):
            _make_system().get_site_details()


# ---------------------------------------------------------------------------
# Customer (v3, customer-identity)
# ---------------------------------------------------------------------------

class TestGetCustomer:
    _CUSTOMER_ID = "cust-0001"
    _URL = f"{_IDENTITY_BASE}/api/v3/customers/{_CUSTOMER_ID}"

    @resp_lib.activate
    def test_returns_full_customer(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json=make_customer_data(), status=200)
        result = _make_system().get_customer(self._CUSTOMER_ID)
        assert isinstance(result, Customer)
        assert result.id == self._CUSTOMER_ID
        assert result.first_name == "John"
        assert result.contact_email == "user@example.com"
        assert result.address_city == "Hamburg"
        assert result.crm_branch_location == "1KOMMA5° Example"

    @resp_lib.activate
    def test_raises_on_server_error(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json={}, status=500)
        with pytest.raises(RequestError, match="Failed to get customer"):
            _make_system().get_customer(self._CUSTOMER_ID)


# ---------------------------------------------------------------------------
# Subscriptions (customer-identity v1)
# ---------------------------------------------------------------------------

class TestGetSubscriptions:
    _CUSTOMER_ID = "cust-0001"
    _URL = f"{_IDENTITY_BASE}/api/v1/customers/{_CUSTOMER_ID}/subscriptions"

    @resp_lib.activate
    def test_returns_all_four_subscription_types(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json=make_subscriptions_data(), status=200)
        result = _make_system().get_subscriptions(self._CUSTOMER_ID)
        assert isinstance(result, SubscriptionsList)
        types = {s.type for s in result.subscriptions}
        assert types == {"DYNAMIC_PULSE", "SMART_METER", "HEARTBEAT", "ENERGY_TRADER"}

    @resp_lib.activate
    def test_universal_fields_parsed(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json=make_subscriptions_data(), status=200)
        subs = {s.type: s for s in _make_system().get_subscriptions(self._CUSTOMER_ID).subscriptions}
        dp = subs["DYNAMIC_PULSE"]
        assert dp.id == "sub-dp-0000-0000-0000-000000000001"
        assert dp.status == "ACTIVE"
        assert dp.price_eur == 0
        assert dp.currency == "EURO"
        assert dp.billing_frequency == "MONTHLY"
        assert dp.notice_period_interval == "MONTHS"
        assert dp.notice_period_number == 1
        assert dp.renewal == "AUTOMATIC"
        assert dp.payment_method == "DIRECT_DEBIT"
        assert dp.country_code == "DE"
        assert dp.terms_and_conditions_url == "https://1k5.link/tos-dynamic-pulse"
        assert dp.site_id == FAKE_SYSTEM_ID
        assert dp.customer_id == "cust-0001"

    @resp_lib.activate
    def test_dynamic_pulse_specific_fields(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json=make_subscriptions_data(), status=200)
        subs = {s.type: s for s in _make_system().get_subscriptions(self._CUSTOMER_ID).subscriptions}
        dp = subs["DYNAMIC_PULSE"]
        assert dp.electricity_contract_number == "600000001"
        assert dp.market_location_id == "50000000001"
        assert dp.price_guarantee_value == 12
        assert dp.price_guarantee_unit == "ct/kWh"
        assert dp.price_guarantee_version == "DE_PRICE_GUARANTEE_V2"

    @resp_lib.activate
    def test_smart_meter_type_recognized_but_hardware_fields_not_mapped(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json=make_subscriptions_data(), status=200)
        subs = {s.type: s for s in _make_system().get_subscriptions(self._CUSTOMER_ID).subscriptions}
        sm = subs["SMART_METER"]
        assert sm.type == "SMART_METER"
        assert sm.notice_period_number == 24
        assert sm.price_eur is None  # SMART_METER has null price
        # SMART_METER-specific hardware fields must NOT be mapped as attributes
        for attr in ("meter_id", "supplier", "device_manufacturer", "device_measuring_type"):
            assert not hasattr(sm, attr), f"{attr!r} must not be a mapped attribute (kept in raw only)"

    @resp_lib.activate
    def test_raw_preserves_pii_fields(self) -> None:
        """Regression protection: PII fields must stay in raw, NOT be mapped as attributes.

        Breaks the moment someone accidentally maps IBAN / metadata.payload
        / statusHistory / CRM IDs onto Subscription.
        """
        resp_lib.add(resp_lib.GET, self._URL, json=make_subscriptions_data(), status=200)
        subs = {s.type: s for s in _make_system().get_subscriptions(self._CUSTOMER_ID).subscriptions}
        dp = subs["DYNAMIC_PULSE"]
        # PII is available via raw
        assert dp.raw["paymentIban"] == "DE00000000000000000000"
        assert dp.raw["metadata"]["payload"]["payment_iban"] == "DE00000000000000000000"
        assert dp.raw["metadata"]["payload"]["former_supplier_id"] == "9900000000000"
        assert dp.raw["lumenazaContractId"] == "600000001"
        assert dp.raw["deliveryAddressStreet"] == "Musterstraße"
        assert len(dp.raw["statusHistory"]) == 1
        # PII is NOT a Subscription attribute
        for pii_attr in (
            "payment_iban", "metadata_payload", "delivery_address_street",
            "lumenaza_contract_id", "zoho_reference_id", "status_history",
        ):
            assert not hasattr(dp, pii_attr), f"{pii_attr!r} must not be a mapped attribute"

    @resp_lib.activate
    def test_pagination_metadata(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json=make_subscriptions_data(), status=200)
        result = _make_system().get_subscriptions(self._CUSTOMER_ID)
        assert result.total_items == 4
        assert result.page_index == 0
        assert result.page_size == 15
        assert result.total_pages == 1

    @resp_lib.activate
    def test_empty_list_when_no_subscriptions(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL,
                     json={"data": [], "pageIndex": 0, "pageSize": 15, "totalPages": 0, "totalItems": 0},
                     status=200)
        result = _make_system().get_subscriptions(self._CUSTOMER_ID)
        assert result.subscriptions == []
        assert result.total_items == 0

    @resp_lib.activate
    def test_url_uses_identity_host(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json=make_subscriptions_data(), status=200)
        _make_system().get_subscriptions(self._CUSTOMER_ID)
        assert "customer-identity" in resp_lib.calls[0].request.url
        assert "heartbeat" not in resp_lib.calls[0].request.url

    @resp_lib.activate
    def test_raises_on_server_error(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json={}, status=500)
        with pytest.raises(RequestError, match="Failed to get subscriptions"):
            _make_system().get_subscriptions(self._CUSTOMER_ID)


# ---------------------------------------------------------------------------
# Notifications (v1)
# ---------------------------------------------------------------------------

class TestGetNotifications:
    _URL = f"{_BASE}/api/v1/users/{FAKE_USER_ID}/notifications/latest"

    @resp_lib.activate
    def test_returns_notifications_and_query(self) -> None:
        resp_lib.add(resp_lib.GET, _USERS_ME_URL, json=make_user_data(), status=200)
        resp_lib.add(resp_lib.GET, self._URL, json=make_notifications_data(), status=200)
        result = _make_system().get_notifications()
        assert isinstance(result, NotificationsList)
        assert len(result.notifications) == 1
        assert result.notifications[0].type == "ENERGY_MARKET_UPPER_TARGET_REACHED"
        assert result.notifications[0].title == "Energiepreise steigen"
        assert result.notifications[0].meta["price"]["value"] == 20.41
        # Second call (notifications/latest) has systemId query
        assert f"systemId={FAKE_SYSTEM_ID}" in resp_lib.calls[1].request.url

    @resp_lib.activate
    def test_empty_list_when_no_notifications(self) -> None:
        resp_lib.add(resp_lib.GET, _USERS_ME_URL, json=make_user_data(), status=200)
        resp_lib.add(resp_lib.GET, self._URL, json={"data": []}, status=200)
        assert _make_system().get_notifications().notifications == []

    @resp_lib.activate
    def test_raises_on_server_error(self) -> None:
        resp_lib.add(resp_lib.GET, _USERS_ME_URL, json=make_user_data(), status=200)
        resp_lib.add(resp_lib.GET, self._URL, json={}, status=500)
        with pytest.raises(RequestError, match="Failed to get notifications"):
            _make_system().get_notifications()


# ---------------------------------------------------------------------------
# Notification settings (v1)
# ---------------------------------------------------------------------------

class TestGetNotificationSettings:
    _URL = f"{_SYSTEM_BASE}/users/{FAKE_USER_ID}/notifications/settings"

    @resp_lib.activate
    def test_returns_settings_with_channel_toggles(self) -> None:
        resp_lib.add(resp_lib.GET, _USERS_ME_URL, json=make_user_data(), status=200)
        resp_lib.add(resp_lib.GET, self._URL, json=make_notification_settings_data(), status=200)
        result = _make_system().get_notification_settings()
        assert isinstance(result, NotificationSettings)
        assert result.lang_code == "de"
        assert result.settings["CO2_IMPACT"] == []
        broadcast = result.settings["BROADCAST_NEW_ELECTRICITY_PRICES"]
        assert len(broadcast) == 1
        assert broadcast[0].app is True
        assert broadcast[0].email is False
        health = result.settings["SYSTEM_HEALTH"]
        assert health[0].email is True

    @resp_lib.activate
    def test_raises_on_server_error(self) -> None:
        resp_lib.add(resp_lib.GET, _USERS_ME_URL, json=make_user_data(), status=200)
        resp_lib.add(resp_lib.GET, self._URL, json={}, status=500)
        with pytest.raises(RequestError, match="Failed to get notification settings"):
            _make_system().get_notification_settings()


# ---------------------------------------------------------------------------
# Impact overview (v2)
# ---------------------------------------------------------------------------

class TestGetImpactOverview:
    _URL = f"{_BASE}/api/v2/systems/{FAKE_SYSTEM_ID}/impact-overview"

    @resp_lib.activate
    def test_returns_instance(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json=make_impact_overview_data(), status=200)
        result = _make_system().get_impact_overview()
        assert isinstance(result, ImpactOverview)
        assert result.co2_savings_kg == pytest.approx(1234.5)
        assert result.co2_collective_savings_kg == pytest.approx(50_000_000.0)
        assert result.co2_global_savings_estimate_tons == pytest.approx(2_000_000.0)

    @resp_lib.activate
    def test_handles_missing_fields(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json={}, status=200)
        result = _make_system().get_impact_overview()
        assert result.co2_savings_kg is None
        assert result.co2_collective_savings_kg is None
        assert result.co2_global_savings_estimate_tons is None

    @resp_lib.activate
    def test_raises_on_server_error(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json={}, status=500)
        with pytest.raises(RequestError, match="Failed to get impact overview"):
            _make_system().get_impact_overview()


# ---------------------------------------------------------------------------
# Energy trader (v2)
# ---------------------------------------------------------------------------

class TestGetEnergyTrader:
    _URL = f"{_BASE}/api/v2/energy-trader"

    @resp_lib.activate
    def test_returns_instance_and_query_param(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json=make_energy_trader_data(), status=200)
        result = _make_system().get_energy_trader()
        assert isinstance(result, EnergyTrader)
        assert result.status == "ACTIVE"
        assert result.green_energy_savings_eur == pytest.approx(1500.75)
        assert result.energy_trader_savings_eur == pytest.approx(125.40)
        assert f"siteId={FAKE_SYSTEM_ID}" in resp_lib.calls[0].request.url

    @resp_lib.activate
    def test_handles_missing_wrapper(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json={}, status=200)
        result = _make_system().get_energy_trader()
        assert result.status is None
        assert result.green_energy_savings_eur is None

    @resp_lib.activate
    def test_raises_on_server_error(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json={}, status=500)
        with pytest.raises(RequestError, match="Failed to get energy trader"):
            _make_system().get_energy_trader()


# ---------------------------------------------------------------------------
# Heartbeat AI summary (v2)
# ---------------------------------------------------------------------------

class TestGetHeartbeatPrices:
    _URL = f"{_BASE}/api/v3/heartbeat-prices"

    @resp_lib.activate
    def test_returns_all_five_windows(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json=make_heartbeat_prices_data(), status=200)
        result = _make_system().get_heartbeat_prices()
        assert isinstance(result, HeartbeatPrices)
        for name in ("day", "week", "month", "half_year", "year"):
            assert isinstance(getattr(result, name), HeartbeatPriceWindow)

    @resp_lib.activate
    def test_correct_price_attribution_year_window(self) -> None:
        """Regression protection for the three distinct price semantics."""
        resp_lib.add(resp_lib.GET, self._URL, json=make_heartbeat_prices_data(), status=200)
        y = _make_system().get_heartbeat_prices().year
        assert y.pv_valuation_price_eur_per_kwh == pytest.approx(0.05)
        assert y.grid_feed_in_tariff_eur_per_kwh == pytest.approx(0.0803)
        assert y.grid_consumption_price_eur_per_kwh == pytest.approx(0.2699)
        assert y.heartbeat_price_eur_per_kwh == pytest.approx(0.1825)
        assert y.comparison_tariff_eur_per_kwh == pytest.approx(0.274)

    @resp_lib.activate
    def test_energy_and_cost_values_extracted(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json=make_heartbeat_prices_data(), status=200)
        y = _make_system().get_heartbeat_prices().year
        assert y.pv_produced_kwh == pytest.approx(7212.1)
        assert y.grid_feed_in_kwh == pytest.approx(1819.3)
        assert y.grid_feed_in_compensation_eur == pytest.approx(146.09)
        assert y.grid_consumed_kwh == pytest.approx(8807.7)
        assert y.grid_consumption_cost_eur == pytest.approx(2377.00)
        assert y.total_consumption_kwh == pytest.approx(14200.6)
        assert y.total_energy_cost_eur == pytest.approx(2591.52)

    @resp_lib.activate
    def test_implausibility_flag_per_window(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json=make_heartbeat_prices_data(), status=200)
        r = _make_system().get_heartbeat_prices()
        assert r.day.should_report_implausible_pv_and_feed_in is False
        assert r.week.should_report_implausible_pv_and_feed_in is False
        assert r.month.should_report_implausible_pv_and_feed_in is False
        assert r.half_year.should_report_implausible_pv_and_feed_in is True
        assert r.year.should_report_implausible_pv_and_feed_in is True

    @resp_lib.activate
    def test_null_regional_fields_pass_through(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json=make_heartbeat_prices_data(), status=200)
        y = _make_system().get_heartbeat_prices().year
        assert y.peak_shaving_savings_raw is None
        assert y.swedish_costs_and_savings_raw is None

    @resp_lib.activate
    def test_url_and_site_id_query_param(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json=make_heartbeat_prices_data(), status=200)
        _make_system().get_heartbeat_prices()
        assert f"siteId={FAKE_SYSTEM_ID}" in resp_lib.calls[0].request.url

    @resp_lib.activate
    def test_raises_on_server_error(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json={}, status=500)
        with pytest.raises(RequestError, match="Failed to get heartbeat prices"):
            _make_system().get_heartbeat_prices()


class TestGetHeartbeatAiSummary:
    _URL = f"{_BASE}/api/v2/heartbeat-ai/summary"

    @resp_lib.activate
    def test_1m_returns_all_metrics(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json=make_heartbeat_ai_summary_data("1M"), status=200)
        result = _make_system().get_heartbeat_ai_summary()
        assert isinstance(result, HeartbeatAiSummary)
        assert result.resolution == "1M"
        assert result.self_sufficiency_percent == pytest.approx(0.73)
        assert result.self_sufficiency_by_solar_kwh == pytest.approx(331.25)
        assert result.earned_amount_eur == pytest.approx(30.41)
        assert result.feed_in_price_eur_per_kwh == pytest.approx(0.0803)
        assert result.co2_saved_kg == pytest.approx(210.5)
        assert result.heartbeat_price_eur_per_kwh == pytest.approx(0.0745)
        assert result.peak_price_avoided_eur == pytest.approx(22.50)
        assert result.peak_battery_charging_cost_eur == pytest.approx(37.68)
        assert result.peak_grid_charging_cost_eur == pytest.approx(60.18)

    @resp_lib.activate
    def test_peak_price_avoided_absent_yields_none(self) -> None:
        body = make_heartbeat_ai_summary_data("1M")
        body["peakPriceAvoided"] = None
        resp_lib.add(resp_lib.GET, self._URL, json=body, status=200)
        result = _make_system().get_heartbeat_ai_summary()
        assert result.peak_price_avoided_eur is None
        assert result.peak_battery_charging_cost_eur is None
        assert result.peak_grid_charging_cost_eur is None

    @resp_lib.activate
    def test_1w_leaves_self_sufficiency_none(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json=make_heartbeat_ai_summary_data("1W"), status=200)
        result = _make_system().get_heartbeat_ai_summary(resolution="1W")
        assert result.resolution == "1W"
        assert result.self_sufficiency_percent is None
        assert result.earned_amount_eur is None
        assert result.co2_saved_kg == pytest.approx(210.5)  # co2 still populated

    @resp_lib.activate
    def test_passes_query_params(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json=make_heartbeat_ai_summary_data("1Y"), status=200)
        _make_system().get_heartbeat_ai_summary(resolution="1Y")
        url = resp_lib.calls[0].request.url
        assert f"siteId={FAKE_SYSTEM_ID}" in url
        assert "resolution=1Y" in url

    @resp_lib.activate
    def test_defaults_to_1m(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json=make_heartbeat_ai_summary_data("1M"), status=200)
        _make_system().get_heartbeat_ai_summary()
        assert "resolution=1M" in resp_lib.calls[0].request.url

    @resp_lib.activate
    def test_raises_on_server_error(self) -> None:
        resp_lib.add(resp_lib.GET, self._URL, json={}, status=500)
        with pytest.raises(RequestError, match="Failed to get Heartbeat AI summary"):
            _make_system().get_heartbeat_ai_summary()


# ---------------------------------------------------------------------------
# Optimizations (v1)
# ---------------------------------------------------------------------------

class TestGetOptimizations:
    @resp_lib.activate
    def test_returns_optimization_events(self) -> None:
        resp_lib.add(resp_lib.GET, _OPTIMIZATIONS_URL, json=make_optimizations_data(), status=200)
        result = _make_system().get_optimizations(
            datetime.datetime(2026, 6, 1, 10),
            datetime.datetime(2026, 6, 1, 12),
        )
        assert isinstance(result, OptimizationEvents)
        assert len(result.events) == 2
        first = result.events[0]
        assert first.decision == "BATTERY_CHARGE_FROM_GRID"
        assert first.asset == "BATTERY"
        assert first.market_price == pytest.approx(0.075)
        assert first.market_price_currency == "EUR"
        assert first.state_of_charge == 42
        assert first.log == ["2026-06-01T10:00:00Z", "2026-06-01T10:15:00Z"]

    @resp_lib.activate
    def test_null_market_price_stays_none(self) -> None:
        resp_lib.add(resp_lib.GET, _OPTIMIZATIONS_URL, json=make_optimizations_data(), status=200)
        result = _make_system().get_optimizations(
            datetime.datetime(2026, 6, 1, 10),
            datetime.datetime(2026, 6, 1, 12),
        )
        second = result.events[1]
        assert second.market_price is None
        assert second.total_cost is None
        assert second.state_of_charge is None
        assert second.log == []

    @resp_lib.activate
    def test_url_and_query_params(self) -> None:
        resp_lib.add(resp_lib.GET, _OPTIMIZATIONS_URL, json=make_optimizations_data(), status=200)
        _make_system().get_optimizations(
            datetime.datetime(2026, 6, 1, 10, 15, 30),
            datetime.datetime(2026, 6, 1, 12, 45, 15),
        )
        url = resp_lib.calls[0].request.url
        assert f"siteId={FAKE_SYSTEM_ID}" in url
        assert "from=2026-06-01T10%3A15%3A30.000Z" in url
        assert "to=2026-06-01T12%3A45%3A15.999Z" in url

    @resp_lib.activate
    def test_raises_on_server_error(self) -> None:
        resp_lib.add(resp_lib.GET, _OPTIMIZATIONS_URL, json={"error": "boom"}, status=500)
        with pytest.raises(RequestError, match="Failed to get optimizations"):
            _make_system().get_optimizations(
                datetime.datetime(2026, 6, 1, 10),
                datetime.datetime(2026, 6, 1, 12),
            )
