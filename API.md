# 1KOMMA5° API — curl Reference

Alle Endpunkte unter Verwendung von Umgebungsvariablen und einem Bearer-Token.

---

## Umgebungsvariablen setzen

```bash
export ONEKOMMAFIVE_USERNAME="user@example.com"
export ONEKOMMAFIVE_PASSWORD="s3cr3t"

# Optional: bestimmtes System per UUID auswählen (wird von der CLI verwendet)
export ONEKOMMAFIVE_SYSTEM="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
```

---

## Bearer-Token holen

```bash
export BEARER_TOKEN=$(python -c '
from onekommafive import Client
import os
c = Client(os.environ["ONEKOMMAFIVE_USERNAME"], os.environ["ONEKOMMAFIVE_PASSWORD"])
print(c.get_token())
')
```

Der Token ist ein JWT mit einer Gültigkeit von 24 Stunden.
Für schnelle Tests lässt er sich auch einmalig ausgeben und manuell exportieren:

```bash
python -c '
from onekommafive import Client
import os
c = Client(os.environ["ONEKOMMAFIVE_USERNAME"], os.environ["ONEKOMMAFIVE_PASSWORD"])
print(c.get_token())
'
```

---

## Base-URLs

| Subdomain | Zweck |
|-----------|-------|
| `https://customer-identity.1komma5grad.com/api/` | Nutzerverwaltung |
| `https://heartbeat.1komma5grad.com/api/` | Anlagen- und Energiedaten |

`siteId` und `systemId` sind identische UUIDs. Das Demo-System hat immer die ID `00000000-0000-0000-0000-000000000000`.

---

## Bekannte API-Endpunkte

### Authentifizierung & Nutzer

| Methode | URL |
|---------|-----|
| `GET` | `https://customer-identity.1komma5grad.com/api/v1/users/me` |

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  https://customer-identity.1komma5grad.com/api/v1/users/me | jq .
```

Antwortstruktur (Auszug):

```json
{
  "id": "<uuid>",
  "firstName": "...",
  "lastName": "...",
  "externalId": "auth0|...",
  "email": "...",
  "status": "ACTIVE",
  "connectedSystems": [
    {
      "systemId": "<uuid>",
      "systemName": "...",
      "addressLine1": "...",
      "addressZipCode": "...",
      "addressCity": "...",
      "addressCountry": "DE"
    }
  ]
}
```

---

### Systeme

| Methode | URL |
|---------|-----|
| `GET` | `https://heartbeat.1komma5grad.com/api/v2/systems` |
| `GET` | `https://heartbeat.1komma5grad.com/api/v4/systems/$ONEKOMMAFIVE_SYSTEM` |

```bash
# Alle Systeme auflisten
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  https://heartbeat.1komma5grad.com/api/v2/systems | jq .

# Einzelnes System
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  https://heartbeat.1komma5grad.com/api/v4/systems/$ONEKOMMAFIVE_SYSTEM | jq .
```

Antwortstruktur Liste:

```json
{
  "pageIndex": 0,
  "pageSize": 15,
  "totalItems": 2,
  "totalPages": 1,
  "data": [
    {
      "id": "<uuid>",
      "systemName": "...",
      "status": "ACTIVE",
      "addressLine1": "...",
      "addressCity": "...",
      "addressCountry": "DE",
      "addressLongitude": 0.0,
      "addressLatitude": 0.0,
      "dynamicPulseCompatible": true,
      "deviceGateways": [
        {
          "id": "<uuid>",
          "gridxStartCode": "...",
          "serialNumber": "I###-###-###-###-###-P-X",
          "installationDate": "YYYY-MM-DD"
        }
      ]
    }
  ]
}
```

Der Einzelabruf (v4) enthält keine `deviceGateways`. Die Felder `energyTraderActive` und `electricityContractActive` waren in v2 vorhanden, sind in v4 entfallen.

#### Details (v1, erweitert)

Reicher als der v4-Einzelabruf: enthält zusätzlich `empType`, `technicalContact*`, eingebetteten `customer`-Block, Smart-Meter-Status, `earliestMeasurement` sowie die installierten `deviceGateways`. Bringt außerdem `energyTraderActive` und `electricityContractActive` wieder mit, die in v4 entfallen waren.

| Methode | URL |
|---------|-----|
| `GET` | `https://heartbeat.1komma5grad.com/api/v1/systems/$ONEKOMMAFIVE_SYSTEM/details` |

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  "https://heartbeat.1komma5grad.com/api/v1/systems/$ONEKOMMAFIVE_SYSTEM/details" | jq .
```

Antwortstruktur (anonymisiert):

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

Hinweis: `empType` beschreibt den Energy-Management-Provider; bisher nur der Wert `"GRIDX"` beobachtet. Die `gridxStartCode`/Serial der Gateways sind anlagenspezifische Kopplungswerte und sollten nicht protokolliert werden.

---

### Status und Assets (v2)

| Methode | URL |
|---------|-----|
| `GET` | `https://heartbeat.1komma5grad.com/api/v2/sites/$ONEKOMMAFIVE_SYSTEM/status-and-assets` |

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  "https://heartbeat.1komma5grad.com/api/v2/sites/$ONEKOMMAFIVE_SYSTEM/status-and-assets" | jq .
```

Antwortstruktur:

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

Typ-spezifische Felder:

- `name` ist bisher nur bei `EV_CHARGER`-Assets gesehen.
- `firmware` fehlt häufig bei `METER` und `HEAT_PUMP`.
- `heatPumpMeterType` tritt nur bei `HEAT_PUMP` auf (Werte z.B. `"HOUSEHOLD"`).
- `serialnumber` ist im API kleingeschrieben (nicht `serialNumber`); bei `HEAT_PUMP`-Geräten kann der Wert das Format `mac_<lowercase-mac>` haben.

Asset-Typen einer typischen Anlage:

| Typ | Hersteller | Modell |
|-----|-----------|--------|
| `HYBRID` | Sungrow | SH6.0RT-V112 |
| `HEAT_PUMP` | Stiebel Eltron | WPMsystem |
| `METER` | Chint | DTSU666 |
| `EV_CHARGER` | go-e | HOMEfix 11kW |

---

### Aktive Feature-Flags (v1, customer-identity)

Listet die für ein Customer/Site-Paar aktiven Feature-Codes. Anderer Host als die übrigen Endpunkte (`customer-identity` statt `heartbeat`).

| Methode | URL |
|---------|-----|
| `GET` | `https://customer-identity.1komma5grad.com/api/v1/customers/$CUSTOMER_ID/sites/$ONEKOMMAFIVE_SYSTEM/active-features` |

