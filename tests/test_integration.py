"""Integration tests against the live 1KOMMA5° API.

These tests perform *real* HTTP requests and require valid credentials.
They are skipped automatically when the environment variables are not set,
so they never block CI pipelines that don't provide credentials.

Usage::

    export ONEKOMMAFIVE_USERNAME="user@example.com"
    export ONEKOMMAFIVE_PASSWORD="s3cr3t"
    PYTHONPATH=. ./venv/bin/pytest tests/test_integration.py -v

All tests are read-only – no state is mutated on the account.
"""

from __future__ import annotations

import datetime
import os

import pytest

from onekommafive import Client, Systems
from onekommafive.errors import AuthenticationError
from onekommafive.models import ChargingMode, EmsSettings, LiveOverview, MarketPrices, User

# ---------------------------------------------------------------------------
# Credential fixtures – tests are skipped when env vars are absent
# ---------------------------------------------------------------------------

_MISSING = object()  # sentinel


def _require_env(name: str) -> str:
    value = os.environ.get(name, _MISSING)
    if value is _MISSING:
        pytest.skip(f"Environment variable {name!r} is not set")
    return value  # type: ignore[return-value]


@pytest.fixture(scope="module")
def credentials() -> tuple[str, str]:
    """Return (username, password) from environment variables."""
    username = _require_env("ONEKOMMAFIVE_USERNAME")
    password = _require_env("ONEKOMMAFIVE_PASSWORD")
    return username, password


@pytest.fixture(scope="module")
def client(credentials: tuple[str, str]) -> Client:
    """Return an authenticated Client for the whole test module."""
    username, password = credentials
    c = Client(username, password)
    # Eagerly trigger login so authentication errors surface here
    c.get_token()
    return c


@pytest.fixture(scope="module")
def systems(client: Client):
    """Return all systems accessible to the authenticated user."""
    return Systems(client).get_systems()


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

class TestAuthentication:
    """Verify that login and token management work against the real Auth0 tenant."""

    def test_login_returns_non_empty_token(self, credentials: tuple[str, str]) -> None:
        username, password = credentials
        c = Client(username, password)
        token = c.get_token()
        assert isinstance(token, str)
        assert len(token) > 0

    def test_second_get_token_returns_cached_token(self, client: Client) -> None:
        """Calling get_token() twice must return the same token (no re-login)."""
        token_a = client.get_token()
        token_b = client.get_token()
        assert token_a == token_b

    def test_wrong_password_raises_authentication_error(self, credentials: tuple[str, str]) -> None:
        username, _ = credentials
        c = Client(username, password="definitely-wrong-password")
        with pytest.raises(AuthenticationError):
            c.get_token()


# ---------------------------------------------------------------------------
# User profile
# ---------------------------------------------------------------------------

class TestGetUser:
    """Verify the /users/me endpoint returns a valid user object."""

    def test_returns_user_with_id_and_email(self, client: Client) -> None:
        user = client.get_user()
        assert isinstance(user, User)
        assert len(user.id) > 0
        assert "@" in user.email

    def test_email_matches_login_username(self, client: Client, credentials: tuple[str, str]) -> None:
        username, _ = credentials
        user = client.get_user()
        assert user.email.lower() == username.lower()


# ---------------------------------------------------------------------------
# Systems
# ---------------------------------------------------------------------------

class TestGetSystems:
    """Verify the systems listing endpoint."""

    def test_returns_at_least_one_system(self, systems) -> None:
        assert len(systems) >= 1, "Expected at least one active system on this account"

    def test_all_systems_have_non_empty_ids(self, systems) -> None:
        for system in systems:
            assert len(system.id()) > 0

    def test_no_null_uuid_in_results(self, systems) -> None:
        null_id = "00000000-0000-0000-0000-000000000000"
        for system in systems:
            assert system.id() != null_id

    def test_get_system_by_id_matches_list(self, client: Client, systems) -> None:
        """Fetching a system by ID must return the same system as the list."""
        first = systems[0]
        fetched = Systems(client).get_system(first.id())
        assert fetched.id() == first.id()


