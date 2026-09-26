"""Tests for :func:`onekommafive.cli._client` and :func:`_get_system`.

These helpers wire the CLI to the SDK; every subcommand routes through
them. Coverage of the env-var branches is required by the 95 % gate.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from onekommafive.cli import _client, _get_system


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
