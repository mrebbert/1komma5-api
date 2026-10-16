# onekommafive

Python API client for the 1KOMMA5° Heartbeat API: wraps the
`heartbeat.1komma5grad.com` service that powers the 1KOMMA5° app
(home energy management: PV, battery, EV charger, heat pump,
dynamic tariff, §14a EnWG grid-fee bundles).

## Install

```bash
pip install onekommafive
```

Requires Python 3.13+.

## Quickstart

```python
import asyncio
from onekommafive import Client, Systems


async def main() -> None:
    async with Client("user@example.com", "s3cr3t") as client:
        systems = await Systems(client).get_systems()
        for system in systems:
            overview = await system.get_live_overview()
            print(system.id(), overview.pv_power, "W")


asyncio.run(main())
```

## Features

**Live and historical**

- Live power snapshot: PV, battery, grid, consumption, per-device flows, self-sufficiency
- Energy summary and timeseries for today or any historical range (`1h` / `15m`)
- Market electricity prices with grid costs and VAT (`1h` / `15m`)
- Weather forecast: today, tomorrow, plus 3-hour slots for 48 h
- Aggregated Heartbeat savings (EUR) for any date range

**Control**

- EV charger: charging mode, target SoC, departure time, current SoC
- EMS: automatic or manual override, Time-of-Use, per-device manual settings

**AI and analytics**

- AI optimisation decisions (battery / EV charging, with market-price context)
- Self-sufficiency events: granular battery-discharge trace
- Heartbeat AI performance summary: self-sufficiency, feed-in earnings, CO₂ saved, peak-price avoided
- Lifetime CO₂ savings (site, community, global estimate)
- Lifetime and monthly energy-trader savings
- §14a EnWG Modul 1 / Modul 3 grid-fee savings; see the [regulatory primer](enwg14a.md)

**Metadata and configuration**

- System, site, and full customer records
- Site status and hardware asset inventory (inverter, heat pump, meter, EV charger with manufacturer / model / serial / firmware / network address)
- Active feature flags per site (Dynamic Pulse, Time-of-Use optimisation, smart charging)
- Wallbox hardware (distinct from vehicle-side EV profile)
- Smart-meter registration (ENTSO-E control-area EIC, DSO BDEW code, concession fee)
- User profile plus every site the user is authorised for
- Notifications and per-category channel preferences
- User-configured and comparison prices, contractual price guarantee
- API version compatibility check

**Cross-cutting**

- OAuth2 + PKCE authentication matching the mobile-app flow, with automatic silent token refresh
- Optional persistent token cache (`chmod 600`, user-bound) so subsequent CLI calls skip the login round-trip
- Built-in `1k5` CLI covering every read endpoint and all mutations
- Ruff-clean, mypy-strict, CodeQL-clean, 95% coverage gate

## What's on this site

- **[CLI reference](cli.md)** — every `1k5` command with flags, example
  output and the setter commands for EV / EMS.
- **[API reference](api.md)** — curl-level documentation of every
  endpoint the client wraps: URL, request parameters, response shape,
  known quirks, VAT and §14a EnWG semantics.
- **[§14a EnWG grid-fee bundle](enwg14a.md)** — regulatory primer,
  Modul 1 vs. Modul 3, exact SDK field mapping, convenience method.
- **[FAQ](faq.md)** — legacy sign-in, token cache, HTTP-400 date
  quirks, 403 on `price-guarantee`, and other recurring questions.
- **[Development](development.md)** — setup, tests, lint, type-check,
  probe-versions, release flow.
- **Postman collection** — exported alongside the API reference,
  available [in the repo](https://github.com/mrebbert/1komma5-api/tree/main/postman).

## About

The library is a reverse-engineering project maintained by the author
against their own 1KOMMA5° system. Response shapes are observed, not
contracted; "working hypothesis" labels in the API reference mark
fields whose semantics are inferred rather than documented by the
vendor. A daily observatory run (separate repository) tracks
response-shape and URL changes and feeds this documentation.

- **Package on PyPI**: <https://pypi.org/project/onekommafive/>
- **Home Assistant integration**: <https://github.com/mrebbert/1komma5-ha>