# ---------------------------------------------------------------------------
# Live overview
# ---------------------------------------------------------------------------

class TestLiveOverview:
    """Verify the live-overview endpoint for each system."""

    def test_returns_live_overview_instance(self, systems) -> None:
        overview = systems[0].get_live_overview()
        assert isinstance(overview, LiveOverview)

    def test_pv_power_is_numeric_or_none(self, systems) -> None:
        overview = systems[0].get_live_overview()
        assert overview.pv_power is None or isinstance(overview.pv_power, (int, float))

    def test_battery_soc_in_valid_range_or_none(self, systems) -> None:
        """State-of-charge must be between 0 and 100 when a battery is present."""
        overview = systems[0].get_live_overview()
        if overview.battery_soc is not None:
            assert 0.0 <= overview.battery_soc <= 100.0

    def test_raw_payload_is_populated(self, systems) -> None:
        overview = systems[0].get_live_overview()
        assert isinstance(overview.raw, dict)
        assert len(overview.raw) > 0


# ---------------------------------------------------------------------------
# EMS settings
# ---------------------------------------------------------------------------

class TestEmsSettings:
    """Verify the EMS settings endpoint."""

    def test_returns_ems_settings_instance(self, systems) -> None:
        settings = systems[0].get_ems_settings()
        assert isinstance(settings, EmsSettings)

    def test_auto_mode_is_boolean(self, systems) -> None:
        settings = systems[0].get_ems_settings()
        assert isinstance(settings.auto_mode, bool)


# ---------------------------------------------------------------------------
# Electricity prices
# ---------------------------------------------------------------------------

class TestMarketPrices:
    """Verify the market-prices chart endpoint.

    The v4 API requires ISO 8601 ZonedDateTime strings for ``from``/``to``
    and a mandatory resolution (``'1h'`` or ``'15m'``).
    """

    def test_returns_market_prices_instance(self, systems) -> None:
        today = datetime.datetime.now()
        result = systems[0].get_prices(
            start=today - datetime.timedelta(days=2),
            end=today - datetime.timedelta(days=1),
        )
        assert isinstance(result, MarketPrices)
        assert len(result.prices) >= 24, (
            "Expected ≥24 hourly price entries for a 1-day window; API returned fewer."
        )

    def test_prices_have_valid_values(self, systems) -> None:
        today = datetime.datetime.now()
        result = systems[0].get_prices(
            start=today - datetime.timedelta(days=2),
            end=today - datetime.timedelta(days=1),
        )
        assert result.average_price > 0
        for ts, price in result.prices.items():
            assert isinstance(ts, str) and len(ts) > 0
            assert isinstance(price, float)

    def test_hourly_resolution_accepted(self, systems) -> None:
        """resolution='1h' with a 1-day range should succeed."""
        today = datetime.datetime.now()
        result = systems[0].get_prices(
            start=today - datetime.timedelta(days=2),
            end=today - datetime.timedelta(days=1),
            resolution="1h",
        )
        assert isinstance(result, MarketPrices)
        assert len(result.prices) >= 24


# ---------------------------------------------------------------------------
# EV chargers  (skipped per system if none are registered)
# ---------------------------------------------------------------------------

class TestEvChargers:
    """Verify EV charger read operations."""

    def test_get_ev_chargers_returns_list(self, systems) -> None:
        chargers = systems[0].get_ev_chargers()
        assert isinstance(chargers, list)

    def test_ev_charger_properties_are_valid(self, systems) -> None:
        chargers = systems[0].get_ev_chargers()
        if not chargers:
            pytest.skip("No EV chargers registered on this system")

        for charger in chargers:
            assert len(charger.id()) > 0
            assert isinstance(charger.charging_mode(), ChargingMode)
            # name may be None if not configured
            assert charger.name() is None or isinstance(charger.name(), str)

    def test_soc_in_valid_range_when_smart_charge(self, systems) -> None:
        chargers = systems[0].get_ev_chargers()
        if not chargers:
            pytest.skip("No EV chargers registered on this system")

        for charger in chargers:
            soc = charger.current_soc()
            if soc is not None:
                assert 0.0 <= soc <= 100.0
