"""Tests for :mod:`onekommafive.cli` – command-line interface."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from onekommafive.cli import main
from onekommafive.models import (
    ChargingMode,
    ComparisonPrice,
    EmsSettings,
    EnergyTrader,
    HeartbeatAiSummary,
    HeartbeatSavings,
    ImpactOverview,
    LiveOverview,
    MarketPrices,
    MonthlyTradingSavings,
    PriceCustomizations,
    PriceGuarantee,
    SmartMeter,
    SystemInfo,
    Wallbox,
)
from tests.fixtures import (
    FAKE_EV_ID,
    FAKE_SYSTEM_ID,
    make_comparison_price_data,
    make_ems_settings_data,
    make_energy_savings_data,
    make_energy_trader_data,
    make_heartbeat_ai_summary_data,
    make_impact_overview_data,
    make_live_overview_data,
    make_monthly_trading_savings_data,
    make_price_customizations_data,
    make_price_data,
    make_price_guarantee_data,
    make_smart_meter_data,
    make_system_data,
    make_wallboxes_data,
)


def _run(*argv: str) -> None:
    """Invoke main() with the given argv list."""
    with patch("sys.argv", ["cli.py", *argv]):
        main()


@pytest.fixture
def mock_system():
    """Patch _client and _system so no real HTTP is needed."""
    system = MagicMock()
    system.id.return_value = FAKE_SYSTEM_ID
    with patch("onekommafive.cli._client"), \
         patch("onekommafive.cli._system", return_value=system):
        yield system


# ---------------------------------------------------------------------------
# info
# ---------------------------------------------------------------------------

class TestCmdInfo:
    def test_prints_system_id(self, mock_system, capsys) -> None:
        mock_system.info.return_value = SystemInfo.from_dict(make_system_data())
        _run("info")
        assert FAKE_SYSTEM_ID in capsys.readouterr().out

    def test_prints_name(self, mock_system, capsys) -> None:
        mock_system.info.return_value = SystemInfo.from_dict(make_system_data())
        _run("info")
        assert "My Home System" in capsys.readouterr().out

    def test_prints_status(self, mock_system, capsys) -> None:
        mock_system.info.return_value = SystemInfo.from_dict(make_system_data())
        _run("info")
        assert "ACTIVE" in capsys.readouterr().out

    def test_prints_address(self, mock_system, capsys) -> None:
        mock_system.info.return_value = SystemInfo.from_dict(make_system_data())
        _run("info")
        out = capsys.readouterr().out
        assert "Musterstraße 1" in out
        assert "Hamburg" in out

    def test_prints_coordinates(self, mock_system, capsys) -> None:
        mock_system.info.return_value = SystemInfo.from_dict(make_system_data())
        _run("info")
        out = capsys.readouterr().out
        assert "53.5000" in out
        assert "10.0000" in out

    def test_prints_feature_flags(self, mock_system, capsys) -> None:
        mock_system.info.return_value = SystemInfo.from_dict(make_system_data())
        _run("info")
        out = capsys.readouterr().out
        assert "Dynamic Pulse" in out
        assert "Energy trading" in out
        assert "Electricity contract" in out

    def test_prints_dash_for_missing_name(self, mock_system, capsys) -> None:
        data = make_system_data()
        data["systemName"] = None
        mock_system.info.return_value = SystemInfo.from_dict(data)
        _run("info")
        assert "—" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# live
# ---------------------------------------------------------------------------

class TestCmdLive:
    def test_prints_system_id(self, mock_system, capsys) -> None:
        mock_system.get_live_overview.return_value = LiveOverview.from_dict(
            make_live_overview_data()
        )
        _run("live")
        assert FAKE_SYSTEM_ID in capsys.readouterr().out

    def test_prints_pv_power(self, mock_system, capsys) -> None:
        mock_system.get_live_overview.return_value = LiveOverview.from_dict(
            make_live_overview_data()
        )
        _run("live")
        assert "2500" in capsys.readouterr().out  # fixture PV = 2500 W

    def test_prints_battery_soc(self, mock_system, capsys) -> None:
        mock_system.get_live_overview.return_value = LiveOverview.from_dict(
            make_live_overview_data()
        )
        _run("live")
        assert "72.5%" in capsys.readouterr().out  # fixture SoC = 0.725

    def test_prints_status(self, mock_system, capsys) -> None:
        mock_system.get_live_overview.return_value = LiveOverview.from_dict(
            make_live_overview_data()
        )
        _run("live")
        assert "ONLINE" in capsys.readouterr().out

    def test_prints_household_power(self, mock_system, capsys) -> None:
        mock_system.get_live_overview.return_value = LiveOverview.from_dict(
            make_live_overview_data()
        )
        _run("live")
        assert "1900" in capsys.readouterr().out  # fixture household = 1900 W

    def test_prints_smart_device_powers(self, mock_system, capsys) -> None:
        mock_system.get_live_overview.return_value = LiveOverview.from_dict(
            make_live_overview_data()
        )
        _run("live")
        out = capsys.readouterr().out
        assert "100" in out   # EV chargers = 100 W
        assert "800" in out   # heat pumps = 800 W
        assert "200" in out   # ACs = 200 W

    def test_prints_self_sufficiency(self, mock_system, capsys) -> None:
        mock_system.get_live_overview.return_value = LiveOverview.from_dict(
            make_live_overview_data()
        )
        _run("live")
        assert "0.0%" in capsys.readouterr().out  # fixture selfSufficiency = 0.0

    def test_prints_grid_import_and_export(self, mock_system, capsys) -> None:
        mock_system.get_live_overview.return_value = LiveOverview.from_dict(
            make_live_overview_data()
        )
        _run("live")
        out = capsys.readouterr().out
        assert "import" in out
        assert "export" in out


# ---------------------------------------------------------------------------
# prices
# ---------------------------------------------------------------------------

class TestCmdPrices:
    def test_prints_eur_unit(self, mock_system, capsys) -> None:
        mock_system.get_prices.return_value = MarketPrices.from_dict(make_price_data())
        _run("prices")
        assert "EUR/kWh" in capsys.readouterr().out

    def test_default_resolution_is_1h(self, mock_system, capsys) -> None:
        mock_system.get_prices.return_value = MarketPrices.from_dict(make_price_data())
        _run("prices")
        assert mock_system.get_prices.call_args.kwargs["resolution"] == "1h"

    def test_custom_resolution_15m(self, mock_system, capsys) -> None:
        mock_system.get_prices.return_value = MarketPrices.from_dict(make_price_data())
        _run("prices", "--resolution", "15m")
        assert mock_system.get_prices.call_args.kwargs["resolution"] == "15m"

    def test_prints_average_price(self, mock_system, capsys) -> None:
        mock_system.get_prices.return_value = MarketPrices.from_dict(make_price_data())
        _run("prices")
        assert "0.0850" in capsys.readouterr().out

    def test_prints_timeseries_rows(self, mock_system, capsys) -> None:
        mock_system.get_prices.return_value = MarketPrices.from_dict(make_price_data())
        _run("prices")
        out = capsys.readouterr().out
        assert "2024-06-01T00:00Z" in out
        assert "2024-06-01T01:00Z" in out

    def test_invalid_resolution_rejected(self, mock_system) -> None:
        with pytest.raises(SystemExit):
            _run("prices", "--resolution", "2h")


# ---------------------------------------------------------------------------
# ev
# ---------------------------------------------------------------------------

class TestCmdEv:
    def test_prints_no_chargers_when_empty(self, mock_system, capsys) -> None:
        mock_system.get_ev_chargers.return_value = []
        _run("ev")
        assert "No EV chargers" in capsys.readouterr().out

    def _ev_mock(self, ev_id: str = FAKE_EV_ID) -> MagicMock:
        """Return a fully-stubbed EV charger mock."""
        ev = MagicMock()
        ev.id.return_value = ev_id
        ev.name.return_value = "My Car"
        ev.manufacturer.return_value = "Volkswagen"
        ev.model.return_value = "Id.4"
        ev.capacity_wh.return_value = 77000.0
        ev.assigned_charger_id.return_value = "charger-001"
        ev.charging_mode.return_value = ChargingMode.SMART_CHARGE
        ev.current_soc.return_value = 80.0
        ev.target_soc.return_value = 80.0
        ev.default_soc.return_value = 35.0
        ev.primary_schedule_days.return_value = []
        ev.updated_at.return_value = "2026-02-28T07:35:39.367Z"
        return ev

    def test_prints_charger_id_name_mode_soc(self, mock_system, capsys) -> None:
        mock_system.get_ev_chargers.return_value = [self._ev_mock()]
        _run("ev")
        out = capsys.readouterr().out
        assert FAKE_EV_ID in out
        assert "My Car" in out
        assert "SMART_CHARGE" in out
        assert "80%" in out

    def test_shows_dash_when_no_soc(self, mock_system, capsys) -> None:
        ev = self._ev_mock()
        ev.name.return_value = None
        ev.charging_mode.return_value = ChargingMode.SOLAR_CHARGE
        ev.current_soc.return_value = None
        mock_system.get_ev_chargers.return_value = [ev]
        _run("ev")
        assert "—" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# ev-modes
# ---------------------------------------------------------------------------

class TestCmdEvModes:
    def test_prints_enabled_modes(self, mock_system, capsys) -> None:
        mock_system.get_displayed_ev_charging_modes.return_value = [
            ChargingMode.SMART_CHARGE,
            ChargingMode.SOLAR_CHARGE,
        ]
        _run("ev-modes")
        out = capsys.readouterr().out
        assert "SMART_CHARGE" in out
        assert "SOLAR_CHARGE" in out

    def test_prints_no_modes_when_empty(self, mock_system, capsys) -> None:
        mock_system.get_displayed_ev_charging_modes.return_value = []
        _run("ev-modes")
        assert "No EV charging modes" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# set-ev-mode
# ---------------------------------------------------------------------------

class TestCmdSetEvMode:
    def _ev(self, ev_id: str = FAKE_EV_ID) -> MagicMock:
        ev = MagicMock()
        ev.id.return_value = ev_id
        return ev

    def test_sets_mode_on_first_charger_by_default(self, mock_system, capsys) -> None:
        ev = self._ev()
        mock_system.get_ev_chargers.return_value = [ev]
        _run("set-ev-mode", "SOLAR_CHARGE")
        ev.set_charging_mode.assert_called_once_with(ChargingMode.SOLAR_CHARGE)
        assert "SOLAR_CHARGE" in capsys.readouterr().out

    def test_selects_charger_by_id(self, mock_system, capsys) -> None:
        ev1 = self._ev("ev-aaa")
        ev2 = self._ev("ev-bbb")
        mock_system.get_ev_chargers.return_value = [ev1, ev2]
        _run("set-ev-mode", "QUICK_CHARGE", "--ev", "ev-bbb")
        ev1.set_charging_mode.assert_not_called()
        ev2.set_charging_mode.assert_called_once_with(ChargingMode.QUICK_CHARGE)

    def test_exits_when_charger_id_not_found(self, mock_system) -> None:
        mock_system.get_ev_chargers.return_value = [self._ev("ev-aaa")]
        with pytest.raises(SystemExit):
            _run("set-ev-mode", "SMART_CHARGE", "--ev", "ev-xxx")

    def test_exits_when_no_chargers(self, mock_system) -> None:
        mock_system.get_ev_chargers.return_value = []
        with pytest.raises(SystemExit):
            _run("set-ev-mode", "SMART_CHARGE")

    def test_invalid_mode_rejected_by_argparse(self, mock_system) -> None:
        with pytest.raises(SystemExit):
            _run("set-ev-mode", "TURBO_CHARGE")


# ---------------------------------------------------------------------------
# set-ev-target-soc
# ---------------------------------------------------------------------------

class TestCmdSetEvTargetSoc:
    def _ev(self, ev_id: str = FAKE_EV_ID) -> MagicMock:
        ev = MagicMock()
        ev.id.return_value = ev_id
        return ev

    def test_sets_target_soc_on_first_charger(self, mock_system, capsys) -> None:
        ev = self._ev()
        mock_system.get_ev_chargers.return_value = [ev]
        _run("set-ev-target-soc", "90")
        ev.set_target_soc.assert_called_once_with(90.0)
        assert "90%" in capsys.readouterr().out

    def test_selects_charger_by_id(self, mock_system) -> None:
        ev1 = self._ev("ev-aaa")
        ev2 = self._ev("ev-bbb")
        mock_system.get_ev_chargers.return_value = [ev1, ev2]
        _run("set-ev-target-soc", "80", "--ev", "ev-bbb")
        ev1.set_target_soc.assert_not_called()
        ev2.set_target_soc.assert_called_once_with(80.0)

    def test_exits_on_invalid_soc_value(self, mock_system) -> None:
        mock_system.get_ev_chargers.return_value = [self._ev()]
        with pytest.raises(SystemExit):
            _run("set-ev-target-soc", "not-a-number")

    def test_exits_on_out_of_range_soc(self, mock_system) -> None:
        mock_system.get_ev_chargers.return_value = [self._ev()]
        with pytest.raises(SystemExit):
            _run("set-ev-target-soc", "110")

    def test_exits_when_no_chargers(self, mock_system) -> None:
        mock_system.get_ev_chargers.return_value = []
        with pytest.raises(SystemExit):
            _run("set-ev-target-soc", "80")


# ---------------------------------------------------------------------------
# set-ev-departure
# ---------------------------------------------------------------------------

class TestCmdSetEvDeparture:
    def _ev(self, ev_id: str = FAKE_EV_ID) -> MagicMock:
        ev = MagicMock()
        ev.id.return_value = ev_id
        return ev

    def test_sets_departure_on_first_charger(self, mock_system, capsys) -> None:
        ev = self._ev()
        mock_system.get_ev_chargers.return_value = [ev]
        _run("set-ev-departure", "07:30")
        ev.set_primary_departure_time.assert_called_once_with("07:30")
        assert "07:30" in capsys.readouterr().out

    def test_selects_charger_by_id(self, mock_system) -> None:
        ev1 = self._ev("ev-aaa")
        ev2 = self._ev("ev-bbb")
        mock_system.get_ev_chargers.return_value = [ev1, ev2]
        _run("set-ev-departure", "06:00", "--ev", "ev-bbb")
        ev1.set_primary_departure_time.assert_not_called()
        ev2.set_primary_departure_time.assert_called_once_with("06:00")

    def test_exits_when_no_chargers(self, mock_system) -> None:
        mock_system.get_ev_chargers.return_value = []
        with pytest.raises(SystemExit):
            _run("set-ev-departure", "07:30")


# ---------------------------------------------------------------------------
# ems
# ---------------------------------------------------------------------------

class TestCmdEms:
    def test_prints_auto_mode(self, mock_system, capsys) -> None:
        mock_system.get_ems_settings.return_value = EmsSettings.from_dict(
            make_ems_settings_data(override=False)
        )
        _run("ems")
        assert "AUTO" in capsys.readouterr().out

    def test_prints_manual_override(self, mock_system, capsys) -> None:
        mock_system.get_ems_settings.return_value = EmsSettings.from_dict(
            make_ems_settings_data(override=True)
        )
        _run("ems")
        assert "MANUAL OVERRIDE" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# set-ems
# ---------------------------------------------------------------------------

class TestCmdSetEms:
    def test_enables_auto(self, mock_system, capsys) -> None:
        _run("set-ems", "auto")
        mock_system.set_ems_mode.assert_called_once_with(auto=True)
        assert "AUTO" in capsys.readouterr().out

    def test_enables_manual(self, mock_system, capsys) -> None:
        _run("set-ems", "manual")
        mock_system.set_ems_mode.assert_called_once_with(auto=False)
        assert "MANUAL OVERRIDE" in capsys.readouterr().out

    def test_invalid_mode_rejected_by_argparse(self, mock_system) -> None:
        with pytest.raises(SystemExit):
            _run("set-ems", "turbo")


# ---------------------------------------------------------------------------
# savings
# ---------------------------------------------------------------------------

class TestCmdSavings:
    def test_prints_savings_value(self, mock_system, capsys) -> None:
        mock_system.get_energy_savings.return_value = HeartbeatSavings.from_dict(
            make_energy_savings_data(value=175.42)
        )
        _run("savings", "--from", "2026-07-01", "--to", "2026-07-31")
        out = capsys.readouterr().out
        assert "175.42" in out
        assert "2026-07-01" in out
        assert "2026-07-31" in out

    def test_default_window_labeled(self, mock_system, capsys) -> None:
        mock_system.get_energy_savings.return_value = HeartbeatSavings.from_dict(
            make_energy_savings_data()
        )
        _run("savings")
        out = capsys.readouterr().out
        assert "API default" in out
        assert "39.39" in out

    def test_missing_value_prints_dash(self, mock_system, capsys) -> None:
        mock_system.get_energy_savings.return_value = HeartbeatSavings.from_dict(
            make_energy_savings_data(value=None)
        )
        _run("savings")
        assert "—" in capsys.readouterr().out

    def test_invalid_date_rejected(self, mock_system) -> None:
        with pytest.raises(SystemExit):
            _run("savings", "--from", "not-a-date")


# ---------------------------------------------------------------------------
# price-config
# ---------------------------------------------------------------------------

class TestCmdPriceConfig:
    def test_prints_all_prices(self, mock_system, capsys) -> None:
        mock_system.get_price_customizations.return_value = PriceCustomizations.from_dict(
            make_price_customizations_data()
        )
        _run("price-config")
        out = capsys.readouterr().out
        assert "0.3039" in out
        assert "0.2740" in out
        assert "13.90" in out


# ---------------------------------------------------------------------------
# comparison-price
# ---------------------------------------------------------------------------

class TestCmdComparisonPrice:
    def test_prints_price(self, mock_system, capsys) -> None:
        mock_system.get_comparison_price.return_value = ComparisonPrice.from_dict(
            make_comparison_price_data()
        )
        _run("comparison-price")
        assert "0.2740" in capsys.readouterr().out

    def test_prints_dash_when_missing(self, mock_system, capsys) -> None:
        mock_system.get_comparison_price.return_value = ComparisonPrice.from_dict({})
        _run("comparison-price")
        assert "—" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# price-guarantee
# ---------------------------------------------------------------------------

class TestCmdPriceGuarantee:
    def test_uses_explicit_customer_id(self, mock_system, capsys) -> None:
        mock_system.get_price_guarantee.return_value = PriceGuarantee.from_dict(
            make_price_guarantee_data()
        )
        _run("price-guarantee", "--customer-id", "cust-explicit")
        mock_system.get_price_guarantee.assert_called_once_with("cust-explicit")
        out = capsys.readouterr().out
        assert "12" in out
        assert "ct/kWh" in out
        assert "DE_PRICE_GUARANTEE_V2" in out

    def test_falls_back_to_details_customer_id(self, mock_system, capsys) -> None:
        details = MagicMock()
        details.customer_id = "cust-from-details"
        mock_system.get_details.return_value = details
        mock_system.get_price_guarantee.return_value = PriceGuarantee.from_dict(
            make_price_guarantee_data()
        )
        _run("price-guarantee")
        mock_system.get_price_guarantee.assert_called_once_with("cust-from-details")

    def test_exits_when_no_customer_id_available(self, mock_system) -> None:
        details = MagicMock()
        details.customer_id = None
        mock_system.get_details.return_value = details
        with pytest.raises(SystemExit):
            _run("price-guarantee")


# ---------------------------------------------------------------------------
# wallboxes
# ---------------------------------------------------------------------------

class TestCmdWallboxes:
    def test_prints_wallbox_info(self, mock_system, capsys) -> None:
        mock_system.get_wallboxes.return_value = [Wallbox.from_dict(w) for w in make_wallboxes_data()]
        _run("wallboxes")
        out = capsys.readouterr().out
        assert "Wallbox" in out
        assert "wb-0001" in out
        assert FAKE_EV_ID in out

    def test_prints_empty_message(self, mock_system, capsys) -> None:
        mock_system.get_wallboxes.return_value = []
        _run("wallboxes")
        assert "No wallboxes" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# smart-meter
# ---------------------------------------------------------------------------

class TestCmdSmartMeter:
    def test_prints_flattened_fields(self, mock_system, capsys) -> None:
        mock_system.get_smart_meter.return_value = SmartMeter.from_dict(make_smart_meter_data())
        _run("smart-meter")
        out = capsys.readouterr().out
        assert "10YDE-RWENET---I" in out
        assert "9900000000009" in out
        assert "0.0159" in out


# ---------------------------------------------------------------------------
# monthly-trading
# ---------------------------------------------------------------------------

class TestCmdMonthlyTrading:
    def test_prints_value(self, mock_system, capsys) -> None:
        mock_system.get_monthly_trading_savings.return_value = MonthlyTradingSavings.from_dict(
            make_monthly_trading_savings_data()
        )
        _run("monthly-trading")
        assert "12.83" in capsys.readouterr().out

    def test_prints_dash_when_missing(self, mock_system, capsys) -> None:
        mock_system.get_monthly_trading_savings.return_value = MonthlyTradingSavings.from_dict({})
        _run("monthly-trading")
        assert "—" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# impact
# ---------------------------------------------------------------------------

class TestCmdImpact:
    def test_prints_co2_figures(self, mock_system, capsys) -> None:
        mock_system.get_impact_overview.return_value = ImpactOverview.from_dict(
            make_impact_overview_data()
        )
        _run("impact")
        out = capsys.readouterr().out
        assert "1,234" in out
        assert "kg" in out
        assert "50,000" in out or "50000" in out


# ---------------------------------------------------------------------------
# trader
# ---------------------------------------------------------------------------

class TestCmdTrader:
    def test_prints_savings_and_status(self, mock_system, capsys) -> None:
        mock_system.get_energy_trader.return_value = EnergyTrader.from_dict(
            make_energy_trader_data()
        )
        _run("trader")
        out = capsys.readouterr().out
        assert "ACTIVE" in out
        assert "1,500.75" in out
        assert "125.40" in out


# ---------------------------------------------------------------------------
# ai-summary
# ---------------------------------------------------------------------------

class TestCmdAiSummary:
    def test_1m_prints_all_metrics(self, mock_system, capsys) -> None:
        mock_system.get_heartbeat_ai_summary.return_value = HeartbeatAiSummary.from_dict(
            "1M", make_heartbeat_ai_summary_data("1M")
        )
        _run("ai-summary")
        out = capsys.readouterr().out
        assert "1M" in out
        assert "73.0%" in out
        assert "30.41" in out
        assert "210.5" in out

    def test_defaults_to_1m_resolution(self, mock_system) -> None:
        mock_system.get_heartbeat_ai_summary.return_value = HeartbeatAiSummary.from_dict(
            "1M", make_heartbeat_ai_summary_data("1M")
        )
        _run("ai-summary")
        mock_system.get_heartbeat_ai_summary.assert_called_once_with(resolution="1M")

    def test_1w_skips_missing_metrics(self, mock_system, capsys) -> None:
        mock_system.get_heartbeat_ai_summary.return_value = HeartbeatAiSummary.from_dict(
            "1W", make_heartbeat_ai_summary_data("1W")
        )
        _run("ai-summary", "--resolution", "1W")
        out = capsys.readouterr().out
        assert "1W" in out
        assert "Self-suff" not in out
        assert "Earned" not in out
        assert "210.5" in out  # co2 still there

    def test_invalid_resolution_rejected(self, mock_system) -> None:
        with pytest.raises(SystemExit):
            _run("ai-summary", "--resolution", "1D")


# ---------------------------------------------------------------------------
# Missing credentials
# ---------------------------------------------------------------------------

class TestMissingCredentials:
    def test_exits_when_env_vars_absent(self, monkeypatch) -> None:
        monkeypatch.delenv("ONEKOMMAFIVE_USERNAME", raising=False)
        monkeypatch.delenv("ONEKOMMAFIVE_PASSWORD", raising=False)
        with pytest.raises(SystemExit):
            _run("live")