`$CUSTOMER_ID` lässt sich aus dem Feld `customerId` der `/api/v1/systems/{id}/details`-Antwort gewinnen.

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  "https://customer-identity.1komma5grad.com/api/v1/customers/$CUSTOMER_ID/sites/$ONEKOMMAFIVE_SYSTEM/active-features" | jq .
```

Antwortstruktur:

```json
{
  "features": [
    "DYNAMIC_TARIFF",
    "TIME_OF_USE_OPTIMIZATION",
    "SMART_CHARGING"
  ]
}
```

Bekannte Feature-Codes (nicht abschließend — die Liste kann sich erweitern):

| Code | Bedeutung |
|------|-----------|
| `DYNAMIC_TARIFF` | Dynamischer Strompreis-Tarif aktiv |
| `TIME_OF_USE_OPTIMIZATION` | Zeitvariable Tarif-Optimierung durch das EMS |
| `SMART_CHARGING` | EV-Smart-Charging verfügbar |

---

### Live-Übersicht (v3)

| Methode | URL |
|---------|-----|
| `GET` | `https://heartbeat.1komma5grad.com/api/v3/systems/$ONEKOMMAFIVE_SYSTEM/live-overview` |

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  "https://heartbeat.1komma5grad.com/api/v3/systems/$ONEKOMMAFIVE_SYSTEM/live-overview" | jq .
```

Antwortstruktur (Auszug):

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
    "heatPumps": [ { "applianceId": "<uuid>", "power": { "value": 0, "unit": "W" } } ],
    "household":    { "power": { "value": 666.53, "unit": "W" } }
  }
}
```

Hinweis: Alle Leistungswerte in **W** (nicht kW). `grid.value` negativ = Einspeisung, positiv = Netzbezug.

---

### Energie heute (v2)

| Methode | URL |
|---------|-----|
| `GET` | `https://heartbeat.1komma5grad.com/api/v2/systems/$ONEKOMMAFIVE_SYSTEM/energy-today` |

Parameter:

