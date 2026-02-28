"""Tests for :mod:`onekommafive.models` – data model construction and behaviour."""

from __future__ import annotations

import pytest

from onekommafive.models import (
    ChargingMode,
    EmsManualDevice,
    EmsSettings,
    LiveOverview,
    MarketPrices,
    SystemInfo,
    User,
)
from tests.fixtures import make_price_data, make_system_data


class TestChargingMode:
    def test_all_values_are_defined(self) -> None:
        assert ChargingMode("SMART_CHARGE") == ChargingMode.SMART_CHARGE
        assert ChargingMode("QUICK_CHARGE") == ChargingMode.QUICK_CHARGE
        assert ChargingMode("SOLAR_CHARGE") == ChargingMode.SOLAR_CHARGE

    def test_invalid_value_raises(self) -> None:
        with pytest.raises(ValueError):
            ChargingMode("UNKNOWN_MODE")


class TestUser:
    def test_from_dict_populates_fields(self) -> None:
        data = {"id": "u1", "email": "a@b.com", "extra": "value"}
        user = User.from_dict(data)
        assert user.id == "u1"
        assert user.email == "a@b.com"
        assert user.raw == data

    def test_from_dict_preserves_raw(self) -> None:
        data = {"id": "u1", "email": "x@y.com", "roles": ["admin"]}
        user = User.from_dict(data)
        assert user.raw["roles"] == ["admin"]


class TestMarketPrices:
    def test_from_dict_populates_summary_fields(self) -> None:
        mp = MarketPrices.from_dict(make_price_data())
        assert mp.average_price == pytest.approx(0.085)
        assert mp.highest_price == pytest.approx(0.13)
        assert mp.lowest_price == pytest.approx(0.015)
        assert mp.grid_costs_total == pytest.approx(0.1637)
        assert mp.vat == pytest.approx(0.19)
        assert mp.uses_fallback_grid_costs is False

    def test_from_dict_builds_prices_dict(self) -> None:
        mp = MarketPrices.from_dict(make_price_data())
        assert mp.prices["2024-06-01T00:00Z"] == pytest.approx(0.08)
        assert mp.prices["2024-06-01T01:00Z"] == pytest.approx(0.09)

    def test_from_dict_builds_prices_with_grid_costs_dict(self) -> None:
        mp = MarketPrices.from_dict(make_price_data())
        assert mp.prices_with_grid_costs["2024-06-01T00:00Z"] == pytest.approx(0.244)

    def test_from_dict_populates_grid_cost_summaries(self) -> None:
        mp = MarketPrices.from_dict(make_price_data())
        assert mp.average_price_with_grid_costs == pytest.approx(0.249)
        assert mp.highest_price_with_grid_costs == pytest.approx(0.294)
        assert mp.lowest_price_with_grid_costs == pytest.approx(0.178)

    def test_from_dict_populates_all_in_summaries(self) -> None:
        mp = MarketPrices.from_dict(make_price_data())
        assert mp.average_price_all_in == pytest.approx(0.29631)
        assert mp.highest_price_all_in == pytest.approx(0.34986)
        assert mp.lowest_price_all_in == pytest.approx(0.21182)

    def test_from_dict_builds_prices_with_vat_dict(self) -> None:
        mp = MarketPrices.from_dict(make_price_data())
        assert mp.prices_with_vat["2024-06-01T00:00Z"] == pytest.approx(0.0952)
        assert mp.prices_with_vat["2024-06-01T01:00Z"] == pytest.approx(0.1071)

    def test_from_dict_builds_all_in_prices_dict(self) -> None:
        mp = MarketPrices.from_dict(make_price_data())
        assert mp.prices_with_grid_costs_and_vat["2024-06-01T00:00Z"] == pytest.approx(0.29036)

    def test_from_dict_builds_grid_consumption_and_feed_in(self) -> None:
        mp = MarketPrices.from_dict(make_price_data())
        assert mp.grid_consumption["2024-06-01T00:00Z"] == pytest.approx(0.5)
        assert mp.grid_feed_in["2024-06-01T00:00Z"] == pytest.approx(0.1)
        assert mp.grid_consumption["2024-06-01T01:00Z"] == pytest.approx(0.8)
        assert mp.grid_feed_in["2024-06-01T01:00Z"] == pytest.approx(0.0)

    def test_from_dict_populates_grid_cost_components(self) -> None:
        mp = MarketPrices.from_dict(make_price_data())
        assert mp.grid_cost_energy_tax == pytest.approx(0.12776)
        assert mp.grid_cost_purchasing == pytest.approx(0.0)
        assert mp.grid_cost_fixed_tariff == pytest.approx(0.0)
        assert mp.grid_cost_dynamic_markup == pytest.approx(0.0)
        assert mp.grid_cost_feed_in_remuneration_adj == pytest.approx(0.0)

    def test_from_dict_handles_missing_grid_cost_components(self) -> None:
        data = make_price_data()
        del data["gridCostsComponents"]
        mp = MarketPrices.from_dict(data)
        assert mp.grid_cost_energy_tax is None
        assert mp.grid_cost_purchasing is None

    def test_raw_is_preserved(self) -> None:
        data = make_price_data()
        mp = MarketPrices.from_dict(data)
        assert mp.raw is data


