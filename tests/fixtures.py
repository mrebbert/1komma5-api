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
FAKE_CHARGER_ID = "cccccccc-0000-0000-0000-000000000001"
FAKE_HEAT_PUMP_ID = "dddddddd-0000-0000-0000-000000000001"


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
    """Return a system response payload matching the /api/v2/systems/{id} shape."""
    return {
        "id": system_id,
        "systemName": "My Home System",
        "status": "ACTIVE",
        "addressName": None,
        "addressLine1": "Musterstraße 1",
        "addressLine2": None,
        "addressZipCode": "20095",
        "addressCity": "Hamburg",
        "addressCountry": "DE",
        "addressLongitude": 10.0,
        "addressLatitude": 53.5,
        "technicalContactId": "tc-0001",
        "customerId": "cust-0001",
        "dynamicPulseCompatible": True,
        "hasThirdPartySmartMeter": None,
        "thirdPartySmartMeterMeterId": None,
        "thirdPartySmartMeterDeletedAt": None,
        "thirdPartySmartMeterMarketLocationId": None,
        "updatedAt": "2025-10-08T15:28:18.743Z",
        "createdAt": "2025-01-23T08:09:40.042Z",
        "energyTraderActive": True,
        "electricityContractActive": True,
    }


def make_ev_data(
    ev_id: str = FAKE_EV_ID,
    charging_mode: str = "SMART_CHARGE",
    manual_soc: float | None = 0.8,
) -> dict:
    """Return an EV charger response payload matching the actual API shape."""
    data: dict = {
        "id": ev_id,
        "profile": {
            "name": "My Car",
            "manufacturer": " Volkswagen ",
            "model": "Id.4",
            "capacity": {"value": 77000, "unit": "Wh"},
            "averageConsumption": None,
            "minChargingCurrent": {"value": 2, "unit": "A"},
            "safetyRange": {"value": 0, "unit": "km"},
        },
        "manualSocTimestamp": "2026-02-27T17:49:55.213Z",
        "assignedChargerId": "cccccccc-0000-0000-0000-000000000001",
        "chargeSettings": {
            "chargingMode": charging_mode,
            "defaultSoc": 0.35,
            "targetSoc": 0.8,
            "chargingModeUpdatedAt": "2026-02-28T07:35:39.367Z",
            "primaryScheduleDays": [],
            "primaryScheduleDepartureTime": "12:00",
            "primaryScheduleDepartureSoc": 1.0,
            "secondaryScheduleDepartureTime": None,
            "secondaryScheduleDepartureSoc": None,
        },
        "updatedAt": "2026-02-28T07:35:39.367Z",
    }
    if manual_soc is not None:
        data["manualSoc"] = manual_soc
    return data


def make_live_overview_data() -> dict:
    """Return a live-overview response payload matching the actual v3 API shape.

    Power balance: PV 2500 W + grid 0 W − consumption 3000 W = battery −500 W (discharging).
    summaryCards reflects the same balance with direct measurements.
    """
    return {
        "timestamp": "2024-06-01T10:00:00Z",
        "status": "ONLINE",
        "liveHeroView": {
            "selfSufficiency": 0.0,
            "production": {"value": 2500.0, "unit": "W"},
            "consumption": {"value": 3000.0, "unit": "W"},
            "gridConsumption": {"value": 0.0, "unit": "W"},
            "gridFeedIn": {"value": 0.0, "unit": "W"},
            "grid": {"value": 0.0, "unit": "W"},
            "totalStateOfCharge": 0.725,
            "evChargersAggregated": {"power": {"value": 100.0, "unit": "W"}},
            "heatPumpsAggregated": {"power": {"value": 800.0, "unit": "W"}, "powerExternal": None},
            "acsAggregated": {"power": {"value": 200.0, "unit": "W"}},
        },
        "summaryCards": {
            "grid": {"power": {"value": 0.0, "unit": "W"}},
            "battery": {
                "power": {"value": 500.0, "unit": "W"},  # positive = discharging in API convention
                "stateOfCharge": 0.725,
            },
            "photovoltaic": {"production": {"value": 2500.0, "unit": "W"}},
            "household": {"power": {"value": 1900.0, "unit": "W"}},
            "evChargers": [],
            "heatPumps": [],
            "acs": [],
        },
    }


