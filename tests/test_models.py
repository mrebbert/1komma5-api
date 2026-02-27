"""Tests for :mod:`onekommafive.models` – data model construction and behaviour."""

from __future__ import annotations

import pytest

from onekommafive.models import (
    ChargingMode,
    EmsSettings,
    LiveOverview,
    MarketPrices,
    User,
)
from tests.fixtures import make_price_data


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
        assert mp.average_price == pytest.approx(8.5)
        assert mp.highest_price == pytest.approx(13.0)
        assert mp.lowest_price == pytest.approx(1.5)
        assert mp.grid_costs_total == pytest.approx(16.37)
        assert mp.vat == pytest.approx(0.19)
        assert mp.uses_fallback_grid_costs is False

    def test_from_dict_builds_prices_dict(self) -> None:
        mp = MarketPrices.from_dict(make_price_data())
        assert mp.prices["2024-06-01T00:00Z"] == pytest.approx(8.0)
        assert mp.prices["2024-06-01T01:00Z"] == pytest.approx(9.0)

    def test_from_dict_builds_prices_with_grid_costs_dict(self) -> None:
        mp = MarketPrices.from_dict(make_price_data())
        assert mp.prices_with_grid_costs["2024-06-01T00:00Z"] == pytest.approx(24.4)

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