class TestLiveOverview:
    def test_from_dict_maps_all_fields(self) -> None:
        # PV 3000 W, consumption 2000 W, grid export 500 W → battery = +500 W (charging)
        data = {
            "liveHeroView": {
                "production": {"value": 3000.0, "unit": "W"},
                "consumption": {"value": 2000.0, "unit": "W"},
                "gridConsumption": {"value": 0.0, "unit": "W"},
                "gridFeedIn": {"value": 500.0, "unit": "W"},
                "totalStateOfCharge": 0.8,
            }
        }
        overview = LiveOverview.from_dict(data)
        assert overview.pv_power == 3000.0
        assert overview.battery_power == 500.0
        assert overview.battery_soc == pytest.approx(80.0)
        assert overview.grid_power == pytest.approx(-500.0)
        assert overview.consumption_power == 2000.0
        assert overview.raw is data

    def test_from_dict_allows_missing_optional_fields(self) -> None:
        overview = LiveOverview.from_dict(
            {"liveHeroView": {"production": {"value": 1500.0, "unit": "W"}}}
        )
        assert overview.pv_power == 1500.0
        assert overview.battery_power is None
        assert overview.battery_soc is None
        assert overview.grid_power is None
        assert overview.consumption_power is None
        assert overview.timestamp is None
        assert overview.status is None
        assert overview.self_sufficiency is None
        assert overview.ev_chargers_power is None
        assert overview.heat_pumps_power is None
        assert overview.acs_power is None
        assert overview.household_power is None

    def test_from_dict_reads_timestamp_and_status(self) -> None:
        overview = LiveOverview.from_dict({
            "timestamp": "2026-02-28T11:17:03Z",
            "status": "ONLINE",
            "liveHeroView": {},
        })
        assert overview.timestamp == "2026-02-28T11:17:03Z"
        assert overview.status == "ONLINE"

    def test_from_dict_reads_smart_device_powers(self) -> None:
        data = {
            "liveHeroView": {
                "selfSufficiency": 0.75,
                "evChargersAggregated": {"power": {"value": 11000.0, "unit": "W"}},
                "heatPumpsAggregated": {"power": {"value": 2000.0, "unit": "W"}, "powerExternal": None},
                "acsAggregated": {"power": {"value": 1500.0, "unit": "W"}},
            },
            "summaryCards": {
                "household": {"power": {"value": 800.0, "unit": "W"}},
            },
        }
        overview = LiveOverview.from_dict(data)
        assert overview.self_sufficiency == pytest.approx(0.75)
        assert overview.ev_chargers_power == pytest.approx(11000.0)
        assert overview.heat_pumps_power == pytest.approx(2000.0)
        assert overview.acs_power == pytest.approx(1500.0)
        assert overview.household_power == pytest.approx(800.0)

    def test_battery_power_prefers_summary_cards(self) -> None:
        """summaryCards direct measurement takes precedence over derived power balance."""
        data = {
            "liveHeroView": {
                "production": {"value": 1000.0, "unit": "W"},
                "consumption": {"value": 1000.0, "unit": "W"},
                "gridConsumption": {"value": 0.0, "unit": "W"},
                "gridFeedIn": {"value": 0.0, "unit": "W"},
            },
            "summaryCards": {
                "battery": {"power": {"value": -500.0, "unit": "W"}},  # negative = charging
            },
        }
        overview = LiveOverview.from_dict(data)
        # API sign flipped: -(-500) = +500 (positive = charging in our convention)
        assert overview.battery_power == pytest.approx(500.0)

    def test_grid_power_prefers_summary_cards(self) -> None:
        data = {
            "liveHeroView": {
                "gridConsumption": {"value": 0.0, "unit": "W"},
                "gridFeedIn": {"value": 0.0, "unit": "W"},
            },
            "summaryCards": {
                "grid": {"power": {"value": 3000.0, "unit": "W"}},
            },
        }
        overview = LiveOverview.from_dict(data)
        assert overview.grid_power == pytest.approx(3000.0)


