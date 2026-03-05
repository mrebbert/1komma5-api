# 1Komma5° 
> **!!!DANGER! This is 100% vibe coded and very experimental!!!**

Unofficial Python client for the [1KOMMA5°](https://1komma5grad.com) Heartbeat API — the home energy management platform behind heat pumps, solar inverters, battery storage, and EV chargers.

> **Unofficial.** This library reverse-engineers the mobile app's API. It may break without notice if 1KOMMA5° changes their backend.

## Features

- OAuth2 + PKCE authentication (matches the mobile app flow), with automatic token refresh
- System metadata (address, status, features) — `SystemInfo`
- Live power snapshot (PV, battery, grid, consumption, heat pumps, EV chargers, ACs, self-sufficiency) — API v3
- EV charger state and control (charging mode, current SoC, target SoC, departure time, vehicle profile)
- Available EV charging modes per site
- EMS settings (auto/manual, Time-of-Use, per-device manual overrides for EV charger, battery, heat pump)
- Market electricity prices with grid costs and VAT — API v4, EUR/kWh, `1h` or `15m` resolution
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

# System metadata
info = system.info()
print(f"{info.name} — {info.address_city}, {info.status}")

# Live overview (API v3)
ov = system.get_live_overview()
print(f"PV: {ov.pv_power} W  Battery: {ov.battery_power} W ({ov.battery_soc:.1f}%)")
print(f"Grid: {ov.grid_power} W  (import {ov.grid_consumption_power} W  export {ov.grid_feed_in_power} W)")
print(f"Consumption: {ov.consumption_power} W")
print(f"Heat pumps: {ov.heat_pumps_power} W  EV chargers: {ov.ev_chargers_power} W")
print(f"Self-sufficiency: {ov.self_sufficiency:.0%}")

# Market prices today (API v4) — resolution "1h" or "15m", prices in EUR/kWh
import datetime
today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
mp = system.get_prices(today, today.replace(hour=23, minute=59, second=59), resolution="1h")
print(f"Avg spot: {mp.average_price:.4f}  +grid: {mp.average_price_with_grid_costs:.4f}  all-in: {mp.average_price_all_in:.4f} EUR/kWh")
for ts, price in sorted(mp.prices.items()):
    print(f"  {ts}  spot {price:.4f}  all-in {mp.prices_with_grid_costs_and_vat[ts]:.4f} EUR/kWh")

# Available EV charging modes for this site
modes = system.get_displayed_ev_charging_modes()
print("Available modes:", [m.value for m in modes])

# EV chargers — read state and set mode
for ev in system.get_ev_chargers():
    print(f"{ev.manufacturer()} {ev.model()} ({ev.capacity_wh()/1000:.0f} kWh)")
    print(f"  Mode: {ev.charging_mode().value}  SoC: {ev.current_soc()} %  Target: {ev.target_soc()} %")

from onekommafive.models import ChargingMode
ev = system.get_ev_chargers()[0]
ev.set_charging_mode(ChargingMode.SOLAR_CHARGE)
ev.set_target_soc(90.0)               # Zielladezustand 90 %
ev.set_primary_departure_time("07:30")  # tägliche Abfahrtzeit

# EMS settings
settings = system.get_ems_settings()
print(f"EMS auto mode: {settings.auto_mode}  ToU: {settings.time_of_use_enabled}")
for dev in settings.manual_devices:
    print(f"  {dev.type}: {dev.raw}")
system.set_ems_mode(auto=True)
```

## CLI

Set credentials via environment variables:

```bash
export ONEKOMMAFIVE_USERNAME="user@example.com"
export ONEKOMMAFIVE_PASSWORD="s3cr3t"
# optional: select a specific system by UUID
export ONEKOMMAFIVE_SYSTEM="<system-uuid>"
```

```
1k5 info                            System metadata (address, status, features)
1k5 live                            Live power overview
1k5 prices                          Market prices for today (hourly, EUR/kWh)
1k5 prices --resolution 15m         15-minute resolution
1k5 ev                              EV charger status and schedule
1k5 ev-modes                        Available EV charging modes for this site
1k5 set-ev-mode SOLAR_CHARGE        Set charging mode on first EV charger
1k5 set-ev-mode QUICK_CHARGE --ev <id>  Set mode on a specific charger
1k5 set-ev-target-soc 90            Set target SoC to 90 % on first EV charger
1k5 set-ev-target-soc 80 --ev <id>  Set target SoC on a specific charger
1k5 set-ev-departure 07:30          Set primary departure time on first EV charger
1k5 set-ev-departure 06:00 --ev <id>  Set departure time on a specific charger
1k5 ems                             EMS settings (mode, ToU, device overrides)
1k5 set-ems auto                    Enable automatic EMS optimisation
1k5 set-ems manual                  Enable manual EMS override
```

Example output:

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

$ 1k5 info
System:       xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
Name:         My Home System
Status:       ACTIVE
Address:      Musterstraße 1, 20095 Hamburg, DE
Coordinates:  53.5000, 10.0000
Customer ID:  cust-0001
Dynamic Pulse:        yes
Energy trading:       yes
Electricity contract: yes
Created:      2025-01-23T08:09:40.042Z
Updated:      2025-10-08T15:28:18.743Z

$ 1k5 prices --resolution 1h
System:        xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
Period:        2026-02-28 – 2026-02-28

                            avg        high        low  EUR/kWh
Spot                     0.0520      0.0952     -0.0003
+ Grid                   0.1896      0.2328      0.1373
All-in (incl. VAT)       0.2256      0.2770      0.1634

Grid costs:    0.1637 EUR/kWh  (VAT 19%,  energy tax 0.1376)

Timestamp                   Spot      + Grid    All-in
-----------------------------------------------------------
2026-02-28T00:00Z          0.0763      0.2139      0.2545
2026-02-28T01:00Z          0.0747      0.2123      0.2526
...

$ 1k5 ems
System:       xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
EMS mode:     AUTO
Time-of-Use:  enabled
Consent:      yes
Updated:      2026-02-21T18:28:27.452Z

Manual device settings:
  EV_CHARGER  Wallbox  →  QUICK_CHARGE  (Id4)
  BATTERY     Forecast charging: disabled
  HEAT_PUMP   <heat-pump-id>  Solar surplus: yes  (max 2.0 kW)
```

## API versions used

| Endpoint | API version |
|----------|-------------|
| List / get systems | v2 |
| System detail | v2 |
| Live power overview | **v3** |
| Market prices | **v4** |
| EV chargers (read / set) | v1 |
| Available EV charging modes | v1 |
| EMS (read / set) | v1 |

## Models

| Class | Description |
|-------|-------------|
| `SystemInfo` | System metadata (address, status, feature flags) |
| `LiveOverview` | Real-time power snapshot (W), incl. net grid power, separate import/export, smart devices and self-sufficiency |
| `MarketPrices` | Spot prices, grid costs and VAT per slot (EUR/kWh) |
| `EmsSettings` | EMS mode, Time-of-Use flag, per-device manual overrides |
| `EmsManualDevice` | One device entry in the EMS manual settings |
| `EVCharger` | EV charger state, vehicle profile, schedule and controls |
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

## Related projects

### [1komma5-ha](https://github.com/mrebbert/1komma5-ha)

A Home Assistant integration built on top of this library. Exposes your 1KOMMA5° system as sensors, switches and controls directly in Home Assistant.

## Credits

This project would not exist without the prior work of the Home Assistant community.

### [hacs_1komma5grad](https://github.com/BirknerAlex/hacs_1komma5grad) by [Alexander Birkner](https://github.com/BirknerAlex)

The unofficial Home Assistant / HACS integration for 1KOMMA5°. Large parts of this library — in particular the API endpoint discovery, the request/response structures, the OAuth2 + PKCE authentication flow, and the overall understanding of the Heartbeat API — are directly derived from or heavily inspired by that project. If you use Home Assistant, that integration is the right tool; this library is just a standalone Python wrapper built on the same knowledge.

> **Please respect the original authors' work.** The 1KOMMA5° API is undocumented and was reverse-engineered by the community. Use responsibly.

## License

MIT
