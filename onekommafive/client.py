"""OAuth2 authentication client for the 1KOMMA5° Heartbeat API.

Authentication uses the OAuth2 Authorization Code flow with PKCE (Proof Key for
Code Exchange), matching the behaviour of the official 1KOMMA5° mobile app.
Tokens are refreshed automatically before they expire.

All I/O is asynchronous via ``aiohttp``. The ``Client`` accepts an optional
:class:`aiohttp.ClientSession` — pass one when running inside Home Assistant
(``homeassistant.helpers.aiohttp_client.async_get_clientsession(hass)``) so the
session lifecycle stays with the host. Without a session, the client owns one
and closes it in :meth:`close` / on ``__aexit__``.

For synchronous callers (scripts, tests), see :mod:`onekommafive.sync`.
"""

from __future__ import annotations

import base64
import datetime
import hashlib
import json
import logging
import re
import secrets
from pathlib import Path
from typing import Any, Self, cast

import aiohttp
import jwt
from jwt import PyJWKSet

from .errors import AuthenticationError, RequestError
from .models import SupportedVersions, User

_LOGGER = logging.getLogger(__name__)

# Aliased so the ``json`` keyword argument on :meth:`Client._request`
# does not shadow the module inside the method body.
json_lib = json

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_AUTH_BASE = "https://auth.1komma5grad.com"
_TOKEN_URL = f"{_AUTH_BASE}/oauth/token"
_AUDIENCE = "https://1komma5grad.com/api"
_JWKS_URL = f"{_AUTH_BASE}/.well-known/jwks.json"

# The client_id is the public identifier registered in the Auth0 tenant for
# the 1KOMMA5° mobile application.
_CLIENT_ID = "zJTm6GFGM5zHcmpl07xTsi6MP0TwRAw6"

# Base64url-encoded JSON metadata required by Auth0 for native app clients.
_AUTH0_CLIENT_HEADER = (
    "eyJuYW1lIjoiYXV0aDAtZmx1dHRlciIsInZlcnNpb24iOiIxLjcuMiIsImVudiI6"
    "eyJzd2lmdCI6IjUueCIsImlPUyI6IjE4LjAiLCJjb3JlIjoiMi43LjIifX0"
)

# The redirect URI registered for the iOS app.
_REDIRECT_URI = (
    "io.onecommafive.my.production.app://"
    "auth.1komma5grad.com/ios/io.onecommafive.my.production.app/callback"
)

# Public API base URLs
HEARTBEAT_API = "https://heartbeat.1komma5grad.com"
_IDENTITY_API = "https://customer-identity.1komma5grad.com"

_DEFAULT_TIMEOUT = aiohttp.ClientTimeout(total=30)


# ---------------------------------------------------------------------------
# PKCE helpers
# ---------------------------------------------------------------------------

