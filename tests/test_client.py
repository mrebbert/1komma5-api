"""Tests for :mod:`onekommafive.client` – authentication and token management."""

from __future__ import annotations

import json
import os
import re as _re
import stat
import time
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from aioresponses import aioresponses

from onekommafive.client import (
    _AUTH_BASE,
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
    make_supported_versions_data,
    make_user_data,
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

    async def test_get_token_triggers_login_when_no_token_set(self) -> None:
        client = Client("user@example.com", "pass")
        client._login = AsyncMock(return_value=FAKE_ACCESS_TOKEN)

        result = await client.get_token()

        client._login.assert_awaited_once()
        assert result == FAKE_ACCESS_TOKEN

    async def test_get_token_returns_cached_token_when_valid(self) -> None:
        client = make_client()
        client._refresh_token = AsyncMock()
        client._login = AsyncMock()

        result = await client.get_token()

        assert result == FAKE_ACCESS_TOKEN
        client._refresh_token.assert_not_awaited()
        client._login.assert_not_awaited()

    async def test_get_token_refreshes_when_expiring(self) -> None:
        client = make_client()
        client._is_token_expiring = AsyncMock(return_value=True)
        client._refresh_token = AsyncMock(return_value="refreshed-token")

        result = await client.get_token()

        client._refresh_token.assert_awaited_once()
        assert result == "refreshed-token"

    async def test_get_token_falls_back_to_login_on_refresh_failure(self) -> None:
        client = make_client()
        client._is_token_expiring = AsyncMock(return_value=True)
        client._refresh_token = AsyncMock(side_effect=AuthenticationError("expired"))
        client._login = AsyncMock(return_value="fresh-login-token")

        result = await client.get_token()

        client._login.assert_awaited_once()
        assert result == "fresh-login-token"

    async def test_is_token_expiring_returns_true_when_no_token(self) -> None:
        client = Client("u", "p")
        assert await client._is_token_expiring(60) is True

    async def test_is_token_expiring_returns_true_on_expired_signature(self) -> None:
        """_is_token_expiring must return True when the JWT is already expired."""
        import jwt as jwt_lib

        client = Client("u", "p")
        client._token_set = {"access_token": "x"}
        client._decode_token = AsyncMock(
            side_effect=jwt_lib.exceptions.ExpiredSignatureError
        )
        assert await client._is_token_expiring(60) is True

    async def test_is_token_expiring_false_for_far_future_exp(self) -> None:
        client = Client("u", "p")
        client._token_set = {"access_token": "x"}
        far_future = int(time.time()) + 9999
        client._decode_token = AsyncMock(return_value={"exp": far_future})
        assert await client._is_token_expiring(60) is False


# ---------------------------------------------------------------------------
# Refresh token
# ---------------------------------------------------------------------------


class TestRefreshToken:
    """Tests for the _refresh_token private method."""

    async def test_raises_when_no_token_set(self) -> None:
        client = Client("u", "p")
        with pytest.raises(AuthenticationError, match="No token set"):
            await client._refresh_token()

    async def test_raises_when_no_refresh_token_in_set(self) -> None:
        client = Client("u", "p")
        client._token_set = {"access_token": "x"}
        with pytest.raises(AuthenticationError, match="No refresh token"):
            await client._refresh_token()

    async def test_successful_refresh(self) -> None:
        with aioresponses() as m:
            m.post(
                _TOKEN_URL,
                payload={
                    "access_token": "new-access-token",
                    "refresh_token": "new-refresh-token",
                },
                status=200,
            )
            client = Client("u", "p")
            client._token_set = FAKE_TOKEN_SET.copy()

            token = await client._refresh_token()

            assert token == "new-access-token"
            assert client._token_set["access_token"] == "new-access-token"
            await client.close()

    async def test_raises_on_server_error_during_refresh(self) -> None:
        with aioresponses() as m:
            m.post(_TOKEN_URL, payload={"error": "invalid_grant"}, status=400)
            client = Client("u", "p")
            client._token_set = FAKE_TOKEN_SET.copy()

            with pytest.raises(AuthenticationError, match="Token refresh failed"):
                await client._refresh_token()
            await client.close()

    async def test_preserves_refresh_token_when_response_omits_it(self) -> None:
        """Regression: Auth0 responses with server-side rotation OFF omit
        the refresh_token field. Previously the SDK overwrote _token_set
        with the response, dropping the still-valid refresh_token and
        causing subsequent refreshes to fail with 'No refresh token found'.
        """
        with aioresponses() as m:
            m.post(
                _TOKEN_URL,
                payload={
                    "access_token": "new-access-token",
                    "id_token": "new-id-token",
                    "expires_in": 86400,
                    "token_type": "Bearer",
                    # NOTE: no refresh_token in the response
                },
                status=200,
            )
            client = Client("u", "p")
            client._token_set = {**FAKE_TOKEN_SET, "refresh_token": "original-refresh"}

            await client._refresh_token()

            assert client._token_set["access_token"] == "new-access-token"
            assert client._token_set["refresh_token"] == "original-refresh"
            await client.close()

    async def test_updates_refresh_token_when_response_rotates_it(self) -> None:
        """Companion test: when Auth0 does rotate, the new refresh_token
        replaces the old one (dict merge picks the newer value)."""
        with aioresponses() as m:
            m.post(
                _TOKEN_URL,
                payload={
                    "access_token": "new-access-token",
                    "refresh_token": "rotated-refresh",
                },
                status=200,
            )
            client = Client("u", "p")
            client._token_set = {**FAKE_TOKEN_SET, "refresh_token": "original-refresh"}

            await client._refresh_token()

            assert client._token_set["refresh_token"] == "rotated-refresh"
            await client.close()


# ---------------------------------------------------------------------------
# get_user
# ---------------------------------------------------------------------------


class TestGetUser:
    """Tests for Client.get_user."""

    _URL = "https://customer-identity.1komma5grad.com/api/v1/users/me"

    async def test_returns_user_object(self) -> None:
        with aioresponses() as m:
            m.get(
                self._URL,
                payload={
                    "id": "user-123",
                    "email": "user@example.com",
                    "name": "Test User",
                },
                status=200,
            )
            client = make_client()
            user = await client.get_user()

            assert user.id == "user-123"
            assert user.email == "user@example.com"
            await client.close()

    async def test_raises_on_server_error(self) -> None:
        with aioresponses() as m:
            m.get(self._URL, payload={"error": "unauthorized"}, status=401)
            client = make_client()
            with pytest.raises(RequestError, match="Failed to get user"):
                await client.get_user()
            await client.close()

    async def test_full_profile_fields_parsed(self) -> None:
        with aioresponses() as m:
            m.get(self._URL, payload=make_user_data(), status=200)
            client = make_client()
            user = await client.get_user()
            assert user.first_name == "John"
            assert user.last_name == "Doe"
            assert user.phone is None
            assert user.status == "ACTIVE"
            assert user.external_id == "auth0|abcdef1234567890"
            assert len(user.connected_systems) == 2
            assert user.connected_systems[0].name == "My Home System"
            assert user.connected_systems[0].address_city == "Hamburg"
            assert user.connected_systems[1].name == "Demo System"
            await client.close()


# ---------------------------------------------------------------------------
# get_supported_versions
# ---------------------------------------------------------------------------


class TestGetSupportedVersions:
    _URL = "https://heartbeat.1komma5grad.com/api/v1/supported-versions"

    async def test_returns_versions(self) -> None:
        with aioresponses() as m:
            m.get(self._URL, payload=make_supported_versions_data(), status=200)
            client = make_client()
            v = await client.get_supported_versions()
            assert v.b2b.target_version == "1.10.0"
            assert v.b2b.minimum_supported_version == "1.12.0"
            assert v.b2c.target_version == "1.73.0"
            assert v.b2c.minimum_supported_version == "1.73.0"
            await client.close()

    async def test_handles_missing_channels(self) -> None:
        with aioresponses() as m:
            m.get(self._URL, payload={}, status=200)
            client = make_client()
            v = await client.get_supported_versions()
            assert v.b2b.target_version is None
            assert v.b2c.minimum_supported_version is None
            await client.close()

    async def test_raises_on_server_error(self) -> None:
        with aioresponses() as m:
            m.get(self._URL, payload={}, status=500)
            client = make_client()
            with pytest.raises(RequestError, match="Failed to get supported versions"):
                await client.get_supported_versions()
            await client.close()


# ---------------------------------------------------------------------------
# logout
# ---------------------------------------------------------------------------


class TestLogout:
    """Tests for Client.logout."""

    _URL = "https://auth.1komma5grad.com/v2/logout?client_id=zJTm6GFGM5zHcmpl07xTsi6MP0TwRAw6"

    async def test_clears_token_set_on_success(self) -> None:
        with aioresponses() as m:
            m.get(self._URL, status=302)
            client = make_client()
            await client.logout()
            assert client._token_set is None
            await client.close()

    async def test_clears_token_set_even_on_server_error(self) -> None:
        """The local token cache must be cleared regardless of server response."""
        with aioresponses() as m:
            m.get(self._URL, status=500)
            client = make_client()
            with pytest.raises(RequestError):
                await client.logout()
            assert client._token_set is None
            await client.close()


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
        cache.write_text(
            json.dumps({**FAKE_TOKEN_SET, "_username": "other@example.com"})
        )

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

    def test_expanduser_resolves_tilde_in_path(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """``~`` in the cache path must be expanded to ``$HOME``."""
        monkeypatch.setenv("HOME", str(tmp_path))
        client = Client("u@example.com", "p", token_cache="~/cache.json")
        assert client._token_cache_path == tmp_path / "cache.json"

    async def test_save_writes_after_refresh_with_chmod_600(
        self, tmp_path: Path
    ) -> None:
        cache = tmp_path / "token.json"
        with aioresponses() as m:
            m.post(
                _TOKEN_URL,
                payload={"access_token": "fresh", "refresh_token": "fresh-refresh"},
                status=200,
            )
            client = Client("u@example.com", "p", token_cache=cache)
            client._token_set = FAKE_TOKEN_SET.copy()
            await client._refresh_token()
            await client.close()

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


class TestAsyncContextManager:
    """__aenter__ / __aexit__ let the client work with ``async with``."""

    async def test_async_context_manager_returns_self_and_closes(self) -> None:
        client = make_client()
        async with client as ctx:
            assert ctx is client
        assert client._session is None or client._session.closed


_AUTHORIZE_URL_RE = _re.compile(rf"{_re.escape(_AUTH_BASE)}/authorize.*")
_RESUME_URL_RE = _re.compile(rf"{_re.escape(_AUTH_BASE)}/resume.*")
_LOGIN_HTML_WITH_STATE = (
    '<html><form action="/u/login"><input name="state" value="STATE_VALUE"/>'
    "</form></html>"
)


class TestLogin:
    """Cover the OAuth2 PKCE flow in ``_login`` end to end."""

    async def test_happy_path_stores_token_set(self) -> None:
        client = Client("user@example.com", "password")
        with aioresponses() as m:
            m.get(
                _AUTHORIZE_URL_RE,
                status=200,
                body=_LOGIN_HTML_WITH_STATE,
                headers={"Content-Type": "text/html"},
            )
            m.post(
                _AUTHORIZE_URL_RE,
                status=302,
                headers={"location": "/resume?state=STATE_VALUE"},
            )
            m.get(
                _RESUME_URL_RE,
                status=302,
                headers={
                    "location": "com.onekommafive://callback?code=AUTHCODE&state=STATE_VALUE",
                },
            )
            m.post(
                _TOKEN_URL,
                payload={"access_token": "login-token", "refresh_token": "r"},
                status=200,
            )
            token = await client._login()
        assert token == "login-token"
        assert client._token_set is not None
        assert client._token_set["access_token"] == "login-token"

    async def test_raises_when_authorize_returns_non_200(self) -> None:
        client = Client("user@example.com", "password")
        with aioresponses() as m:
            m.get(_AUTHORIZE_URL_RE, status=500, body="")
            with pytest.raises(AuthenticationError, match="Authorization"):
                await client._login()

    async def test_raises_when_authorize_html_has_no_state(self) -> None:
        client = Client("user@example.com", "password")
        with aioresponses() as m:
            m.get(_AUTHORIZE_URL_RE, status=200, body="<html>no state here</html>")
            with pytest.raises(AuthenticationError, match="state"):
                await client._login()

    async def test_raises_when_credential_post_is_not_302(self) -> None:
        client = Client("user@example.com", "password")
        with aioresponses() as m:
            m.get(_AUTHORIZE_URL_RE, status=200, body=_LOGIN_HTML_WITH_STATE)
            m.post(_AUTHORIZE_URL_RE, status=401, body="bad password")
            with pytest.raises(AuthenticationError, match="Login failed"):
                await client._login()

    async def test_raises_when_resume_is_not_302(self) -> None:
        client = Client("user@example.com", "password")
        with aioresponses() as m:
            m.get(_AUTHORIZE_URL_RE, status=200, body=_LOGIN_HTML_WITH_STATE)
            m.post(
                _AUTHORIZE_URL_RE,
                status=302,
                headers={"location": "/resume?state=STATE_VALUE"},
            )
            m.get(
                _RESUME_URL_RE,
                status=500,
                body="resume error",
            )
            with pytest.raises(AuthenticationError, match="resume"):
                await client._login()

    async def test_raises_when_redirect_has_no_code(self) -> None:
        client = Client("user@example.com", "password")
        with aioresponses() as m:
            m.get(_AUTHORIZE_URL_RE, status=200, body=_LOGIN_HTML_WITH_STATE)
            m.post(
                _AUTHORIZE_URL_RE,
                status=302,
                headers={"location": "/resume?state=STATE_VALUE"},
            )
            m.get(
                _RESUME_URL_RE,
                status=302,
                headers={"location": "com.onekommafive://callback?state=STATE_VALUE"},
            )
            with pytest.raises(AuthenticationError, match="authorisation code"):
                await client._login()

    async def test_raises_when_token_exchange_fails(self) -> None:
        client = Client("user@example.com", "password")
        with aioresponses() as m:
            m.get(_AUTHORIZE_URL_RE, status=200, body=_LOGIN_HTML_WITH_STATE)
            m.post(
                _AUTHORIZE_URL_RE,
                status=302,
                headers={"location": "/resume?state=STATE_VALUE"},
            )
            m.get(
                _RESUME_URL_RE,
                status=302,
                headers={"location": "cb?code=AUTHCODE&state=STATE_VALUE"},
            )
            m.post(_TOKEN_URL, status=400, body="invalid_grant")
            with pytest.raises(AuthenticationError, match="Token exchange"):
                await client._login()
