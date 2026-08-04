# 1KOMMA5° Python API Client

[![Tests](https://github.com/mrebbert/1komma5-api/actions/workflows/tests.yml/badge.svg)](https://github.com/mrebbert/1komma5-api/actions/workflows/tests.yml)
[![PyPI](https://img.shields.io/pypi/v/onekommafive)](https://pypi.org/project/onekommafive/)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**`onekommafive`** is an unofficial Python client for the [1KOMMA5°](https://1komma5grad.com) Heartbeat home-energy-management API — the platform behind 1KOMMA5°'s heat pumps, solar inverters, battery storage systems, and EV chargers (wallboxes).

Read live power flows, control EV charging, monitor Dynamic Pulse market prices, drive the AI energy-management system (EMS), and pull weather forecasts — from Python or a built-in `1k5` command-line interface.

> ⚠️ **Unofficial**. The API is undocumented and reverse-engineered from the mobile app; it may change without notice. Not affiliated with or endorsed by 1KOMMA5°.

## Table of contents

- [Installation](#installation)
- [Quick start](#quick-start)
  - [Command-line interface](#command-line-interface)
  - [Python library](#python-library)
- [Features](#features)
- [Reference](#reference)
  - [CLI commands](#cli-commands)
  - [Python models](#python-models)
  - [Endpoint reference](#endpoint-reference)
- [Development](#development)
  - [Running tests](#running-tests)
  - [Linting and pre-commit](#linting-and-pre-commit)
  - [API version monitoring](#api-version-monitoring)
- [Compatibility](#compatibility)
- [Related projects](#related-projects)
- [Credits](#credits)
- [License](#license)

## Installation

Requires **Python 3.11 or newer**.

```bash
pip install onekommafive
```

With development extras (pytest, responses, ruff):

```bash
pip install "onekommafive[dev]"
```

## Quick start

Set your 1KOMMA5° credentials once via environment variables. All CLI commands and the token cache pick them up automatically:

```bash
export ONEKOMMAFIVE_USERNAME="user@example.com"
export ONEKOMMAFIVE_PASSWORD="s3cr3t"

# Optional — pin to a specific system (default: first system on the account)
export ONEKOMMAFIVE_SYSTEM="<system-uuid>"
```

### Command-line interface

```
$ 1k5 live
System:       xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
Status:       ONLINE
PV power:     +1837 W
Battery:      +4802 W  SoC 61.0%
Grid:         +5914 W  (import +5914 W  export +0 W)
Consumption:  +2950 W
Household:    +1900 W
EV chargers:  +0 W
Heat pumps:   +2000 W
ACs:          +1500 W
Self-suff.:   0.0%
```

```
$ 1k5 ai-summary
System:      xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
Resolution:  1M
Self-suff.:  73.0%   (solar 331.2 kWh, battery 301.3 kWh)
Earned:      30.41 €   (378.7 kWh sold @ 0.0803 €/kWh)
CO2 saved:   365.0 kg, ≈ 1431 car km (PV 1005.4 kWh)
HB price:    0.0746 €/kWh
Peak avoided: 22.50 €  (grid 60.18 € − battery 37.68 €)
```

See [CLI commands](#cli-commands) for the full list and `1k5 --help` for every option.

### Python library

```python
from onekommafive import Client, Systems

client = Client("user@example.com", "s3cr3t")
system = Systems(client).get_systems()[0]

# Live overview
ov = system.get_live_overview()
print(f"PV: {ov.pv_power} W  Battery: {ov.battery_power} W ({ov.battery_soc:.1f}%)")
print(f"Grid: {ov.grid_power} W  Self-sufficiency: {ov.self_sufficiency:.0%}")

# Market prices for today (EUR/kWh, hourly)
import datetime
today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
mp = system.get_prices(today, today.replace(hour=23, minute=59, second=59))
print(f"Avg spot: {mp.average_price:.4f}  all-in: {mp.average_price_all_in:.4f} EUR/kWh")

# Switch the EV to solar-only charging
from onekommafive.models import ChargingMode
ev = system.get_ev_chargers()[0]
ev.set_charging_mode(ChargingMode.SOLAR_CHARGE)
ev.set_target_soc(90.0)
ev.set_primary_departure_time("07:30")

# Aggregated AI performance (self-sufficiency, earnings, CO2, peak-price avoided)
summary = system.get_heartbeat_ai_summary(resolution="1M")
print(f"{summary.self_sufficiency_percent:.0%} autonomous, "
      f"{summary.earned_amount_eur:.2f} € earned, "
      f"{summary.co2_saved_kg:.0f} kg CO2 saved")
```

Every response is a fully-typed [dataclass](#python-models) — the entire surface has type hints.

## Features

**Live and historical**
- Live power snapshot — PV, battery, grid, consumption, per-device flows, self-sufficiency
- Energy summary and timeseries for today or any historical range (`1h` / `15m`)
- Market electricity prices with grid costs and VAT (`1h` / `15m`)
- Weather forecast — today, tomorrow, plus 3-hour slots for 48 h
- Aggregated Heartbeat savings (EUR) for any date range

**Control**
- EV charger — charging mode, target SoC, departure time, current SoC
- EMS — automatic or manual override, Time-of-Use, per-device manual settings

**AI and analytics**
- AI optimisation decisions (battery / EV charging, with market-price context)
- Self-sufficiency events — granular battery-discharge trace
- Heartbeat AI performance summary — self-sufficiency, feed-in earnings, CO₂ saved, peak-price avoided
- Lifetime CO₂ savings (site, community, global estimate)
- Lifetime and monthly energy-trader savings

**Metadata and configuration**
- System, site, and full customer records
- Site status and hardware asset inventory (inverter, heat pump, meter, EV charger — with manufacturer / model / serial / firmware / network address)
- Active feature flags per site (Dynamic Pulse, Time-of-Use optimisation, smart charging)
- Wallbox hardware (distinct from vehicle-side EV profile)
- Smart-meter registration (ENTSO-E control-area EIC, DSO BDEW code, concession fee)
- User profile plus every site the user is authorised for
- Notifications and per-category channel preferences
- User-configured and comparison prices, contractual price guarantee
- API version compatibility check

**Cross-cutting**
- OAuth2 + PKCE authentication matching the mobile-app flow, with automatic silent token refresh
- Optional persistent token cache (`chmod 600`, user-bound) — subsequent CLI calls skip the login round-trip
- Built-in `1k5` CLI covering every read endpoint and all mutations
- 348 unit tests, live-verified against real accounts
- Ruff-clean, CodeQL-clean, pre-commit hooks

## Reference

### CLI commands

Set credentials with `ONEKOMMAFIVE_USERNAME` / `ONEKOMMAFIVE_PASSWORD` env vars (see [Quick start](#quick-start)), then:

| Category | Commands |
|----------|----------|
| System & metadata | `info`, `details`, `site-details`, `assets`, `features`, `customer`, `me` |
| Live & energy | `live`, `energy-today`, `energy-historical`, `savings` |
| Prices | `prices`, `price-config`, `comparison-price`, `price-guarantee` |
| EV & wallbox | `ev`, `ev-modes`, `set-ev-mode`, `set-ev-target-soc`, `set-ev-departure`, `wallboxes` |
| EMS | `ems`, `set-ems` |
| AI & analytics | `optimizations`, `ai-decisions`, `ai-summary`, `heartbeat-prices`, `impact`, `trader`, `monthly-trading` |
| Notifications | `notifications`, `notification-settings` |
| Weather & meta | `weather`, `smart-meter`, `versions` |

Run `1k5 --help` or `1k5 <command> --help` for parameters and defaults.

<details>
<summary>Example output — <code>1k5 optimizations</code></summary>

```
$ 1k5 optimizations
System:  xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
Period:  2026-03-19 – 2026-03-19
Events:  25

Timestamp               Asset     Decision                    Price    SoC
--------------------------------------------------------------------------------
2026-03-19 00:00:00     BATTERY   BATTERY_NO_DISCHARGE        29.79     55%
2026-03-19 00:00:00     EV        EV_CHARGE_FROM_GRID         29.79     55%
2026-03-19 10:00:00     BATTERY   BATTERY_CHARGE_FROM_GRID    18.82     24%
2026-03-19 14:00:00     BATTERY   BATTERY_CHARGE_FROM_GRID    21.46     92%
2026-03-19 16:00:00     BATTERY   BATTERY_NO_DISCHARGE        28.44     87%
2026-03-19 22:30:00     BATTERY   BATTERY_NO_DISCHARGE        31.97      —
```

</details>

<details>
<summary>Example output — <code>1k5 weather --forecasts</code></summary>

```
$ 1k5 weather --forecasts
System:   xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
Heute:    Regen                         16.1 °C  ☀ 6.4 h  🌧 5.2 mm (87%)  ↑2026-03-11 05:57  ↓17:32
Morgen:   Heiter                        14.3 °C  ☀ 4.1 h  🌧 1.0 mm (20%)  ↑2026-03-12 05:55  ↓17:34

Zeit (UTC)           Wetter                         Temp    Wind      Regen   Prob   Sonne
--------------------------------------------------------------------------------------------
2026-03-11 15:00     Regen                          10.2°C  3.8 m/s   1.1 mm   51%   0 min
2026-03-11 18:00     Regen (Nacht)                   8.5°C  2.9 m/s   0.5 mm   40%   0 min
2026-03-11 21:00     Klar (Nacht)                    7.1°C  1.8 m/s   0.0 mm    5%   0 min
```

</details>

### Python models

Every endpoint returns a typed [dataclass](https://docs.python.org/3/library/dataclasses.html) from `onekommafive.models`:

| Domain | Classes |
|--------|---------|
| System | `SystemInfo`, `SystemDetails`, `SystemCustomer`, `DeviceGateway`, `SiteStatus`, `Asset`, `SiteDetails`, `SmartMeter` |
| User & customer | `User`, `ConnectedSystem`, `Customer` |
| Live & energy | `LiveOverview`, `EnergyData`, `EnergySlot`, `HeartbeatSavings` |
| Prices | `MarketPrices`, `PriceCustomizations`, `ComparisonPrice`, `PriceGuarantee` |
| EV & EMS | `EVCharger`, `ChargingMode`, `Wallbox`, `EmsSettings`, `EmsManualDevice` |
| Weather | `WeatherData`, `WeatherDay`, `WeatherSlot`, `WEATHER_SYMBOLS` |
| AI & analytics | `OptimizationEvents`, `OptimizationEvent`, `SelfSufficiencyEvents`, `HeartbeatAiSummary`, `ImpactOverview`, `EnergyTrader`, `MonthlyTradingSavings` |
| Notifications | `Notification`, `NotificationsList`, `NotificationSettings`, `NotificationChannelSettings` |
| API meta | `SupportedVersions`, `VersionInfo` |

Every model exposes a `raw` attribute (`dict[str, Any]`) with the full untouched API response for fields that are not (yet) mapped.

### Endpoint reference

Complete curl-level reference for every HTTP endpoint — URLs, query parameters, response JSON, and every known API quirk — is in **[API.md](API.md)**.

## Development

### Running tests

```bash
pip install "onekommafive[dev]"
pytest
```

Integration tests (require credentials, read-only, no mutations):

```bash
ONEKOMMAFIVE_USERNAME=... ONEKOMMAFIVE_PASSWORD=... pytest tests/test_integration.py -v
```

### Linting and pre-commit

Lint with [ruff](https://docs.astral.sh/ruff/):

```bash
ruff check .
```

Install the [pre-commit](https://pre-commit.com/) hooks once after cloning:

```bash
pre-commit install
```

The hooks run ruff on every commit. CI runs ruff and CodeQL on every push and pull request.

### API version monitoring

[`scripts/probe_versions.py`](scripts/probe_versions.md) probes every known endpoint for newer API versions than the ones currently used by the client. Run it after a 1KOMMA5° app update to catch version bumps early:

```bash
ONEKOMMAFIVE_USERNAME=... ONEKOMMAFIVE_PASSWORD=... \
PYTHONPATH=. python scripts/probe_versions.py
```

## Compatibility

This project is developed against the author's own 1KOMMA5° installation. It has not been tested broadly across hardware configurations — a lot of it is "it works for me". Use at your own risk.

Reference setup:

| Component | Model |
|-----------|-------|
| Hybrid inverter | Sungrow SH6.0RT-V112 |
| Battery | Sungrow SBR256 |
| Wallbox | go-e homeFix 11 kW |
| EV | Volkswagen ID.5 |
| Heat pump | Stiebel Eltron WPL-A 10 HK 400 Premium |
| Smart meter | Chint DTSU666 |

## Related projects

### [1komma5-ha](https://github.com/mrebbert/1komma5-ha)

A Home Assistant integration built on top of this library. Exposes your 1KOMMA5° system as sensors, switches, and controls directly in Home Assistant.

## Credits

Large parts of this project are inspired by and based on the work of [Alex Birkner](https://github.com/BirknerAlex) and his [hacs_1komma5grad](https://github.com/BirknerAlex/hacs_1komma5grad) integration. Many thanks for paving the way.

## License

MIT — see [LICENSE](LICENSE).
