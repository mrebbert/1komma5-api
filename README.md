# onekommafive
> **!!!DANGER! This is 100% vibe coded and very experimental!!!**

Unofficial Python client for the [1KOMMA5°](https://1komma5grad.com) Heartbeat API — the home energy management platform behind heat pumps, solar inverters, battery storage, and EV chargers.

> **Unofficial.** This library reverse-engineers the mobile app's API. It may break without notice if 1KOMMA5° changes their backend.
## Features

- OAuth2 + PKCE authentication (matches the mobile app flow), with automatic token refresh
- Read live power data (PV, battery, grid, consumption)
- Read and control EV chargers (charging mode, target SoC)
- Read and set EMS (energy management system) mode
- Fetch hourly or daily electricity market prices
- Built-in CLI (`1k5`) for quick terminal access

## Requirements

- Python 3.11+
- A 1KOMMA5° account with at least one registered system

## Installation

```bash
pip install .

# with dev dependencies (pytest, responses, …)
pip install ".[dev]"
```

## Library usage

```python
from onekommafive import Client, Systems

client = Client("user@example.com", "s3cr3t")
systems = Systems(client).get_systems()
system = systems[0]

# Live overview
ov = system.get_live_overview()
print(f"PV: {ov.pv_power} W  Battery: {ov.battery_power} W ({ov.battery_soc:.1f}%)")
print(f"Grid: {ov.grid_power} W  Consumption: {ov.consumption_power} W")

# Market prices (yesterday, hourly)
import datetime
today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
mp = system.get_prices(today - datetime.timedelta(days=1), today, resolution="1h")
print(f"Avg spot price: {mp.average_price:.2f} ct/kWh")
for ts, price in sorted(mp.prices.items()):
    print(f"  {ts}  {price:.4f} ct/kWh")

# EV chargers
for ev in system.get_ev_chargers():
    print(f"{ev.name()}: {ev.charging_mode().value}  SoC {ev.current_soc()} %")

# EMS mode
settings = system.get_ems_settings()
print(f"EMS auto mode: {settings.auto_mode}")
system.set_ems_mode(auto=True)
```

## CLI

Set credentials via environment variables:

```bash
export ONEKOMMAFIVE_USERNAME="user@example.com"
export ONEKOMMAFIVE_PASSWORD="s3cr3t"
# optional: select a specific system by UUID
export ONEKOMMAFIVE_SYSTEM="8ef7677c-..."
```

```
1k5 live        Live power overview
1k5 prices      Market prices for yesterday (default: hourly)
1k5 prices --resolution 1h
1k5 ev          EV charger status
1k5 ems         EMS mode
```

Example output:

```
$ 1k5 live
System:       8ef7677c-c8c7-413a-9f13-20a3f202f811
PV power:     +0 W
Battery:      -2872 W  SoC 23.0%
Grid:         +2 W
Consumption:  +2874 W
```

## Models

| Class | Description |
|-------|-------------|
| `LiveOverview` | Real-time power snapshot |
| `MarketPrices` | Hourly/daily spot prices + grid costs |
| `EmsSettings` | EMS auto/manual mode |
| `EVCharger` | EV charger state and controls |
| `ChargingMode` | `SMART_CHARGE` / `QUICK_CHARGE` / `SOLAR_CHARGE` |

## Running tests

```bash
pip install ".[dev]"
pytest
```

Integration tests (require credentials, read-only):

```bash
ONEKOMMAFIVE_USERNAME=... ONEKOMMAFIVE_PASSWORD=... pytest tests/test_integration.py -v
```

## License

MIT
