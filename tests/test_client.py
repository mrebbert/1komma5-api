"""Tests for :mod:`onekommafive.client` – authentication and token management."""

from __future__ import annotations

import json
import os
import stat
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import responses as resp_lib

from onekommafive.client import (
    _TOKEN_URL,
    Client,
    _generate_code_challenge,
    _generate_code_verifier,
)
from onekommafive.errors import AuthenticationError, RequestError
from tests.fixtures import (
    FAKE_ACCESS_TOKEN,
    FAKE_TOKEN_SET,
    make_client,
)

# ---------------------------------------------------------------------------
# PKCE helpers
# ---------------------------------------------------------------------------

class TestPkceHelpers:
    """Unit tests for the PKCE code-verifier/challenge functions."""

    def test_verifier_is_non_empty_string(self) -> None:
        verifier = _generate_code_verifier()
        assert isinstance(verifier, str)
        assert len(verifier) > 0

    def test_verifier_is_url_safe(self) -> None:
        """Verifier must not contain characters that require URL encoding."""
        verifier = _generate_code_verifier()
        safe = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_")
        assert all(c in safe for c in verifier), f"Unexpected characters in: {verifier}"

    def test_challenge_differs_from_verifier(self) -> None:
        verifier = _generate_code_verifier()
        challenge = _generate_code_challenge(verifier)
        assert challenge != verifier

    def test_challenge_is_deterministic(self) -> None:
        """Same verifier must always produce the same challenge."""
        verifier = "static-test-verifier"
        assert _generate_code_challenge(verifier) == _generate_code_challenge(verifier)

    def test_two_verifiers_are_unique(self) -> None:
        """Each call should produce a different verifier."""
        assert _generate_code_verifier() != _generate_code_verifier()


# ---------------------------------------------------------------------------
# Token state management
# ---------------------------------------------------------------------------

class TestTokenManagement:
    """Tests for get_token, _is_token_expiring, and related logic."""

    def test_get_token_triggers_login_when_no_token_set(self) -> None:
        client = Client("user@example.com", "pass")
        client._login = MagicMock(return_value=FAKE_ACCESS_TOKEN)

        result = client.get_token()

        client._login.assert_called_once()
        assert result == FAKE_ACCESS_TOKEN

    def test_get_token_returns_cached_token_when_valid(self) -> None:
        client = make_client()
        client._refresh_token = MagicMock()
        client._login = MagicMock()

        result = client.get_token()

        assert result == FAKE_ACCESS_TOKEN
        client._refresh_token.assert_not_called()
        client._login.assert_not_called()

    def test_get_token_refreshes_when_expiring(self) -> None:
        client = make_client()
        client._is_token_expiring = MagicMock(return_value=True)
        client._refresh_token = MagicMock(return_value="refreshed-token")

        result = client.get_token()

        client._refresh_token.assert_called_once()
        assert result == "refreshed-token"

    def test_get_token_falls_back_to_login_on_refresh_failure(self) -> None:
        client = make_client()
        client._is_token_expiring = MagicMock(return_value=True)
        client._refresh_token = MagicMock(side_effect=AuthenticationError("expired"))
        client._login = MagicMock(return_value="fresh-login-token")

        result = client.get_token()

        client._login.assert_called_once()
        assert result == "fresh-login-token"

    def test_is_token_expiring_returns_true_when_no_token(self) -> None:
        client = Client("u", "p")
        # Reset the mock so we call the real implementation
        assert client._is_token_expiring(60) is True

    def test_is_token_expiring_returns_true_on_expired_signature(self) -> None:
        """_is_token_expiring must return True when the JWT is already expired."""
        import jwt as jwt_lib

        client = Client("u", "p")
        client._token_set = {"access_token": "x"}
        client._decode_token = MagicMock(
            side_effect=jwt_lib.exceptions.ExpiredSignatureError
        )
        assert client._is_token_expiring(60) is True

    def test_is_token_expiring_false_for_far_future_exp(self) -> None:
        client = Client("u", "p")
        client._token_set = {"access_token": "x"}
        far_future = int(time.time()) + 9999
        client._decode_token = MagicMock(return_value={"exp": far_future})
        assert client._is_token_expiring(60) is False


# ---------------------------------------------------------------------------
# Refresh token
# ---------------------------------------------------------------------------

class TestRefreshToken:
    """Tests for the _refresh_token private method."""

    def test_raises_when_no_token_set(self) -> None:
        client = Client("u", "p")
        with pytest.raises(AuthenticationError, match="No token set"):
            client._refresh_token()

    def test_raises_when_no_refresh_token_in_set(self) -> None:
        client = Client("u", "p")
        client._token_set = {"access_token": "x"}
        with pytest.raises(AuthenticationError, match="No refresh token"):
            client._refresh_token()

    @resp_lib.activate
    def test_successful_refresh(self) -> None:
        resp_lib.add(
            resp_lib.POST,
            _TOKEN_URL,
            json={
                "access_token": "new-access-token",
                "refresh_token": "new-refresh-token",
            },
            status=200,
        )
        client = Client("u", "p")
        client._token_set = FAKE_TOKEN_SET.copy()

        token = client._refresh_token()

        assert token == "new-access-token"
        assert client._token_set["access_token"] == "new-access-token"

    @resp_lib.activate
    def test_raises_on_server_error_during_refresh(self) -> None:
        resp_lib.add(resp_lib.POST, _TOKEN_URL, json={"error": "invalid_grant"}, status=400)
        client = Client("u", "p")
        client._token_set = FAKE_TOKEN_SET.copy()

        with pytest.raises(AuthenticationError, match="Token refresh failed"):
            client._refresh_token()