def make_price_data() -> dict:
    """Return a market-prices API response (v4, two hourly slots) matching the full API shape."""
    return {
        "energyMarket": {
            "averagePrice": {"price": {"amount": "0.085", "currency": "EUR"}, "unit": "kWh"},
            "highestPrice": {"price": {"amount": "0.13", "currency": "EUR"}, "unit": "kWh"},
            "lowestPrice": {"price": {"amount": "0.015", "currency": "EUR"}, "unit": "kWh"},
        },
        "energyMarketWithGridCosts": {
            "averagePrice": {"price": {"amount": "0.249", "currency": "EUR"}, "unit": "kWh"},
            "highestPrice": {"price": {"amount": "0.294", "currency": "EUR"}, "unit": "kWh"},
            "lowestPrice": {"price": {"amount": "0.178", "currency": "EUR"}, "unit": "kWh"},
        },
        "energyMarketWithGridCostsAndVat": {
            "averagePrice": {"price": {"amount": "0.29631", "currency": "EUR"}, "unit": "kWh"},
            "highestPrice": {"price": {"amount": "0.34986", "currency": "EUR"}, "unit": "kWh"},
            "lowestPrice": {"price": {"amount": "0.21182", "currency": "EUR"}, "unit": "kWh"},
        },
        "timeseries": {
            "2024-06-01T00:00Z": {
                "marketPrice": "0.08",
                "marketPriceWithVat": "0.0952",
                "marketPriceWithGridCost": "0.244",
                "marketPriceWithGridCostAndVat": "0.29036",
                "gridCosts": "0.12776",
                "gridCostsWithVat": "0.152034",
                "gridConsumption": 0.5,
                "gridFeedIn": 0.1,
            },
            "2024-06-01T01:00Z": {
                "marketPrice": "0.09",
                "marketPriceWithVat": "0.1071",
                "marketPriceWithGridCost": "0.254",
                "marketPriceWithGridCostAndVat": "0.30226",
                "gridCosts": "0.12776",
                "gridCostsWithVat": "0.152034",
                "gridConsumption": 0.8,
                "gridFeedIn": 0.0,
            },
        },
        "timeseriesMetadata": {
            "units": {"price": {"currency": "EUR", "perUnit": "kWh"}, "energy": "kWh"},
        },
        "usesFallbackGridCosts": False,
        "gridCostsComponents": {
            "purchasingCost": {"price": {"amount": "0", "currency": "EUR"}, "unit": "kWh"},
            "energyTax": {"price": {"amount": "0.12776", "currency": "EUR"}, "unit": "kWh"},
            "fixedTariff": {"price": {"amount": "0", "currency": "EUR"}, "unit": "kWh"},
            "dynamicMarkup": {"price": {"amount": "0", "currency": "EUR"}, "unit": "kWh"},
            "feedInRemunerationAdjustment": {"price": {"amount": "0", "currency": "EUR"}, "unit": "kWh"},
        },
        "vat": 0.19,
        "gridCostsTotal": {"price": {"amount": "0.1637", "currency": "EUR"}, "unit": "kWh"},
    }


def make_displayed_ev_charging_modes_data() -> dict:
    """Return a minimal displayed-ev-charging-modes response payload."""
    return {
        "displayedEvChargingModes": [
            {"type": "SMART_CHARGE", "disabled": False},
            {"type": "SOLAR_CHARGE", "disabled": False},
            {"type": "QUICK_CHARGE", "disabled": True},
        ],
        "emsMode": "TOU",
    }


def make_ems_settings_data(override: bool = False) -> dict:
    """Return an EMS settings payload matching the full API shape."""
    return {
        "systemId": FAKE_SYSTEM_ID,
        "createdAt": "2025-01-23T08:09:40.508Z",
        "updatedAt": "2026-02-21T18:28:27.452Z",
        "consentGiven": True,
        "overrideAutoSettings": override,
        "manualSettings": {
            "0": {
                "id": "cccccccc-0000-0000-0000-000000000001",
                "type": "EV_CHARGER",
                "chargerName": "Wallbox",
                "assignedEvId": FAKE_EV_ID,
                "assignedEvName": "Id4",
                "activeChargingMode": "QUICK_CHARGE",
            },
            "1": {
                "type": "BATTERY",
                "enableForecastCharging": False,
            },
            "2": {
                "id": "dddddddd-0000-0000-0000-000000000001",
                "type": "HEAT_PUMP",
                "useSolarSurplus": True,
                "maxSolarSurplusUsage": {"value": 2, "unit": "kW"},
            },
        },
        "timeOfUseEnabled": True,
    }
