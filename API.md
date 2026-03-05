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

## Bekannte API-Endpunkte

### Authentifizierung & Nutzer

| Methode | URL |
|---------|-----|
| `GET` | `https://customer-identity.1komma5grad.com/api/v1/users/me` |

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  https://customer-identity.1komma5grad.com/api/v1/users/me | jq .
```

---

### Systeme

| Methode | URL |
|---------|-----|
| `GET` | `https://heartbeat.1komma5grad.com/api/v2/systems` |
| `GET` | `https://heartbeat.1komma5grad.com/api/v2/systems/$ONEKOMMAFIVE_SYSTEM` |

```bash
# Alle Systeme auflisten
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  https://heartbeat.1komma5grad.com/api/v2/systems | jq .

# Einzelnes System
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  https://heartbeat.1komma5grad.com/api/v2/systems/$ONEKOMMAFIVE_SYSTEM | jq .
```

---

### Live-Übersicht (v3)

| Methode | URL |
|---------|-----|
| `GET` | `https://heartbeat.1komma5grad.com/api/v3/systems/$ONEKOMMAFIVE_SYSTEM/live-overview` |

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  "https://heartbeat.1komma5grad.com/api/v3/systems/$ONEKOMMAFIVE_SYSTEM/live-overview" | jq .
```

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

```bash
curl -s -H "Authorization: Bearer $BEARER_TOKEN" \
  "https://heartbeat.1komma5grad.com/api/v1/sites/$ONEKOMMAFIVE_SYSTEM/assets/evs/displayed-ev-charging-modes" | jq .
```

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
