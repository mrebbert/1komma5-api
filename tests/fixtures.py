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


def make_system_details_data(system_id: str = FAKE_SYSTEM_ID) -> dict:
    """Return a system details payload matching the /api/v1/systems/{id}/details shape.

    All identifiers and personal data are fully synthetic.
    """
    return {
        "id": system_id,
        "empType": "GRIDX",
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
        "updatedAt": "2026-03-12T21:15:31.358Z",
        "createdAt": "2025-01-23T08:09:40.042Z",
        "technicalContactName": "Example Installer",
        "customer": {
            "id": "cust-0001",
            "firstName": "John",
            "lastName": "Doe",
            "email": "user@example.com",
        },
        "energyTraderActive": True,
        "earliestMeasurement": "2025-01-24",
        "electricityContractActive": True,
        "deviceGateways": [
            {
                "id": "gw-0001-0000-0000-0000-000000000001",
                "gridxStartCode": "0000000000000000",
                "serialNumber": "I000-000-000-000-000-X-X",
                "installationDate": "2025-01-24",
            }
        ],
    }


def make_status_and_assets_data() -> dict:
    """Return a /status-and-assets v2 response with synthetic assets covering all known types."""
    return {
        "status": "CONNECTED",
        "assets": [
            {
                "id": "asset-hyb-0000-0000-0000-000000000001",
                "type": "HYBRID",
                "empType": "GRIDX",
                "connectionStatus": {"status": "CONNECTED"},
                "manufacturer": "Sungrow",
                "model": "SH6.0RT-V112",
                "serialnumber": "A00000000000",
                "firmware": "ARM_SAPPHIRE-H_V11_V01_B",
                "network": {"address": "192.0.2.10"},
            },
            {
                "id": "asset-hp-0000-0000-0000-000000000001",
                "type": "HEAT_PUMP",
                "empType": "GRIDX",
                "connectionStatus": {"status": "CONNECTED"},
                "manufacturer": "Stiebel Eltron",
                "model": "WPMsystem",
                "serialnumber": "mac_00:00:00:00:00:00",
                "network": {"address": "192.0.2.20"},
                "heatPumpMeterType": "HOUSEHOLD",
            },
            {
                "id": "asset-meter-0000-0000-0000-000000000001",
                "type": "METER",
                "empType": "GRIDX",
                "connectionStatus": {"status": "CONNECTED"},
                "manufacturer": "Chint",
                "model": "DTSU666",
                "serialnumber": "A00000000000",
                "network": {"address": "192.0.2.10"},
            },
            {
                "id": "asset-ev-0000-0000-0000-000000000001",
                "type": "EV_CHARGER",
                "empType": "GRIDX",
                "name": "Wallbox",
                "connectionStatus": {"status": "CONNECTED"},
                "manufacturer": "go-e",
                "model": "HOMEfix 11kW",
                "serialnumber": "00000",
                "firmware": "60.4",
                "network": {"address": "192.0.2.30"},
            },
        ],
    }


