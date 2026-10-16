"""Tests for :func:`onekommafive.cli._client`, :func:`_get_system`, the
small formatter helpers (``_kwh``, ``_w``, ``_pct``) and the ``main``
dispatch wrapper.

Every CLI subcommand routes through these; coverage of the env-var and
dispatch branches is required by the 95 % gate.
"""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest

from onekommafive.cli import _client, _get_system, _kwh, _pct, _w, main


class TestClientHelper:
    def test_exits_when_username_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("ONEKOMMAFIVE_USERNAME", raising=False)
        monkeypatch.setenv("ONEKOMMAFIVE_PASSWORD", "p")
        with pytest.raises(SystemExit, match="ONEKOMMAFIVE_USERNAME"):
            _client()

    def test_exits_when_password_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ONEKOMMAFIVE_USERNAME", "u@example.com")
        monkeypatch.delenv("ONEKOMMAFIVE_PASSWORD", raising=False)
        with pytest.raises(SystemExit, match="ONEKOMMAFIVE_PASSWORD"):
            _client()

    def test_returns_client_with_cache_by_default(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("ONEKOMMAFIVE_USERNAME", "u@example.com")
        monkeypatch.setenv("ONEKOMMAFIVE_PASSWORD", "p")
        monkeypatch.delenv("ONEKOMMAFIVE_NO_CACHE", raising=False)
        with patch("onekommafive.cli.Client") as ctor:
            ctor.return_value = MagicMock()
            _client()
            _, kwargs = ctor.call_args
            assert kwargs["token_cache"] is not None

    def test_no_cache_env_disables_token_cache(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("ONEKOMMAFIVE_USERNAME", "u@example.com")
        monkeypatch.setenv("ONEKOMMAFIVE_PASSWORD", "p")
        monkeypatch.setenv("ONEKOMMAFIVE_NO_CACHE", "1")
        with patch("onekommafive.cli.Client") as ctor:
            ctor.return_value = MagicMock()
            _client()
            _, kwargs = ctor.call_args
            assert kwargs["token_cache"] is None


class TestGetSystemHelper:
    def test_exits_when_no_systems_available(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("ONEKOMMAFIVE_USERNAME", "u@example.com")
        monkeypatch.setenv("ONEKOMMAFIVE_PASSWORD", "p")
        with (
            patch("onekommafive.cli._client", return_value=MagicMock()),
            patch("onekommafive.cli.Systems") as systems_ctor,
        ):
            systems_ctor.return_value.get_systems.return_value = []
            with pytest.raises(SystemExit, match="no systems"):
                _get_system()

    def test_returns_first_system_when_no_target_id_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("ONEKOMMAFIVE_USERNAME", "u@example.com")
        monkeypatch.setenv("ONEKOMMAFIVE_PASSWORD", "p")
        monkeypatch.delenv("ONEKOMMAFIVE_SYSTEM", raising=False)
        first = MagicMock()
        first.id.return_value = "sys-1"
        second = MagicMock()
        second.id.return_value = "sys-2"
        with (
            patch("onekommafive.cli._client", return_value=MagicMock()),
            patch("onekommafive.cli.Systems") as systems_ctor,
        ):
            systems_ctor.return_value.get_systems.return_value = [first, second]
            assert _get_system() is first

    def test_returns_matching_system_when_target_id_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("ONEKOMMAFIVE_USERNAME", "u@example.com")
        monkeypatch.setenv("ONEKOMMAFIVE_PASSWORD", "p")
        monkeypatch.setenv("ONEKOMMAFIVE_SYSTEM", "sys-2")
        first = MagicMock()
        first.id.return_value = "sys-1"
        second = MagicMock()
        second.id.return_value = "sys-2"
        with (
            patch("onekommafive.cli._client", return_value=MagicMock()),
            patch("onekommafive.cli.Systems") as systems_ctor,
        ):
            systems_ctor.return_value.get_systems.return_value = [first, second]
            assert _get_system() is second

    def test_exits_when_target_id_does_not_match(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("ONEKOMMAFIVE_USERNAME", "u@example.com")
        monkeypatch.setenv("ONEKOMMAFIVE_PASSWORD", "p")
        monkeypatch.setenv("ONEKOMMAFIVE_SYSTEM", "sys-nonexistent")
        first = MagicMock()
        first.id.return_value = "sys-1"
        with (
            patch("onekommafive.cli._client", return_value=MagicMock()),
            patch("onekommafive.cli.Systems") as systems_ctor,
        ):
            systems_ctor.return_value.get_systems.return_value = [first]
            with pytest.raises(SystemExit, match="not found"):
                _get_system()


class TestFormatHelpers:
    """``_kwh``, ``_w`` and ``_pct`` cover the formatter branches used by
    every print path."""

    def test_kwh_formats_two_decimals(self) -> None:
        assert _kwh(1.2345) == "1.23 kWh"

    def test_kwh_renders_none_as_dash(self) -> None:
        assert _kwh(None) == "—"

    def test_w_adds_plus_sign_for_positive_power(self) -> None:
        assert _w(123.6) == "+124 W"

    def test_w_omits_sign_for_zero(self) -> None:
        assert _w(0) == "0 W"

    def test_w_keeps_minus_for_negative(self) -> None:
        assert _w(-50.4) == "-50 W"

    def test_w_renders_none_as_dash(self) -> None:
        assert _w(None) == "—"

    def test_pct_formats_one_decimal(self) -> None:
        assert _pct(42.57) == "42.6%"

    def test_pct_renders_none_as_dash(self) -> None:
        assert _pct(None) == "—"


class TestMainDispatch:
    """``main`` dispatches to the parsed subcommand and always closes any
    live sync-client, even when the subcommand raises."""

    def test_closes_live_clients_in_finally_on_success(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(sys, "argv", ["1k5", "live"])
        live_client = MagicMock()
        with (
            patch("onekommafive.cli.cmd_live") as cmd,
            patch("onekommafive.cli.Client._live", {live_client}),
        ):
            main()
        cmd.assert_called_once()
        live_client.close.assert_called_once()

    def test_closes_live_clients_in_finally_on_exception(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(sys, "argv", ["1k5", "live"])
        live_client = MagicMock()
        with (
            patch("onekommafive.cli.cmd_live", side_effect=RuntimeError("boom")),
            patch("onekommafive.cli.Client._live", {live_client}),
            pytest.raises(RuntimeError, match="boom"),
        ):
            main()
        live_client.close.assert_called_once()
