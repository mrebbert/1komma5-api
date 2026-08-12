# 1KOMMA5° Heartbeat API — curl Reference

Reverse-engineered reference for every endpoint used by the [`onekommafive`](https://pypi.org/project/onekommafive/) Python client.

Requests unless noted send `Authorization: Bearer $BEARER_TOKEN`. All personal identifiers below are anonymised (Erika Mustermann / Musterstraße 1 / Hamburg / DE). Example UUIDs use the placeholder `<uuid>`.

## Table of contents

- [Setup](#setup)
  - [Environment variables](#environment-variables)
  - [Bearer token](#bearer-token)
  - [Base URLs](#base-urls)
  - [Endpoint entry template](#endpoint-entry-template)
- [User and customer](#user-and-customer)
  - [Authenticated user profile](#authenticated-user-profile)
  - [Customer record (v3)](#customer-record-v3)
  - [Price guarantee](#price-guarantee)
  - [Subscriptions](#subscriptions)
- [System and site](#system-and-site)
  - [List systems](#list-systems)
  - [Single system (v4)](#single-system-v4)
  - [System details (v1, extended)](#system-details-v1-extended)
  - [Site details (v2, superset)](#site-details-v2-superset)
  - [Site status and assets](#site-status-and-assets)
  - [Active feature flags](#active-feature-flags)
- [Live data](#live-data)
  - [Live overview](#live-overview)
- [Energy](#energy)
  - [Energy today](#energy-today)
  - [Energy historical](#energy-historical)
  - [Heartbeat savings](#heartbeat-savings)
- [Prices](#prices)
  - [Market prices](#market-prices)
  - [Price customizations](#price-customizations)
  - [Comparison price](#comparison-price)
- [EV chargers and wallbox](#ev-chargers-and-wallbox)
  - [List EV chargers](#list-ev-chargers)
  - [Available charging modes](#available-charging-modes)
  - [Update EV settings](#update-ev-settings)
  - [List wallboxes (hardware)](#list-wallboxes-hardware)
- [Energy management (EMS)](#energy-management-ems)
  - [Get EMS settings](#get-ems-settings)
  - [Set EMS mode](#set-ems-mode)
- [Weather](#weather)
  - [Weather forecast](#weather-forecast)
- [Heartbeat AI](#heartbeat-ai)
  - [Optimizations](#optimizations)
  - [Self-sufficiency events](#self-sufficiency-events)
  - [AI summary](#ai-summary)
- [Analytics](#analytics)
  - [Impact overview (CO2)](#impact-overview-co2)
  - [Energy trader (lifetime)](#energy-trader-lifetime)
  - [Monthly trading savings](#monthly-trading-savings)
  - [Heartbeat prices](#heartbeat-prices)
- [Smart meter](#smart-meter)
  - [Smart meter registration](#smart-meter-registration)
- [Notifications](#notifications)
  - [Latest notifications](#latest-notifications)
  - [Notification settings](#notification-settings)
- [API meta](#api-meta)
  - [Supported versions](#supported-versions)
- [Unit reference](#unit-reference)
- [Known API quirks](#known-api-quirks)

---

## Setup

### Environment variables

```bash
export ONEKOMMAFIVE_USERNAME="user@example.com"
export ONEKOMMAFIVE_PASSWORD="s3cr3t"

# Optional — pin to a specific system UUID (used by the CLI when
# multiple systems are visible to the account).
export ONEKOMMAFIVE_SYSTEM="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
```

### Bearer token

The API accepts a JWT valid for 24 hours. The easiest way to obtain one is via the Python client:

```bash
export BEARER_TOKEN=$(python -c '
from onekommafive import Client
import os
c = Client(os.environ["ONEKOMMAFIVE_USERNAME"], os.environ["ONEKOMMAFIVE_PASSWORD"])
print(c.get_token())
')
```

The token can also be printed once and exported manually for quick tests:

```bash
python -c '
from onekommafive import Client
import os
c = Client(os.environ["ONEKOMMAFIVE_USERNAME"], os.environ["ONEKOMMAFIVE_PASSWORD"])
print(c.get_token())
'
```

### Base URLs

| Subdomain | Purpose |
|-----------|---------|
| `heartbeat.1komma5grad.com/api/` | System, energy, EMS, EV, weather, AI, analytics |
| `customer-identity.1komma5grad.com/api/` | User profile, customer, price guarantee, active features |

`siteId` and `systemId` are the same UUID in this API. The demo system always has ID `00000000-0000-0000-0000-000000000000`.

### Endpoint entry template

Each endpoint below follows the same structure:

- `METHOD /path` header
- One-line purpose
- **Query parameters** table (when any)
- **Request body** (POST / PATCH only)
- **Example** — a runnable curl invocation
- **Response** — anonymised JSON payload
- **Notes** — quirks, gotchas, related endpoints

---

## User and customer

### Authenticated user profile

`GET /api/v1/users/me` — profile of the currently authenticated user, plus a summary of every site they can access.

**Example**

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  https://customer-identity.1komma5grad.com/api/v1/users/me | jq .
```

**Response**

```json
{
  "id": "<uuid>",
  "createdAt": "ISO8601",
  "firstName": "Erika",
  "lastName": "Mustermann",
  "externalId": "auth0|abcdef1234567890",
  "email": "user@example.com",
  "phone": null,
  "status": "ACTIVE",
  "connectedSystems": [
    {
      "systemId": "<uuid>",
      "systemName": "Mustermann",
      "addressName": null,
      "addressLine1": "Musterstraße 1",
      "addressLine2": null,
      "addressZipCode": "20095",
      "addressCity": "Hamburg",
      "addressCountry": "DE",
      "technicalContactId": "<uuid>"
    }
  ]
}
```

**Notes**

- Lives on the `customer-identity` host, not `heartbeat`.
- `connectedSystems` lists every site the caller is authorised for — useful for multi-system accounts (families, installer logins).

---

### Customer record (v3)

`GET /api/v3/customers/$CUSTOMER_ID` — full customer profile; superset of the `customer` block embedded in `/systems/{id}/details`.

`$CUSTOMER_ID` comes from the `customerId` field of `/api/v1/systems/{id}/details`.

**Example**

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  "https://customer-identity.1komma5grad.com/api/v3/customers/$CUSTOMER_ID" | jq .
```

**Response**

```json
{
  "id": "<uuid>",
  "firstName": "Erika",
  "lastName": "Mustermann",
  "contactEmail": "user@example.com",
  "contactPhone": "+490000000000",
  "companyName": null,
  "companyTaxId": null,
  "addressName": null,
  "addressLine1": "Musterstraße 1",
  "addressLine2": null,
  "addressZipCode": "20095",
  "addressCity": "Hamburg",
  "addressCountry": "Deutschland",
  "crmContactId": "<crm-id>",
  "customerType": "UNKNOWN",
  "title": null,
  "crmBranchLocation": "1KOMMA5° <Region>",
  "createdAt": "ISO8601",
  "updatedAt": "ISO8601"
}
```

**Notes**

- Email field is `contactEmail`, not `email` (which is used by the embedded `SystemCustomer`).
- `addressCountry` is a plain-name string (e.g. `"Deutschland"`), **not** an ISO code — differs from `/systems/{id}` which returns `"DE"`.
- `customerType` observed only as `"UNKNOWN"` so far; likely also `"PRIVATE"` / `"BUSINESS"`.
- `crmBranchLocation` is the assigned 1KOMMA5° branch office (e.g. `"1KOMMA5° Moers"`).

---

### Price guarantee

`GET /api/v1/customers/$CUSTOMER_ID/price-guarantee?systemId=$ONEKOMMAFIVE_SYSTEM` — contractual electricity-price guarantee.

**Query parameters**

| Name | Required | Description |
|------|----------|-------------|
| `systemId` | yes | System UUID. Path takes `customerId`, but the required query parameter is confusingly named `systemId` (not `customerId`, not `siteId`). Omitting it returns HTTP 400. |

**Example**

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  "https://customer-identity.1komma5grad.com/api/v1/customers/$CUSTOMER_ID/price-guarantee?systemId=$ONEKOMMAFIVE_SYSTEM" | jq .
```

**Response**

```json
{
  "priceGuaranteeUnit": "ct/kWh",
  "priceGuaranteeValue": 12,
  "priceGuaranteeVersion": "DE_PRICE_GUARANTEE_V2"
}
```

**Notes**

- Lives on the `customer-identity` host.
- Observed versions: `DE_PRICE_GUARANTEE_V2` (Germany). The same version identifier also appears in the `priceGuaranteeVersion` field of individual subscription records.

---

### Subscriptions

`GET /api/v1/customers/$CUSTOMER_ID/subscriptions` — all active service contracts for a customer. Typical composition: an electricity contract (`DYNAMIC_PULSE`), a smart-meter contract (`SMART_METER`), a platform-access contract (`HEARTBEAT`), and a trading contract (`ENERGY_TRADER`).

**Example**

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  "https://customer-identity.1komma5grad.com/api/v1/customers/$CUSTOMER_ID/subscriptions" | jq .
```

**Response** (excerpt — one DYNAMIC_PULSE contract; PII fields anonymised)

```json
{
  "data": [
    {
      "id": "<uuid>",
      "type": "DYNAMIC_PULSE",
      "status": "ACTIVE",
      "customerId": "<uuid>",
      "siteId": "<uuid>",
      "countryCode": "DE",
      "createdAt": "ISO8601",
      "updatedAt": "ISO8601",
      "signedDate": "ISO8601",
      "startDate": "ISO8601",
      "endDate": null,

      "price": 0,
      "currency": "EURO",
      "billingFrequency": "MONTHLY",
      "renewal": "AUTOMATIC",
      "noticePeriodInterval": "MONTHS",
      "noticePeriodNumber": 1,
      "paymentMethod": "DIRECT_DEBIT",
      "paymentIban": "<IBAN>",

      "electricityContractNumber": "<number>",
      "marketLocationId": "<11-digit-id>",
      "priceGuaranteeUnit": "ct/kWh",
      "priceGuaranteeValue": 12,
      "priceGuaranteeVersion": "DE_PRICE_GUARANTEE_V2",
      "heartbeatPriceGuarantee": "NONE",

      "deliveryAddressStreet": "Musterstraße",
      "deliveryAddressHouseNumber": "1",
      "deliveryAddressZipCode": "20095",
      "deliveryAddressCity": "Hamburg",

      "termsAndConditionsLink": "https://1k5.link/tos-dynamic-pulse",

      "statusHistory": [ /* contract state-transition history */ ],
      "metadata": {
        "version": "1",
        "payload": {
          /* Full Zoho booking record: IBAN, former supplier, hardware
             selection, feature flags, address, salutation, delivery
             preferences, Lumenaza IDs — all PII */
        }
      },
      "crmDealId": null,
      "lumenazaContractId": "<id>",
      "lumenazaConsumerId": "<id>",
      "zohoReferenceId": "<id>"
    }
  ],
  "pageIndex": 0,
  "pageSize": 15,
  "totalPages": 1,
  "totalItems": 4
}
```

Other contract types share the universal fields (`id`, `type`, `status`, `price`, dates, notice period, renewal, `termsAndConditionsLink`) but have type-specific details:

- `SMART_METER` — has `null` price, 24-month notice, plus `meterId`, `supplier`, `deviceManufacturer`, `deviceMeasuringType`, `marketLocationIdConsumption`/`FeedIn`, `crmBranchLocation` (installer name), `meterInstallationDate`.
- `HEARTBEAT` — minimal shape, `price: 0`, `paymentMethod: "NO_PAYMENT"`.
- `ENERGY_TRADER` — typical price 14.99 EUR / month.

**Notes**

- Lives on the `customer-identity` host.
- `$CUSTOMER_ID` comes from the `customerId` field of `/api/v1/systems/{id}/details`.
- **PII handling**: the response mixes universal contract metadata with heavy PII — `paymentIban`, complete delivery/billing addresses, CRM identifiers (`crmDealId`, `zohoReferenceId`, `lumenazaContractId`, `lumenazaConsumerId`, `crmInstallationId`), a `statusHistory` block, and an embedded `metadata.payload` with the full Zoho booking record (IBAN again, former supplier, feature flags, hardware selection). Callers building dashboards should stick to the universal fields; PII should never be logged or shared.
- **SMART_METER duplication**: the same meter details are also served by `/sites/{id}/smart-meter`. Prefer that endpoint if you only need meter data.
- **Invoices endpoint** (`GET /api/v1/customers/{cid}/subscriptions/{sub_id}/invoices`) exists but returns an empty list on accounts without generated invoices. Not documented here until a populated response is available for reference.

---

## System and site

### List systems

`GET /api/v2/systems` — all systems (sites) the authenticated caller has access to, paginated.

**Example**

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  https://heartbeat.1komma5grad.com/api/v2/systems | jq .
```

**Response**

```json
{
  "pageIndex": 0,
  "pageSize": 15,
  "totalItems": 2,
  "totalPages": 1,
  "data": [
    {
      "id": "<uuid>",
      "systemName": "Mustermann",
      "status": "ACTIVE",
      "addressLine1": "Musterstraße 1",
      "addressCity": "Hamburg",
      "addressCountry": "DE",
      "addressLongitude": 0.0,
      "addressLatitude": 0.0,
      "dynamicPulseCompatible": true,
      "deviceGateways": [
        {
          "id": "<uuid>",
          "gridxStartCode": "<hex-token>",
          "serialNumber": "I###-###-###-###-###-P-X",
          "installationDate": "YYYY-MM-DD"
        }
      ]
    }
  ]
}
```

**Notes**

- The list variant carries `deviceGateways` inline. The single-system variant (`v4`) does **not** — use `/details` for those.

---

### Single system (v4)

`GET /api/v4/systems/$ONEKOMMAFIVE_SYSTEM` — static metadata for one system.

**Example**

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  "https://heartbeat.1komma5grad.com/api/v4/systems/$ONEKOMMAFIVE_SYSTEM" | jq .
```

**Notes**

- Does **not** include `deviceGateways`, `energyTraderActive`, or `electricityContractActive`. Those were dropped from v2 to v4 — for the full picture use `/details` (v1).

---

### System details (v1, extended)

`GET /api/v1/systems/$ONEKOMMAFIVE_SYSTEM/details` — richer than the v4 endpoint. Adds `empType`, `technicalContact*`, embedded `customer` block, smart-meter status, `earliestMeasurement`, and installed `deviceGateways`. Also brings back the v2-only `energyTraderActive` / `electricityContractActive`.

**Example**

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  "https://heartbeat.1komma5grad.com/api/v1/systems/$ONEKOMMAFIVE_SYSTEM/details" | jq .
```

**Response**

```json
{
  "id": "<uuid>",
  "empType": "GRIDX",
  "systemName": "Mustermann",
  "status": "ACTIVE",
  "addressName": null,
  "addressLine1": "Musterstraße 1",
  "addressLine2": null,
  "addressZipCode": "20095",
  "addressCity": "Hamburg",
  "addressCountry": "DE",
  "addressLongitude": 0.0,
  "addressLatitude": 0.0,
  "technicalContactId": "<uuid>",
  "technicalContactName": "1KOMMA5° <Region>",
  "customerId": "<uuid>",
  "customer": {
    "id": "<uuid>",
    "firstName": "Erika",
    "lastName": "Mustermann",
    "email": "user@example.com"
  },
  "dynamicPulseCompatible": true,
  "energyTraderActive": true,
  "electricityContractActive": true,
  "hasThirdPartySmartMeter": null,
  "thirdPartySmartMeterMeterId": null,
  "thirdPartySmartMeterDeletedAt": null,
  "thirdPartySmartMeterMarketLocationId": null,
  "earliestMeasurement": "YYYY-MM-DD",
  "createdAt": "ISO8601",
  "updatedAt": "ISO8601",
  "deviceGateways": [
    {
      "id": "<uuid>",
      "gridxStartCode": "<hex-token>",
      "serialNumber": "I000-000-000-000-000-X-X",
      "installationDate": "YYYY-MM-DD"
    }
  ]
}
```

**Notes**

- `empType` describes the energy-management provider; so far only `"GRIDX"` has been observed.
- `gridxStartCode` / `serialNumber` on `deviceGateways` are hardware pairing tokens — **sensitive**, do not log or share.

---

### Site details (v2, superset)

`GET /api/v3/sites/$ONEKOMMAFIVE_SYSTEM/details` — superset of the two `/systems/{id}` endpoints above. Adds bidding zone, EMP connection block, `impactedByEnwg`, grid-connection capacity and — most usefully — the current EMS runtime state (`emsMode`, `emsState`, `emsStateReasons`), which no other endpoint surfaces.

**Example**

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  "https://heartbeat.1komma5grad.com/api/v3/sites/$ONEKOMMAFIVE_SYSTEM/details" | jq .
```

**Response**

```json
{
  "id": "<uuid>",
  "siteName": "Mustermann",
  "status": "ACTIVE",
  "empType": "GRIDX",
  "biddingZone": "DE_LU",
  "biddingZoneEic": "10Y1001A1001A82H",
  "emsMode": "TOU",
  "emsState": "OPERATIONAL",
  "emsStateReasons": [],
  "empDetails": {
    "empConnectionId": "<uuid>",
    "empConfigurationId": "<uuid>",
    "serialNumber": "I000-000-000-000-000-X-X",
    "startCode": "<hex-token>",
    "installationDate": "YYYY-MM-DD"
  },
  "empReferenceId": "<uuid>",
  "gridConnectionPointPhases": 3,
  "maxCurrentPerPhaseAmpere": 63,
  "physicalAttributes": {},
  "addressLine1": "Musterstraße 1",
  "addressZipCode": "20095",
  "addressCity": "Hamburg",
  "addressCountry": "DE",
  "addressLatitude": 0.0,
  "addressLongitude": 0.0,
  "customerId": "<uuid>",
  "customer": {
    "id": "<uuid>",
    "firstName": "Erika",
    "lastName": "Mustermann",
    "email": "user@example.com"
  },
  "technicalContactId": "<uuid>",
  "technicalContactName": "1KOMMA5° <Region>",
  "dynamicPulseCompatible": true,
  "earliestMeasurement": "YYYY-MM-DD",
  "energyTraderActive": true,
  "electricityContractActive": true,
  "impactedByEnwg": false,
  "createdAt": "ISO8601",
  "updatedAt": "ISO8601"
}
```

**Notes**

- `biddingZone` — ENTSO-E bidding zone (Germany + Luxembourg = `DE_LU`).
- `emsMode` — operating mode (`TOU` = time-of-use / Dynamic Pulse).
- `emsState` / `emsStateReasons` — current EMS runtime state (`OPERATIONAL` with an empty reason list has been observed; likely populated with codes during faults).
- `empDetails` carries gateway **pairing values** (`serialNumber`, `startCode`) — sensitive, do not log or share.
- `impactedByEnwg` — German regulatory flag related to the Energiewirtschaftsgesetz (EnWG). **Exact meaning not documented** by the API. Most plausible interpretation: **§14a EnWG** (since 2024-01-01, DSOs may reduce controllable consumption devices — heat pump / wallbox / battery storage / AC ≥ 4.2 kW — during grid stress, in exchange for reduced grid fees). A `true` value would presumably mean the site has at least one such device registered under §14a.
- `gridConnectionPointPhases` / `maxCurrentPerPhaseAmpere` — grid-connection capacity (phase count; max amperes per phase). Both can be `null`.
- `customer` is the short embedded block; for the full record see [Customer record (v3)](#customer-record-v3).
- `earliestMeasurement`, `energyTraderActive`, `electricityContractActive` are also on `/systems/{id}/details` — redundant here but included in one response.
- Does **not** carry `deviceGateways` — use `/systems/{id}/details` for those.
- **v2 and v3 return byte-identical payloads** (verified 2026-08-02) — no reason to switch.

---

### Site status and assets

`GET /api/v3/sites/$ONEKOMMAFIVE_SYSTEM/status-and-assets` — site connection status plus the installed hardware inventory (inverter, heat pump, meter, EV charger).

**Example**

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  "https://heartbeat.1komma5grad.com/api/v3/sites/$ONEKOMMAFIVE_SYSTEM/status-and-assets" | jq .
```

**Response**

```json
{
  "status": "CONNECTED",
  "assets": [
    {
      "id": "<uuid>",
      "type": "HYBRID | HEAT_PUMP | METER | EV_CHARGER",
      "empType": "GRIDX",
      "name": "Wallbox",
      "connectionStatus": { "status": "CONNECTED" },
      "manufacturer": "...",
      "model": "...",
      "serialnumber": "...",
      "firmware": "...",
      "network": { "address": "<local-ip>" },
      "heatPumpMeterType": "HOUSEHOLD"
    }
  ]
}
```

**Notes**

- Type-specific fields:
  - `name` has only been observed on `EV_CHARGER` assets.
  - `firmware` is often missing on `METER` and `HEAT_PUMP`.
  - `heatPumpMeterType` appears only on `HEAT_PUMP` (values e.g. `"HOUSEHOLD"`).
  - **`serialnumber` is lowercase-n in the API** (not `serialNumber`). On heat pumps the value can take the form `mac_<lowercase-mac>`.
- Typical asset composition for a full installation:

  | Type | Manufacturer | Model |
  |------|--------------|-------|
  | `HYBRID` | Sungrow | SH6.0RT-V112 |
  | `HEAT_PUMP` | Stiebel Eltron | WPMsystem |
  | `METER` | Chint | DTSU666 |
  | `EV_CHARGER` | go-e | HOMEfix 11kW |

---

### Active feature flags

`GET /api/v1/customers/$CUSTOMER_ID/sites/$ONEKOMMAFIVE_SYSTEM/active-features` — active feature codes for the given customer + site pair.

`$CUSTOMER_ID` comes from the `customerId` field of `/api/v1/systems/{id}/details`.

**Example**

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  "https://customer-identity.1komma5grad.com/api/v1/customers/$CUSTOMER_ID/sites/$ONEKOMMAFIVE_SYSTEM/active-features" | jq .
```

**Response**

```json
{
  "features": [
    "DYNAMIC_TARIFF",
    "TIME_OF_USE_OPTIMIZATION",
    "SMART_CHARGING"
  ]
}
```

**Notes**

- Lives on the `customer-identity` host, not `heartbeat`.
- Known feature codes (not exhaustive — the list can grow):

  | Code | Meaning |
  |------|---------|
  | `DYNAMIC_TARIFF` | Dynamic electricity tariff is active |
  | `TIME_OF_USE_OPTIMIZATION` | Time-variable tariff optimisation by the EMS |
  | `SMART_CHARGING` | EV smart-charging available |

---

## Live data

### Live overview

`GET /api/v3/systems/$ONEKOMMAFIVE_SYSTEM/live-overview` — real-time energy overview.

**Example**

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  "https://heartbeat.1komma5grad.com/api/v3/systems/$ONEKOMMAFIVE_SYSTEM/live-overview" | jq .
```

**Response** (excerpt)

```json
{
  "timestamp": "ISO8601",
  "status": "ONLINE",
  "liveHeroView": {
    "selfSufficiency": 1,
    "production":      { "value": 0,      "unit": "W" },
    "consumption":     { "value": 666.53, "unit": "W" },
    "gridFeedIn":      { "value": 4.66,   "unit": "W" },
    "gridConsumption": { "value": 0,      "unit": "W" },
    "grid":            { "value": -4.66,  "unit": "W" },
    "totalStateOfCharge": 0.45,
    "evChargersAggregated":  { "power": { "value": 0, "unit": "W" } },
    "heatPumpsAggregated":   { "power": { "value": 0, "unit": "W" } }
  },
  "summaryCards": {
    "grid":         { "power": { "value": -4.66, "unit": "W" } },
    "battery":      { "power": { "value": 671.19, "unit": "W" }, "stateOfCharge": 0.45 },
    "photovoltaic": { "production": { "value": 0, "unit": "W" } },
    "evChargers": [
      {
        "applianceId": "<uuid>",
        "currentSoc": null,
        "power": { "value": 0, "unit": "W" },
        "powerSource": null
      }
    ],
    "heatPumps":  [ { "applianceId": "<uuid>", "power": { "value": 0, "unit": "W" } } ],
    "household":  { "power": { "value": 666.53, "unit": "W" } }
  }
}
```

**Notes**

- All power values are in **Watts** (not kW).
- `grid.value` sign convention: negative = feeding in, positive = drawing from the grid.
- Prefer `summaryCards.battery.power` over `liveHeroView.production`-derived battery estimates (API convention: negative = charging; the client flips the sign to positive-for-charging).

---

## Energy

### Energy today

`GET /api/v2/systems/$ONEKOMMAFIVE_SYSTEM/energy-today` — today's production and consumption plus a timestamped timeseries.

**Query parameters**

| Name | Values | Description |
|------|--------|-------------|
| `resolution` | `1h` (default), `15m` | Time-series bucket size. |

**Example**

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  'https://heartbeat.1komma5grad.com/api/v2/systems/'"$ONEKOMMAFIVE_SYSTEM"'/energy-today?resolution=1h' | jq .
```

**Response** (excerpt)

```json
{
  "energyProduced":  { "value": 30.76, "unit": "kWh" },
  "selfSufficiencyPercent": 0.61,
  "heartbeatSavings": { "value": 6.48, "unit": "€" },
  "grid": {
    "feedIn":  { "value": 6.76,  "unit": "kWh" },
    "supply":  { "value": 10.33, "unit": "kWh" }
  },
  "battery": {
    "charge":    { "value": 22.42, "unit": "kWh" },
    "discharge": { "value": 14.58, "unit": "kWh" }
  },
  "consumption": {
    "direct": { "value": 4.60,  "unit": "kWh" },
    "total":  { "value": 26.50, "unit": "kWh" },
    "consumers": {
      "ev":        { "value": 5.0,  "unit": "kWh" },
      "heatPump":  { "value": 12.0, "unit": "kWh" },
      "household": { "value": 13.5, "unit": "kWh" },
      "battery":   { "value": ...,  "unit": "kWh" }
    }
  },
  "timestampedProductionAndConsumption": {
    "data": {
      "2026-03-08T12:00Z": {
        "production": 5.008,
        "consumption": {
          "household":      0.267,
          "householdTotal": 0.602,
          "ev":             0,
          "evCharge":       0,
          "heatPump":       0,
          "heatPumpTotal":  0,
          "battery":        4.688,
          "direct":         0.267
        },
        "gridSupply":           0.334,
        "gridFeedIn":           0.053,
        "batteryStateOfCharge": 0.536,
        "batteryCharge":        4.688,
        "batteryDischarge":     0
      }
    },
    "metadata": { "units": { "production": "kW", "gridSupply": "kW", "gridFeedIn": "kW" } }
  }
}
```

**Notes**

- Scalar totals are in **kWh**; timeseries values in **kW**.
- `household` vs `householdTotal`: `household` = share sourced directly from PV; `householdTotal` = total consumption from all sources (PV + battery + grid). Same convention for `heatPump`/`heatPumpTotal` and `ev`/`evCharge`.

---

### Energy historical

`GET /api/v3/systems/$ONEKOMMAFIVE_SYSTEM/energy-historical` — historical energy for an inclusive date range. Same payload shape as [Energy today](#energy-today).

**Query parameters**

| Name | Values | Description |
|------|--------|-------------|
| `from` | `YYYY-MM-DD` | Start date. |
| `to`   | `YYYY-MM-DD` | End date. |
| `resolution` | `1h` (default), `15m` | For `15m`, the date range must be a single day. |

**Example**

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  'https://heartbeat.1komma5grad.com/api/v3/systems/'"$ONEKOMMAFIVE_SYSTEM"'/energy-historical?from=2026-03-07&to=2026-03-07&resolution=1h' | jq .
```

**Notes**

- Payload structure is identical to [Energy today](#energy-today).

---

### Heartbeat savings

`GET /api/v1/systems/$ONEKOMMAFIVE_SYSTEM/energy-savings` — aggregated Heartbeat savings (EUR) for a date range as a single value. Useful when the timeseries overhead of `energy-today`/`energy-historical` is not needed.

**Query parameters** (both optional)

| Name | Values | Description |
|------|--------|-------------|
| `from` | `YYYY-MM-DD` | Start date. **Date-only** — passing a time component returns HTTP 400. |
| `to`   | `YYYY-MM-DD` | End date. Same date-only rule. |

Without parameters the endpoint returns a server-side rolling window (undocumented — neither today nor the current month).

**Example**

```bash
# Default rolling window
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  "https://heartbeat.1komma5grad.com/api/v1/systems/$ONEKOMMAFIVE_SYSTEM/energy-savings" | jq .

# Custom date range
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  "https://heartbeat.1komma5grad.com/api/v1/systems/$ONEKOMMAFIVE_SYSTEM/energy-savings?from=2026-07-01&to=2026-07-31" | jq .
```

**Response**

```json
{ "heartbeatSavings": { "value": 175.42, "unit": "€" } }
```

---

## Prices

### Market prices

`GET /api/v4/systems/$ONEKOMMAFIVE_SYSTEM/charts/market-prices` — spot electricity prices with grid-cost and VAT breakdowns.

**Query parameters**

| Name | Values | Description |
|------|--------|-------------|
| `from` | ISO-8601 with millis, e.g. `2026-03-01T00:00:00.000Z` | Start (UTC). |
| `to`   | ISO-8601 with millis, e.g. `2026-03-01T23:59:59.999Z` | End (UTC). |
| `resolution` | `1h`, `15m` | Bucket size. |

**Example**

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  'https://heartbeat.1komma5grad.com/api/v4/systems/'"$ONEKOMMAFIVE_SYSTEM"'/charts/market-prices?from=2026-03-01T00%3A00%3A00.000Z&to=2026-03-01T23%3A59%3A59.999Z&resolution=1h' | jq .
```

**Response**

```json
{
  "energyMarket":                    { "averagePrice": { "price": { "amount": "0.137", "currency": "EUR" }, "unit": "kWh" }, "highestPrice": {}, "lowestPrice": {} },
  "energyMarketWithGridCosts":       {  },
  "energyMarketWithGridCostsAndVat": {  },
  "vat": 0.19,
  "gridCostsTotal": { "price": { "amount": "0.1636964", "currency": "EUR" }, "unit": "kWh" },
  "usesFallbackGridCosts": false,
  "timeseries": {
    "2026-03-10T18:00Z": {
      "marketPrice":                   "0.23715",
      "marketPriceWithVat":            "0.2822085",
      "marketPriceWithGridCost":       "0.37471",
      "marketPriceWithGridCostAndVat": "0.4459049",
      "gridCosts":                     "0.13756",
      "gridConsumption": 0.00956125,
      "gridFeedIn":      0.01150825
    }
  }
}
```

**Notes**

- All prices are delivered as **strings** in **EUR/kWh**.
- Timestamps are UTC. `gridConsumption` / `gridFeedIn` are in kWh.

---

### Price customizations

`GET /api/v2/systems/$ONEKOMMAFIVE_SYSTEM/price-customizations` — user-configured prices (grid price, comparison price, monthly base fee).

**Example**

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  "https://heartbeat.1komma5grad.com/api/v2/systems/$ONEKOMMAFIVE_SYSTEM/price-customizations" | jq .
```

**Response**

```json
{
  "gridEnergyPrice":       { "price": { "amount": "0.3039", "currency": "EUR" }, "unit": "kWh" },
  "comparisonEnergyPrice": { "price": { "amount": "0.274",  "currency": "EUR" }, "unit": "kWh" },
  "monthlyBasePrice":      { "amount": "13.9", "currency": "EUR" }
}
```

**Notes**

- Prices are **strings** (EUR/kWh); `monthlyBasePrice` is in EUR / month.

---

### Comparison price

`GET /api/v2/comparison-price?siteId=$ONEKOMMAFIVE_SYSTEM` — single-value grid-supplier reference price. Equivalent to `comparisonEnergyPrice` from [Price customizations](#price-customizations), without the surrounding envelope.

**Query parameters**

| Name | Required | Description |
|------|----------|-------------|
| `siteId` | yes | Site UUID as a query parameter — **not a path segment**. |

**Example**

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  "https://heartbeat.1komma5grad.com/api/v2/comparison-price?siteId=$ONEKOMMAFIVE_SYSTEM" | jq .
```

**Response**

```json
{ "comparisonPrice": { "price": { "amount": "0.274", "currency": "EUR" }, "unit": "kWh" } }
```

---

## EV chargers and wallbox

### List EV chargers

`GET /api/v1/systems/$ONEKOMMAFIVE_SYSTEM/devices/evs` — the **vehicle-side** charging profiles registered to a system (charging mode, target SoC, departure schedule).

For the physical wallbox hardware, see [List wallboxes (hardware)](#list-wallboxes-hardware).

**Example**

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  "https://heartbeat.1komma5grad.com/api/v1/systems/$ONEKOMMAFIVE_SYSTEM/devices/evs" | jq .
```

**Response** (array)

```json
[
  {
    "id": "<uuid>",
    "profile": {
      "name": "...",
      "manufacturer": "...",
      "model": "...",
      "capacity": { "value": 77000, "unit": "Wh" },
      "minChargingCurrent": { "value": 2, "unit": "A" }
    },
    "manualSoc": 0.5,
    "manualSocTimestamp": "ISO8601",
    "assignedChargerId": "<uuid>",
    "chargeSettings": {
      "defaultSoc": 0.35,
      "targetSoc": 0.8,
      "chargingMode": "SMART_CHARGE",
      "primaryScheduleDays": [],
      "primaryScheduleDepartureTime": "06:30",
      "primaryScheduleDepartureSoc": 1,
      "secondaryScheduleDepartureTime": null,
      "secondaryScheduleDepartureSoc": null
    }
  }
]
```

**Notes**

- **`capacity.unit` is Wh, not kWh** (77 000 Wh = 77 kWh).
- `manualSoc` is a decimal in `[0, 1]` (not a percentage), and is set manually because the wallbox has no SoC feedback channel.

---

### Available charging modes

`GET /api/v1/sites/$ONEKOMMAFIVE_SYSTEM/assets/evs/displayed-ev-charging-modes` — charging modes available at this site and whether each is currently enabled.

Note the `/sites/` prefix (path IDs are the same as for `/systems/`).

**Example**

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  "https://heartbeat.1komma5grad.com/api/v1/sites/$ONEKOMMAFIVE_SYSTEM/assets/evs/displayed-ev-charging-modes" | jq .
```

**Response**

```json
{
  "displayedEvChargingModes": [
    { "type": "SMART_CHARGE", "disabled": false },
    { "type": "SOLAR_CHARGE", "disabled": false },
    { "type": "QUICK_CHARGE", "disabled": false }
  ],
  "emsMode": "TOU"
}
```

**Notes**

- `emsMode: "TOU"` = time-of-use (Dynamic Pulse tariff active, exchange prices drive charging decisions).

---

### Update EV settings

`PATCH /api/v1/systems/$ONEKOMMAFIVE_SYSTEM/devices/evs/$EV_ID` — update charging mode, target SoC, current SoC, or departure time.

Each call sends a partial body matching the target field.

**Set charging mode**

```bash
# Allowed values: SMART_CHARGE | QUICK_CHARGE | SOLAR_CHARGE
curl -s -X PATCH \
  -H "Authorization: Bearer $BEARER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"chargeSettings": {"chargingMode": "SOLAR_CHARGE"}}' \
  "https://heartbeat.1komma5grad.com/api/v1/systems/$ONEKOMMAFIVE_SYSTEM/devices/evs/$EV_ID" | jq .
```

**Set current SoC** (decimal `0.0`–`1.0`)

```bash
curl -s -X PATCH \
  -H "Authorization: Bearer $BEARER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"manualSoc": 0.8}' \
  "https://heartbeat.1komma5grad.com/api/v1/systems/$ONEKOMMAFIVE_SYSTEM/devices/evs/$EV_ID" | jq .
```

**Set target SoC** (decimal `0.0`–`1.0`)

```bash
curl -s -X PATCH \
  -H "Authorization: Bearer $BEARER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"chargeSettings": {"targetSoc": 0.9}}' \
  "https://heartbeat.1komma5grad.com/api/v1/systems/$ONEKOMMAFIVE_SYSTEM/devices/evs/$EV_ID" | jq .
```

**Set primary departure time** (format `HH:MM`)

```bash
curl -s -X PATCH \
  -H "Authorization: Bearer $BEARER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"chargeSettings": {"primaryScheduleDepartureTime": "07:30"}}' \
  "https://heartbeat.1komma5grad.com/api/v1/systems/$ONEKOMMAFIVE_SYSTEM/devices/evs/$EV_ID" | jq .
```

---

### List wallboxes (hardware)

`GET /api/v1/systems/$ONEKOMMAFIVE_SYSTEM/devices/ev-chargers` — the **physical wallbox hardware** assigned to a system (GridX hardware ID, name, currently-paired EV).

Distinct from [List EV chargers](#list-ev-chargers) which returns the vehicle-side profile. `assignedEvId` links to an entry in `/devices/evs`.

**Example**

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  "https://heartbeat.1komma5grad.com/api/v1/systems/$ONEKOMMAFIVE_SYSTEM/devices/ev-chargers" | jq .
```

**Response** (array)

```json
[
  {
    "gridxHardwareId": "<uuid>",
    "name": "Wallbox",
    "assignedEvId": "<uuid>"
  }
]
```

---

## Energy management (EMS)

### Get EMS settings

`GET /api/v1/systems/$ONEKOMMAFIVE_SYSTEM/ems/actions/get-settings` — current EMS configuration and per-device manual settings.

**Example**

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  "https://heartbeat.1komma5grad.com/api/v1/systems/$ONEKOMMAFIVE_SYSTEM/ems/actions/get-settings" | jq .
```

**Response**

```json
{
  "systemId": "<uuid>",
  "consentGiven": true,
  "overrideAutoSettings": false,
  "timeOfUseEnabled": true,
  "manualSettings": {
    "0": {
      "type": "EV_CHARGER",
      "id": "<uuid>",
      "assignedEvId": "<uuid>",
      "activeChargingMode": "SMART_CHARGE"
    },
    "1": {
      "type": "BATTERY",
      "enableForecastCharging": false
    },
    "2": {
      "type": "HEAT_PUMP",
      "id": "<uuid>",
      "useSolarSurplus": true,
      "maxSolarSurplusUsage": { "value": 2, "unit": "kW" }
    }
  }
}
```

**Notes**

- `overrideAutoSettings: false` = AI automatic mode active.
- `manualSettings` uses numeric string keys (`"0"`, `"1"`, `"2"`); use the `type` field for identification.

---

### Set EMS mode

`POST /api/v1/systems/$ONEKOMMAFIVE_SYSTEM/ems/actions/set-manual-override` — switch between automatic and manual override.

**Request body**

```json
{
  "manualSettings": {},
  "overrideAutoSettings": false
}
```

- `overrideAutoSettings: false` → automatic mode.
- `overrideAutoSettings: true`  → manual override.

**Example**

```bash
# Enable automatic mode
curl -s -X POST \
  -H "Authorization: Bearer $BEARER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"overrideAutoSettings": false}' \
  "https://heartbeat.1komma5grad.com/api/v1/systems/$ONEKOMMAFIVE_SYSTEM/ems/actions/set-manual-override" | jq .
```

**Notes**

- Successful response is HTTP **201**, not 200.

---

## Weather

### Weather forecast

`GET /api/v1/systems/$ONEKOMMAFIVE_SYSTEM/weather` — weather forecast for the site location: daily summaries for today + tomorrow, plus 3-hour slots for the next 48 hours.

Primarily used by the AI for PV-yield estimation and charging planning.

**Example**

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  "https://heartbeat.1komma5grad.com/api/v1/systems/$ONEKOMMAFIVE_SYSTEM/weather" | jq .
```

**Response**

```json
{
  "today": {
    "temperatureCelsius": 16.1,
    "precipitationMm": 5.2,
    "precipitationProbability": 86.5,
    "sunshineMinutes": 383.7,
    "sunrise": "2026-03-11T05:57Z",
    "sunset":  "2026-03-11T17:32Z",
    "weatherSymbolId": 5
  },
  "tomorrow": {  },
  "fineGrainedForecasts": [
    {
      "periodStart": "2026-03-11T15:00Z",
      "windSpeed": 3.8,
      "temperatureCelsius": 10.2,
      "weatherSymbolId": 5,
      "sunshineMinutes": 0,
      "precipitationMm": 1.07,
      "precipitationProbability": 51.4
    }
  ]
}
```

**Notes**

- All timestamps in **UTC**. `fineGrainedForecasts` contains 3-hour slots for the next 48 hours.
- `precipitationProbability` is a float in `0–100`.
- `sunshineMinutes` on `today`/`tomorrow` is a full-day forecast (can exceed 600); on slots it's max ~60 minutes (out of 180).
- Symbol `2` (fair) can appear even with low `sunshineMinutes` — it describes broken cloud cover, not necessarily much sunshine.

**Weather symbol IDs**

Night IDs follow the pattern **day-ID + 100** (e.g. `5` → `105`). Night symbols appear in `fineGrainedForecasts` slots after sunset.

| Day ID | Night ID | Meaning |
|--------|----------|---------|
| `1` | `101` | Sunny / clear |
| `2` | `102` | Fair (partly cloudy) |
| `3` | `103` | Changing cloudiness |
| `4` | `104` | Overcast / heavy cloud |
| `5` | `105` | Rain |
| `8` | `108` | Slight cloud with showers |
| `15` | `115` | Heavy rain / showers |

Values derived from observation, not officially documented.

---

## Heartbeat AI

### Optimizations

`GET /api/v1/heartbeat-ai/optimizations` — AI optimisation decisions (battery charge / discharge / EV charge) for a time window.

**Query parameters**

| Name | Required | Description |
|------|----------|-------------|
| `siteId` | yes | Site UUID. |
| `from`   | yes | ISO-8601 with milliseconds, URL-encoded. Format `%Y-%m-%dT%H:%M:%S.000Z`. |
| `to`     | yes | ISO-8601 with milliseconds, URL-encoded. Format `%Y-%m-%dT%H:%M:%S.999Z`. |

**Example**

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  'https://heartbeat.1komma5grad.com/api/v1/heartbeat-ai/optimizations?siteId='"$ONEKOMMAFIVE_SYSTEM"'&from=2026-03-08T00%3A00%3A00.000Z&to=2026-03-08T23%3A59%3A59.999Z' | jq .
```

**Response**

```json
{
  "events": [
    {
      "id": "<uuid>",
      "timestamp": "ISO8601",
      "data": {
        "decision": "BATTERY_CHARGE_FROM_GRID",
        "from": "ISO8601",
        "to": "ISO8601",
        "asset": "BATTERY",
        "marketPrice": { "value": 24.76, "currency": "EUR" },
        "stateOfCharge": 3,
        "log": ["ISO8601", "..."]
      }
    }
  ]
}
```

**Notes**

- Known `decision` values (not exhaustive):

  | Value | Asset | Meaning |
  |-------|-------|---------|
  | `BATTERY_CHARGE_FROM_GRID` | BATTERY | Charge battery from the grid (cheap price) |
  | `BATTERY_NO_DISCHARGE` | BATTERY | Do not discharge battery (price too low) |
  | `EV_CHARGE_FROM_GRID` | EV | Charge EV from the grid |

- `marketPrice.value` is in **EUR/MWh** — but empirically closer to the feed-in / trader-side price than to the spot purchase price. See [Self-sufficiency events](#self-sufficiency-events) for the observed factor ~4-5 delta vs `charts/market-prices`.
- `stateOfCharge` is a **percentage** (0–100).
- `log` contains ISO timestamps of follow-up slots with the same decision.

---

### Self-sufficiency events

`GET /api/v1/heartbeat-ai/self-sufficiency` — AI events that explain self-sufficiency outcomes (typically the granular battery discharge/charge trace).

**Same payload shape** as [Optimizations](#optimizations), but a **different subset** of AI activity — the two are complementary. In a window where `/optimizations` returns `[]`, `/self-sufficiency` can return multiple events.

**Query parameters** — same as [Optimizations](#optimizations).

**Example**

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  'https://heartbeat.1komma5grad.com/api/v1/heartbeat-ai/self-sufficiency?siteId='"$ONEKOMMAFIVE_SYSTEM"'&from=2026-08-01T00%3A00%3A00.000Z&to=2026-08-01T23%3A59%3A59.999Z' | jq .
```

**Response** — identical to [Optimizations](#optimizations).

**Notes on `marketPrice`**

Empirically the values are much lower than the spot price returned by `charts/market-prices` at the same timestamp — a factor of roughly 4–5 lower. Presumably the feed-in / trader-side price used by the Dynamic-Pulse regime, but the API does not document which of the two it is.

Example (author's account):

| Time | AI `marketPrice` (EUR/MWh → ct/kWh) | `charts/market-prices` (ct/kWh) |
|---|---|---|
| 00:15 | 35.30 → 3.53 | 16.27 |
| 03:00 | 34.55 → 3.46 | 15.45 |
| 06:45 | 31.11 → 3.11 | 14.64 |

---

### AI summary

`GET /api/v2/heartbeat-ai/summary` — aggregated Heartbeat-AI metrics for a resolution window: self-sufficiency, feed-in earnings, CO₂ saved, effective Heartbeat price, and peak-price avoidance.

**Query parameters**

| Name | Required | Description |
|------|----------|-------------|
| `siteId` | yes | Site UUID. |
| `resolution` | yes | One of `1W`, `1M`, `1Y`. Any other value returns HTTP 400. |

**Only `resolution=1M` returns all metrics.** `1W` and `1Y` return only `co2Saved`, `production`, `carTravelEmission`; `selfSufficiency` and `energyEarned` come back as `null`.

**Example**

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  "https://heartbeat.1komma5grad.com/api/v2/heartbeat-ai/summary?siteId=$ONEKOMMAFIVE_SYSTEM&resolution=1M" | jq .
```

**Response** (`resolution=1M`)

```json
{
  "selfSufficiency": {
    "percentage": 0.73,
    "bySolar":   { "value": 331.25, "unit": "kWh" },
    "byBattery": { "value": 301.30, "unit": "kWh" },
    "socialStanding": null
  },
  "energyEarned": {
    "earnedAmount": { "amount": "30.41",   "currency": "EUR" },
    "soldEnergy":   { "value": 378.75,     "unit": "kWh" },
    "feedInPrice":  { "price": { "amount": "0.0803", "currency": "EUR" }, "unit": "kWh" },
    "socialStanding": null
  },
  "co2Saved": {
    "co2Saved": 210.5,
    "production":        { "value": 580.0, "unit": "kWh" },
    "carTravelEmission": { "value": 825.0, "unit": "km"  },
    "socialStanding": null
  },
  "heartbeatPrice": { "price": { "amount": "0.0745", "currency": "EUR" }, "unit": "kWh" },
  "heartbeatPriceSocialStanding": null,
  "peakPriceAvoided": {
    "priceAvoided":        { "amount": "22.50", "currency": "EUR" },
    "batteryChargingCost": { "amount": "37.68", "currency": "EUR" },
    "gridChargingCost":    { "amount": "60.18", "currency": "EUR" }
  }
}
```

`peakPriceAvoided` = savings from strategically discharging the battery to avoid expensive grid hours: `priceAvoided` = net saving, `gridChargingCost` = what grid consumption would have cost without the strategy, `batteryChargingCost` = what the strategic battery charging did cost (net saving = grid − battery). Top-level fields of the same name (`priceAvoided`, `batteryChargingCost`, `gridChargingCost`) are empirically always `null` — the actual value sits exclusively in this nested block.

**Response** (`resolution=1W` / `1Y`)

```json
{
  "selfSufficiency": null,
  "energyEarned": null,
  "co2Saved": { "co2Saved": null, "production": {}, "carTravelEmission": {} },
  "heartbeatPrice": {  },
  "peakPriceAvoided": null
}
```

`socialStanding` fields (throughout) presumably contain community percentiles — always observed as `null` so far, possibly feature-flagged or anonymised.

---

## Analytics

### Impact overview (CO2)

`GET /api/v2/systems/$ONEKOMMAFIVE_SYSTEM/impact-overview` — lifetime figures: kg of CO₂ saved for the site, aggregate for the entire customer base, and a global marketing estimate.

The endpoint ignores `from`, `to`, and `resolution` — values are always lifetime totals.

**Example**

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  "https://heartbeat.1komma5grad.com/api/v2/systems/$ONEKOMMAFIVE_SYSTEM/impact-overview" | jq .
```

**Response**

```json
{
  "co2Savings":                { "value": 3099.24,     "unit": "kg" },
  "co2CollectiveSavings":      { "value": 84779526.33, "unit": "kg" },
  "co2GlobalSavingsEstimate":  { "value": 2000000,     "unit": "tons" }
}
```

**Notes**

- `co2GlobalSavingsEstimate` is a marketing figure (tons), not a site-specific measurement.

---

### Energy trader (lifetime)

`GET /api/v2/energy-trader?siteId=$ONEKOMMAFIVE_SYSTEM` — cumulative trading savings for the site. Values accumulate over the site's entire trading history; no date range is supported.

**Query parameters**

| Name | Required | Description |
|------|----------|-------------|
| `siteId` | yes | Site UUID — as a **query parameter**, not a path segment (unlike most heartbeat endpoints). |

**Example**

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  "https://heartbeat.1komma5grad.com/api/v2/energy-trader?siteId=$ONEKOMMAFIVE_SYSTEM" | jq .
```

**Response**

```json
{
  "energyTrader": {
    "status": "ACTIVE",
    "greenEnergySavings":  { "amount": "2678.49", "currency": "EUR" },
    "energyTraderSavings": { "amount": "231.26",  "currency": "EUR" }
  }
}
```

---

### Monthly trading savings

`GET /api/v1/energy-trader-savings/$ONEKOMMAFIVE_SYSTEM/month` — average monthly savings from variable-price trading. Complements the lifetime view of [Energy trader](#energy-trader-lifetime).

**Path parameter caveat:** the segment is the **site ID** (= `$ONEKOMMAFIVE_SYSTEM`), **not** the customer ID, despite the misleading URL structure. Verified live (customer_id → HTTP 403, site_id → 200).

**Example**

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  "https://heartbeat.1komma5grad.com/api/v1/energy-trader-savings/$ONEKOMMAFIVE_SYSTEM/month" | jq .
```

**Response**

```json
{ "averagePastVariableSavings": { "value": 12.83, "unit": "€" } }
```

---

### Heartbeat prices

`GET /api/v3/heartbeat-prices?siteId={id}` — financial breakdown across **five aggregation windows** (`day`, `week`, `month`, `halfYear`, `year`). Each window has the same structure: PV production, grid feed-in, grid consumption, site totals, and the effective per-kWh Heartbeat price. This is the primary economic dashboard endpoint.

**Query parameters**

| Name | Required | Description |
|------|----------|-------------|
| `siteId` | yes | Site UUID as a **query parameter** — not a path segment. |

**Example**

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  "https://heartbeat.1komma5grad.com/api/v3/heartbeat-prices?siteId=$ONEKOMMAFIVE_SYSTEM" | jq .
```

**Response** (one window shown — remaining windows have identical structure)

```json
{
  "day":      { /* … same shape as year, populated for the trailing day … */ },
  "week":     { /* … trailing week … */ },
  "month":    { /* … trailing month … */ },
  "halfYear": { /* … trailing 6 months … */ },
  "year": {
    "vat": 0.19,
    "shouldReportImplausiblePvAndFeedIn": true,
    "shouldReportOverriddenPvCost": false,
    "usesFeedInEarningsAsHbPrice": false,
    "feedInDiscrepancy": 50.46,
    "pvProduction": {
      "energyProduced": { "value": 7212.12, "unit": "kWh" },
      "cost":  { "amount": "360.61", "currency": "EUR" },
      "price": { "price": { "amount": "0.05", "currency": "EUR" }, "unit": "kWh" }
    },
    "gridFeedIn": {
      "energyFedIn":   { "value": 1819.25, "unit": "kWh" },
      "compensation":  { "amount": "146.09", "currency": "EUR" },
      "price":         { "price": { "amount": "0.0803", "currency": "EUR" }, "unit": "kWh" }
    },
    "gridConsumption": {
      "energyConsumed": { "value": 8807.68, "unit": "kWh" },
      "cost":           { "amount": "2377.00", "currency": "EUR" },
      "price":          { "price": { "amount": "0.2699", "currency": "EUR" }, "unit": "kWh" }
    },
    "totalConsumption": { "value": 14200.55, "unit": "kWh" },
    "totalEnergyCost":  { "amount": "2591.52", "currency": "EUR" },
    "heartbeatPrice":   { "price": { "amount": "0.1825", "currency": "EUR" }, "unit": "kWh" },
    "comparisonTariff": { "price": { "amount": "0.2740", "currency": "EUR" }, "unit": "kWh" },
    "gridElectricityCost":  { "amount": "123.30", "currency": "EUR" },
    "energyTaxReduction":   { "amount": "0",      "currency": "EUR" },
    "fixedCostsAndSavings": { "amount": "123.30", "currency": "EUR" },
    "peakShavingSavings": null,
    "swedishCostsAndSavings": null
  }
}
```

**Notes**

**Three distinct price semantics — do not confuse:**

| Field | Meaning |
|-------|---------|
| `pvProduction.price` | Heartbeat's **internal valuation** of own PV production. Empirically constant at `0.05 EUR/kWh` across all windows. **Not a market price** — an accounting convention. |
| `gridFeedIn.price` | The **contractual feed-in tariff** the grid operator pays for exported energy. |
| `gridConsumption.price` | The **effective per-kWh grid-purchase price** averaged over the window (varies with dynamic tariff). |
| `heartbeatPrice.price` | The site's **effective all-in per-kWh price** for consumed energy — reflects the PV/battery/grid mix minus feed-in earnings plus fixed costs. |
| `comparisonTariff.price` | Static grid-supplier reference (grundversorger) used for savings comparisons. |

**VAT convention** (undocumented, working assumption):

The values are presented **1:1 as displayed in the 1KOMMA5° app**. German consumer-app price displays are conventionally **gross** (VAT-inclusive), and `comparisonTariff ≈ 0.274 EUR/kWh` matches typical German utility gross tariffs. A net-vs-gross mismatch between site prices and grundversorger reference would be misleading UX — so the values are **most likely gross**. The `vat: 0.19` field is included but the API does not document whether it has been applied or is informational. If your application is sensitive to gross/net semantics, verify against your electricity invoice.

**Quality flags** (per window):

- `shouldReportImplausiblePvAndFeedIn: true` signals that PV/feed-in values in that window may be implausible (typically appears for `halfYear` and `year` when historical data has gaps).
- `usesFeedInEarningsAsHbPrice` controls whether the `heartbeatPrice` calculation uses the actual feed-in earnings instead of the internal PV valuation.
- `feedInDiscrepancy` — numeric metric of the discrepancy between measured and expected feed-in.

**Regional/feature-flagged** (usually null, structure unknown when populated):

- `peakShavingSavings` — presumably savings from peak-shaving strategy
- `swedishCostsAndSavings` — Sweden-specific cost structure

---

## Smart meter

### Smart meter registration

`GET /api/v1/sites/$ONEKOMMAFIVE_SYSTEM/smart-meter` — regulatory smart-meter registration data: ENTSO-E control-area EIC, DSO BDEW code, municipality concession fee per kWh — each with validity periods.

**Example**

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  "https://heartbeat.1komma5grad.com/api/v1/sites/$ONEKOMMAFIVE_SYSTEM/smart-meter" | jq .
```

**Response**

```json
{
  "siteId": "<uuid>",
  "controlAreaEIC": "10YDE-RWENET---I",
  "controlAreaEIC__metadata": {
    "qualityDescription": "Imported from Enet via address lookup",
    "updatedAt": "ISO8601"
  },
  "dsoBdewCode": [
    {
      "validFromDate": "2020-01-01",
      "validUntilDate": "2027-12-31",
      "reference": "9900000000009",
      "__metadata": { "qualityDescription": "Imported ...", "updatedAt": "ISO8601" }
    }
  ],
  "concessionFeeEURperkWh": [
    {
      "validFromDate": "2020-01-01",
      "validUntilDate": "2027-12-31",
      "value": 0.0159,
      "__metadata": { "qualityDescription": "Imported ...", "updatedAt": "ISO8601" }
    }
  ]
}
```

**Notes**

- `controlAreaEIC` = ENTSO-E control zone (Germany: `10YDE-*` per transmission-system operator — TenneT / 50Hertz / Amprion / RWENET).
- `dsoBdewCode` = 13-digit BDEW code of the distribution-system operator.
- `concessionFeeEURperkWh.value` = municipality concession fee in EUR/kWh.
- Both arrays contain historic entries with `validFromDate` / `validUntilDate`; the current entry is typically the first element.
- `__metadata` blocks document origin and last update — usually `Imported from Enet via address lookup`.

---

## Notifications

### Latest notifications

`GET /api/v1/users/$USER_ID/notifications/latest?systemId=$ONEKOMMAFIVE_SYSTEM` — recent push / in-app notifications for the authenticated user, scoped to one system.

`$USER_ID` comes from `GET /api/v1/users/me`.

**Query parameters**

| Name | Required | Description |
|------|----------|-------------|
| `systemId` | yes | System UUID — omitting it returns HTTP 400. |

**Example**

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  "https://heartbeat.1komma5grad.com/api/v1/users/$USER_ID/notifications/latest?systemId=$ONEKOMMAFIVE_SYSTEM" | jq .
```

**Response**

```json
{
  "data": [
    {
      "id": "<uuid>",
      "createdAt": "ISO8601",
      "updatedAt": "ISO8601",
      "systemId": "<uuid>",
      "userId": "<uuid>",
      "type": "ENERGY_MARKET_UPPER_TARGET_REACHED",
      "read": true,
      "dismissed": false,
      "locale": "de",
      "title": "Energiepreise steigen",
      "body": "Achtung! Die Energiepreise werden heute um 22:00 auf 20.41 ct/kWh steigen. …",
      "notificationDetails": {
        "settings": {},
        "meta": {
          "price": { "value": 20.41, "unit": "ct/kWh" },
          "dateTime_utc": "ISO8601"
        }
      }
    }
  ]
}
```

**Notes**

- `type` values match the categories from [Notification settings](#notification-settings) below.

---

### Notification settings

`GET /api/v1/systems/$ONEKOMMAFIVE_SYSTEM/users/$USER_ID/notifications/settings` — user preferences per notification category with channel toggles (app / push / email).

**Example**

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  "https://heartbeat.1komma5grad.com/api/v1/systems/$ONEKOMMAFIVE_SYSTEM/users/$USER_ID/notifications/settings" | jq .
```

**Response**

```json
{
  "langCode": "de",
  "settings": {
    "CO2_IMPACT": [],
    "BATTERY_SOC": [],
    "BROADCAST_NEW_ELECTRICITY_PRICES": [
      {
        "subscriptionId": "<uuid>",
        "channels": { "app": true, "push": true, "email": false },
        "personalizations": {}
      }
    ],
    "SYSTEM_DATA_COLLECTION_ENDED": [],
    "EV_DYNAMIC_PULSE": [],
    "ENERGY_MARKET_UPPER_TARGET_REACHED": [],
    "ENERGY_MARKET_LOWER_TARGET_REACHED": [],
    "SYSTEM_HEALTH": []
  }
}
```

An empty array per category = **not subscribed**. An entry per category carries the associated subscription ID and the active channels.

**Observed categories** (not exhaustive)

| Category | Meaning |
|----------|---------|
| `CO2_IMPACT` | CO₂ impact milestones |
| `BATTERY_SOC` | Battery SoC thresholds |
| `BROADCAST_NEW_ELECTRICITY_PRICES` | Daily electricity-price forecast broadcast |
| `SYSTEM_DATA_COLLECTION_ENDED` | System-data collection stopped |
| `EV_DYNAMIC_PULSE` | Dynamic-Pulse EV trigger |
| `ENERGY_MARKET_UPPER_TARGET_REACHED` | Price alert — upper threshold |
| `ENERGY_MARKET_LOWER_TARGET_REACHED` | Price alert — lower threshold |
| `SYSTEM_HEALTH` | System health warnings |

---

## API meta

### Supported versions

`GET /api/v1/supported-versions` — not site-scoped meta endpoint returning target and minimum-supported versions for each client channel.

**Example**

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  "https://heartbeat.1komma5grad.com/api/v1/supported-versions" | jq .
```

**Response**

```json
{
  "b2b": { "targetVersion": "1.10.0", "minimumSupportedVersion": "1.12.0" },
  "b2c": { "targetVersion": "1.73.0", "minimumSupportedVersion": "1.73.0" }
}
```

**Notes**

- `b2b` = installer / partner client channel.
- `b2c` = end-user app channel.
- Useful for warning when your own client implementation drops below `minimumSupportedVersion`.

---

## Unit reference

| Endpoint | Unit convention |
|----------|-----------------|
| `live-overview` | **W** (instantaneous power) |
| `energy-today`, `energy-historical` | **kW** (timeseries) / **kWh** (daily totals) |
| `charts/market-prices` | Prices as **string EUR/kWh**, quantities in **kWh** |
| `heartbeat-ai/optimizations`, `heartbeat-ai/self-sufficiency` | **EUR/MWh** (see quirks) |
| `heartbeat-ai/summary` | **kWh** / **EUR** / **kg** CO₂ / **km** car equivalent, prices as **string EUR/kWh** |
| `impact-overview` | **kg** CO₂ (site + collective), **tons** (global estimate) |
| `energy-trader`, `energy-trader-savings/.../month` | **EUR** |
| `heartbeat-prices` | **kWh** / **EUR** / **EUR/kWh** (prices as **string**, most likely gross) |
| `energy-savings` | **EUR** |
| `price-customizations`, `comparison-price` | **String EUR/kWh** (base fee: **EUR/month**) |
| `price-guarantee` | Value per `priceGuaranteeUnit` (e.g. `ct/kWh`) |
| `smart-meter` | Concession fee in **EUR/kWh** |
| `devices/evs` | Capacity in **Wh**, charging current in **A** |
| `ems/actions/get-settings` | **kW** (`maxSolarSurplusUsage`) |

---

## Known API quirks

Consolidated reference of every non-obvious behaviour documented above:

**Query parameters vs path segments**

- `siteId` is a **query parameter** (not a path segment) in: `/energy-trader`, `/comparison-price`, `/heartbeat-ai/summary`, `/heartbeat-ai/optimizations`, `/heartbeat-ai/self-sufficiency`, `/users/{uid}/notifications/latest`.
- In `/customers/{cid}/price-guarantee` the required query parameter is named `systemId` (not `customerId`, not `siteId`), despite the customer scope in the path.
- `/energy-trader-savings/{site_id}/month` takes the **site ID** in the path, not the customer ID.

**Date and time formats**

- `energy-savings` requires **date-only** (`YYYY-MM-DD`) — datetimes with a time component return HTTP 400.
- `heartbeat-ai/optimizations` and `heartbeat-ai/self-sufficiency` require **ISO-8601 with milliseconds** (`%Y-%m-%dT%H:%M:%S.000Z` / `%Y-%m-%dT%H:%M:%S.999Z`), URL-encoded.
- `charts/market-prices` requires ISO-8601 with millisecond precision, URL-encoded.
- `energy-historical` accepts date-only. For `resolution=15m` the range must be a single day.

**Resolution / range constraints**

- `heartbeat-ai/summary`: only `resolution=1M` returns all metrics. `1W` and `1Y` return only `co2Saved` + `production` + `carTravelEmission`; `selfSufficiency` and `energyEarned` are `null`. Any other resolution returns HTTP 400.
- `impact-overview` ignores query parameters (always lifetime).
- `energy-trader` accepts no date range (always lifetime).

**Hosts**

- The `customer-identity` host is used by: `/users/me`, `/customers/{cid}` (v3), `/customers/{cid}/sites/{sid}/active-features`, `/customers/{cid}/price-guarantee`.
- Everything else lives on `heartbeat`.

**Field naming inconsistencies**

- `status-and-assets`: the API returns `serialnumber` in **lowercase-n**, not `serialNumber`. On heat-pump assets the value can take the form `mac_<lowercase-mac>`.
- Customer v3: the email field is `contactEmail`, not `email` (the embedded `SystemCustomer` uses `email`).
- Customer v3: `addressCountry` is a plain-name string (e.g. `"Deutschland"`), not an ISO code — differs from `/systems/{id}` which returns `"DE"`.

**Semantic pitfalls**

- `heartbeat-ai/optimizations` + `heartbeat-ai/self-sufficiency`: `data.marketPrice` is empirically much lower than the spot price from `charts/market-prices` (factor ~4–5). Likely the feed-in / trader-side price rather than the grid-purchase price — not documented by the API.
- `heartbeat-ai/summary` top-level fields `priceAvoided` / `batteryChargingCost` / `gridChargingCost` are empirically always `null`; the populated values sit inside the `peakPriceAvoided` block.
- `/devices/evs` returns the **vehicle-side** profile (charging mode, target SoC, schedules). `/devices/ev-chargers` returns the **physical wallbox hardware**. They are complementary — link them via `assignedEvId`.
- `/sites/{id}/details` **v2 and v3 return byte-identical payloads** (verified 2026-08-02). Do NOT include `deviceGateways` — use `/systems/{id}/details` for those.

**Unit surprises**

- EV `capacity.unit` is **Wh** (not kWh). 77000 Wh = 77 kWh.
- EV `manualSoc` / `targetSoc` / `defaultSoc` are decimals in `[0, 1]` — **not** percentages.
- Weather night-symbol IDs = day-symbol ID + **100**.

**Response-code surprises**

- `POST /ems/actions/set-manual-override` returns HTTP **201** on success, not 200.
