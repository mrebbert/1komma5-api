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

For the full feature tour, see the project
[README on GitHub](https://github.com/mrebbert/1komma5-api#readme).

## What's on this site

- **[API reference](api.md)** — curl-level documentation of every
  endpoint the client wraps: URL, request parameters, response shape,
  known quirks, VAT and §14a EnWG semantics.
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
