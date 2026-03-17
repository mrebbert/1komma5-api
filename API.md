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
      "connectionStatus": { "status": "CONNECTED" },
      "manufacturer": "...",
      "model": "...",
      "serialnumber": "...",
      "firmware": "...",
      "network": { "address": "<local-ip>" }
    }
  ]
}
```

Asset-Typen einer typischen Anlage:

| Typ | Hersteller | Modell |
|-----|-----------|--------|
| `HYBRID` | Sungrow | SH6.0RT-V112 |
| `HEAT_PUMP` | Stiebel Eltron | WPMsystem |
| `METER` | Chint | DTSU666 |
| `EV_CHARGER` | go-e | HOMEfix 11kW |

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

`marketPrice.value` in **EUR/MWh**. `stateOfCharge` in %. Das `log`-Feld enthält Zeitstempel von Folge-Slots mit derselben Entscheidung.

---

## Einheitenübersicht

| Endpunkt | Einheit |
|----------|---------|
| `live-overview` | **W** (Momentanleistung) |
| `energy-today`, `energy-historical` | **kW** (Zeitreihe) / **kWh** (Tagessummen) |
| `charts/market-prices` | Preise als **String EUR/kWh**, Mengen in **kWh** |
| `heartbeat-ai/optimizations` | **EUR/MWh** |
| `devices/evs` | Kapazität in **Wh**, Ladestrom in **A** |
| `ems/actions/get-settings` | **kW** (maxSolarSurplusUsage) |
