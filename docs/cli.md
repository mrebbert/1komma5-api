# CLI reference

The `1k5` command-line tool wraps the SDK's read endpoints plus the
small set of safe setters (EV charger, EMS mode). It uses the same
OAuth2 PKCE flow as the library and caches tokens at
`~/.cache/onekommafive/cli_token.json`.

## Setup

Credentials and system identifier come from environment variables.
Export them once per shell, or keep them in a `.env` next to your
shell profile:

```bash
export ONEKOMMAFIVE_USERNAME="user@example.com"
export ONEKOMMAFIVE_PASSWORD="s3cr3t"
export ONEKOMMAFIVE_SYSTEM="00000000-0000-0000-0000-000000000000"
```

The system UUID is the one that identifies your site at
`heartbeat.1komma5grad.com`. If you own several systems, run
`1k5 me` and pick the ID of the one you want to target from
`connectedSystems`.

## Command index

Thematic groups, each with the commands it contains, their flags and
a short real-world example per group.

### System and site metadata

| Command | Flags | Purpose |
|---|---|---|
| `info` | — | Address, status, feature flags. |
| `details` | — | Extended metadata: customer block, installer, device gateways. |
| `site-details` | — | Site record incl. EMS runtime state. |
| `assets` | — | Connection status + hardware list. |
| `system-info` | — | Compact site availability + §14a module enrolment. |
| `features` | `--customer-id UUID` | Active per-customer+site feature flags. |
| `customer` | — | Full customer record (v3). |
| `subscriptions` | — | Contracts / subscriptions with monthly cost. |
| `me` | — | Authenticated user profile + connected systems. |
| `versions` | — | API compatibility (b2b/b2c target + minimum). |

```console
$ 1k5 info
System:       My home
Address:      Hauptstraße 1, 12345 Musterstadt, DE
Status:       OPERATIONAL
Features:     dynamicPulseCompatible, enwg14aEnabled
Updated:      2026-10-10T14:35:08Z
```

### Live and energy

| Command | Flags | Purpose |
|---|---|---|
| `live` | — | Live power overview. |
| `weather` | — | Weather forecast for the site location. |
| `energy-today` | `--resolution 1h\|15m` | Energy production + consumption today. |
| `energy-historical` | `--from YYYY-MM-DD` `--to YYYY-MM-DD` `--resolution 1h\|15m` | Historical range. For `15m` the range must be a single day. |
| `impact` | — | Lifetime CO2 savings (site + community). |
| `trader` | — | Lifetime energy-trading savings in EUR. |

```console
$ 1k5 energy-historical --from 2026-10-01 --to 2026-10-07
Production:  412.6 kWh
Consumption: 203.4 kWh
Self-cons.:  58.7 %
Grid import: 84.1 kWh
Grid export: 125.3 kWh
```

### Prices

| Command | Flags | Purpose |
|---|---|---|
| `prices` | `--resolution 1h\|15m` | Market electricity prices (today). |
| `price-config` | — | User-configured energy prices. |
| `comparison-price` | — | Grid-supplier comparison price (EUR/kWh). |
| `price-guarantee` | — | Contractual electricity-price guarantee. |
| `heartbeat-prices` | — | Financial breakdown per window. Shows §14a Modul 1 / Modul 3 section when the account has it. |
| `savings` | `--from YYYY-MM-DD` `--to YYYY-MM-DD` | Aggregated Heartbeat savings for a range. Date-only. |
| `monthly-trading` | — | Average monthly Energy-Trader savings. |

```console
$ 1k5 heartbeat-prices
Window       Buy €/kWh  Sell €/kWh  Grid €   HB €   ...
day              0.32      0.08     -1.42   -0.78
week             0.31      0.08     -8.90   -4.12
month            0.30      0.08    -42.10  -18.65
...

§14a EnWG
  Modul 1 (month):     12.60 €   (184 active days, 25.20 €/year)
  Modul 3 (month):     18.76 €   (comparison 21.42 €, actual 2.66 €)
  §14a combined:       31.36 €
  Comparison fee:      0.0989 €/kWh
  Variable fee:        0.0866 €/kWh
```