def make_active_features_data() -> dict:
    """Return an /active-features v1 response."""
    return {
        "features": [
            "DYNAMIC_TARIFF",
            "TIME_OF_USE_OPTIMIZATION",
            "SMART_CHARGING",
        ]
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


def make_energy_data() -> dict:
    """Return an energy response matching the real API shape (v2/v3).

    Timeseries is nested under ``timestampedProductionAndConsumption.data``.
    """
    return {
        "updatedAt": "2026-03-08T14:00:00Z",
        "energyProduced": {"value": 30.76, "unit": "kWh"},
        "selfSufficiencyPercent": 0.61,
        "grid": {
            "feedIn": {"value": 6.76, "unit": "kWh"},
            "supply": {"value": 10.33, "unit": "kWh"},
        },
        "battery": {
            "charge": {"value": 22.42, "unit": "kWh"},
            "discharge": {"value": 14.58, "unit": "kWh"},
        },
        "consumption": {
            "direct": {"value": 4.60, "unit": "kWh"},
            "self": None,
            "total": {"value": 26.50, "unit": "kWh"},
            "consumers": {
                "ev": {"value": 0, "unit": "kWh"},
                "heatPump": {"value": 8.0, "unit": "kWh"},
                "ac": None,
                "household": {"value": 2.5, "unit": "kWh"},
                "battery": {"value": 22.42, "unit": "kWh"},
            },
            "consumersTotal": {
                "ev": {"value": 5.0, "unit": "kWh"},
                "heatPump": {"value": 12.0, "unit": "kWh"},
                "ac": None,
                "household": {"value": 13.5, "unit": "kWh"},
            },
        },
        "heartbeatSavings": {"value": 6.48, "unit": "€"},
        "productionSurplus": None,
        "timestampedProductionAndConsumption": {
            "data": {
                "2026-03-08T12:00Z": {
                    "production": 5.008,
                    "consumption": {
                        "household": 0.267,
                        "householdTotal": 0.602,
                        "ev": 0.0,
                        "evCharge": 0.0,
                        "heatPump": 0.0,
                        "heatPumpTotal": 0.0,
                        "ac": None,
                        "acTotal": None,
                        "battery": 4.688,
                        "direct": 0.267,
                    },
                    "gridSupply": 0.334,
                    "gridFeedIn": 0.053,
                    "batteryStateOfCharge": 0.536,
                    "batteryCharge": 4.688,
                    "batteryDischarge": 0.0,
                },
                "2026-03-08T13:00Z": {
                    "production": 3.5,
                    "consumption": {
                        "household": 0.5,
                        "householdTotal": 1.0,
                        "ev": 1.0,
                        "evCharge": 1.5,
                        "heatPump": 0.0,
                        "heatPumpTotal": 0.0,
                        "ac": None,
                        "acTotal": None,
                        "battery": 2.0,
                        "direct": 1.5,
                    },
                    "gridSupply": 0.5,
                    "gridFeedIn": 0.0,
                    "batteryStateOfCharge": 0.62,
                    "batteryCharge": 2.0,
                    "batteryDischarge": 0.0,
                },
            },
            "metadata": {
                "units": {"production": "kW", "gridSupply": "kW", "gridFeedIn": "kW"},
            },
        },
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


def make_price_customizations_data() -> dict:
    """Return a /price-customizations v2 response payload."""
    return {
        "gridEnergyPrice":       {"price": {"amount": "0.3039", "currency": "EUR"}, "unit": "kWh"},
        "comparisonEnergyPrice": {"price": {"amount": "0.274",  "currency": "EUR"}, "unit": "kWh"},
        "monthlyBasePrice":      {"amount": "13.9", "currency": "EUR"},
    }


def make_comparison_price_data(amount: str = "0.274") -> dict:
    """Return a /comparison-price v2 response payload."""
    return {"comparisonPrice": {"price": {"amount": amount, "currency": "EUR"}, "unit": "kWh"}}


def make_price_guarantee_data(value: int | None = 12) -> dict:
    """Return a /customers/{cid}/price-guarantee v1 response payload."""
    if value is None:
        return {"priceGuaranteeUnit": None, "priceGuaranteeValue": None, "priceGuaranteeVersion": None}
    return {
        "priceGuaranteeUnit": "ct/kWh",
        "priceGuaranteeValue": value,
        "priceGuaranteeVersion": "DE_PRICE_GUARANTEE_V2",
    }


def make_wallboxes_data() -> list[dict]:
    """Return a /devices/ev-chargers v1 response payload (list of wallboxes)."""
    return [
        {
            "gridxHardwareId": "wb-0001-0000-0000-0000-000000000001",
            "name": "Wallbox",
            "assignedEvId": FAKE_EV_ID,
        }
    ]


def make_smart_meter_data() -> dict:
    """Return a /sites/{id}/smart-meter v1 response payload."""
    return {
        "siteId": FAKE_SYSTEM_ID,
        "controlAreaEIC": "10YDE-RWENET---I",
        "controlAreaEIC__metadata": {
            "qualityDescription": "Imported from Enet via address lookup",
            "updatedAt": "2026-01-01T00:00:00.000Z",
        },
        "dsoBdewCode": [
            {
                "validFromDate": "2020-01-01",
                "validUntilDate": "2027-12-31",
                "reference": "9900000000009",
                "__metadata": {"qualityDescription": "Imported", "updatedAt": "2026-01-01T00:00:00.000Z"},
            }
        ],
        "concessionFeeEURperkWh": [
            {
                "validFromDate": "2020-01-01",
                "validUntilDate": "2027-12-31",
                "value": 0.0159,
                "__metadata": {"qualityDescription": "Imported", "updatedAt": "2026-01-01T00:00:00.000Z"},
            }
        ],
    }


def make_monthly_trading_savings_data(value: float | None = 12.83) -> dict:
    """Return a /energy-trader-savings/{site_id}/month v1 response payload."""
    if value is None:
        return {}
    return {"averagePastVariableSavings": {"value": value, "unit": "€"}}


def make_self_sufficiency_events_data() -> dict:
    """Return a /heartbeat-ai/self-sufficiency v1 response payload."""
    return {
        "events": [
            {
                "id": "ss-0000-0000-0000-0000-000000000001",
                "timestamp": "2026-08-01T05:30:00Z",
                "data": {
                    "decision": "BATTERY_DISCHARGE",
                    "from": "2026-08-01T05:30:00Z",
                    "to": "2026-08-01T05:45:00Z",
                    "asset": "BATTERY",
                    "marketPrice": {"value": 33.24, "currency": "EUR"},
                    "energySold": None,
                    "energyBought": None,
                    "totalCost": None,
                    "stateOfCharge": 56,
                },
            }
        ]
    }


def make_site_details_data() -> dict:
    """Return a /sites/{id}/details v2 response payload."""
    return {
        "id": FAKE_SYSTEM_ID,
        "createdAt": "2025-01-23T08:09:40.042Z",
        "updatedAt": "2026-08-01T00:00:00.000Z",
        "siteName": "My Home Site",
        "status": "ACTIVE",
        "empType": "GRIDX",
        "biddingZone": "DE_LU",
        "biddingZoneEic": "10Y1001A1001A82H",
        "emsMode": "TOU",
        "emsState": "OPERATIONAL",
        "emsStateReasons": [],
        "dynamicPulseCompatible": True,
        "addressLine1": "Musterstraße 1",
        "addressLine2": None,
        "addressZipCode": "20095",
        "addressCity": "Hamburg",
        "addressCountry": "DE",
        "addressLatitude": 53.5,
        "addressLongitude": 10.0,
        "customerId": "cust-0001",
        "customer": {
            "id": "cust-0001",
            "firstName": "John",
            "lastName": "Doe",
            "email": "user@example.com",
        },
        "technicalContactId": "tc-0001",
        "technicalContactName": "Example Installer",
        "earliestMeasurement": "2025-01-24",
        "energyTraderActive": True,
        "electricityContractActive": True,
        "impactedByEnwg": False,
        "empReferenceId": "emp-ref-0001",
        "empDetails": {
            "empConnectionId": "gw-0001-0000-0000-0000-000000000001",
            "empConfigurationId": "cfg-0001-0000-0000-0000-000000000001",
            "serialNumber": "I000-000-000-000-000-X-X",
            "startCode": "0000000000000000",
            "installationDate": "2025-01-24",
        },
        "physicalAttributes": {},
    }


def make_customer_data() -> dict:
    """Return a /v3/customers/{id} response payload."""
    return {
        "id": "cust-0001",
        "createdAt": "2025-01-23T08:09:38.762Z",
        "updatedAt": "2026-03-12T21:15:31.061Z",
        "firstName": "John",
        "lastName": "Doe",
        "contactEmail": "user@example.com",
        "contactPhone": "+490000000000",
        "companyName": None,
        "companyTaxId": None,
        "addressName": None,
        "addressLine1": "Musterstraße 1",
        "addressLine2": None,
        "addressZipCode": "20095",
        "addressCity": "Hamburg",
        "addressCountry": "Deutschland",
        "crmContactId": "crm-0001",
        "customerType": "UNKNOWN",
        "title": None,
        "crmBranchLocation": "1KOMMA5° Example",
    }


FAKE_USER_ID = "user-0000-0000-0000-0000-000000000001"


def make_user_data() -> dict:
    """Return a /users/me v1 response payload (minimal, for CLI/system tests)."""
    return {
        "id": FAKE_USER_ID,
        "firstName": "John",
        "lastName": "Doe",
        "email": "user@example.com",
        "status": "ACTIVE",
    }


def make_notifications_data() -> dict:
    """Return a /users/{uid}/notifications/latest v1 response payload."""
    return {
        "data": [
            {
                "id": "n-0000-0000-0000-0000-000000000001",
                "createdAt": "2026-07-31T18:06:38.141Z",
                "updatedAt": "2026-07-31T18:06:38.141Z",
                "systemId": FAKE_SYSTEM_ID,
                "type": "ENERGY_MARKET_UPPER_TARGET_REACHED",
                "userId": FAKE_USER_ID,
                "read": True,
                "notificationDetails": {
                    "settings": {},
                    "meta": {"price": {"value": 20.41, "unit": "ct/kWh"}, "dateTime_utc": "2026-07-31T20:00Z"},
                },
                "dismissed": False,
                "body": "Energiepreise steigen heute um 22:00 auf 20.41 ct/kWh.",
                "title": "Energiepreise steigen",
                "locale": "de",
            }
        ]
    }


def make_notification_settings_data() -> dict:
    """Return a /systems/{id}/users/{uid}/notifications/settings v1 response payload."""
    return {
        "langCode": "de",
        "settings": {
            "CO2_IMPACT": [],
            "BATTERY_SOC": [],
            "BROADCAST_NEW_ELECTRICITY_PRICES": [
                {
                    "subscriptionId": "sub-0001-0000-0000-0000-000000000001",
                    "channels": {"app": True, "push": True, "email": False},
                    "personalizations": {},
                }
            ],
            "SYSTEM_HEALTH": [
                {
                    "subscriptionId": "sub-0002-0000-0000-0000-000000000002",
                    "channels": {"app": True, "push": False, "email": True},
                    "personalizations": {},
                }
            ],
        },
    }


def make_supported_versions_data() -> dict:
    """Return a /v1/supported-versions response payload."""
    return {
        "b2b": {"targetVersion": "1.10.0", "minimumSupportedVersion": "1.12.0"},
        "b2c": {"targetVersion": "1.73.0", "minimumSupportedVersion": "1.73.0"},
    }


def make_impact_overview_data() -> dict:
    """Return an /impact-overview v2 response payload."""
    return {
        "co2Savings":         {"value": 1234.5, "unit": "kg"},
        "co2CollectiveSavings": {"value": 50_000_000.0, "unit": "kg"},
        "co2GlobalSavingsEstimate": {"value": 2_000_000.0, "unit": "tons"},
    }


def make_energy_trader_data() -> dict:
    """Return an /energy-trader v2 response payload."""
    return {
        "energyTrader": {
            "status": "ACTIVE",
            "greenEnergySavings":  {"amount": "1500.75", "currency": "EUR"},
            "energyTraderSavings": {"amount": "125.40", "currency": "EUR"},
        }
    }


def make_heartbeat_ai_summary_data(resolution: str = "1M") -> dict:
    """Return a /heartbeat-ai/summary v2 response payload.

    For ``resolution="1W"`` or ``"1Y"`` the API returns null for
    self-sufficiency and energy-earned blocks; only co2Saved is populated.
    """
    body: dict = {
        "co2Saved": {
            "co2Saved": 210.5,
            "production":        {"value": 580.0, "unit": "kWh"},
            "carTravelEmission": {"value": 825.0, "unit": "km"},
            "socialStanding": None,
        },
        "heartbeatPrice": {"price": {"amount": "0.0745", "currency": "EUR"}, "unit": "kWh"},
        "heartbeatPriceSocialStanding": None,
        "peakPriceAvoided": None,
    }
    if resolution == "1M":
        body["selfSufficiency"] = {
            "percentage": 0.73,
            "bySolar":   {"value": 331.25, "unit": "kWh"},
            "byBattery": {"value": 301.30, "unit": "kWh"},
            "socialStanding": None,
        }
        body["energyEarned"] = {
            "earnedAmount": {"amount": "30.41", "currency": "EUR"},
            "soldEnergy":   {"value": 378.75, "unit": "kWh"},
            "feedInPrice":  {"price": {"amount": "0.0803", "currency": "EUR"}, "unit": "kWh"},
            "socialStanding": None,
        }
    else:
        body["selfSufficiency"] = None
        body["energyEarned"] = None
    return body


def make_energy_savings_data(value: float | None = 39.39) -> dict:
    """Return a /energy-savings v1 response payload."""
    if value is None:
        return {"heartbeatSavings": None}
    return {"heartbeatSavings": {"value": value, "unit": "€"}}


def make_weather_data() -> dict:
    """Return a /weather v1 response payload with two daily summaries and two forecast slots."""
    return {
        "today": {
            "temperatureCelsius": 22.5,
            "precipitationMm": 0.4,
            "precipitationProbability": 30.0,
            "sunshineMinutes": 480.0,
            "sunrise": "2026-06-01T04:52:00Z",
            "sunset": "2026-06-01T19:47:00Z",
            "weatherSymbolId": 2,
        },
        "tomorrow": {
            "temperatureCelsius": 19.0,
            "precipitationMm": 3.2,
            "precipitationProbability": 85.0,
            "sunshineMinutes": 120.0,
            "sunrise": "2026-06-02T04:52:00Z",
            "sunset": "2026-06-02T19:48:00Z",
            "weatherSymbolId": None,
        },
        "fineGrainedForecasts": [
            {
                "periodStart": "2026-06-01T09:00:00Z",
                "temperatureCelsius": 18.0,
                "windSpeed": 3.5,
                "precipitationMm": 0.0,
                "precipitationProbability": 10.0,
                "sunshineMinutes": 165.0,
                "weatherSymbolId": 2,
            },
            {
                "periodStart": "2026-06-01T12:00:00Z",
                "temperatureCelsius": 22.0,
                "windSpeed": 4.1,
                "precipitationMm": 0.2,
                "precipitationProbability": 25.0,
                "sunshineMinutes": 140.0,
                "weatherSymbolId": 3,
            },
        ],
    }


def make_optimizations_data() -> dict:
    """Return a /heartbeat-ai/optimizations v1 response with two decision events."""
    return {
        "events": [
            {
                "id": "opt-0000-0000-0000-0000-000000000001",
                "timestamp": "2026-06-01T10:00:00Z",
                "data": {
                    "decision": "BATTERY_CHARGE_FROM_GRID",
                    "asset": "BATTERY",
                    "from": "2026-06-01T10:00:00Z",
                    "to": "2026-06-01T11:00:00Z",
                    "marketPrice": {"value": "0.075", "currency": "EUR"},
                    "energySold": 0.0,
                    "energyBought": 2.4,
                    "totalCost": 0.18,
                    "stateOfCharge": 42,
                    "log": ["2026-06-01T10:00:00Z", "2026-06-01T10:15:00Z"],
                },
            },
            {
                "id": "opt-0000-0000-0000-0000-000000000002",
                "timestamp": "2026-06-01T11:00:00Z",
                "data": {
                    "decision": "BATTERY_NO_DISCHARGE",
                    "asset": "BATTERY",
                    "from": "2026-06-01T11:00:00Z",
                    "to": "2026-06-01T12:00:00Z",
                    "marketPrice": {"value": None, "currency": "EUR"},
                    "energySold": None,
                    "energyBought": None,
                    "totalCost": None,
                    "stateOfCharge": None,
                    "log": [],
                },
            },
        ]
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
