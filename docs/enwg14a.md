# §14a EnWG grid-fee bundle

Primer on the two §14a EnWG modules that the Heartbeat API reports on
the `heartbeat-prices` endpoint, with the exact field mapping the SDK
exposes.

## Regulatory background

§14a Energiewirtschaftsgesetz (EnWG) governs how operators of
controllable consumption devices (heat pumps, EV chargers, batteries
over 4.2 kW) are compensated by the Distribution-System Operator for
accepting network-side grid interventions. Since **BK6-22-300** (BNetzA
decision of November 2023, binding from 2024), the DSO must offer **one
of three modules** to every §14a-registered site. The vendor splits the
observed data accordingly:

| Module | Compensation mechanism | SDK coverage |
|---|---|---|
| **Modul 1** | Flat annual reduction of the grid fee, fixed €/year | fully mapped |
| **Modul 2** | Percentage reduction of the controllable device's grid fee | not seen in captures |
| **Modul 3** | Time-variable grid fee (HT / NT), savings vs. a baseline | fully mapped |

Modul 2 could ship later if we observe it; the current wrapper
handles its absence by returning `None` across all Modul-2-shaped
fields that would be inferred from it.

## Modul 1: flat annual reduction

Fields on `HeartbeatPriceWindow`:

| Attribute | Type | Semantics |
|---|---|---|
| `module1_provisioning_date` | `str \| None` | ISO date when the Modul 1 bundle was provisioned. `None` until the site opts in. |
| `module1_active_days` | `int \| None` | Days counted as active in this window. Currently mirrors the window length. |
| `module1_savings_per_year_eur` | `float \| None` | Annual Modul-1 savings projected by the backend, constant across windows. |
| `module1_total_savings_eur` | `float \| None` | Window-accumulated savings. Backend formula: `savings_per_year × active_days / 365`. |

A non-participating account carries `None` on all four across every
window. Opting in flips all four to populated values on the next
backend tick.

## Where to read the enrolment flag

Two independent sources on the SDK side:

1. **`SiteSystemInfo.enwg14a_module`** (from `System.get_system_info()`)
   is the authoritative single-field answer: either `None` or an
   `Enwg14aModule(value, valid_from_date)` with `value` observed as
   `"module-1"`. Cheap, no price arithmetic involved.
2. **`HeartbeatPriceWindow`** fields: `module1_provisioning_date`
   populated means Modul 1; `module3_total_savings_eur` populated means
   Modul 3. Useful when you already have a `HeartbeatPrices` instance
   in hand.

The two sources are redundant by design; they came in with separate
backend rollouts and are expected to agree.

## Modul 3: time-variable grid fees

Modul 3 ties the controllable device's grid fee to time-of-use tariffs
(**HT**, Hochtarif / **NT**, Niedertarif). The backend computes savings
by comparing what the site actually paid under HT/NT to what it would
have paid under the uniform baseline tariff.

Fields on `HeartbeatPriceWindow`:

| Attribute | Type | Semantics |
|---|---|---|
| `comparison_grid_fee_eur_per_kwh` | `float \| None` | The baseline (uniform) grid-fee tariff used for the comparison, in EUR/kWh. |
| `comparison_grid_fees_total_eur` | `float \| None` | What the site would have paid under the baseline tariff in this window. |
| `variable_grid_fee_eur_per_kwh` | `float \| None` | Effective variable (HT/NT) grid-fee rate for the window, in EUR/kWh. Counterpart to `comparison_grid_fee_eur_per_kwh`. |
| `variable_grid_fees_total_eur` | `float \| None` | What the site actually paid under the HT/NT tariff. |
| `module3_total_savings_eur` | `float \| None` | Net Modul-3 savings for the window. Backend formula: `comparison_grid_fees_total − variable_grid_fees_total`. |
| `enwg14a_total_savings_eur` | `float \| None` | Combined Modul-1 + Modul-3 savings. Carries the §14a envelope that the UI surfaces to the user. |

All six are `None` until the site opts into Modul 3. The flip usually
coincides with the DSO's rollout milestones.

## Convenience method

For code that just needs the Modul-3 savings for a given window:

```python
from onekommafive import HeartbeatPrices


prices: HeartbeatPrices = await system.get_heartbeat_prices()
monthly = prices.module3_savings(window="month")
yearly = prices.module3_savings(window="year")
```

Valid window names: `day`, `week`, `month`, `halfYear`, `year`. Returns
`None` for accounts not on Modul 3; raises `ValueError` on an unknown
window name.

For the full breakdown, iterate the windows directly:

```python
for name in ("day", "week", "month", "halfYear", "year"):
    win = getattr(prices, name)
    if win.module3_total_savings_eur is None:
        continue
    print(
        f"{name:>8}: "
        f"baseline={win.comparison_grid_fees_total_eur:.2f} € "
        f"actual={win.variable_grid_fees_total_eur:.2f} € "
        f"savings={win.module3_total_savings_eur:.2f} €"
    )
```

## CLI

`1k5 heartbeat-prices` prints a §14a section after the main table when
at least one window carries populated Modul-1 or Modul-3 values. On a
non-participating account the section is suppressed, so the output
stays clean.

## Related

- Full response reference: [API.md § heartbeat-prices](api.md).
- Daily observatory diff that first flagged Modul-3 (2026-10-09):
  tracked out-of-tree in the sibling repo.
- BNetzA decision text: BK6-22-300 (search the BNetzA portal).
