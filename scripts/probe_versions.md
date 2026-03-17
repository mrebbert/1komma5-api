# scripts/probe_versions.py

Probes the 1KOMMA5° Heartbeat API for newer endpoint versions than the ones currently used in the client library.

## What it does

1. **Parses** all versioned API paths (`/api/vN/…`) from the `onekommafive/` source files to build a map of `endpoint → current version`.
2. **Probes** each endpoint for higher versions (`current+1` up to v7) using an authenticated GET request.
3. **Reports** any endpoint where a higher version responds (HTTP status other than 404/405/401/403).
4. **Compares** the JSON response of the current and the newer version and summarises structural differences (added / removed fields).

Run this script after a 1KOMMA5° app update to catch API version bumps before they break the library.

## Usage

```bash
# With username + password (token is obtained automatically)
ONEKOMMAFIVE_USERNAME=user@example.com \
ONEKOMMAFIVE_PASSWORD=s3cr3t \
PYTHONPATH=. ./venv/bin/python scripts/probe_versions.py

# With an existing Bearer token
BEARER_TOKEN=<jwt> \
ONEKOMMAFIVE_SYSTEM=<system-uuid> \
PYTHONPATH=. ./venv/bin/python scripts/probe_versions.py
```

## Example output — nothing new

```
Parsing current API versions from source …
Found 11 distinct endpoint paths in client.

Obtaining credentials …
System ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

Path                                                     Current  Probing …
---------------------------------------------------------------------------
/sites/{id}/assets/evs/displayed-ev-charging-modes            v1  ok
/systems                                                      v2  ok
/systems/{id}                                                 v2  ok
/systems/{id}/charts/market-prices                            v4  ok
/systems/{id}/devices/evs                                     v1  ok
/systems/{id}/ems/actions/get-settings                        v1  ok
/systems/{id}/ems/actions/set-manual-override                 v1  ok
/systems/{id}/energy-historical                               v3  ok
/systems/{id}/energy-today                                    v2  ok
/systems/{id}/live-overview                                   v3  ok
/users/me                                                     v1  ok

No newer versions found. Client is up to date.
```

## Example output — new version found

```
/systems/{id}/energy-today                                    v2  *** v3=200

======================================================================
POSSIBLE NEW VERSIONS FOUND:
======================================================================
  /systems/{id}/energy-today
    current: v2  (defined in system.py)
    newer:   v3 → HTTP 200
    diff:    new fields: `consumption.consumers.ac`, `consumption.consumers.heatPumpTotal`
```

## Notes

- Only GET requests are made — no data is modified.
- Endpoints returning 401/403 are treated as non-existent (token scope issue, not a new version).
- The diff compares the top-level and nested JSON key structure of the current vs. newest version. It does not diff individual values.
- `MAX_VERSION` (default: 7) can be raised in the script if needed.
