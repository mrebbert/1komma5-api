# FAQ

Known gotchas, recurring questions and the answers that save you a round
trip through the issue tracker.

## Authentication fails with "Login failed" or `invalid_auth` in Home Assistant, but my credentials work in the mobile app and on `my.1komma5.io`

Most likely cause: your account is served from the **legacy sign-in path**
and has no record in the 1KOMMA5° Auth0 tenant that this SDK talks to.

What the SDK supports:

- Auth0 PKCE against `auth.1komma5grad.com`.
- API traffic against `heartbeat.1komma5grad.com` and
  `customer-identity.1komma5grad.com`.

What exists in the wild but is **out of scope** here:

- Resource-Owner-Password grant against `gridx.eu.auth0.com` with
  audience `my.gridx`, API traffic against `api.gridx.de`. This is the
  legacy stack that the pre-acquisition gridX integration (see
  [derlangemarkus/1komma5grad_ha](https://github.com/derlangemarkus/1komma5grad_ha))
  spoke to. Accounts that still live only on `my.1komma5.io` tend to
  belong here.

Why the SDK will not grow legacy support:

- Different auth tenant, different grant type, different audience,
  different API host, different URL schema, different token semantics
  (`id_token` as bearer vs. `access_token`). A legacy variant would
  effectively be a second SDK, not a tenant switch.
- The author has no legacy test account; a second branch would ship
  without the live-integration coverage the current stack has.

If this is you: the mobile app may still work because its login flow
performs a backend-discovery step the SDK does not have. There is no
workaround on the SDK side. Vendor migration to the current stack is
the only route.

## Where does the CLI cache its token?

In `~/.cache/onekommafive/cli_token.json`, owned by the current user
and `chmod 600`. The cache is username-bound: if you change
`ONEKOMMAFIVE_USERNAME`, the SDK ignores the cached token and performs
a fresh login.

Tokens refresh automatically 60 seconds before their stated expiry; the
refresh token is used when the access token lapses. To force a fresh
login, delete the cache file.

The SDK itself (library use, not CLI) does not touch disk unless you
pass `cache_tokens=True` to `Client(...)`. Default is in-memory only.

## I get HTTP 400 on a date range endpoint

Date formats are not uniform across the API. The usual culprits:

- **`/energy-savings`** requires date-only, `YYYY-MM-DD`. Passing a
  datetime with a time component returns 400.
- **`/heartbeat-ai/optimizations`** and
  **`/heartbeat-ai/self-sufficiency`** require ISO-8601 with
  millisecond precision, URL-encoded:
  `%Y-%m-%dT%H:%M:%S.000Z` / `%Y-%m-%dT%H:%M:%S.999Z`.
- **`/charts/market-prices`** requires ISO-8601 with millisecond
  precision.
- **`/energy-historical`** accepts date-only; for `resolution=15m` the
  range must be a single day.

The CLI handles the formatting for you; the quirks matter only if you
call the API directly.

## I get HTTP 403 on `/price-guarantee`

The path segment there is the **site ID** (same as
`$ONEKOMMAFIVE_SYSTEM`), not the customer ID, despite the misleading
URL structure. Verified live: customer_id returns 403, site_id returns
200. See [API.md § price-guarantee](api.md).

## What does "Working hypothesis" mean in the API reference?

Fields marked that way are observed, not contracted. The API ships no
schema; everything in `API.md` comes from captured responses and the
daily observatory diff. "Working hypothesis" flags fields whose
semantics the author inferred (unit, direction, meaning) but could not
confirm against vendor documentation. Treat them as plausible defaults
to validate against your own data before relying on them.

## My observatory diff / live response contains a field the SDK does not expose

That is expected. The SDK deliberately maps only fields with stable
semantics; freshly observed ones land in `API.md` first and in the
dataclasses only once their meaning is confirmed. Raw responses are
always available via the `raw: dict` attribute on every model, so you
can read unmapped fields without waiting for an SDK release.

If a field is production-relevant, open an issue with a sanitized
sample and the observatory report that first showed it.

## Rate limits

The vendor publishes no limits. Empirically the SDK's defaults are
safe for interactive and daily-cron usage. Patterns worth avoiding:

- Tight loops over `get_optimizations` or
  `get_self_sufficiency_events` for long ranges without pacing.
- Simultaneous live-overview polls at sub-minute frequency across
  many sites.

If you hit a 429 or sustained 500s, pause for a minute and retry. The
Heartbeat backend occasionally returns 500 on perfectly valid requests
during vendor-side deploys; a single retry resolves it.

## What is §14a EnWG, Modul 1 and Modul 3?

See the dedicated primer in [§14a EnWG grid-fee bundle](enwg14a.md).

## `/ev-charging-sessions/active` returns `{"sessions": []}` even while my EV is charging

The endpoint only tracks **vendor-orchestrated** charging sessions, not
raw wallbox power flow. Two fields on the EV asset gate what you see:

- `connectionStatus.status` — anything but a concrete status (observed:
  `UNKNOWN`) means the backend has no live link to the vehicle itself.
- `dataSource` — `USER_INPUT` means the user types the state-of-charge
  manually; the backend has no OEM telemetry (VW WeConnect, Tesla API,
  etc.) to correlate against.

If **both** are set to the "no live link" variant, the Heartbeat
dashboard still shows the wallbox power
(`liveHeroView.evChargersAggregated.power`) because that comes straight
from the hardware, but there is no *session* for the backend to attach
start, target SoC, departure time and progress to. `active` therefore
stays empty. Verified live on 2026-10-14: 1.9 kW on
`evChargersAggregated.power`, `/ev-charging-sessions/active` returned
`{"sessions": []}` the whole time.

To see a populated response, the account needs an OEM-integrated EV
with `connectionStatus != UNKNOWN` and `dataSource != USER_INPUT`. Until
then, the endpoint is intentionally not wrapped by the SDK, and
`liveHeroView.evChargersAggregated.power` from
`System.get_live_overview()` is the right field to read live EV power.
