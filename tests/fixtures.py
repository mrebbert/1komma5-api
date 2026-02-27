"""Shared test fixtures and factory helpers."""

from __future__ import annotations

from unittest.mock import MagicMock

from onekommafive.client import Client


# ---------------------------------------------------------------------------
# A valid (but non-expiring) fake token set – no real signature verification
# happens in unit tests because we mock _decode_token / _is_token_expiring.
# ---------------------------------------------------------------------------

FAKE_ACCESS_TOKEN = "fake.access.token"
FAKE_REFRESH_TOKEN = "fake.refresh.token"

FAKE_TOKEN_SET = {
    "access_token": FAKE_ACCESS_TOKEN,
    "refresh_token": FAKE_REFRESH_TOKEN,
    "token_type": "Bearer",
    "expires_in": 86400,
}

FAKE_SYSTEM_ID = "aaaaaaaa-0000-0000-0000-000000000001"
FAKE_SYSTEM_ID_2 = "bbbbbbbb-0000-0000-0000-000000000002"
NULL_SYSTEM_ID = "00000000-0000-0000-0000-000000000000"

FAKE_EV_ID = "ev-1111-1111-1111-111111111111"


def make_client(token_set: dict | None = None) -> Client:
    """Return a :class:`Client` instance with a pre-loaded token set.

    The PKCE / HTTP login flow is not exercised; token validation is
    intentionally bypassed so tests can focus on API behaviour.
    """
    client = Client(username="user@example.com", password="password")
    client._token_set = token_set or FAKE_TOKEN_SET
    # Prevent real JWT validation by making the expiry check always return False
    client._is_token_expiring = MagicMock(return_value=False)
    return client


def make_system_data(system_id: str = FAKE_SYSTEM_ID) -> dict:
    """Return a minimal system response payload."""
    return {"id": system_id, "name": "My Home System"}


def make_ev_data(
    ev_id: str = FAKE_EV_ID,
    charging_mode: str = "SMART_CHARGE",
    manual_soc: float | None = 0.8,
) -> dict:
    """Return a minimal EV charger response payload."""
    data: dict = {
        "id": ev_id,
        "profile": {"name": "My Car"},
        "chargeSettings": {"chargingMode": charging_mode},
    }
    if manual_soc is not None:
        data["manualSoc"] = manual_soc
    return data


def make_live_overview_data() -> dict:
    """Return a minimal live-overview response payload matching the actual API shape.

    Power balance: PV 2500 W + grid 0 W − consumption 3000 W = battery −500 W (discharging).
    """
    return {
        "timestamp": "2024-06-01T10:00:00Z",
        "status": "ONLINE",
        "liveHeroView": {
            "production": {"value": 2500.0, "unit": "W"},
            "consumption": {"value": 3000.0, "unit": "W"},
            "gridConsumption": {"value": 0.0, "unit": "W"},
            "gridFeedIn": {"value": 0.0, "unit": "W"},
            "grid": {"value": 0.0, "unit": "W"},
            "totalStateOfCharge": 0.725,
        },
    }


def make_price_data() -> dict:
    """Return a minimal market-prices API response (two hourly slots)."""
    return {
        "energyMarket": {
            "averagePrice": 8.5,
            "highestPrice": 13.0,
            "lowestPrice": 1.5,
            "data": {
                "2024-06-01T00:00Z": {"price": 8.0},
                "2024-06-01T01:00Z": {"price": 9.0},
            },
            "metadata": {"units": {"price": "ct/kWh"}},
        },
        "energyMarketWithGridCosts": {
            "averagePrice": 24.9,
            "highestPrice": 29.4,
            "lowestPrice": 17.8,
            "data": {
                "2024-06-01T00:00Z": {"price": 24.4},
                "2024-06-01T01:00Z": {"price": 25.4},
            },
            "metadata": {"units": {"price": "ct/kWh"}},
        },
        "consumption": {
            "data": {"2024-06-01T00:00Z": {"energy": 1.5}},
            "metadata": {"units": {"energy": "kWh"}},
        },
        "feedIn": {
            "data": {"2024-06-01T00:00Z": {"energy": 0.1}},
            "metadata": {"units": {"energy": "kWh"}},
        },
        "usesFallbackGridCosts": False,
        "gridCostsComponents": {
            "purchasingCost": {"value": 0, "unit": "ct/kWh"},
            "energyTax": {"value": 13.756, "unit": "ct/kWh"},
        },
        "vat": 0.19,
        "gridCostsTotal": {"value": 16.37, "unit": "ct/kWh"},
    }


def make_ems_settings_data(override: bool = False) -> dict:
    """Return minimal EMS settings payload."""
    return {"overrideAutoSettings": override, "manualSettings": {}}
