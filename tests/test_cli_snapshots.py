"""Snapshot tests for CLI output formatting.

Each subcommand is exercised against a stable mock payload. The stdout
is captured and compared against a stored ``*.ambr`` snapshot via
syrupy. Format drift (new column, re-ordered row, dropped unit suffix)
breaks the suite immediately instead of landing silently.

Update snapshots after an intentional format change:

    uv run pytest tests/test_cli_snapshots.py --snapshot-update

Then review the diff in ``tests/__snapshots__/`` as part of the PR.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from onekommafive.cli import main
from onekommafive.models import (
    EmsSettings,
    HeartbeatPrices,
    LiveOverview,
    SiteStatus,
    SiteSystemInfo,
    SystemInfo,
    WeatherData,
)
from tests.fixtures import (
    FAKE_SYSTEM_ID,
    make_active_features_data,
    make_ems_settings_data,
    make_heartbeat_prices_data,
    make_live_overview_data,
    make_status_and_assets_data,
    make_system_data,
    make_system_info_data,
    make_weather_data,
)


def _run(*argv: str) -> None:
    with patch("sys.argv", ["cli.py", *argv]):
        main()


@pytest.fixture
def mock_system():
    """Hand command handlers a MagicMock instead of a live System."""

    system = MagicMock()
    system.id.return_value = FAKE_SYSTEM_ID
    with patch("onekommafive.cli._get_system", return_value=system):
        yield system


class TestCliSnapshots:
    """One snapshot per user-facing subcommand with a stable mock payload."""

    def test_info_output(self, mock_system, capsys, snapshot) -> None:
        mock_system.info.return_value = SystemInfo.from_dict(make_system_data())
        mock_system.get_status_and_assets.return_value = SiteStatus.from_dict(
            make_status_and_assets_data()
        )
        mock_system.get_active_features.return_value = set(
            make_active_features_data()["features"]
        )
        _run("info")
        assert capsys.readouterr().out == snapshot

    def test_live_output(self, mock_system, capsys, snapshot) -> None:
        mock_system.get_live_overview.return_value = LiveOverview.from_dict(
            make_live_overview_data()
        )
        _run("live")
        assert capsys.readouterr().out == snapshot

    def test_weather_output(self, mock_system, capsys, snapshot) -> None:
        mock_system.get_weather.return_value = WeatherData.from_dict(
            make_weather_data()
        )
        _run("weather")
        assert capsys.readouterr().out == snapshot

    def test_system_info_output(self, mock_system, capsys, snapshot) -> None:
        mock_system.get_system_info.return_value = SiteSystemInfo.from_dict(
            make_system_info_data(
                availability="READY",
                enwg14a_module_value="module-1",
                enwg14a_module_valid_from="2025-09-19",
            )
        )
        _run("system-info")
        assert capsys.readouterr().out == snapshot

    def test_system_info_output_no_enrolment(
        self, mock_system, capsys, snapshot
    ) -> None:
        mock_system.get_system_info.return_value = SiteSystemInfo.from_dict(
            make_system_info_data()
        )
        _run("system-info")
        assert capsys.readouterr().out == snapshot

    def test_heartbeat_prices_output(self, mock_system, capsys, snapshot) -> None:
        mock_system.get_heartbeat_prices.return_value = HeartbeatPrices.from_dict(
            make_heartbeat_prices_data()
        )
        _run("heartbeat-prices")
        assert capsys.readouterr().out == snapshot

    def test_ems_output(self, mock_system, capsys, snapshot) -> None:
        mock_system.get_ems_settings.return_value = EmsSettings.from_dict(
            make_ems_settings_data()
        )
        _run("ems")
        assert capsys.readouterr().out == snapshot
