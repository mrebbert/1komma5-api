"""Named failure-path suite — the SDK's resilience contract in one place.

Individual test modules exercise their own happy paths plus a few
negative tests each. This file collects the degraded-mode guarantees
the SDK makes to callers:

- the error-class hierarchy a caller can rely on when writing
  ``except`` blocks;
- the way :class:`Client.get_token` falls back when refresh fails;
- how :meth:`Client._request` surfaces non-success statuses, empty
  bodies and malformed JSON;
- the resource-method wrapper (e.g. :meth:`System.get_live_overview`)
  propagating the underlying :class:`RequestError` with a label.

If a change here breaks tests, the caller contract moved; update the
docs together with the fix.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from aioresponses import aioresponses

from onekommafive.client import Client
from onekommafive.errors import ApiError, AuthenticationError, RequestError
from onekommafive.system import System
from tests.fixtures import FAKE_ACCESS_TOKEN, make_client

# ---------------------------------------------------------------------------
# 1. Error-class hierarchy contract
# ---------------------------------------------------------------------------


class TestErrorHierarchy:
    """``AuthenticationError`` and ``RequestError`` are both ``ApiError``.

    Callers can therefore write a single ``except ApiError`` block and
    catch every error the SDK raises.
    """

    def test_authentication_error_is_api_error(self) -> None:
        err = AuthenticationError("x")
        assert isinstance(err, ApiError)
        assert isinstance(err, Exception)

    def test_request_error_is_api_error(self) -> None:
        err = RequestError("x")
        assert isinstance(err, ApiError)
        assert isinstance(err, Exception)

    def test_api_error_carries_message_attribute(self) -> None:
        """``str(err)`` and ``err.message`` both yield the stored text."""

        err = ApiError("boom")
        assert str(err) == "boom"
        assert err.message == "boom"

    def test_api_error_defaults_to_empty_string(self) -> None:
        err = ApiError()
        assert err.message == ""


# ---------------------------------------------------------------------------
# 2. Token-refresh fallback contract
# ---------------------------------------------------------------------------


class TestTokenRefreshFallback:
    """When a refresh fails the client logs in again rather than erroring out."""

    async def test_falls_back_to_login_on_refresh_failure(self) -> None:
        client = make_client(token_set={"access_token": "old", "refresh_token": "r"})
        client._is_token_expiring = AsyncMock(return_value=True)
        client._refresh_token = AsyncMock(side_effect=AuthenticationError("expired"))
        client._login = AsyncMock(return_value="fresh")

        token = await client.get_token()

        assert token == "fresh"
        client._login.assert_awaited_once()


# ---------------------------------------------------------------------------
# 3. _request status-code and body contract
# ---------------------------------------------------------------------------


_URL = "https://heartbeat.1komma5grad.com/api/v1/_fp_test"


class TestRequestFailurePaths:
    """``_request`` raises :class:`RequestError` with the custom label."""

    async def test_raises_request_error_on_401(self) -> None:
        client = Client("user@example.com", "password")
        client.get_token = AsyncMock(return_value=FAKE_ACCESS_TOKEN)
        with aioresponses() as m:
            m.get(_URL, status=401, body="unauthorized")
            with pytest.raises(RequestError, match="failure-path: unauthorized"):
                await client._request("GET", _URL, error_label="failure-path")

    async def test_raises_request_error_on_403(self) -> None:
        client = Client("user@example.com", "password")
        client.get_token = AsyncMock(return_value=FAKE_ACCESS_TOKEN)
        with aioresponses() as m:
            m.get(_URL, status=403, body="forbidden")
            with pytest.raises(RequestError, match="forbidden"):
                await client._request("GET", _URL, error_label="failure-path")

    async def test_raises_request_error_on_500(self) -> None:
        client = Client("user@example.com", "password")
        client.get_token = AsyncMock(return_value=FAKE_ACCESS_TOKEN)
        with aioresponses() as m:
            m.get(_URL, status=500, body="internal")
            with pytest.raises(RequestError, match="internal"):
                await client._request("GET", _URL, error_label="failure-path")

    async def test_raises_on_mismatched_expected_status(self) -> None:
        """Setting ``expected_status=201`` and getting 200 is a failure."""

        client = Client("user@example.com", "password")
        client.get_token = AsyncMock(return_value=FAKE_ACCESS_TOKEN)
        with aioresponses() as m:
            m.get(_URL, status=200, body='{"ok": true}')
            with pytest.raises(RequestError):
                await client._request(
                    "GET",
                    _URL,
                    expected_status=201,
                    error_label="expected-201",
                )

    async def test_raises_on_malformed_json_body(self) -> None:
        """A 200 with non-JSON body surfaces as JSONDecodeError, not RequestError.

        Rationale: a non-success status is a protocol failure (``RequestError``);
        a non-JSON body on a success status is a backend contract violation
        and callers should see the raw decoder failure, not a wrapped one.
        """

        import json as json_lib

        client = Client("user@example.com", "password")
        client.get_token = AsyncMock(return_value=FAKE_ACCESS_TOKEN)
        with aioresponses() as m:
            m.get(_URL, status=200, body="not json {{{")
            with pytest.raises(json_lib.JSONDecodeError):
                await client._request("GET", _URL)


# ---------------------------------------------------------------------------
# 4. Resource-method wrapping contract
# ---------------------------------------------------------------------------


class TestResourceErrorLabels:
    """Resource methods propagate ``RequestError`` with a method-specific label."""

    async def test_live_overview_wraps_underlying_error(self) -> None:
        client = Client("user@example.com", "password")
        client.get_token = AsyncMock(return_value=FAKE_ACCESS_TOKEN)
        system = System(client, {"id": "sys-xyz"})
        url = f"{client.HEARTBEAT_API}/api/v3/systems/sys-xyz/live-overview"
        with aioresponses() as m:
            m.get(url, status=500, body="server down")
            with pytest.raises(RequestError, match="Failed to get live overview"):
                await system.get_live_overview()


# ---------------------------------------------------------------------------
# 5. Rate-limit retry contract
# ---------------------------------------------------------------------------


_BQ_RATE_LIMIT_BODY = (
    '{"error_code":70102,"message":"Permission denied submitting query job: '
    'Exceeded rate limits: too many api requests per user per method for this '
    'user_method (JobService.query)."}'
)


class TestRateLimitRetry:
    """Transient vendor-side rate limits are retried with exponential backoff.

    Target scenario: ``/charts/market-prices`` sits in front of BigQuery
    on the vendor side. A burst of concurrent client traffic (Flutter
    app + HA integration + probe) can briefly saturate the shared BQ
    ``JobService.query`` quota and return 403 with ``Exceeded rate
    limits``. The client transparently retries up to three times.
    """

    async def test_retries_on_403_with_rate_limit_body(self, mocker) -> None:
        mocker.patch("asyncio.sleep", new_callable=AsyncMock)
        client = Client("user@example.com", "password")
        client.get_token = AsyncMock(return_value=FAKE_ACCESS_TOKEN)
        with aioresponses() as m:
            m.get(_URL, status=403, body=_BQ_RATE_LIMIT_BODY)
            m.get(_URL, status=200, body='{"ok": true}')
            result = await client._request("GET", _URL)
            assert result == {"ok": True}

    async def test_retries_on_429(self, mocker) -> None:
        mocker.patch("asyncio.sleep", new_callable=AsyncMock)
        client = Client("user@example.com", "password")
        client.get_token = AsyncMock(return_value=FAKE_ACCESS_TOKEN)
        with aioresponses() as m:
            m.get(_URL, status=429, body="rate limited")
            m.get(_URL, status=200, body='{"ok": true}')
            result = await client._request("GET", _URL)
            assert result == {"ok": True}

    async def test_does_not_retry_plain_403(self, mocker) -> None:
        """A 403 without the rate-limit signature stays a hard failure."""
        sleep = mocker.patch("asyncio.sleep", new_callable=AsyncMock)
        client = Client("user@example.com", "password")
        client.get_token = AsyncMock(return_value=FAKE_ACCESS_TOKEN)
        with aioresponses() as m:
            m.get(_URL, status=403, body="forbidden")
            with pytest.raises(RequestError, match="forbidden"):
                await client._request("GET", _URL)
        sleep.assert_not_called()

    async def test_gives_up_after_max_retries(self, mocker) -> None:
        mocker.patch("asyncio.sleep", new_callable=AsyncMock)
        client = Client("user@example.com", "password")
        client.get_token = AsyncMock(return_value=FAKE_ACCESS_TOKEN)
        with aioresponses() as m:
            # 1 original + 3 retries = 4 attempts total, all rate-limited
            for _ in range(4):
                m.get(_URL, status=403, body=_BQ_RATE_LIMIT_BODY)
            with pytest.raises(RequestError, match="Exceeded rate limits"):
                await client._request("GET", _URL)

    async def test_retry_can_be_disabled_per_client(self, mocker) -> None:
        sleep = mocker.patch("asyncio.sleep", new_callable=AsyncMock)
        client = Client(
            "user@example.com", "password", retry_on_rate_limit=False
        )
        client.get_token = AsyncMock(return_value=FAKE_ACCESS_TOKEN)
        with aioresponses() as m:
            m.get(_URL, status=429, body="rate limited")
            with pytest.raises(RequestError, match="rate limited"):
                await client._request("GET", _URL)
        sleep.assert_not_called()

    async def test_retry_after_header_overrides_backoff(self, mocker) -> None:
        sleep = mocker.patch("asyncio.sleep", new_callable=AsyncMock)
        client = Client("user@example.com", "password")
        client.get_token = AsyncMock(return_value=FAKE_ACCESS_TOKEN)
        with aioresponses() as m:
            m.get(
                _URL,
                status=429,
                body="rate limited",
                headers={"Retry-After": "7"},
            )
            m.get(_URL, status=200, body='{"ok": true}')
            await client._request("GET", _URL)
        sleep.assert_awaited_once_with(7.0)