| Parameter | Wert |
|-----------|------|
| `resolution` | `1h` (Standard) oder `15m` |

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  'https://heartbeat.1komma5grad.com/api/v2/systems/'"$ONEKOMMAFIVE_SYSTEM"'/energy-today?resolution=1h' | jq .
```

Antwortstruktur (Auszug):

```json
{
  "energyProduced": { "value": 30.76, "unit": "kWh" },
  "selfSufficiencyPercent": 0.61,
  "heartbeatSavings": { "value": 6.48, "unit": "€" },
  "grid": {
    "feedIn":  { "value": 6.76, "unit": "kWh" },
    "supply":  { "value": 10.33, "unit": "kWh" }
  },
  "battery": {
    "charge":    { "value": 22.42, "unit": "kWh" },
    "discharge": { "value": 14.58, "unit": "kWh" }
  },
  "consumption": {
    "direct": { "value": 4.60, "unit": "kWh" },
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

Unterschied `household` vs. `householdTotal`: `household` = PV-Direktanteil, `householdTotal` = Gesamtverbrauch (PV + Batterie + Netz). Entsprechend für `heatPump`/`heatPumpTotal` und `ev`/`evCharge`.

---

### Energie historisch (v3)

| Methode | URL |
|---------|-----|
| `GET` | `https://heartbeat.1komma5grad.com/api/v3/systems/$ONEKOMMAFIVE_SYSTEM/energy-historical` |

Parameter:

| Parameter | Wert |
|-----------|------|
| `from` | Datum ISO-8601, z. B. `2026-03-07` |
| `to` | Datum ISO-8601, z. B. `2026-03-07` |
| `resolution` | `1h` (Standard) oder `15m` (nur für einen einzelnen Tag) |

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  'https://heartbeat.1komma5grad.com/api/v3/systems/'"$ONEKOMMAFIVE_SYSTEM"'/energy-historical?from=2026-03-07&to=2026-03-07&resolution=1h' | jq .
```

Gleiche Antwortstruktur wie `energy-today`.

---

### Marktpreise (v4)

| Methode | URL |
|---------|-----|
| `GET` | `https://heartbeat.1komma5grad.com/api/v4/systems/$ONEKOMMAFIVE_SYSTEM/charts/market-prices` |

Parameter:

| Parameter | Wert |
|-----------|------|
| `from` | ISO-8601-Zeitstempel, z. B. `2026-03-01T00:00:00.000Z` |
| `to` | ISO-8601-Zeitstempel, z. B. `2026-03-01T23:59:59.999Z` |
| `resolution` | `1h` oder `15m` |

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  'https://heartbeat.1komma5grad.com/api/v4/systems/'"$ONEKOMMAFIVE_SYSTEM"'/charts/market-prices?from=2026-03-01T00%3A00%3A00.000Z&to=2026-03-01T23%3A59%3A59.999Z&resolution=1h' | jq .
```

Antwortstruktur:

```json
{
  "energyMarket":                    { "averagePrice": { "price": { "amount": "0.137", "currency": "EUR" }, "unit": "kWh" }, "highestPrice": {...}, "lowestPrice": {...} },
  "energyMarketWithGridCosts":       { ... },
  "energyMarketWithGridCostsAndVat": { ... },
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

Alle Preise als **String** (EUR/kWh). Zeitstempel in UTC. `gridConsumption`/`gridFeedIn` in kWh.

---

### Wetter (v1)

Liefert eine Wettervorhersage für den Standort der Anlage – Tagesübersicht für heute/morgen sowie eine feingranulare 3-Stunden-Prognose für 48 Stunden. Dient primär der PV-Ertragsprognose und Ladeplanung.

| Methode | URL |
|---------|-----|
| `GET` | `https://heartbeat.1komma5grad.com/api/v1/systems/$ONEKOMMAFIVE_SYSTEM/weather` |

Keine Query-Parameter erforderlich.

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  "https://heartbeat.1komma5grad.com/api/v1/systems/$ONEKOMMAFIVE_SYSTEM/weather" | jq .
```

Antwortstruktur:

```json
{
  "today": {
    "temperatureCelsius": 16.1,       // Tageshöchsttemperatur
    "precipitationMm": 5.2,           // Gesamtniederschlag in mm
    "precipitationProbability": 86.5, // float, 0–100 %
    "sunshineMinutes": 383.7,         // Sonnenscheindauer in Minuten (Vorhersage, kann >600 sein)
    "sunrise": "2026-03-11T05:57Z",   // ISO8601, UTC
    "sunset":  "2026-03-11T17:32Z",
    "weatherSymbolId": 5              // Wettersymbol-Code (s. u.)
  },
  "tomorrow": { ... },                // identische Struktur
  "fineGrainedForecasts": [
    {
      "periodStart": "2026-03-11T15:00Z", // Beginn des 3h-Slots, UTC
      "windSpeed": 3.8,                   // m/s
      "temperatureCelsius": 10.2,
      "weatherSymbolId": 5,
      "sunshineMinutes": 0,               // Sonnenschein im Slot (max. ~60 min bei 3h)
      "precipitationMm": 1.07,
      "precipitationProbability": 51.4    // float, 0–100 %
    }
  ]
}
```

`fineGrainedForecasts` enthält 3-Stunden-Slots für 48 h. Alle Zeitstempel in UTC.

#### Wettersymbol-IDs

Nacht-IDs folgen dem Muster **Tag-ID + 100** (z. B. `5` → `105`). Nacht-Symbole erscheinen in `fineGrainedForecasts`-Slots nach Sonnenuntergang.

| Tag-ID | Nacht-ID | Bedeutung |
|--------|----------|-----------|
| `1` | `101` | Sonnig / klar |
| `2` | `102` | Heiter (leicht bewölkt) |
| `3` | `103` | Wechselnd bewölkt |
| `4` | `104` | Bedeckt / stark bewölkt |
| `5` | `105` | Regen |
| `8` | `108` | Leicht bewölkt mit Schauern |
| `15` | `115` | Starker Regen / Schauer |

Alle Werte durch Beobachtung abgeleitet, nicht offiziell dokumentiert.

Hinweis: Symbol `2` (heiter) kann auch bei niedrigem `sunshineMinutes`-Wert (z. B. 43 min) vergeben werden – es beschreibt aufgelockerte Bewölkung, nicht zwingend viel Sonnenschein.

---

### EV-Lader

| Methode | URL |
|---------|-----|
| `GET` | `https://heartbeat.1komma5grad.com/api/v1/systems/$ONEKOMMAFIVE_SYSTEM/devices/evs` |
| `PATCH` | `https://heartbeat.1komma5grad.com/api/v1/systems/$ONEKOMMAFIVE_SYSTEM/devices/evs/$EV_ID` |

```bash
# Alle EV-Lader abrufen
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  "https://heartbeat.1komma5grad.com/api/v1/systems/$ONEKOMMAFIVE_SYSTEM/devices/evs" | jq .
```

Antwortstruktur (Array):

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

Hinweis: `capacity.unit` ist **Wh** (nicht kWh) – 77.000 Wh = 77 kWh. `manualSoc` wird manuell gesetzt, da die Wallbox keinen SoC-Rückkanal hat.

```bash
# Lademodus setzen (SMART_CHARGE | QUICK_CHARGE | SOLAR_CHARGE)
curl -s -X PATCH \
  -H "Authorization: Bearer $BEARER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"chargeSettings": {"chargingMode": "SOLAR_CHARGE"}}' \
  "https://heartbeat.1komma5grad.com/api/v1/systems/$ONEKOMMAFIVE_SYSTEM/devices/evs/$EV_ID" | jq .

# Aktuellen SoC setzen (Dezimalwert 0.0–1.0)
curl -s -X PATCH \
  -H "Authorization: Bearer $BEARER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"manualSoc": 0.8}' \
  "https://heartbeat.1komma5grad.com/api/v1/systems/$ONEKOMMAFIVE_SYSTEM/devices/evs/$EV_ID" | jq .

# Zielladezustand setzen (Dezimalwert 0.0–1.0)
curl -s -X PATCH \
  -H "Authorization: Bearer $BEARER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"chargeSettings": {"targetSoc": 0.9}}' \
  "https://heartbeat.1komma5grad.com/api/v1/systems/$ONEKOMMAFIVE_SYSTEM/devices/evs/$EV_ID" | jq .

# Tägliche Abfahrtzeit setzen (Format HH:MM)
curl -s -X PATCH \
  -H "Authorization: Bearer $BEARER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"chargeSettings": {"primaryScheduleDepartureTime": "07:30"}}' \
  "https://heartbeat.1komma5grad.com/api/v1/systems/$ONEKOMMAFIVE_SYSTEM/devices/evs/$EV_ID" | jq .
```

---

### Verfügbare EV-Lademodi

| Methode | URL |
|---------|-----|
| `GET` | `https://heartbeat.1komma5grad.com/api/v1/sites/$ONEKOMMAFIVE_SYSTEM/assets/evs/displayed-ev-charging-modes` |

Verwendet `/sites/` statt `/systems/` als Pfadpräfix (IDs sind identisch).

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  "https://heartbeat.1komma5grad.com/api/v1/sites/$ONEKOMMAFIVE_SYSTEM/assets/evs/displayed-ev-charging-modes" | jq .
```

Antwortstruktur:

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

`emsMode: "TOU"` = Time of Use (Dynamic-Pulse-Tarif aktiv, Börsenpreise steuern Ladeentscheidungen).

---

### EMS-Einstellungen

| Methode | URL |
|---------|-----|
| `GET` | `https://heartbeat.1komma5grad.com/api/v1/systems/$ONEKOMMAFIVE_SYSTEM/ems/actions/get-settings` |
| `POST` | `https://heartbeat.1komma5grad.com/api/v1/systems/$ONEKOMMAFIVE_SYSTEM/ems/actions/set-manual-override` |

```bash
# EMS-Einstellungen abrufen
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  "https://heartbeat.1komma5grad.com/api/v1/systems/$ONEKOMMAFIVE_SYSTEM/ems/actions/get-settings" | jq .
```

Antwortstruktur:

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

`overrideAutoSettings: false` = KI-Automatik aktiv. `manualSettings` verwendet numerische String-Keys (`"0"`, `"1"`, `"2"`); das `type`-Feld zur Identifikation verwenden.

```bash
# Automatischen Modus aktivieren
curl -s -X POST \
  -H "Authorization: Bearer $BEARER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"overrideAutoSettings": false}' \
  "https://heartbeat.1komma5grad.com/api/v1/systems/$ONEKOMMAFIVE_SYSTEM/ems/actions/set-manual-override" | jq .

# Manuellen Override aktivieren
curl -s -X POST \
  -H "Authorization: Bearer $BEARER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"overrideAutoSettings": true}' \
  "https://heartbeat.1komma5grad.com/api/v1/systems/$ONEKOMMAFIVE_SYSTEM/ems/actions/set-manual-override" | jq .
```

---

### Heartbeat AI – KI-Optimierungsentscheidungen (v1)

| Methode | URL |
|---------|-----|
| `GET` | `https://heartbeat.1komma5grad.com/api/v1/heartbeat-ai/optimizations` |

Parameter:

| Parameter | Wert |
|-----------|------|
| `siteId` | UUID der Anlage |
| `from` | ISO-8601-Zeitstempel mit Millisekunden, URL-kodiert |
| `to` | ISO-8601-Zeitstempel mit Millisekunden, URL-kodiert |

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  'https://heartbeat.1komma5grad.com/api/v1/heartbeat-ai/optimizations?siteId='"$ONEKOMMAFIVE_SYSTEM"'&from=2026-03-08T00%3A00%3A00.000Z&to=2026-03-08T23%3A59%3A59.999Z' | jq .
```

Antwortstruktur:

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
        "log": ["ISO8601", ...]
      }
    }
  ]
}
```

Bekannte `decision`-Werte:

| Wert | Asset | Bedeutung |
|------|-------|-----------|
| `BATTERY_CHARGE_FROM_GRID` | BATTERY | Batterie lädt aus dem Netz (günstiger Preis) |
| `BATTERY_NO_DISCHARGE` | BATTERY | Batterie entlädt nicht (Preis zu niedrig) |
| `EV_CHARGE_FROM_GRID` | EV | EV lädt aus dem Netz |

`marketPrice.value` in **EUR/MWh** — empirisch näher am Feed-in-/Trader-Preis als am Spot-Bezug (siehe Self-Sufficiency-Sektion für den beobachteten Faktor ~4-5 gegenüber `charts/market-prices`). `stateOfCharge` in %. Das `log`-Feld enthält Zeitstempel von Folge-Slots mit derselben Entscheidung.

---

### Heartbeat AI – Self-Sufficiency-Events (v1)

Zeigt AI-Entscheidungen, die die Autarkie-Bilanz erklären — typischerweise das granulare Batterie-Entlade-Trace. **Gleiche Payload-Struktur** wie `/optimizations`, aber ein **anderer Subset** der AI-Aktivität — die beiden Endpunkte ergänzen sich (in einem Fenster in dem `/optimizations` `[]` liefert, kann `/self-sufficiency` mehrere Events zeigen).

| Methode | URL |
|---------|-----|
| `GET` | `https://heartbeat.1komma5grad.com/api/v1/heartbeat-ai/self-sufficiency` |

Parameter (alle required):

| Parameter | Wert |
|-----------|------|
| `siteId` | UUID der Anlage |
| `from` | ISO-8601 mit Millisekunden, URL-kodiert |
| `to` | ISO-8601 mit Millisekunden, URL-kodiert |

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  'https://heartbeat.1komma5grad.com/api/v1/heartbeat-ai/self-sufficiency?siteId='"$ONEKOMMAFIVE_SYSTEM"'&from=2026-08-01T00%3A00%3A00.000Z&to=2026-08-01T23%3A59%3A59.999Z' | jq .
```

Antwortstruktur — identisch zu `/optimizations`:

```json
{
  "events": [
    {
      "id": "<uuid>",
      "timestamp": "ISO8601",
      "data": {
        "decision": "BATTERY_DISCHARGE",
        "from": "ISO8601",
        "to": "ISO8601",
        "asset": "BATTERY",
        "marketPrice": { "value": 35.30, "currency": "EUR" },
        "energySold": null,
        "energyBought": null,
        "totalCost": null,
        "stateOfCharge": 67
      }
    }
  ]
}
```

Hinweis zu `marketPrice`: **empirisch** deutlich niedriger als der zeitgleich in `charts/market-prices` gemeldete `marketPrice` (Faktor ~4-5). Vermutet Feed-in-/Verkaufspreis aus dem Trader-Regime statt Spot-Bezug, aber API-seitig nicht dokumentiert.

---

### Heartbeat-Ersparnis für Zeitraum (v1)

Aggregiert die kumulierten Heartbeat-Einsparungen für einen Datumsbereich in einem einzelnen EUR-Wert. Praktisch, wenn nur die Summe interessiert und der Timeseries-Overhead von `energy-today` / `energy-historical` unerwünscht ist.

| Methode | URL |
|---------|-----|
| `GET` | `https://heartbeat.1komma5grad.com/api/v1/systems/$ONEKOMMAFIVE_SYSTEM/energy-savings` |

Parameter (beide optional):

| Parameter | Wert |
|-----------|------|
| `from` | Datum **date-only** (`YYYY-MM-DD`). Mit Zeit-Anteil → HTTP 400. |
| `to` | Datum **date-only** (`YYYY-MM-DD`). |

Ohne Parameter liefert der Endpoint ein serverseitig rollendes Fenster (undokumentiert — weder Tag noch aktueller Monat).

```bash
# Rollierendes Default-Fenster
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  "https://heartbeat.1komma5grad.com/api/v1/systems/$ONEKOMMAFIVE_SYSTEM/energy-savings" | jq .

# Beliebiger Zeitraum
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  "https://heartbeat.1komma5grad.com/api/v1/systems/$ONEKOMMAFIVE_SYSTEM/energy-savings?from=2026-07-01&to=2026-07-31" | jq .
```

Antwortstruktur:

```json
{ "heartbeatSavings": { "value": 175.42, "unit": "€" } }
```

---

### CO₂-Bilanz (v2)

Lifetime-Kennzahlen: eingesparte kg CO₂ für den Standort, aggregierte Community-Werte und eine globale Marketing-Schätzung. Der Endpoint ignoriert `from`/`to`/`resolution` — die Werte sind immer Lifetime-Totals.

| Methode | URL |
|---------|-----|
| `GET` | `https://heartbeat.1komma5grad.com/api/v2/systems/$ONEKOMMAFIVE_SYSTEM/impact-overview` |

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  "https://heartbeat.1komma5grad.com/api/v2/systems/$ONEKOMMAFIVE_SYSTEM/impact-overview" | jq .
```

Antwortstruktur:

```json
{
  "co2Savings":                { "value": 3099.24,     "unit": "kg" },
  "co2CollectiveSavings":      { "value": 84779526.33, "unit": "kg" },
  "co2GlobalSavingsEstimate":  { "value": 2000000,     "unit": "tons" }
}
```

Hinweis: `co2GlobalSavingsEstimate` ist eine Marketing-Kennzahl (Tonnen), keine standortspezifische Messung.

---

### Energy Trader – Lifetime-Statistik (v2)

Kumulierte Ersparnisse durch dynamischen Handel für den Standort. Keine Zeitraum-Parameter — Werte akkumulieren über die gesamte Trading-Historie der Anlage.

| Methode | URL |
|---------|-----|
| `GET` | `https://heartbeat.1komma5grad.com/api/v2/energy-trader?siteId=$ONEKOMMAFIVE_SYSTEM` |

**Achtung:** `siteId` als Query-Param, **nicht** als Pfad-Segment — anders als die meisten heartbeat-Endpunkte.

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  "https://heartbeat.1komma5grad.com/api/v2/energy-trader?siteId=$ONEKOMMAFIVE_SYSTEM" | jq .
```

Antwortstruktur:

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

### Energy Trader – Monats-Ø (v1)

Durchschnittliche monatliche Ersparnis aus variabler Preisführung. Ergänzt die Lifetime-Sicht aus `/energy-trader` um eine Monats-Perspektive.

| Methode | URL |
|---------|-----|
| `GET` | `https://heartbeat.1komma5grad.com/api/v1/energy-trader-savings/$ONEKOMMAFIVE_SYSTEM/month` |

**Achtung:** der Pfad-Placeholder ist die **Site-ID** (= `$ONEKOMMAFIVE_SYSTEM`), **nicht** die Customer-ID — trotz missverständlicher URL-Struktur. Verifiziert per Live-Test (Customer-ID → HTTP 403, Site-ID → 200).

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  "https://heartbeat.1komma5grad.com/api/v1/energy-trader-savings/$ONEKOMMAFIVE_SYSTEM/month" | jq .
```

Antwortstruktur:

```json
{ "averagePastVariableSavings": { "value": 12.83, "unit": "€" } }
```

---

### Heartbeat AI – Kurzstatistik (v2)

Aggregierte AI-Kennzahlen für ein Zeitfenster: Autarkiegrad, verdiente Einspeisevergütung, CO₂-Ersparnis, effektiver Heartbeat-Preis.

| Methode | URL |
|---------|-----|
| `GET` | `https://heartbeat.1komma5grad.com/api/v2/heartbeat-ai/summary?siteId=$ONEKOMMAFIVE_SYSTEM&resolution=1M` |

Parameter (beide required):

| Parameter | Wert |
|-----------|------|
| `siteId` | UUID der Anlage |
| `resolution` | `1W`, `1M` oder `1Y`. Jeder andere Wert → HTTP 400. |

**Achtung:** Nur `resolution=1M` liefert alle Metriken. Bei `1W` und `1Y` sind `selfSufficiency` und `energyEarned` `null`; nur `co2Saved`, `production` und `carTravelEmission` sind gefüllt.

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  "https://heartbeat.1komma5grad.com/api/v2/heartbeat-ai/summary?siteId=$ONEKOMMAFIVE_SYSTEM&resolution=1M" | jq .
```

Antwortstruktur (`resolution=1M`):

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
  "peakPriceAvoided": null
}
```

Bei `resolution=1W` / `1Y`:

```json
{
  "selfSufficiency": null,
  "energyEarned": null,
  "co2Saved": { "co2Saved": ..., "production": {...}, "carTravelEmission": {...} },
  "heartbeatPrice": { ... },
  "peakPriceAvoided": null
}
```

`socialStanding` (überall) enthält vermutlich Community-Percentile — bislang immer `null`; möglicherweise feature-flagged oder anonymisiert.

---

### Preisanpassungen (v2)

Nutzer-konfigurierte Preise: Netzstrompreis, Vergleichspreis, monatlicher Grundpreis. Wird für „Ersparnis vs. Grundversorger"-Rechnungen und Dashboards genutzt.

| Methode | URL |
|---------|-----|
| `GET` | `https://heartbeat.1komma5grad.com/api/v2/systems/$ONEKOMMAFIVE_SYSTEM/price-customizations` |

Keine Query-Parameter.

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  "https://heartbeat.1komma5grad.com/api/v2/systems/$ONEKOMMAFIVE_SYSTEM/price-customizations" | jq .
```

Antwortstruktur:

```json
{
  "gridEnergyPrice":       { "price": { "amount": "0.3039", "currency": "EUR" }, "unit": "kWh" },
  "comparisonEnergyPrice": { "price": { "amount": "0.274",  "currency": "EUR" }, "unit": "kWh" },
  "monthlyBasePrice":      { "amount": "13.9", "currency": "EUR" }
}
```

Alle Preise als **String** (EUR/kWh); `monthlyBasePrice` in EUR.

---

### Vergleichspreis Grundversorger (v2)

Einzelwert: aktueller Grundversorger-Referenzpreis in EUR/kWh — die Basis für Sparen-Berechnungen. Ergibt genau denselben Wert wie `comparisonEnergyPrice` aus `/price-customizations`, aber ohne den Rest.

| Methode | URL |
|---------|-----|
| `GET` | `https://heartbeat.1komma5grad.com/api/v2/comparison-price?siteId=$ONEKOMMAFIVE_SYSTEM` |

**Achtung:** `siteId` als Query-Param, kein Pfad-Segment.

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  "https://heartbeat.1komma5grad.com/api/v2/comparison-price?siteId=$ONEKOMMAFIVE_SYSTEM" | jq .
```

Antwortstruktur:

```json
{ "comparisonPrice": { "price": { "amount": "0.274", "currency": "EUR" }, "unit": "kWh" } }
```

---

### Preisgarantie (v1, customer-identity)

Vertragliche Preisgarantie des Kunden (z. B. gedeckelte Netzpreise für einen Vertragszeitraum). Liegt wie `active-features` auf dem `customer-identity`-Host.

| Methode | URL |
|---------|-----|
| `GET` | `https://customer-identity.1komma5grad.com/api/v1/customers/$CUSTOMER_ID/price-guarantee?systemId=$ONEKOMMAFIVE_SYSTEM` |

**Achtung:** Der Pfad nimmt die Customer-ID, aber der Query-Parameter heißt `systemId` (**nicht** `customerId`, **nicht** `siteId`) — inkonsistente API-Konvention. Ohne den Query-Param → HTTP 400. `$CUSTOMER_ID` stammt aus dem Feld `customerId` der `/api/v1/systems/{id}/details`-Antwort.

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  "https://customer-identity.1komma5grad.com/api/v1/customers/$CUSTOMER_ID/price-guarantee?systemId=$ONEKOMMAFIVE_SYSTEM" | jq .
```

Antwortstruktur:

```json
{
  "priceGuaranteeUnit": "ct/kWh",
  "priceGuaranteeValue": 12,
  "priceGuaranteeVersion": "DE_PRICE_GUARANTEE_V2"
}
```

Beobachtete Versionen: `DE_PRICE_GUARANTEE_V2` (Deutschland, Version 2). Die Version taucht auch als `priceGuaranteeVersion` in einzelnen Subscription-Records auf.

---

### Wallbox-Hardware (v1)

Physische Wallbox-Hardware am Standort. **Anderer Endpoint** als `/devices/evs`: dieser liefert die reine Hardware-Sicht (GridX-ID, Anzeigename, EV-Zuordnung); `/devices/evs` dagegen die Fahrzeug-Seite (Fahrzeug-Profil, `chargingMode`, `targetSoc`, Fahrpläne).

| Methode | URL |
|---------|-----|
| `GET` | `https://heartbeat.1komma5grad.com/api/v1/systems/$ONEKOMMAFIVE_SYSTEM/devices/ev-chargers` |

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  "https://heartbeat.1komma5grad.com/api/v1/systems/$ONEKOMMAFIVE_SYSTEM/devices/ev-chargers" | jq .
```

Antwortstruktur (Array):

```json
[
  {
    "gridxHardwareId": "<uuid>",
    "name": "Wallbox",
    "assignedEvId": "<uuid>"
  }
]
```

`assignedEvId` verweist auf die `id` aus `/devices/evs` (Fahrzeug-Profil) — dort finden sich die Ladeeinstellungen.

---

### Smart Meter (v1)

Regulatorische Registrierungsdaten des Smart Meters: ENTSO-E-Regelzonen-EIC, BDEW-Code des Netzbetreibers, Konzessionsabgabe pro kWh. Beides mit Gültigkeitszeiträumen.

| Methode | URL |
|---------|-----|
| `GET` | `https://heartbeat.1komma5grad.com/api/v1/sites/$ONEKOMMAFIVE_SYSTEM/smart-meter` |

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  "https://heartbeat.1komma5grad.com/api/v1/sites/$ONEKOMMAFIVE_SYSTEM/smart-meter" | jq .
```

Antwortstruktur:

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

Hinweise:

- `controlAreaEIC` = ENTSO-E Regelzone (Deutschland: `10YDE-*` je nach Übertragungsnetzbetreiber wie TenneT/50Hertz/Amprion/RWENET).
- `dsoBdewCode` = 13-stelliger BDEW-Code des Verteilnetzbetreibers.
- `concessionFeeEURperkWh.value` = Konzessionsabgabe der Kommune in EUR/kWh.
- Beide Arrays enthalten historische Einträge mit `validFromDate`/`validUntilDate`; der jeweils aktuelle Eintrag steht typischerweise zuerst.
- Die `__metadata`-Blöcke dokumentieren Herkunft und letztes Update — meist `Imported from Enet via address lookup`.

---

### Site-Details (v2)

Erweitertes Site-Metadaten — Superset von `/systems/{id}` und `/systems/{id}/details`. Fügt Bidding-Zone, EMP-Verbindungsdaten und — am wertvollsten — den **aktuellen EMS-Runtime-Zustand** hinzu, den weder `SystemInfo` noch `SystemDetails` bieten.

| Methode | URL |
|---------|-----|
| `GET` | `https://heartbeat.1komma5grad.com/api/v2/sites/$ONEKOMMAFIVE_SYSTEM/details` |

Keine Query-Parameter.

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  "https://heartbeat.1komma5grad.com/api/v2/sites/$ONEKOMMAFIVE_SYSTEM/details" | jq .
```

Antwortstruktur (anonymisiert):

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

Hinweise:

- `biddingZone` = ENTSO-E Bidding-Zone (Deutschland/Luxemburg = `DE_LU`).
- `emsMode` = Betriebsmodus (`TOU` = Time-of-Use / Dynamic Pulse).
- `emsState` / `emsStateReasons` = aktueller EMS-Runtime-Zustand (bislang beobachtet: `OPERATIONAL` mit leerer Reason-Liste; bei Störungen vermutlich mit Codes).
- `empDetails` enthält die **Kopplungswerte** des Gateways (`serialNumber`, `startCode`) — sicherheitsrelevant, nicht protokollieren/teilen.
- `impactedByEnwg` = regulatorisches Flag für §14a EnWG (Steuerung / reduzierte Netzentgelte für steuerbare Verbrauchseinrichtungen).
- `customer` ist der eingebettete Kurz-Block; für den vollen Datensatz (Adresse, Phone, `crmBranchLocation`) siehe **Customer-Datensatz (v3)**.
- `earliestMeasurement`, `energyTraderActive`, `electricityContractActive` sind auch via `/systems/{id}/details` verfügbar — hier redundant, aber praktisch weil in einem Response.
- Keine `deviceGateways` — dafür `/systems/{id}/details` verwenden.
- **v2 und v3 liefern byte-identische Payloads** (verifiziert 2026-08-02) — kein Grund für einen Versions-Wechsel.

---

### Customer-Datensatz (v3, customer-identity)

Vollständiges Customer-Profil — Superset des embedded `customer`-Blocks in `/systems/{id}/details` (der nur `id`, `firstName`, `lastName`, `email` liefert). Liegt wie `active-features` und `price-guarantee` auf dem `customer-identity`-Host.

| Methode | URL |
|---------|-----|
| `GET` | `https://customer-identity.1komma5grad.com/api/v3/customers/$CUSTOMER_ID` |

`$CUSTOMER_ID` stammt aus dem Feld `customerId` der `/api/v1/systems/{id}/details`-Antwort.

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  "https://customer-identity.1komma5grad.com/api/v3/customers/$CUSTOMER_ID" | jq .
```

Antwortstruktur (anonymisiert):

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

Hinweise:

- Feldname ist `contactEmail`, nicht `email` (letzteres nur im eingebetteten `SystemCustomer`).
- `addressCountry` als **Klarname-String** (z. B. `"Deutschland"`), nicht als ISO-Code — Abweichung von `/systems/{id}` das `"DE"` liefert.
- `customerType` bisher nur `"UNKNOWN"` beobachtet — vermutlich weitere Werte wie `"PRIVATE"`/`"BUSINESS"` möglich.
- `crmBranchLocation` = zugewiesene 1KOMMA5°-Filiale (z. B. `"1KOMMA5° Moers"`).

---

### Notifications – letzte Meldungen (v1)

Zeigt die zuletzt ausgelieferten Push- und In-App-Notifications für den authentifizierten Nutzer, gescoped auf eine Anlage.

| Methode | URL |
|---------|-----|
| `GET` | `https://heartbeat.1komma5grad.com/api/v1/users/$USER_ID/notifications/latest?systemId=$ONEKOMMAFIVE_SYSTEM` |

`$USER_ID` stammt aus `GET /api/v1/users/me`. **Achtung:** `systemId` als Query-Param ist required — ohne → HTTP 400.

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  "https://heartbeat.1komma5grad.com/api/v1/users/$USER_ID/notifications/latest?systemId=$ONEKOMMAFIVE_SYSTEM" | jq .
```

Antwortstruktur:

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

`type`-Werte entsprechen den Kategorien aus `/notifications/settings` (siehe unten).

---

### Notifications – Einstellungen (v1)

Nutzer-Präferenzen pro Notification-Kategorie mit Channel-Toggles (App/Push/Email).

| Methode | URL |
|---------|-----|
| `GET` | `https://heartbeat.1komma5grad.com/api/v1/systems/$ONEKOMMAFIVE_SYSTEM/users/$USER_ID/notifications/settings` |

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  "https://heartbeat.1komma5grad.com/api/v1/systems/$ONEKOMMAFIVE_SYSTEM/users/$USER_ID/notifications/settings" | jq .
```

Antwortstruktur:

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
    "ENERGY_MARKET_UPPER_TARGET_REACHED": [ ... ],
    "ENERGY_MARKET_LOWER_TARGET_REACHED": [ ... ],
    "SYSTEM_HEALTH": [ ... ]
  }
}
```

Ein leeres Array pro Kategorie = **nicht abonniert**. Ein Eintrag pro Kategorie enthält die zugehörige Subscription-ID und die aktivierten Channels.

Beobachtete Kategorien (nicht abschließend):

| Kategorie | Bedeutung |
|-----------|-----------|
| `CO2_IMPACT` | CO₂-Impact-Meilensteine |
| `BATTERY_SOC` | Batterie-SoC-Grenzwerte |
| `BROADCAST_NEW_ELECTRICITY_PRICES` | Tägliche Ansage der Strompreis-Prognose |
| `SYSTEM_DATA_COLLECTION_ENDED` | Systemdaten-Erfassung beendet |
| `EV_DYNAMIC_PULSE` | Dynamic-Pulse-EV-Trigger |
| `ENERGY_MARKET_UPPER_TARGET_REACHED` | Preis-Alert nach oben |
| `ENERGY_MARKET_LOWER_TARGET_REACHED` | Preis-Alert nach unten |
| `SYSTEM_HEALTH` | Anlagen-Gesundheitswarnungen |

---

### API-Kompatibilität (v1)

Nicht anlagen-gebundene Meta-Endpunkt: liefert die Ziel- und Mindest-Version für die zwei Client-Kanäle.

| Methode | URL |
|---------|-----|
| `GET` | `https://heartbeat.1komma5grad.com/api/v1/supported-versions` |

Keine Query-Parameter, kein Site/Customer-Kontext.

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  "https://heartbeat.1komma5grad.com/api/v1/supported-versions" | jq .
```

Antwortstruktur:

```json
{
  "b2b": { "targetVersion": "1.10.0", "minimumSupportedVersion": "1.12.0" },
  "b2c": { "targetVersion": "1.73.0", "minimumSupportedVersion": "1.73.0" }
}
```

`b2b` = Installer/Partner-Client, `b2c` = End-Nutzer-App. Kann genutzt werden, um zu warnen wenn eigene Client-Implementierung hinter `minimumSupportedVersion` zurückfällt.

---

## Einheitenübersicht

| Endpunkt | Einheit |
|----------|---------|
| `live-overview` | **W** (Momentanleistung) |
| `energy-today`, `energy-historical` | **kW** (Zeitreihe) / **kWh** (Tagessummen) |
| `charts/market-prices` | Preise als **String EUR/kWh**, Mengen in **kWh** |
| `heartbeat-ai/optimizations` | **EUR/MWh** |
| `heartbeat-ai/summary` | **kWh** / **EUR** / **kg** (CO₂) / **km** (Auto-Äquivalent), Preise als **String EUR/kWh** |
| `impact-overview` | **kg** CO₂ (site + collective), **tons** (global estimate) |
| `energy-trader`, `energy-trader-savings/.../month` | **EUR** |
| `energy-savings` | **EUR** |
| `price-customizations`, `comparison-price` | **String EUR/kWh** (Grundpreis: **EUR/Monat**) |
| `price-guarantee` | Wert je `priceGuaranteeUnit` (z. B. `ct/kWh`) |
| `smart-meter` | Konzessionsabgabe in **EUR/kWh** |
| `devices/evs` | Kapazität in **Wh**, Ladestrom in **A** |
| `ems/actions/get-settings` | **kW** (maxSolarSurplusUsage) |
