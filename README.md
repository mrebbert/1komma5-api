# 1KOMMA5° Python API Client

[![Tests](https://github.com/mrebbert/1komma5-api/actions/workflows/tests.yml/badge.svg)](https://github.com/mrebbert/1komma5-api/actions/workflows/tests.yml)
[![PyPI](https://img.shields.io/pypi/v/onekommafive)](https://pypi.org/project/onekommafive/)
[![Python](https://img.shields.io/badge/python-3.13%2B-blue)](https://www.python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**`onekommafive`** is an unofficial Python client for the [1KOMMA5°](https://1komma5grad.com) Heartbeat home-energy-management API — the platform behind 1KOMMA5°'s heat pumps, solar inverters, battery storage systems, and EV chargers (wallboxes).

Read live power flows, control EV charging, monitor Dynamic Pulse market prices, drive the AI energy-management system (EMS), and pull weather forecasts — from Python or a built-in `1k5` command-line interface.

> ⚠️ **Unofficial**. The API is undocumented and reverse-engineered from the mobile app; it may change without notice. Not affiliated with or endorsed by 1KOMMA5°.

## Documentation

Full documentation lives at **<https://mrebbert.github.io/1komma5-api/>**. The README stays short and points there.

- **[CLI reference](https://mrebbert.github.io/1komma5-api/cli/)** — every `1k5` command with flags and example output.
- **[API reference](https://mrebbert.github.io/1komma5-api/api/)** — curl-level documentation of every endpoint the client wraps: URLs, request parameters, response JSON, known quirks. Source: [`API.md`](API.md).
- **[§14a EnWG grid-fee bundle](https://mrebbert.github.io/1komma5-api/enwg14a/)** — regulatory primer, Modul 1 vs. Modul 3, field mapping, convenience method.
- **[FAQ](https://mrebbert.github.io/1komma5-api/faq/)** — legacy sign-in, token cache, HTTP-400 date quirks, HTTP-403 on `price-guarantee`, and other recurring questions.
- **[Development](https://mrebbert.github.io/1komma5-api/development/)** — setup, tests, lint, type-check, probe-versions, release flow.
- **[Changelog](CHANGELOG.md)** — per-version additions, changes and fixes.
- **[Postman collection](postman/)** — importable alongside the API reference.

## Installation

Requires **Python 3.13 or newer**. The SDK became async in 1.0.0; if you need Python 3.11/3.12 compatibility, pin `onekommafive<1.0`.

```bash
pip install onekommafive
```

With development extras (pytest, aioresponses, mypy, ruff):

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

Full command catalogue and flags: **[CLI reference](https://mrebbert.github.io/1komma5-api/cli/)**. Local help via `1k5 --help` or `1k5 <command> --help`.

### Python library (async, default since 1.0.0)

```python
import asyncio
import datetime
from onekommafive import Client, Systems
from onekommafive.models import ChargingMode


async def main() -> None:
    async with Client("user@example.com", "s3cr3t") as client:
        system = (await Systems(client).get_systems())[0]

        # Live overview
        ov = await system.get_live_overview()
        print(
            f"PV: {ov.pv_power} W  Battery: {ov.battery_power} W ({ov.battery_soc:.1f}%)"
        )
        print(f"Grid: {ov.grid_power} W  Self-sufficiency: {ov.self_sufficiency:.0%}")

        # Market prices for today (EUR/kWh, hourly)
        today = datetime.datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        mp = await system.get_prices(
            today, today.replace(hour=23, minute=59, second=59)
        )
        print(
            f"Avg spot: {mp.average_price:.4f}  all-in: {mp.average_price_all_in:.4f} EUR/kWh"
        )

        # Switch the EV to solar-only charging
        ev = (await system.get_ev_chargers())[0]
        await ev.set_charging_mode(ChargingMode.SOLAR_CHARGE)
        await ev.set_target_soc(90.0)
        await ev.set_primary_departure_time("07:30")

        # Aggregated AI performance
        summary = await system.get_heartbeat_ai_summary(resolution="1M")
        print(
            f"{summary.self_sufficiency_percent:.0%} autonomous, "
            f"{summary.earned_amount_eur:.2f} € earned, "
            f"{summary.co2_saved_kg:.0f} kg CO2 saved"
        )


asyncio.run(main())
```

Inside Home Assistant, pass the shared client session so lifecycle stays with the host:

```python
from homeassistant.helpers.aiohttp_client import async_get_clientsession

client = Client(user, pw, session=async_get_clientsession(hass))
```

Every response is a fully-typed dataclass (see [Python models](#python-models) below); the package ships `py.typed` (PEP 561) so `mypy --strict` sees the whole surface.

### Python library (sync)

For scripts, notebooks, and other callers who don't want to introduce `asyncio`, `onekommafive.sync` wraps the async API on a dedicated background event loop:

```python
from onekommafive.sync import Client, Systems
from onekommafive.models import ChargingMode

with Client("user@example.com", "s3cr3t") as client:
    system = Systems(client).get_systems()[0]
    ov = system.get_live_overview()
    ev = system.get_ev_chargers()[0]
    ev.set_charging_mode(ChargingMode.SOLAR_CHARGE)
```

Same method names, same return types, just without `await`. The CLI uses this wrapper internally.

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
- §14a EnWG Modul 1 / Modul 3 grid-fee savings — see the [regulatory primer](https://mrebbert.github.io/1komma5-api/enwg14a/)

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
- Ruff-clean, mypy-strict, CodeQL-clean, 95 % coverage gate

## Python models

Every endpoint returns a typed [dataclass](https://docs.python.org/3/library/dataclasses.html) from `onekommafive.models`:

| Domain | Classes |
|--------|---------|
| System | `SystemInfo`, `SystemDetails`, `SystemCustomer`, `DeviceGateway`, `SiteStatus`, `SiteSystemInfo`, `Enwg14aModule`, `Asset`, `SiteDetails`, `SmartMeter` |
| User & customer | `User`, `ConnectedSystem`, `Customer` |
| Live & energy | `LiveOverview`, `EnergyData`, `EnergySlot`, `HeartbeatSavings` |
| Prices | `MarketPrices`, `PriceCustomizations`, `ComparisonPrice`, `PriceGuarantee`, `HeartbeatPrices`, `HeartbeatPriceWindow` |
| EV & EMS | `EVCharger`, `ChargingMode`, `Wallbox`, `EmsSettings`, `EmsManualDevice` |
| Weather | `WeatherData`, `WeatherDay`, `WeatherSlot`, `WEATHER_SYMBOLS` |
| AI & analytics | `OptimizationEvents`, `OptimizationEvent`, `SelfSufficiencyEvents`, `HeartbeatAiSummary`, `ImpactOverview`, `EnergyTrader`, `MonthlyTradingSavings` |
| Notifications | `Notification`, `NotificationsList`, `NotificationSettings`, `NotificationChannelSettings` |
| API meta | `SupportedVersions`, `VersionInfo` |

Every model exposes a `raw` attribute (`dict[str, Any]`) with the full untouched API response for fields that are not yet mapped. See the [FAQ entry](https://mrebbert.github.io/1komma5-api/faq/) on the escape hatch.

## Development

Full developer guide (setup, tests, lint, type-check, probe, release)
lives at **[Development](https://mrebbert.github.io/1komma5-api/development/)**.
Quick reference:

```bash
uv sync --all-extras
uv run pre-commit install
uv run pytest
```

Integration tests opt-in via `ONEKOMMAFIVE_USERNAME` / `ONEKOMMAFIVE_PASSWORD`
environment variables (read-only, no mutations). Contribution policy
and PR expectations: [CONTRIBUTING.md](CONTRIBUTING.md).

See [CHANGELOG.md](CHANGELOG.md) for the release history, [API.md](API.md)
for the full curl-level endpoint reference, and `scripts/probe_versions.py`
for the local version-bump probe.

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

Legacy accounts served only from `my.1komma5.io` / `api.gridx.de` are out of scope; see the [FAQ](https://mrebbert.github.io/1komma5-api/faq/).

## Related projects

### [1komma5-ha](https://github.com/mrebbert/1komma5-ha)

A Home Assistant integration built on top of this library. Exposes your 1KOMMA5° system as sensors, switches, and controls directly in Home Assistant.

## Credits

Large parts of this project are inspired by and based on the work of [Alex Birkner](https://github.com/BirknerAlex) and his [hacs_1komma5grad](https://github.com/BirknerAlex/hacs_1komma5grad) integration. Many thanks for paving the way.

## License

MIT — see [LICENSE](LICENSE).