The §14a block appears only when at least one window carries populated
values; see [§14a EnWG grid-fee bundle](enwg14a.md).

### Heartbeat AI

| Command | Flags | Purpose |
|---|---|---|
| `ai-summary` | `--resolution 1W\|1M\|1Y` | Self-sufficiency, earnings, CO2. Only `1M` returns all metrics. |
| `ai-decisions` | `--from YYYY-MM-DD[THH:MM]` `--to YYYY-MM-DD[THH:MM]` | Self-sufficiency events. |
| `optimizations` | `--from YYYY-MM-DD[THH:MM]` `--to YYYY-MM-DD[THH:MM]` | AI optimisation decisions. |

```console
$ 1k5 ai-summary --resolution 1M
CO2 saved:         184.2 kg
Production:        412.6 kWh
Self-sufficiency:  61.4 %
Energy earned:     42.10 €
Car-travel equiv.: 1 150 km
```

### EV charger

| Command | Flags | Purpose |
|---|---|---|
| `ev` | — | EV charger status. |
| `ev-modes` | — | Available charging modes for this site. |
| `set-ev-mode MODE` | `--ev EV_ID`, `--all-evs` | `SMART_CHARGE`, `QUICK_CHARGE`, `SOLAR_CHARGE`. |
| `set-ev-target-soc SOC` | `--ev EV_ID`, `--all-evs` | Target state-of-charge in percent (0–100). |
| `set-ev-departure HH:MM` | `--ev EV_ID`, `--all-evs` | Primary departure time, e.g. `07:30`. |
| `wallboxes` | — | Physical wallbox hardware. |

Use `--ev EV_ID` to pick one of several registered chargers; use
`--all-evs` to apply the change to every registered charger (handy for
single-car households that may churn through replacement chargers).

```console
$ 1k5 set-ev-mode SMART_CHARGE
Charging mode set to SMART_CHARGE on ev-00000000-0000-0000-0000-000000000001.
```

### EMS

| Command | Flags | Purpose |
|---|---|---|
| `ems` | — | EMS mode status. |
| `set-ems {auto,manual}` | — | `auto` for automatic optimisation, `manual` to override. |

```console
$ 1k5 ems
Mode:   AUTO
State:  OPERATIONAL
Reasons: (none)
```

### Notifications

| Command | Flags | Purpose |
|---|---|---|
| `notifications` | — | Recent push / in-app notifications. |
| `notification-settings` | — | Per-category channel preferences. |

### Hardware

| Command | Flags | Purpose |
|---|---|---|
| `smart-meter` | — | Smart-meter registration details (EIC, DSO code, concession fee). |
| `wallboxes` | — | Physical wallbox hardware. |

## Error handling

Every command exits with a non-zero status on failure and prints a
compact error message to stderr. The underlying exception comes from
the SDK: `AuthenticationError`, `RequestError`, or domain-specific
`ValueError` on invalid input (e.g. an unknown EV charging mode).

Common cases:

- **Login failed** → see [FAQ: `invalid_auth` with working app](faq.md).
- **No EV charger registered** → the EV commands fail with a clear
  message pointing at your account.
- **HTTP 400 on date range** → format quirk per endpoint, see
  [FAQ: HTTP 400 on a date range endpoint](faq.md).

## Scripting

The CLI prints human-readable tables. For scripting, prefer the
library directly:

```python
import asyncio
from onekommafive import Client, Systems


async def main() -> None:
    async with Client("user@example.com", "s3cr3t") as client:
        systems = await Systems(client).get_systems()
        system = systems[0]
        prices = await system.get_heartbeat_prices()
        print(prices.month.module3_total_savings_eur)


asyncio.run(main())
```