def _base64url_encode(data: bytes) -> str:
    """Return a Base64url-encoded string without padding characters."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _generate_code_verifier() -> str:
    """Generate a cryptographically random PKCE code verifier (RFC 7636)."""
    return secrets.token_urlsafe(32)


def _generate_code_challenge(verifier: str) -> str:
    """Derive the S256 PKCE code challenge from *verifier*."""
    digest = hashlib.sha256(verifier.encode("utf-8")).digest()
    return _base64url_encode(digest)


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class Client:
    """Authenticated async HTTP client for the 1KOMMA5° API.

    Handles OAuth2 login, silent token refresh, and token validation.
    All resource classes accept an instance of this class to authenticate
    requests.

    Args:
        username: The e-mail address registered with the 1KOMMA5° account.
        password: The account password.
        session: Optional :class:`aiohttp.ClientSession` to use for all HTTP
            traffic. When ``None`` (default) the client owns its session and
            closes it in :meth:`close` / on ``__aexit__``. Home Assistant
            callers should pass ``async_get_clientsession(hass)``.
        token_cache: Optional path to a JSON file used to persist the OAuth2
            token set across process restarts. When provided, the client
            loads any cached tokens on construction and writes back after
            every successful login or refresh. The file is created with
            ``chmod 600`` and bound to ``username``; cached tokens belonging
            to a different user are ignored.

    Example::

        from onekommafive import Client, Systems

        async with Client("user@example.com", "s3cr3t") as client:
            systems = await Systems(client).get_systems()
            info = await systems[0].info()
    """

    HEARTBEAT_API: str = HEARTBEAT_API
    IDENTITY_API: str = _IDENTITY_API

    def __init__(
        self,
        username: str,
        password: str,
        *,
        session: aiohttp.ClientSession | None = None,
        token_cache: Path | str | None = None,
    ) -> None:
        self._username = username
        self._password = password
        self._token_set: dict[str, Any] | None = None
        self._jwks: PyJWKSet | None = None
        self._session: aiohttp.ClientSession | None = session
        self._own_session: bool = session is None
        self._token_cache_path: Path | None = (
            Path(token_cache).expanduser() if token_cache else None
        )
        if self._token_cache_path is not None:
            self._load_token_cache()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_exc: object) -> None:
        await self.close()

    async def close(self) -> None:
        """Close the owned aiohttp session.

        No-op when the session was injected via the constructor; that
        session's lifecycle belongs to the caller.
        """
        if self._own_session and self._session is not None:
            await self._session.close()
            self._session = None

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def get_token(self) -> str:
        """Return a valid Bearer access token, refreshing or logging in as needed.

        Refreshes automatically within 60 s of expiry; falls back to a full
        re-login if refresh fails.
        """
        if self._token_set is None:
            return await self._login()

        if await self._is_token_expiring(before_seconds=60):
            try:
                return await self._refresh_token()
            except AuthenticationError:
                _LOGGER.debug("Refresh failed for %s, falling back to full login", self._username)
                return await self._login()

        return cast(str, self._token_set["access_token"])

    async def get_user(self) -> User:
        """Fetch the profile of the currently authenticated user."""
        data = await self._request(
            "GET",
            f"{_IDENTITY_API}/api/v1/users/me",
            error_label="Failed to get user",
        )
        return User.from_dict(cast(dict[str, Any], data))

    async def get_supported_versions(self) -> SupportedVersions:
        """Fetch the API compatibility matrix (``b2b``/``b2c`` target and minimum versions).

        Not system-scoped — describes the current API deployment as a whole.
        """
        data = await self._request(
            "GET",
            f"{HEARTBEAT_API}/api/v1/supported-versions",
            error_label="Failed to get supported versions",
        )
        return SupportedVersions.from_dict(cast(dict[str, Any], data))

    async def logout(self) -> None:
        """Invalidate the current session on the Auth0 server.

        Clears the local token cache regardless of the server response.
        """
        session = await self._ensure_session()
        async with session.get(
            f"{_AUTH_BASE}/v2/logout",
            params={"client_id": _CLIENT_ID},
            allow_redirects=False,
            timeout=_DEFAULT_TIMEOUT,
        ) as response:
            status = response.status
            body = await response.text() if status >= 400 else ""
        self._token_set = None
        if status >= 400:
            raise RequestError(f"Failed to logout: {body}")

    # ------------------------------------------------------------------
    # Internal helpers used by other modules
    # ------------------------------------------------------------------

    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Lazily create the owned session on first use."""
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self._session

    async def _auth_headers(self) -> dict[str, str]:
        """Return HTTP headers containing a fresh Bearer token."""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {await self.get_token()}",
        }

    async def _request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        expected_status: int = 200,
        error_label: str = "Request failed",
    ) -> Any:
        """Issue an authenticated HTTP request and return the parsed JSON body.

        Returns ``None`` for empty response bodies (e.g. 201 Created with no body).
        Raises :class:`RequestError` if the response status doesn't match
        ``expected_status``.
        """
        session = await self._ensure_session()
        headers = await self._auth_headers()
        async with session.request(
            method,
            url,
            params=params,
            json=json,
            headers=headers,
            timeout=_DEFAULT_TIMEOUT,
        ) as response:
            if response.status != expected_status:
                text = await response.text()
                raise RequestError(f"{error_label}: {text}")
            if response.content_length == 0:
                return None
            body = await response.read()
            if not body:
                return None
            return json_lib.loads(body)

    # ------------------------------------------------------------------
    # Token management
    # ------------------------------------------------------------------

    async def _get_jwks(self) -> PyJWKSet:
        """Fetch and cache the Auth0 JWK set."""
        if self._jwks is None:
            session = await self._ensure_session()
            async with session.get(_JWKS_URL, timeout=_DEFAULT_TIMEOUT) as resp:
                text = await resp.text()
            self._jwks = PyJWKSet.from_json(text)
        return self._jwks

    async def _decode_token(self) -> dict[str, Any]:
        """Validate and decode the current access token."""
        assert self._token_set is not None
        token = cast(str, self._token_set["access_token"])
        jwks = await self._get_jwks()
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        signing_key = next(
            (k for k in jwks.keys if k.key_id == kid),
            None,
        )
        if signing_key is None:
            raise AuthenticationError("No matching JWK for token 'kid'")
        decoded: dict[str, Any] = jwt.decode(
            jwt=token,
            key=signing_key.key,
            options={"verify_exp": True},
            audience=_AUDIENCE,
            algorithms=["RS256"],
        )
        return decoded

    def _load_token_cache(self) -> None:
        """Populate ``self._token_set`` from the cache file when available.

        Silently ignores: missing file, unreadable file, invalid JSON, and
        cached tokens that belong to a different username (cache files are
        per-user; mixing them is a privacy/security hazard).
        """
        if self._token_cache_path is None or not self._token_cache_path.exists():
            return
        try:
            data = json_lib.loads(self._token_cache_path.read_text())
        except (OSError, ValueError):
            return
        if data.get("_username") != self._username:
            return
        self._token_set = {k: v for k, v in data.items() if not k.startswith("_")}

    def _save_token_cache(self) -> None:
        """Persist ``self._token_set`` to the cache file with ``chmod 600``."""
        if self._token_cache_path is None or self._token_set is None:
            return
        self._token_cache_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {**self._token_set, "_username": self._username}
        self._token_cache_path.write_text(json_lib.dumps(payload))
        self._token_cache_path.chmod(0o600)

    async def _is_token_expiring(self, before_seconds: int) -> bool:
        """Return ``True`` when the access token expires within *before_seconds*.

        Also returns ``True`` if no token is stored or if the token is already
        expired.
        """
        if self._token_set is None:
            return True
        try:
            payload = await self._decode_token()
            expiry_threshold = datetime.datetime.now().timestamp() + before_seconds
            return cast(float, payload["exp"]) < expiry_threshold
        except jwt.exceptions.ExpiredSignatureError:
            return True

    async def _login(self) -> str:
        """Perform a full OAuth2 Authorization Code + PKCE login.

        Mirrors the 1KOMMA5° mobile app flow: authorize → submit credentials
        → follow resume redirect → exchange code for tokens.

        Uses a dedicated aiohttp session for the redirect chain so cookies
        stay isolated from the shared session used for API traffic.
        """
        _LOGGER.debug("Starting OAuth2 PKCE login for %s", self._username)
        verifier = _generate_code_verifier()
        challenge = _generate_code_challenge(verifier)

        jar = aiohttp.CookieJar(unsafe=True)
        async with aiohttp.ClientSession(cookie_jar=jar, timeout=_DEFAULT_TIMEOUT) as auth_session:
            # Step 1 – authorise
            async with auth_session.get(
                f"{_AUTH_BASE}/authorize",
                params={
                    "scope": "openid profile email offline_access",
                    "client_id": _CLIENT_ID,
                    "code_challenge": challenge,
                    "code_challenge_method": "S256",
                    "response_type": "code",
                    "audience": _AUDIENCE,
                    "redirect_uri": _REDIRECT_URI,
                    "state": "",
                    "auth0Client": _AUTH0_CLIENT_HEADER,
                },
            ) as auth_response:
                if auth_response.status != 200:
                    raise AuthenticationError(
                        f"Authorization request failed ({auth_response.status})"
                    )
                auth_url = str(auth_response.url)
                auth_html = await auth_response.text()

            state_match = re.search(r'name="state"\s+value="([^"]+)"', auth_html)
            if state_match is None:
                raise AuthenticationError("Could not parse state from login page")
            state = state_match.group(1).strip()

            # Step 2 – submit credentials
            async with auth_session.post(
                auth_url,
                data={
                    "state": state,
                    "username": self._username,
                    "password": self._password,
                    "action": "default",
                },
                allow_redirects=False,
            ) as login_response:
                if login_response.status != 302:
                    body = await login_response.text()
                    raise AuthenticationError(f"Login failed: {body}")
                resume_location = login_response.headers.get("location", "")

            # Step 3 – follow Auth0 resume redirect
            resume_url = _AUTH_BASE + resume_location
            async with auth_session.get(resume_url, allow_redirects=False) as resume_response:
                if resume_response.status != 302:
                    body = await resume_response.text()
                    raise AuthenticationError(f"Login resume failed: {body}")
                location = resume_response.headers.get("location", "")

            if "code=" not in location:
                raise AuthenticationError("No authorisation code in redirect location")
            code = location.split("code=")[1].split("&")[0]

            # Step 4 – exchange code for tokens
            async with auth_session.post(
                _TOKEN_URL,
                json={
                    "client_id": _CLIENT_ID,
                    "code": code,
                    "code_verifier": verifier,
                    "grant_type": "authorization_code",
                    "redirect_uri": _REDIRECT_URI,
                },
            ) as token_response:
                if token_response.status != 200:
                    body = await token_response.text()
                    raise AuthenticationError(f"Token exchange failed: {body}")
                self._token_set = await token_response.json()

        _LOGGER.debug("OAuth2 PKCE login succeeded for %s", self._username)
        self._save_token_cache()
        assert self._token_set is not None
        return cast(str, self._token_set["access_token"])

    async def _refresh_token(self) -> str:
        """Use the stored refresh token to obtain a new access token."""
        if self._token_set is None:
            raise AuthenticationError("No token set available for refresh")
        if "refresh_token" not in self._token_set:
            raise AuthenticationError("No refresh token found in token set")

        _LOGGER.debug("Refreshing access token for %s", self._username)
        session = await self._ensure_session()
        async with session.post(
            _TOKEN_URL,
            json={
                "client_id": _CLIENT_ID,
                "refresh_token": self._token_set["refresh_token"],
                "grant_type": "refresh_token",
            },
            timeout=_DEFAULT_TIMEOUT,
        ) as response:
            if response.status != 200:
                body = await response.text()
                raise AuthenticationError(f"Token refresh failed: {body}")
            fresh = await response.json()

        # Merge into the existing token set instead of replacing it. Auth0
        # only returns a new refresh_token when server-side rotation is on;
        # otherwise the refresh response omits the field. Overwriting the
        # whole token set would clobber our still-valid refresh_token,
        # forcing a full password login on the next refresh cycle.
        self._token_set = {**self._token_set, **fresh}
        self._save_token_cache()
        return cast(str, self._token_set["access_token"])
