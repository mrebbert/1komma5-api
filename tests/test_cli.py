"""Tests for :mod:`onekommafive.cli` – command-line interface."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from onekommafive.cli import main
from onekommafive.models import ChargingMode, EmsSettings, LiveOverview, MarketPrices, SystemInfo
from tests.fixtures import (
    FAKE_EV_ID,
    FAKE_SYSTEM_ID,
    make_ems_settings_data,
    make_live_overview_data,
    make_price_data,
    make_system_data,
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
# Missing credentials
# ---------------------------------------------------------------------------

class TestMissingCredentials:
    def test_exits_when_env_vars_absent(self, monkeypatch) -> None:
        monkeypatch.delenv("ONEKOMMAFIVE_USERNAME", raising=False)
        monkeypatch.delenv("ONEKOMMAFIVE_PASSWORD", raising=False)
        with pytest.raises(SystemExit):
            _run("live")
