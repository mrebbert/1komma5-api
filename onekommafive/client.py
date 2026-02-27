"""OAuth2 authentication client for the 1KOMMA5° Heartbeat API.

Authentication uses the OAuth2 Authorization Code flow with PKCE (Proof Key for
Code Exchange), matching the behaviour of the official 1KOMMA5° mobile app.
Tokens are refreshed automatically before they expire.
"""

from __future__ import annotations

import base64
import datetime
import hashlib
import secrets
from typing import Any

import jwt
from jwt import PyJWKClient
import requests

from .errors import AuthenticationError, RequestError
from .models import User


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
    """Authenticated HTTP client for the 1KOMMA5° API.

    Handles OAuth2 login, silent token refresh, and token validation.
    All API modules accept an instance of this class to authenticate requests.

    Args:
        username: The e-mail address registered with the 1KOMMA5° account.
        password: The account password.

    Example::

        from onekommafive import Client

        client = Client("user@example.com", "s3cr3t")
        token = client.get_token()   # logs in on first call
    """

    #: Base URL of the Heartbeat REST API – exposed as a class attribute so
    #: that dependent modules (System, EVCharger, …) can build URLs without
    #: importing the module-level constant directly.
    HEARTBEAT_API: str = HEARTBEAT_API

    def __init__(self, username: str, password: str) -> None:
        self._username = username
        self._password = password
        self._token_set: dict[str, Any] | None = None
        self._jwks_client = PyJWKClient(_JWKS_URL)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def get_token(self) -> str:
        """Return a valid Bearer access token, refreshing or logging in as needed.

        The token is refreshed automatically when it is within 60 seconds of
        expiry. If refresh fails the client falls back to a full re-login.

        Returns:
            A JWT access token string suitable for use in an
            ``Authorization: Bearer <token>`` header.

        Raises:
            AuthenticationError: If neither refresh nor login succeeds.
        """
        if self._token_set is None:
            return self._login()

        if self._is_token_expiring(before_seconds=60):
            try:
                return self._refresh_token()
            except AuthenticationError:
                return self._login()

        return self._token_set["access_token"]

    def get_user(self) -> User:
        """Fetch the profile of the currently authenticated user.

        Returns:
            A :class:`~onekommafive.models.User` populated from the identity API.

        Raises:
            RequestError: If the server returns a non-200 response.
        """
        response = requests.get(
            url=f"{_IDENTITY_API}/api/v1/users/me",
            headers=self._auth_headers(),
            timeout=30,
        )
        if response.status_code != 200:
            raise RequestError(f"Failed to get user: {response.text}")
        return User.from_dict(response.json())

    def logout(self) -> None:
        """Invalidate the current session on the Auth0 server.

        Clears the local token cache regardless of the server response.

        Raises:
            RequestError: If the server returns a 4xx or 5xx response.
        """
        response = requests.get(
            url=f"{_AUTH_BASE}/v2/logout",
            params={"client_id": _CLIENT_ID},
            allow_redirects=False,
            timeout=30,
        )
        self._token_set = None
        if response.status_code >= 400:
            raise RequestError(f"Failed to logout: {response.text}")

    # ------------------------------------------------------------------
    # Internal helpers used by other modules
    # ------------------------------------------------------------------

    def _auth_headers(self) -> dict[str, str]:
        """Return HTTP headers containing a fresh Bearer token."""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.get_token()}",
        }

    # ------------------------------------------------------------------
    # Token management
    # ------------------------------------------------------------------

    def _decode_token(self) -> dict[str, Any]:
        """Validate and decode the current access token.

        Returns:
            The decoded JWT payload as a dictionary.

        Raises:
            jwt.exceptions.ExpiredSignatureError: If the token has expired.
            jwt.exceptions.InvalidTokenError: If signature verification fails.
        """
        signing_key = self._jwks_client.get_signing_key_from_jwt(
            self._token_set["access_token"]
        )
        return jwt.decode(
            jwt=self._token_set["access_token"],
            key=signing_key,
            options={"verify_exp": True},
            audience=_AUDIENCE,
            algorithms=["RS256"],
        )

    def _is_token_expiring(self, before_seconds: int) -> bool:
        """Return ``True`` when the access token expires within *before_seconds*.

        Also returns ``True`` if no token is stored or if the token is already
        expired.
        """
        if self._token_set is None:
            return True
        try:
            payload = self._decode_token()
            expiry_threshold = datetime.datetime.now().timestamp() + before_seconds
            return payload["exp"] < expiry_threshold
        except jwt.exceptions.ExpiredSignatureError:
            return True

    def _login(self) -> str:
        """Perform a full OAuth2 Authorization Code + PKCE login.

        The flow mimics the 1KOMMA5° mobile app:

        1. ``GET /authorize`` to obtain the Auth0 state cookie.
        2. ``POST`` credentials to the universal login page.
        3. Follow redirects to extract the authorisation code.
        4. ``POST /oauth/token`` to exchange the code for tokens.

        Returns:
            The new access token string.

        Raises:
            AuthenticationError: If any step fails.
        """
        session = requests.Session()
        verifier = _generate_code_verifier()
        challenge = _generate_code_challenge(verifier)

        # Step 1 – authorise
        auth_response = session.get(
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
            timeout=30,
        )
        if auth_response.status_code != 200:
            raise AuthenticationError(
                f"Authorization request failed ({auth_response.status_code})"
            )

        # Extract the opaque state value embedded in the HTML form
        try:
            state = auth_response.text.split('name="state" value="')[1].split('"')[0].strip()
        except IndexError as exc:
            raise AuthenticationError("Could not parse state from login page") from exc

        # Step 2 – submit credentials
        login_response = session.post(
            auth_response.url,
            data={
                "state": state,
                "username": self._username,
                "password": self._password,
                "action": "default",
            },
            allow_redirects=False,
            timeout=30,
        )
        if login_response.status_code != 302:
            raise AuthenticationError(f"Login failed: {login_response.text}")

        # Step 3 – follow Auth0 resume redirect
        resume_url = _AUTH_BASE + login_response.headers["location"]
        resume_response = session.get(resume_url, allow_redirects=False, timeout=30)
        if resume_response.status_code != 302:
            raise AuthenticationError(f"Login resume failed: {resume_response.text}")

        location = resume_response.headers.get("location", "")
        if "code=" not in location:
            raise AuthenticationError("No authorisation code in redirect location")
        code = location.split("code=")[1].split("&")[0]

        # Step 4 – exchange code for tokens
        token_response = requests.post(
            url=_TOKEN_URL,
            json={
                "client_id": _CLIENT_ID,
                "code": code,
                "code_verifier": verifier,
                "grant_type": "authorization_code",
                "redirect_uri": _REDIRECT_URI,
            },
            timeout=30,
        )
        if token_response.status_code != 200:
            raise AuthenticationError(f"Token exchange failed: {token_response.text}")

        self._token_set = token_response.json()
        return self._token_set["access_token"]

    def _refresh_token(self) -> str:
        """Use the stored refresh token to obtain a new access token.

        Returns:
            The new access token string.

        Raises:
            AuthenticationError: If no refresh token is available or the
                server rejects the refresh request.
        """
        if self._token_set is None:
            raise AuthenticationError("No token set available for refresh")
        if "refresh_token" not in self._token_set:
            raise AuthenticationError("No refresh token found in token set")

        response = requests.post(
            url=_TOKEN_URL,
            json={
                "client_id": _CLIENT_ID,
                "refresh_token": self._token_set["refresh_token"],
                "grant_type": "refresh_token",
            },
            timeout=30,
        )
        if response.status_code != 200:
            raise AuthenticationError(f"Token refresh failed: {response.text}")

        self._token_set = response.json()
        return self._token_set["access_token"]