# ---------------------------------------------------------------------------
# get_user
# ---------------------------------------------------------------------------

class TestGetUser:
    """Tests for Client.get_user."""

    @resp_lib.activate
    def test_returns_user_object(self) -> None:
        resp_lib.add(
            resp_lib.GET,
            "https://customer-identity.1komma5grad.com/api/v1/users/me",
            json={"id": "user-123", "email": "user@example.com", "name": "Test User"},
            status=200,
        )
        client = make_client()
        user = client.get_user()

        assert user.id == "user-123"
        assert user.email == "user@example.com"

    @resp_lib.activate
    def test_raises_on_server_error(self) -> None:
        resp_lib.add(
            resp_lib.GET,
            "https://customer-identity.1komma5grad.com/api/v1/users/me",
            json={"error": "unauthorized"},
            status=401,
        )
        client = make_client()
        with pytest.raises(RequestError, match="Failed to get user"):
            client.get_user()


# ---------------------------------------------------------------------------
# logout
# ---------------------------------------------------------------------------

class TestLogout:
    """Tests for Client.logout."""

    @resp_lib.activate
    def test_clears_token_set_on_success(self) -> None:
        resp_lib.add(
            resp_lib.GET,
            "https://auth.1komma5grad.com/v2/logout",
            status=302,
        )
        client = make_client()
        client.logout()
        assert client._token_set is None

    @resp_lib.activate
    def test_clears_token_set_even_on_server_error(self) -> None:
        """The local token cache must be cleared regardless of server response."""
        resp_lib.add(
            resp_lib.GET,
            "https://auth.1komma5grad.com/v2/logout",
            status=500,
        )
        client = make_client()
        with pytest.raises(RequestError):
            client.logout()
        assert client._token_set is None


# ---------------------------------------------------------------------------
# Token cache (cross-process persistence)
# ---------------------------------------------------------------------------

class TestTokenCache:
    """Tests for the optional ``token_cache`` constructor parameter."""

    def test_no_cache_param_keeps_behaviour_unchanged(self, tmp_path: Path) -> None:
        """Default (cache disabled) must not touch the filesystem."""
        client = Client("u@example.com", "p")
        assert client._token_cache_path is None
        assert client._token_set is None

    def test_load_populates_token_set_from_existing_file(self, tmp_path: Path) -> None:
        cache = tmp_path / "token.json"
        cache.write_text(json.dumps({**FAKE_TOKEN_SET, "_username": "u@example.com"}))

        client = Client("u@example.com", "p", token_cache=cache)

        assert client._token_set == FAKE_TOKEN_SET

    def test_load_ignores_cache_for_different_user(self, tmp_path: Path) -> None:
        """Cache files are bound to a single user; cross-user reads must be rejected."""
        cache = tmp_path / "token.json"
        cache.write_text(json.dumps({**FAKE_TOKEN_SET, "_username": "other@example.com"}))

        client = Client("u@example.com", "p", token_cache=cache)

        assert client._token_set is None

    def test_load_silently_skips_missing_file(self, tmp_path: Path) -> None:
        client = Client("u@example.com", "p", token_cache=tmp_path / "absent.json")
        assert client._token_set is None

    def test_load_silently_skips_corrupt_json(self, tmp_path: Path) -> None:
        cache = tmp_path / "token.json"
        cache.write_text("not-valid-json{")
        client = Client("u@example.com", "p", token_cache=cache)
        assert client._token_set is None

    def test_expanduser_resolves_tilde_in_path(self, tmp_path: Path, monkeypatch) -> None:
        """``~`` in the cache path must be expanded to ``$HOME``."""
        monkeypatch.setenv("HOME", str(tmp_path))
        client = Client("u@example.com", "p", token_cache="~/cache.json")
        assert client._token_cache_path == tmp_path / "cache.json"

    @resp_lib.activate
    def test_save_writes_after_refresh_with_chmod_600(self, tmp_path: Path) -> None:
        cache = tmp_path / "token.json"
        resp_lib.add(
            resp_lib.POST,
            _TOKEN_URL,
            json={"access_token": "fresh", "refresh_token": "fresh-refresh"},
            status=200,
        )
        client = Client("u@example.com", "p", token_cache=cache)
        client._token_set = FAKE_TOKEN_SET.copy()
        client._refresh_token()

        assert cache.exists()
        data = json.loads(cache.read_text())
        assert data["access_token"] == "fresh"
        assert data["_username"] == "u@example.com"
        # chmod 600 — owner read/write only
        mode = stat.S_IMODE(os.stat(cache).st_mode)
        assert mode == 0o600

    def test_save_is_noop_without_token_set(self, tmp_path: Path) -> None:
        cache = tmp_path / "token.json"
        client = Client("u@example.com", "p", token_cache=cache)
        # token_set is None — no login happened — nothing to save
        client._save_token_cache()
        assert not cache.exists()

    def test_save_creates_parent_directories(self, tmp_path: Path) -> None:
        cache = tmp_path / "nested" / "dir" / "token.json"
        client = Client("u@example.com", "p", token_cache=cache)
        client._token_set = FAKE_TOKEN_SET.copy()
        client._save_token_cache()
        assert cache.exists()