class TestSystemInfo:
    def test_from_dict_populates_core_fields(self) -> None:
        si = SystemInfo.from_dict(make_system_data())
        assert si.id == "aaaaaaaa-0000-0000-0000-000000000001"
        assert si.name == "My Home System"
        assert si.status == "ACTIVE"

    def test_from_dict_populates_address(self) -> None:
        si = SystemInfo.from_dict(make_system_data())
        assert si.address_line1 == "Musterstraße 1"
        assert si.address_zip_code == "20095"
        assert si.address_city == "Hamburg"
        assert si.address_country == "DE"
        assert si.address_latitude == pytest.approx(53.5)
        assert si.address_longitude == pytest.approx(10.0)

    def test_from_dict_populates_flags(self) -> None:
        si = SystemInfo.from_dict(make_system_data())
        assert si.dynamic_pulse_compatible is True
        assert si.energy_trader_active is True
        assert si.electricity_contract_active is True

    def test_from_dict_populates_timestamps(self) -> None:
        si = SystemInfo.from_dict(make_system_data())
        assert si.created_at == "2025-01-23T08:09:40.042Z"
        assert si.updated_at == "2025-10-08T15:28:18.743Z"

    def test_optional_fields_default_to_none(self) -> None:
        si = SystemInfo.from_dict({"id": "x"})
        assert si.name is None
        assert si.address_line1 is None
        assert si.address_latitude is None
        assert si.dynamic_pulse_compatible is False

    def test_raw_is_preserved(self) -> None:
        data = make_system_data()
        assert SystemInfo.from_dict(data).raw is data


class TestEmsSettings:
    def test_auto_mode_true_when_not_overriding(self) -> None:
        settings = EmsSettings.from_dict({"overrideAutoSettings": False, "manualSettings": {}})
        assert settings.auto_mode is True

    def test_auto_mode_false_when_overriding(self) -> None:
        settings = EmsSettings.from_dict({"overrideAutoSettings": True, "manualSettings": {}})
        assert settings.auto_mode is False

    def test_auto_mode_defaults_to_true_when_key_absent(self) -> None:
        """If the key is missing the EMS should be considered to be in auto mode."""
        settings = EmsSettings.from_dict({})
        assert settings.auto_mode is True

    def test_from_dict_populates_top_level_fields(self) -> None:
        from tests.fixtures import make_ems_settings_data, FAKE_SYSTEM_ID
        settings = EmsSettings.from_dict(make_ems_settings_data())
        assert settings.system_id == FAKE_SYSTEM_ID
        assert settings.created_at == "2025-01-23T08:09:40.508Z"
        assert settings.updated_at == "2026-02-21T18:28:27.452Z"
        assert settings.consent_given is True
        assert settings.time_of_use_enabled is True

    def test_from_dict_parses_ev_charger_device(self) -> None:
        from tests.fixtures import make_ems_settings_data, FAKE_EV_ID
        settings = EmsSettings.from_dict(make_ems_settings_data())
        ev = next(d for d in settings.manual_devices if d.type == "EV_CHARGER")
        assert isinstance(ev, EmsManualDevice)
        assert ev.charger_name == "Wallbox"
        assert ev.assigned_ev_id == FAKE_EV_ID
        assert ev.assigned_ev_name == "Id4"
        assert ev.active_charging_mode == "QUICK_CHARGE"

    def test_from_dict_parses_battery_device(self) -> None:
        from tests.fixtures import make_ems_settings_data
        settings = EmsSettings.from_dict(make_ems_settings_data())
        bat = next(d for d in settings.manual_devices if d.type == "BATTERY")
        assert bat.enable_forecast_charging is False

    def test_from_dict_parses_heat_pump_device(self) -> None:
        from tests.fixtures import make_ems_settings_data
        settings = EmsSettings.from_dict(make_ems_settings_data())
        hp = next(d for d in settings.manual_devices if d.type == "HEAT_PUMP")
        assert hp.use_solar_surplus is True
        assert hp.max_solar_surplus_usage_kw == pytest.approx(2.0)

    def test_from_dict_devices_ordered_by_index(self) -> None:
        from tests.fixtures import make_ems_settings_data
        settings = EmsSettings.from_dict(make_ems_settings_data())
        types = [d.type for d in settings.manual_devices]
        assert types == ["EV_CHARGER", "BATTERY", "HEAT_PUMP"]

    def test_from_dict_empty_manual_settings(self) -> None:
        settings = EmsSettings.from_dict({"manualSettings": {}})
        assert settings.manual_devices == []
