#!/usr/bin/env python3
"""Simple CLI for the 1KOMMA5° Heartbeat API.

Usage:
    python cli.py info             # basic system metadata (v4)
    python cli.py details          # extended system metadata incl. gateways + customer (v1)
    python cli.py assets           # site connection status + installed hardware assets
    python cli.py features [--customer-id UUID]  # active feature flags
    python cli.py live             # net grid power + separate import/export
    python cli.py weather          # weather forecast (today/tomorrow + optional 3h slots)
    python cli.py weather --forecasts
    python cli.py prices [--resolution 1h|15m]
    python cli.py ev
    python cli.py ev-modes
    python cli.py set-ev-mode <mode> [--ev <ev_id>]
    python cli.py set-ev-target-soc <soc> [--ev <ev_id>]
    python cli.py set-ev-departure <HH:MM> [--ev <ev_id>]
    python cli.py optimizations [--from YYYY-MM-DD[THH:MM]] [--to YYYY-MM-DD[THH:MM]]
    python cli.py savings [--from YYYY-MM-DD] [--to YYYY-MM-DD]
    python cli.py impact
    python cli.py trader
    python cli.py ai-summary [--resolution 1W|1M|1Y]
    python cli.py heartbeat-prices
    python cli.py price-config
    python cli.py comparison-price
    python cli.py price-guarantee [--customer-id UUID]
    python cli.py wallboxes
    python cli.py smart-meter
    python cli.py monthly-trading
    python cli.py ai-decisions [--from YYYY-MM-DD[THH:MM]] [--to YYYY-MM-DD[THH:MM]]
    python cli.py site-details
    python cli.py customer [--customer-id UUID]
    python cli.py subscriptions [--customer-id UUID]
    python cli.py notifications
    python cli.py notification-settings
    python cli.py versions
    python cli.py me
    python cli.py ems
    python cli.py set-ems auto|manual

Credentials are read from the environment:
    ONEKOMMAFIVE_USERNAME
    ONEKOMMAFIVE_PASSWORD

An optional ONEKOMMAFIVE_SYSTEM env var selects a system by ID;
otherwise the first system is used.

After the first login the OAuth2 token set is cached in
~/.cache/onekommafive/cli_token.json (chmod 600) so subsequent CLI
invocations skip the login round-trip until the JWT expires (~1h).
Set ONEKOMMAFIVE_NO_CACHE=1 to disable, or delete the file to force a
fresh login.
"""

from __future__ import annotations

import argparse
import datetime
import os
import sys
from pathlib import Path

from onekommafive import Client, Systems
from onekommafive.models import ChargingMode, MarketPrices

# Token cache for the CLI: skips the OAuth2 login round-trip on subsequent
# invocations while the JWT is still valid (~1h). Delete the file or set
# ONEKOMMAFIVE_NO_CACHE=1 to force a fresh login.
_CLI_TOKEN_CACHE = Path.home() / ".cache" / "onekommafive" / "cli_token.json"


def _client() -> Client:
    username = os.environ.get("ONEKOMMAFIVE_USERNAME")
    password = os.environ.get("ONEKOMMAFIVE_PASSWORD")
    if not username or not password:
        sys.exit("Error: set ONEKOMMAFIVE_USERNAME and ONEKOMMAFIVE_PASSWORD")
    cache = None if os.environ.get("ONEKOMMAFIVE_NO_CACHE") else _CLI_TOKEN_CACHE
    return Client(username, password, token_cache=cache)


def _system(client: Client):
    systems = Systems(client).get_systems()
    if not systems:
        sys.exit("Error: no systems found on this account")
    target_id = os.environ.get("ONEKOMMAFIVE_SYSTEM")
    if target_id:
        for s in systems:
            if s.id() == target_id:
                return s
        sys.exit(f"Error: system {target_id!r} not found")
    return systems[0]


def _get_system():
    return _system(_client())


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

def _resolve_customer_id(args: argparse.Namespace, system) -> str:
    """Return ``args.customer_id`` if set, else look it up via system details.

    Exits with a descriptive error if neither source yields an ID.
    """
    if args.customer_id:
        return args.customer_id
    customer_id = system.get_details().customer_id
    if not customer_id:
        sys.exit("Error: system details do not expose a customer_id; pass --customer-id explicitly")
    return customer_id


def _format_address(o) -> str:
    parts = filter(None, [
        o.address_line1,
        o.address_line2,
        f"{o.address_zip_code} {o.address_city}".strip() or None,
        o.address_country,
    ])
    return ", ".join(parts) or "—"


def cmd_info(args: argparse.Namespace) -> None:
    system = _get_system()
    si = system.info()
    print(f"System:       {si.id}")
    print(f"Name:         {si.name or '—'}")
    print(f"Status:       {si.status or '—'}")
    print(f"Address:      {_format_address(si)}")
    if si.address_latitude is not None and si.address_longitude is not None:
        print(f"Coordinates:  {si.address_latitude:.4f}, {si.address_longitude:.4f}")
    print(f"Customer ID:  {si.customer_id or '—'}")
    print(f"Dynamic Pulse:        {'yes' if si.dynamic_pulse_compatible else 'no'}")
    if si.energy_trader_active is not None:
        print(f"Energy trading:       {'yes' if si.energy_trader_active else 'no'}")
    if si.electricity_contract_active is not None:
        print(f"Electricity contract: {'yes' if si.electricity_contract_active else 'no'}")
    print(f"Created:      {si.created_at or '—'}")
    print(f"Updated:      {si.updated_at or '—'}")


def cmd_details(args: argparse.Namespace) -> None:
    system = _get_system()
    d = system.get_details()
    print(f"System:       {d.id}")
    print(f"Name:         {d.name or '—'}")
    print(f"Status:       {d.status or '—'}")
    print(f"EMP type:     {d.emp_type or '—'}")
    print(f"Address:      {_format_address(d)}")
    if d.address_latitude is not None and d.address_longitude is not None:
        print(f"Coordinates:  {d.address_latitude:.4f}, {d.address_longitude:.4f}")
    if d.customer is not None:
        name = " ".join(filter(None, [d.customer.first_name, d.customer.last_name])) or "—"
        print(f"Customer:     {name}  <{d.customer.email or '—'}>  ({d.customer.id})")
    elif d.customer_id:
        print(f"Customer ID:  {d.customer_id}")
    if d.technical_contact_name or d.technical_contact_id:
        contact = d.technical_contact_name or d.technical_contact_id
        print(f"Installer:    {contact}")
    print(f"Dynamic Pulse:        {'yes' if d.dynamic_pulse_compatible else 'no'}")
    if d.energy_trader_active is not None:
        print(f"Energy trading:       {'yes' if d.energy_trader_active else 'no'}")
    if d.electricity_contract_active is not None:
        print(f"Electricity contract: {'yes' if d.electricity_contract_active else 'no'}")
    if d.has_third_party_smart_meter is not None:
        sm = "yes" if d.has_third_party_smart_meter else "no"
        extra = f"  (meter {d.third_party_smart_meter_meter_id})" if d.third_party_smart_meter_meter_id else ""
        print(f"3rd-party smart meter: {sm}{extra}")
    if d.earliest_measurement:
        print(f"Earliest measurement: {d.earliest_measurement}")
    print(f"Created:      {d.created_at or '—'}")
    print(f"Updated:      {d.updated_at or '—'}")
    if d.device_gateways:
        print()
        print("Device gateways:")
        for gw in d.device_gateways:
            print(f"  {gw.id}")
            if gw.serial_number:
                print(f"    Serial:        {gw.serial_number}")
            if gw.gridx_start_code:
                print(f"    GridX code:    {gw.gridx_start_code}")
            if gw.installation_date:
                print(f"    Installed:     {gw.installation_date}")


def cmd_assets(args: argparse.Namespace) -> None:
    system = _get_system()
    s = system.get_status_and_assets()
    print(f"System:       {system.id()}")
    print(f"Site status:  {s.status or '—'}")
    if not s.assets:
        print("No assets registered.")
        return
    print()
    for a in s.assets:
        label = a.name or a.type
        print(f"  {a.type:<11}  {label}")
        if a.manufacturer or a.model:
            print(f"    Hardware:    {a.manufacturer or '—'}  {a.model or ''}".rstrip())
        if a.serial_number:
            print(f"    Serial:      {a.serial_number}")
        if a.firmware:
            print(f"    Firmware:    {a.firmware}")
        if a.network_address:
            print(f"    Network:     {a.network_address}")
        if a.heat_pump_meter_type:
            print(f"    Meter type:  {a.heat_pump_meter_type}")
        print(f"    Status:      {a.connection_status or '—'}  (id {a.id})")


def cmd_features(args: argparse.Namespace) -> None:
    system = _get_system()
    customer_id = _resolve_customer_id(args, system)
    features = system.get_active_features(customer_id)
    print(f"System:       {system.id()}")
    print(f"Customer:     {customer_id}")
    if not features:
        print("No active features.")
        return
    print(f"Active features ({len(features)}):")
    for f in features:
        print(f"  {f}")


def cmd_live(args: argparse.Namespace) -> None:
    system = _get_system()
    ov = system.get_live_overview()
    print(f"System:       {system.id()}")
    print(f"Status:       {ov.status or '—'}")
    print(f"PV power:     {_w(ov.pv_power)}")
    print(f"Battery:      {_w(ov.battery_power)}  SoC {_pct(ov.battery_soc)}")
    print(f"Grid:         {_w(ov.grid_power)}  (import {_w(ov.grid_consumption_power)}  export {_w(ov.grid_feed_in_power)})")
    print(f"Consumption:  {_w(ov.consumption_power)}")
    print(f"Household:    {_w(ov.household_power)}")
    if ov.ev_chargers_power is not None:
        print(f"EV chargers:  {_w(ov.ev_chargers_power)}")
    if ov.heat_pumps_power is not None:
        print(f"Heat pumps:   {_w(ov.heat_pumps_power)}")
    if ov.acs_power is not None:
        print(f"ACs:          {_w(ov.acs_power)}")
    if ov.self_sufficiency is not None:
        print(f"Self-suff.:   {_pct(ov.self_sufficiency * 100)}")


def cmd_prices(args: argparse.Namespace) -> None:
    system = _get_system()
    today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start = today
    end = today + datetime.timedelta(days=1)
    mp: MarketPrices = system.get_prices(
        start=start,
        end=end,
        resolution=args.resolution,
    )
    vat_pct = f"{mp.vat * 100:.0f}%"
    print(f"System:        {system.id()}")
    print(f"Period:        {start.date()}")
    print()
    print(f"{'':25}  {'avg':>9}  {'high':>9}  {'low':>9}  EUR/kWh")
    print(f"{'Spot':25}  {mp.average_price:>9.4f}  {mp.highest_price:>9.4f}  {mp.lowest_price:>9.4f}")
    print(f"{'+ Grid':25}  {mp.average_price_with_grid_costs:>9.4f}  {mp.highest_price_with_grid_costs:>9.4f}  {mp.lowest_price_with_grid_costs:>9.4f}")
    print(f"{'All-in (incl. VAT)':25}  {mp.average_price_all_in:>9.4f}  {mp.highest_price_all_in:>9.4f}  {mp.lowest_price_all_in:>9.4f}")
    print()
    gc_parts = []
    if mp.grid_cost_energy_tax is not None:
        gc_parts.append(f"energy tax {mp.grid_cost_energy_tax:.4f}")
    if mp.grid_cost_purchasing is not None and mp.grid_cost_purchasing != 0:
        gc_parts.append(f"purchasing {mp.grid_cost_purchasing:.4f}")
    if mp.grid_cost_fixed_tariff is not None and mp.grid_cost_fixed_tariff != 0:
        gc_parts.append(f"fixed {mp.grid_cost_fixed_tariff:.4f}")
    if mp.grid_cost_dynamic_markup is not None and mp.grid_cost_dynamic_markup != 0:
        gc_parts.append(f"dynamic {mp.grid_cost_dynamic_markup:.4f}")
    gc_detail = f"  ({', '.join(gc_parts)})" if gc_parts else ""
    print(f"Grid costs:    {mp.grid_costs_total:.4f} EUR/kWh  (VAT {vat_pct}){gc_detail}")
    print()
    print(f"{'Timestamp':<25}  {'Spot':>9}  {'+ Grid':>9}  {'All-in':>9}")
    print("-" * 59)
    for ts in sorted(mp.prices):
        spot = mp.prices[ts]
        grid = mp.prices_with_grid_costs.get(ts, float("nan"))
        all_in = mp.prices_with_grid_costs_and_vat.get(ts, float("nan"))
        print(f"{ts:<25}  {spot:>9.4f}  {grid:>9.4f}  {all_in:>9.4f}")


def cmd_price_config(args: argparse.Namespace) -> None:
    system = _get_system()
    p = system.get_price_customizations()
    print(f"System:            {system.id()}")
    if p.grid_energy_price_eur_per_kwh is not None:
        print(f"Grid price:        {p.grid_energy_price_eur_per_kwh:.4f} €/kWh")
    if p.comparison_energy_price_eur_per_kwh is not None:
        print(f"Comparison price:  {p.comparison_energy_price_eur_per_kwh:.4f} €/kWh")
    if p.monthly_base_price_eur is not None:
        print(f"Monthly base:      {p.monthly_base_price_eur:.2f} €")


def cmd_comparison_price(args: argparse.Namespace) -> None:
    system = _get_system()
    c = system.get_comparison_price()
    print(f"System:            {system.id()}")
    if c.price_eur_per_kwh is not None:
        print(f"Comparison price:  {c.price_eur_per_kwh:.4f} €/kWh")
    else:
        print("Comparison price:  —")


def cmd_price_guarantee(args: argparse.Namespace) -> None:
    system = _get_system()
    customer_id = _resolve_customer_id(args, system)
    pg = system.get_price_guarantee(customer_id)
    print(f"System:    {system.id()}")
    print(f"Customer:  {customer_id}")
    if pg.value is None:
        print("Guarantee: —")
    else:
        unit = pg.unit or ""
        version = f"  ({pg.version})" if pg.version else ""
        print(f"Guarantee: {pg.value:g} {unit}{version}")


def cmd_wallboxes(args: argparse.Namespace) -> None:
    system = _get_system()
    boxes = system.get_wallboxes()
    print(f"System: {system.id()}")
    if not boxes:
        print("No wallboxes registered.")
        return
    for w in boxes:
        print(f"  {w.name or '—'}")
        print(f"    ID:           {w.id or '—'}")
        print(f"    Assigned EV:  {w.assigned_ev_id or '—'}")


def cmd_smart_meter(args: argparse.Namespace) -> None:
    system = _get_system()
    m = system.get_smart_meter()
    print(f"Site:              {m.site_id or system.id()}")
    print(f"Control area EIC: {m.control_area_eic or '—'}")
    print(f"DSO BDEW code:    {m.dso_bdew_code or '—'}")
    if m.concession_fee_eur_per_kwh is not None:
        print(f"Concession fee:   {m.concession_fee_eur_per_kwh:.4f} €/kWh")


def cmd_monthly_trading(args: argparse.Namespace) -> None:
    system = _get_system()
    s = system.get_monthly_trading_savings()
    print(f"System:                    {system.id()}")
    if s.average_past_variable_savings_eur is None:
        print("Avg. monthly savings:      —")
    else:
        print(f"Avg. monthly savings:      {s.average_past_variable_savings_eur:.2f} €")


def cmd_ai_decisions(args: argparse.Namespace) -> None:
    today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    try:
        start = _parse_dt(args.from_date, end_of_day=False) if args.from_date else today
        end = _parse_dt(args.to_date, end_of_day=True) if args.to_date else today.replace(hour=23, minute=59, second=59)
    except ValueError as e:
        sys.exit(f"Error: invalid date — {e}")
    system = _get_system()
    result = system.get_self_sufficiency_events(start=start, end=end)
    print(f"System:  {system.id()}")
    print(f"Period:  {start.date()} – {end.date()}")
    print(f"Events:  {len(result.events)}")
    if not result.events:
        return
    print()
    print(f"{'Timestamp':<22}  {'Asset':<8}  {'Decision':<26}  {'Price':>9}  {'SoC':>4}")
    print("-" * 80)
    for ev in sorted(result.events, key=lambda e: e.timestamp):
        soc = f"{ev.state_of_charge}%" if ev.state_of_charge is not None else "—"
        price = f"{ev.market_price:.2f}" if ev.market_price is not None else "—"
        ts = ev.from_time[:19].replace("T", " ")
        print(f"{ts:<22}  {ev.asset:<8}  {ev.decision:<26}  {price:>9}  {soc:>4}")


def cmd_site_details(args: argparse.Namespace) -> None:
    system = _get_system()
    d = system.get_site_details()
    print(f"Site:              {d.id}")
    print(f"Name:              {d.name or '—'}")
    print(f"Status:            {d.status or '—'}")
    print(f"EMP type:          {d.emp_type or '—'}")
    print(f"Bidding zone:      {d.bidding_zone or '—'}  ({d.bidding_zone_eic or '—'})")
    print(f"EMS mode:          {d.ems_mode or '—'}")
    print(f"EMS state:         {d.ems_state or '—'}")
    if d.ems_state_reasons:
        print(f"EMS state reasons: {', '.join(d.ems_state_reasons)}")
    print(f"Address:           {_format_address(d)}")
    if d.address_latitude is not None and d.address_longitude is not None:
        print(f"Coordinates:       {d.address_latitude:.4f}, {d.address_longitude:.4f}")
    print(f"Customer ID:       {d.customer_id or '—'}")
    if d.customer is not None:
        name = " ".join(filter(None, [d.customer.first_name, d.customer.last_name])) or "—"
        print(f"Customer:          {name}  <{d.customer.email or '—'}>")
    if d.technical_contact_name:
        print(f"Installer:         {d.technical_contact_name}")
    print(f"Dynamic Pulse:     {'yes' if d.dynamic_pulse_compatible else 'no'}")
    if d.energy_trader_active is not None:
        print(f"Energy trading:    {'yes' if d.energy_trader_active else 'no'}")
    if d.electricity_contract_active is not None:
        print(f"Electricity ctr.:  {'yes' if d.electricity_contract_active else 'no'}")
    if d.impacted_by_enwg is not None:
        print(f"§14a EnWG:         {'yes' if d.impacted_by_enwg else 'no'}")
    if d.grid_connection_point_phases is not None:
        print(f"Grid phases:       {d.grid_connection_point_phases}")
    if d.max_current_per_phase_ampere is not None:
        print(f"Max A/phase:       {d.max_current_per_phase_ampere:g} A")
    if d.earliest_measurement:
        print(f"Earliest measurement: {d.earliest_measurement}")
    if d.emp_reference_id:
        print(f"EMP reference:     {d.emp_reference_id}")
    print(f"Updated:           {d.updated_at or '—'}")


def cmd_customer(args: argparse.Namespace) -> None:
    system = _get_system()
    customer_id = _resolve_customer_id(args, system)
    c = system.get_customer(customer_id)
    name = " ".join(filter(None, [c.first_name, c.last_name])) or "—"
    print(f"Customer:   {c.id}")
    print(f"Name:       {name}")
    print(f"Email:      {c.contact_email or '—'}")
    if c.contact_phone:
        print(f"Phone:      {c.contact_phone}")
    if c.company_name:
        print(f"Company:    {c.company_name}")
    print(f"Address:    {_format_address(c)}")
    print(f"Type:       {c.customer_type or '—'}")
    if c.crm_branch_location:
        print(f"Branch:     {c.crm_branch_location}")


def cmd_subscriptions(args: argparse.Namespace) -> None:
    system = _get_system()
    customer_id = _resolve_customer_id(args, system)
    result = system.get_subscriptions(customer_id)

    print(f"Customer:  {customer_id}")
    print(f"Subscriptions ({result.total_items}):")
    if not result.subscriptions:
        return
    print()
    header = f"  {'Type':<18} {'Status':<8} {'Price/month':>12}  {'Notice':>8}   {'Renewal':<10} Since"
    print(header)
    print("  " + "-" * (len(header) - 2))

    monthly_total = 0.0
    for s in result.subscriptions:
        price_str = f"{s.price_eur:.2f} €" if s.price_eur is not None else "—"
        if s.price_eur:
            monthly_total += s.price_eur
        notice = (
            f"{s.notice_period_number} mo"
            if s.notice_period_number is not None and (s.notice_period_interval or "").upper() == "MONTHS"
            else (str(s.notice_period_number) if s.notice_period_number is not None else "—")
        )
        since = s.signed_date[:10] if s.signed_date else (s.start_date[:10] if s.start_date else "—")
        print(f"  {s.type:<18} {s.status:<8} {price_str:>12}  {notice:>8}   {s.renewal or '—':<10} {since}")

    # DYNAMIC_PULSE price guarantee detail line
    for s in result.subscriptions:
        if s.type == "DYNAMIC_PULSE" and s.price_guarantee_value is not None:
            version = f" ({s.price_guarantee_version})" if s.price_guarantee_version else ""
            print()
            print(f"  DYNAMIC_PULSE price guarantee: {s.price_guarantee_value:g} {s.price_guarantee_unit or ''}{version}")
            break

    print()
    print(f"Total monthly: {monthly_total:.2f} €")


def cmd_notifications(args: argparse.Namespace) -> None:
    system = _get_system()
    result = system.get_notifications()
    print(f"System:  {system.id()}")
    print(f"Count:   {len(result.notifications)}")
    if not result.notifications:
        return
    print()
    for n in result.notifications:
        marker = " " if n.read else "*"
        ts = (n.created_at or "")[:19].replace("T", " ")
        print(f"  {marker} [{ts}] {n.type}")
        if n.title:
            print(f"       {n.title}")
        if n.body:
            print(f"       {n.body}")


def cmd_notification_settings(args: argparse.Namespace) -> None:
    system = _get_system()
    s = system.get_notification_settings()
    print(f"System:  {system.id()}")
    print(f"Locale:  {s.lang_code or '—'}")
    print()
    for category, entries in s.settings.items():
        if not entries:
            print(f"  {category:<40}  (not subscribed)")
            continue
        for e in entries:
            active = [name for name, on in [("app", e.app), ("push", e.push), ("email", e.email)] if on]
            ch = ", ".join(active) if active else "(no channels)"
            print(f"  {category:<40}  {ch}")


def cmd_versions(args: argparse.Namespace) -> None:
    v = _client().get_supported_versions()
    print(f"{'':<10}  {'target':<10}  minimum")
    print("-" * 34)
    print(f"{'b2b':<10}  {v.b2b.target_version or '—':<10}  {v.b2b.minimum_supported_version or '—'}")
    print(f"{'b2c':<10}  {v.b2c.target_version or '—':<10}  {v.b2c.minimum_supported_version or '—'}")


def cmd_me(args: argparse.Namespace) -> None:
    u = _client().get_user()
    name = " ".join(filter(None, [u.first_name, u.last_name])) or "—"
    print(f"User:      {u.id}")
    print(f"Name:      {name}")
    print(f"Email:     {u.email or '—'}")
    if u.phone:
        print(f"Phone:     {u.phone}")
    print(f"Status:    {u.status or '—'}")
    if u.external_id:
        print(f"External:  {u.external_id}")
    if u.created_at:
        print(f"Created:   {u.created_at}")
    if u.connected_systems:
        print()
        print(f"Connected systems ({len(u.connected_systems)}):")
        for s in u.connected_systems:
            print(f"  {s.system_id}  {s.name or '—'}")
            print(f"    {_format_address(s)}")


def cmd_impact(args: argparse.Namespace) -> None:
    system = _get_system()
    i = system.get_impact_overview()
    print(f"System:            {system.id()}")
    print(f"CO2 saved (site):  {i.co2_savings_kg:,.1f} kg" if i.co2_savings_kg is not None else "CO2 saved (site):  —")
    if i.co2_collective_savings_kg is not None:
        print(f"CO2 (community):   {i.co2_collective_savings_kg / 1000:,.0f} t")
    if i.co2_global_savings_estimate_tons is not None:
        print(f"CO2 (global est.): {i.co2_global_savings_estimate_tons:,.0f} t")


def cmd_trader(args: argparse.Namespace) -> None:
    system = _get_system()
    t = system.get_energy_trader()
    print(f"System:                {system.id()}")
    print(f"Status:                {t.status or '—'}")
    if t.green_energy_savings_eur is not None:
        print(f"Green energy savings:  {t.green_energy_savings_eur:,.2f} €")
    if t.energy_trader_savings_eur is not None:
        print(f"Energy trader savings: {t.energy_trader_savings_eur:,.2f} €")


def cmd_ai_summary(args: argparse.Namespace) -> None:
    system = _get_system()
    s = system.get_heartbeat_ai_summary(resolution=args.resolution)
    print(f"System:      {system.id()}")
    print(f"Resolution:  {s.resolution}")
    if s.self_sufficiency_percent is not None:
        print(f"Self-suff.:  {s.self_sufficiency_percent * 100:.1f}%   "
              f"(solar {s.self_sufficiency_by_solar_kwh:.1f} kWh, "
              f"battery {s.self_sufficiency_by_battery_kwh:.1f} kWh)")
    if s.earned_amount_eur is not None:
        feed_in = f" @ {s.feed_in_price_eur_per_kwh:.4f} €/kWh" if s.feed_in_price_eur_per_kwh is not None else ""
        print(f"Earned:      {s.earned_amount_eur:.2f} €   "
              f"({s.sold_energy_kwh:.1f} kWh sold{feed_in})")
    if s.co2_saved_kg is not None:
        car = f", ≈ {s.car_travel_emission_km:.0f} car km" if s.car_travel_emission_km is not None else ""
        prod = f" (PV {s.production_kwh:.1f} kWh)" if s.production_kwh is not None else ""
        print(f"CO2 saved:   {s.co2_saved_kg:.1f} kg{car}{prod}")
    if s.heartbeat_price_eur_per_kwh is not None:
        print(f"HB price:    {s.heartbeat_price_eur_per_kwh:.4f} €/kWh")
    if s.peak_price_avoided_eur is not None:
        detail = ""
        if s.peak_grid_charging_cost_eur is not None and s.peak_battery_charging_cost_eur is not None:
            detail = f"  (grid {s.peak_grid_charging_cost_eur:.2f} € − battery {s.peak_battery_charging_cost_eur:.2f} €)"
        print(f"Peak avoided:{s.peak_price_avoided_eur:>7.2f} €{detail}")


def cmd_heartbeat_prices(args: argparse.Namespace) -> None:
    system = _get_system()
    hb = system.get_heartbeat_prices()
    windows = [
        ("day",      hb.day),
        ("week",     hb.week),
        ("month",    hb.month),
        ("half-y",   hb.half_year),
        ("year",     hb.year),
    ]

    def _fmt(val, spec):
        return format(val, spec) if val is not None else "—"

    rows = [
        ("PV produced (kWh)",         "pv_produced_kwh",                     ",.1f"),
        ("Grid feed-in (kWh)",        "grid_feed_in_kwh",                    ",.1f"),
        ("Grid feed-in comp. (€)",    "grid_feed_in_compensation_eur",       ",.2f"),
        ("Grid consumed (kWh)",       "grid_consumed_kwh",                   ",.1f"),
        ("Grid consumption cost (€)", "grid_consumption_cost_eur",           ",.2f"),
        ("Total consumption (kWh)",   "total_consumption_kwh",               ",.1f"),
        ("Total energy cost (€)",     "total_energy_cost_eur",               ",.2f"),
        ("Heartbeat price (€/kWh)",   "heartbeat_price_eur_per_kwh",         ".4f"),
        ("Comparison tariff (€/kWh)", "comparison_tariff_eur_per_kwh",       ".4f"),
        ("Feed-in tariff (€/kWh)",    "grid_feed_in_tariff_eur_per_kwh",     ".4f"),
        ("Grid buy price (€/kWh)",    "grid_consumption_price_eur_per_kwh",  ".4f"),
    ]

    print(f"System:  {system.id()}")
    print()
    # Header
    print(f"{'Metric':<28}" + "".join(f"{lbl:>11}" for lbl, _ in windows))
    print("-" * (28 + 11 * len(windows)))
    for label, attr, spec in rows:
        cells = "".join(f"{_fmt(getattr(w, attr), spec):>11}" for _, w in windows)
        print(f"{label:<28}{cells}")

    # Implausibility flags
    flagged = [name for name, w in windows if w.should_report_implausible_pv_and_feed_in]
    if flagged:
        print()
        print(f"⚠ Implausible PV/feed-in values reported for: {', '.join(flagged)}")


def cmd_savings(args: argparse.Namespace) -> None:
    try:
        from_d = datetime.date.fromisoformat(args.from_date) if args.from_date else None
        to_d = datetime.date.fromisoformat(args.to_date) if args.to_date else None
    except ValueError as e:
        sys.exit(f"Error: invalid date — {e}")
    system = _get_system()
    savings = system.get_energy_savings(from_date=from_d, to_date=to_d)
    range_lbl = f"{from_d} – {to_d}" if from_d or to_d else "(API default window)"
    print(f"System:   {system.id()}")
    print(f"Range:    {range_lbl}")
    if savings.savings_eur is None:
        print("Savings:  —")
    else:
        print(f"Savings:  {savings.savings_eur:.2f} €")


def cmd_energy_today(args: argparse.Namespace) -> None:
    system = _get_system()
    ed = system.get_energy_today(resolution=args.resolution)
    _print_energy(system.id(), ed, args.resolution)


def cmd_energy_historical(args: argparse.Namespace) -> None:
    try:
        from_date = datetime.date.fromisoformat(args.from_date)
        to_date = datetime.date.fromisoformat(args.to_date)
    except ValueError as e:
        sys.exit(f"Error: invalid date — {e}")
    system = _get_system()
    ed = system.get_energy_historical(from_date=from_date, to_date=to_date, resolution=args.resolution)
    _print_energy(system.id(), ed, args.resolution)


def _print_energy(system_id: str, ed, resolution: str) -> None:
    suf = f"  (self-suff. {ed.self_sufficiency * 100:.0f}%)" if ed.self_sufficiency is not None else ""
    print(f"System:        {system_id}")
    if ed.updated_at:
        print(f"Updated:       {ed.updated_at}")
    print(f"Resolution:    {resolution}")
    print()
    print(f"{'PV produced:':28} {_kwh(ed.energy_produced_kwh)}{suf}")
    print(f"{'Grid supply:':28} {_kwh(ed.grid_supply_kwh)}")
    print(f"{'Grid feed-in:':28} {_kwh(ed.grid_feed_in_kwh)}")
    print(f"{'Battery charge:':28} {_kwh(ed.battery_charge_kwh)}")
    print(f"{'Battery discharge:':28} {_kwh(ed.battery_discharge_kwh)}")
    print(f"{'Total consumption:':28} {_kwh(ed.consumption_total_kwh)}")
    if ed.consumption_household_total_kwh is not None:
        print(f"{'  Household:':28} {_kwh(ed.consumption_household_total_kwh)}")
    if ed.consumption_ev_total_kwh is not None:
        print(f"{'  EV:':28} {_kwh(ed.consumption_ev_total_kwh)}")
    if ed.consumption_heat_pump_total_kwh is not None:
        print(f"{'  Heat pump:':28} {_kwh(ed.consumption_heat_pump_total_kwh)}")
    if ed.consumption_ac_total_kwh is not None:
        print(f"{'  AC:':28} {_kwh(ed.consumption_ac_total_kwh)}")
    if ed.savings_eur is not None:
        print(f"{'Savings:':28} {ed.savings_eur:.2f} €")
    if ed.timeseries:
        print()
        print(f"{'Timestamp':<25}  {'PV':>6}  {'Grid+':>6}  {'Grid-':>6}  {'Bat%':>5}  {'Bat kW':>7}  kW")
        print("-" * 68)
        for ts in sorted(ed.timeseries):
            slot = ed.timeseries[ts]
            pv = f"{slot.production:.3f}" if slot.production is not None else "—"
            gs = f"{slot.grid_supply:.3f}" if slot.grid_supply is not None else "—"
            gf = f"{slot.grid_feed_in:.3f}" if slot.grid_feed_in is not None else "—"
            soc = f"{slot.battery_soc * 100:.1f}%" if slot.battery_soc is not None else "—"
            bat_kw: float | None = None
            if slot.battery_charge is not None and slot.battery_charge > 0:
                bat_kw = slot.battery_charge
            elif slot.battery_discharge is not None and slot.battery_discharge > 0:
                bat_kw = -slot.battery_discharge
            bat = f"{bat_kw:+.3f}" if bat_kw is not None else "—"
            print(f"{ts:<25}  {pv:>6}  {gs:>6}  {gf:>6}  {soc:>5}  {bat:>7}")


def cmd_ev(args: argparse.Namespace) -> None:
    system = _get_system()
    chargers = system.get_ev_chargers()
    if not chargers:
        print("No EV chargers registered.")
        return
    print(f"System: {system.id()}")
    print()
    for ev in chargers:
        soc = f"{ev.current_soc():.0f}%" if ev.current_soc() is not None else "—"
        vehicle_parts = filter(None, [ev.manufacturer(), ev.model()])
        vehicle = " ".join(vehicle_parts) or "—"
        capacity = f"{ev.capacity_wh() / 1000:.0f} kWh" if ev.capacity_wh() is not None else "—"
        target = _pct(ev.target_soc())
        default = _pct(ev.default_soc())
        print(f"  {ev.id()}")
        print(f"    Name:      {ev.name() or '—'}")
        print(f"    Vehicle:   {vehicle}  ({capacity})")
        print(f"    Charger:   {ev.assigned_charger_id() or '—'}")
        print(f"    Mode:      {ev.charging_mode().value}")
        print(f"    SoC:       {soc}  (target {target}  default {default})")
        if ev.primary_schedule_days():
            days = ", ".join(ev.primary_schedule_days())
            print(f"    Schedule:  {days}  dep. {ev.primary_schedule_departure_time()}  SoC {_pct(ev.primary_schedule_departure_soc())}")
        print(f"    Updated:   {ev.updated_at() or '—'}")


def cmd_ev_modes(args: argparse.Namespace) -> None:
    system = _get_system()
    modes = system.get_displayed_ev_charging_modes()
    print(f"System: {system.id()}")
    if not modes:
        print("No EV charging modes available.")
        return
    print("Available EV charging modes:")
    for mode in modes:
        print(f"  {mode.value}")


def cmd_set_ev_mode(args: argparse.Namespace) -> None:
    try:
        mode = ChargingMode(args.mode.upper())
    except ValueError:
        valid = ", ".join(m.value for m in ChargingMode)
        sys.exit(f"Error: invalid mode {args.mode!r}. Valid values: {valid}")

    ev = _resolve_ev(args)
    ev.set_charging_mode(mode)
    print(f"EV {ev.id()}: charging mode set to {mode.value}")


def _resolve_ev(args):
    """Return the targeted EVCharger from args (--ev or first charger)."""
    system = _get_system()
    chargers = system.get_ev_chargers()
    if not chargers:
        sys.exit("Error: no EV chargers registered on this system")
    if args.ev:
        ev = next((e for e in chargers if e.id() == args.ev), None)
        if ev is None:
            sys.exit(f"Error: EV charger {args.ev!r} not found")
        return ev
    return chargers[0]


def cmd_set_ev_target_soc(args: argparse.Namespace) -> None:
    try:
        soc = float(args.soc)
    except ValueError:
        sys.exit(f"Error: invalid SoC value {args.soc!r} — must be a number between 0 and 100")
    if not 0.0 <= soc <= 100.0:
        sys.exit(f"Error: SoC must be between 0 and 100, got {soc}")
    ev = _resolve_ev(args)
    ev.set_target_soc(soc)
    print(f"EV {ev.id()}: target SoC set to {soc:.0f}%")


def cmd_set_ev_departure(args: argparse.Namespace) -> None:
    ev = _resolve_ev(args)
    ev.set_primary_departure_time(args.time)
    print(f"EV {ev.id()}: primary departure time set to {args.time}")


def cmd_ems(args: argparse.Namespace) -> None:
    system = _get_system()
    settings = system.get_ems_settings()
    print(f"System:       {system.id()}")
    print(f"EMS mode:     {'AUTO' if settings.auto_mode else 'MANUAL OVERRIDE'}")
    print(f"Time-of-Use:  {'enabled' if settings.time_of_use_enabled else 'disabled'}")
    print(f"Consent:      {'yes' if settings.consent_given else 'no'}")
    print(f"Updated:      {settings.updated_at or '—'}")
    if settings.manual_devices:
        print()
        print("Manual device settings:")
        for dev in settings.manual_devices:
            if dev.type == "EV_CHARGER":
                mode = dev.active_charging_mode or "—"
                ev = dev.assigned_ev_name or dev.assigned_ev_id or "—"
                print(f"  EV_CHARGER  {dev.charger_name or dev.id or '—'}  ->  {mode}  ({ev})")
            elif dev.type == "BATTERY":
                fc = "enabled" if dev.enable_forecast_charging else "disabled"
                print(f"  BATTERY     Forecast charging: {fc}")
            elif dev.type == "HEAT_PUMP":
                surplus = f"yes  (max {dev.max_solar_surplus_usage_kw:.1f} kW)" if dev.use_solar_surplus and dev.max_solar_surplus_usage_kw is not None else ("yes" if dev.use_solar_surplus else "no")
                print(f"  HEAT_PUMP   {dev.id or '—'}  Solar surplus: {surplus}")
            else:
                print(f"  {dev.type}")


def cmd_weather(args: argparse.Namespace) -> None:
    system = _get_system()
    w = system.get_weather()

    def _day_label(d) -> str:
        symbol = d.weather_description
        sun_h = f"{d.sunshine_minutes / 60:.1f} h" if d.sunshine_minutes is not None else "—"
        rain = f"{d.precipitation_mm:.1f} mm" if d.precipitation_mm is not None else "—"
        prob = f"{d.precipitation_probability:.0f}%" if d.precipitation_probability is not None else "—"
        temp = f"{d.temperature_celsius:.1f} °C" if d.temperature_celsius is not None else "—"
        rise = d.sunrise[:16].replace("T", " ") if d.sunrise else "—"
        sset = d.sunset[:16].replace("T", " ") if d.sunset else "—"
        return f"{symbol:<28}  {temp}  Sun {sun_h}  Rain {rain} ({prob})  Rise {rise}  Set {sset}"

    print(f"System:   {system.id()}")
    print(f"Heute:    {_day_label(w.today)}")
    print(f"Morgen:   {_day_label(w.tomorrow)}")

    if args.forecasts and w.forecasts:
        print()
        print(f"{'Zeit (UTC)':<18}  {'Wetter':<28}  {'Temp':>6}  {'Wind':>6}  {'Regen':>8}  {'Prob':>5}  {'Sonne':>6}")
        print("-" * 92)
        for slot in w.forecasts:
            ts = slot.period_start[:16].replace("T", " ")
            desc = slot.weather_description
            temp = f"{slot.temperature_celsius:.1f}°C" if slot.temperature_celsius is not None else "—"
            wind = f"{slot.wind_speed:.1f} m/s" if slot.wind_speed is not None else "—"
            rain = f"{slot.precipitation_mm:.1f} mm" if slot.precipitation_mm is not None else "—"
            prob = f"{slot.precipitation_probability:.0f}%" if slot.precipitation_probability is not None else "—"
            sun = f"{slot.sunshine_minutes:.0f} min" if slot.sunshine_minutes is not None else "—"
            print(f"{ts:<18}  {desc:<28}  {temp:>6}  {wind:>6}  {rain:>8}  {prob:>5}  {sun:>6}")


def _parse_dt(value: str, end_of_day: bool) -> datetime.datetime:
    """Parse a date or datetime string; fill missing time with start/end of day."""
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            parsed = datetime.datetime.strptime(value, fmt)
            if fmt == "%Y-%m-%d" and end_of_day:
                parsed = parsed.replace(hour=23, minute=59, second=59)
            return parsed
        except ValueError:
            continue
    raise ValueError(f"unrecognised date/time format: {value!r}  (expected YYYY-MM-DD or YYYY-MM-DD HH:MM)")


def cmd_optimizations(args: argparse.Namespace) -> None:
    today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    try:
        start = _parse_dt(args.from_date, end_of_day=False) if args.from_date else today
        end = _parse_dt(args.to_date, end_of_day=True) if args.to_date else today.replace(hour=23, minute=59, second=59)
    except ValueError as e:
        sys.exit(f"Error: invalid date — {e}")

    system = _get_system()
    result = system.get_optimizations(start=start, end=end)

    print(f"System:  {system.id()}")
    print(f"Period:  {start.date()} – {end.date()}")
    print(f"Events:  {len(result.events)}")
    if not result.events:
        return
    print()
    print(f"{'Timestamp':<22}  {'Asset':<8}  {'Decision':<26}  {'Price':>9}  {'SoC':>4}")
    print("-" * 80)
    for ev in sorted(result.events, key=lambda e: e.timestamp):
        soc = f"{ev.state_of_charge}%" if ev.state_of_charge is not None else "—"
        price = f"{ev.market_price:.2f}" if ev.market_price is not None else "—"
        ts = ev.from_time[:19].replace("T", " ")
        print(f"{ts:<22}  {ev.asset:<8}  {ev.decision:<26}  {price:>9}  {soc:>4}")


def cmd_set_ems(args: argparse.Namespace) -> None:
    auto = args.mode == "auto"
    system = _get_system()
    system.set_ems_mode(auto=auto)
    print(f"System: {system.id()}")
    print(f"EMS mode set to: {'AUTO' if auto else 'MANUAL OVERRIDE'}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _kwh(value: float | None) -> str:
    return f"{value:.2f} kWh" if value is not None else "—"


def _w(value: float | None) -> str:
    if value is None:
        return "—"
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.0f} W"


def _pct(value: float | None) -> str:
    return f"{value:.1f}%" if value is not None else "—"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="1KOMMA5° Heartbeat API CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", metavar="command")
    sub.required = True

    sub.add_parser("info", help="System metadata (address, status, features)")
    sub.add_parser("details", help="Extended system metadata (customer, installer, gateways)")
    sub.add_parser("assets", help="Site connection status + installed hardware assets")

    features_p = sub.add_parser("features", help="Active site feature flags (per customer + site)")
    features_p.add_argument(
        "--customer-id", dest="customer_id", metavar="UUID", default=None,
        help="Customer UUID (default: looked up via system details)",
    )

    sub.add_parser("live", help="Live power overview")

    prices_p = sub.add_parser("prices", help="Market electricity prices (today) [--resolution 1h|15m]")
    prices_p.add_argument(
        "--resolution",
        metavar="RES",
        default="1h",
        choices=["1h", "15m"],
        help="Data resolution: '1h' (default) or '15m'",
    )

    weather_p = sub.add_parser("weather", help="Weather forecast for the site location")
    weather_p.add_argument(
        "--forecasts", action="store_true",
        help="Show 3-hour forecast slots for the next 48 h",
    )

    sub.add_parser("ev", help="EV charger status")

    sub.add_parser("ev-modes", help="Available EV charging modes for this site")

    set_ev_p = sub.add_parser("set-ev-mode", help="Set EV charging mode")
    set_ev_p.add_argument(
        "mode",
        metavar="MODE",
        choices=[m.value for m in ChargingMode],
        help=f"Charging mode: {', '.join(m.value for m in ChargingMode)}",
    )
    set_ev_p.add_argument(
        "--ev",
        metavar="EV_ID",
        default=None,
        help="EV charger ID (default: first charger)",
    )

    set_soc_p = sub.add_parser("set-ev-target-soc", help="Set EV target state-of-charge")
    set_soc_p.add_argument("soc", metavar="SOC", help="Target SoC in percent (0–100)")
    set_soc_p.add_argument(
        "--ev", metavar="EV_ID", default=None, help="EV charger ID (default: first charger)"
    )

    set_dep_p = sub.add_parser("set-ev-departure", help="Set EV primary departure time")
    set_dep_p.add_argument("time", metavar="HH:MM", help="Departure time, e.g. 07:30")
    set_dep_p.add_argument(
        "--ev", metavar="EV_ID", default=None, help="EV charger ID (default: first charger)"
    )

    sub.add_parser("price-config", help="User-configured energy prices (grid, comparison, monthly base)")
    sub.add_parser("comparison-price", help="Grid-supplier comparison price (EUR/kWh)")

    pg_p = sub.add_parser("price-guarantee", help="Contractual electricity-price guarantee")
    pg_p.add_argument(
        "--customer-id", dest="customer_id", metavar="UUID", default=None,
        help="Customer UUID (default: looked up via system details)",
    )

    sub.add_parser("wallboxes", help="Physical wallbox hardware assigned to this system")
    sub.add_parser("smart-meter", help="Smart-meter registration details (EIC, DSO code, concession fee)")
    sub.add_parser("monthly-trading", help="Average monthly Energy-Trader savings")

    ai_dec_p = sub.add_parser("ai-decisions", help="AI self-sufficiency events (companion to 'optimizations')")
    ai_dec_p.add_argument(
        "--from", dest="from_date", metavar="YYYY-MM-DD[THH:MM]", default=None,
        help="Start date/time (default: today 00:00)",
    )
    ai_dec_p.add_argument(
        "--to", dest="to_date", metavar="YYYY-MM-DD[THH:MM]", default=None,
        help="End date/time (default: today 23:59)",
    )

    sub.add_parser("site-details", help="Extended site metadata incl. EMS runtime state")

    cust_p = sub.add_parser("customer", help="Full customer record (v3)")
    cust_p.add_argument(
        "--customer-id", dest="customer_id", metavar="UUID", default=None,
        help="Customer UUID (default: looked up via system details)",
    )

    subs_p = sub.add_parser("subscriptions", help="Customer contracts / subscriptions with monthly cost")
    subs_p.add_argument(
        "--customer-id", dest="customer_id", metavar="UUID", default=None,
        help="Customer UUID (default: looked up via system details)",
    )

    sub.add_parser("notifications", help="Recent push/in-app notifications")
    sub.add_parser("notification-settings", help="Notification preferences per category")
    sub.add_parser("versions", help="API compatibility (b2b/b2c target and minimum versions)")
    sub.add_parser("me", help="Authenticated user profile + connected systems")

    sub.add_parser("impact", help="Lifetime CO2 savings (site + community)")
    sub.add_parser("trader", help="Lifetime energy-trading savings (€)")

    sub.add_parser("heartbeat-prices", help="Financial breakdown per time window (PV, feed-in, grid, effective HB price)")

    ai_sum_p = sub.add_parser("ai-summary", help="Heartbeat-AI performance summary (self-sufficiency, earnings, CO2)")
    ai_sum_p.add_argument(
        "--resolution", metavar="RES", default="1M", choices=["1W", "1M", "1Y"],
        help="Window: '1W', '1M' (default), or '1Y'. Only '1M' returns all metrics.",
    )

    savings_p = sub.add_parser("savings", help="Aggregated Heartbeat savings (€) for a date range")
    savings_p.add_argument(
        "--from", dest="from_date", metavar="YYYY-MM-DD", default=None,
        help="Start date (default: API rolling window)",
    )
    savings_p.add_argument(
        "--to", dest="to_date", metavar="YYYY-MM-DD", default=None,
        help="End date (default: API rolling window)",
    )

    energy_today_p = sub.add_parser("energy-today", help="Energy production and consumption for today")
    energy_today_p.add_argument(
        "--resolution", metavar="RES", default="1h", choices=["1h", "15m"],
        help="Data resolution: '1h' (default) or '15m'",
    )

    energy_hist_p = sub.add_parser("energy-historical", help="Historical energy data for a date range")
    energy_hist_p.add_argument("--from", dest="from_date", metavar="YYYY-MM-DD", required=True, help="Start date")
    energy_hist_p.add_argument("--to", dest="to_date", metavar="YYYY-MM-DD", required=True, help="End date")
    energy_hist_p.add_argument(
        "--resolution", metavar="RES", default="1h", choices=["1h", "15m"],
        help="Data resolution: '1h' (default) or '15m'",
    )

    opt_p = sub.add_parser("optimizations", help="AI optimisation decisions for a date range")
    opt_p.add_argument(
        "--from", dest="from_date", metavar="YYYY-MM-DD[THH:MM]", default=None,
        help="Start date/time (default: today 00:00)",
    )
    opt_p.add_argument(
        "--to", dest="to_date", metavar="YYYY-MM-DD[THH:MM]", default=None,
        help="End date/time (default: today 23:59)",
    )

    sub.add_parser("ems", help="EMS mode status")

    set_ems_p = sub.add_parser("set-ems", help="Set EMS operating mode")
    set_ems_p.add_argument(
        "mode",
        choices=["auto", "manual"],
        help="'auto' for automatic optimisation, 'manual' for manual override",
    )

    args = parser.parse_args()
    {
        "info": cmd_info,
        "details": cmd_details,
        "assets": cmd_assets,
        "features": cmd_features,
        "live": cmd_live,
        "weather": cmd_weather,
        "prices": cmd_prices,
        "ev": cmd_ev,
        "ev-modes": cmd_ev_modes,
        "set-ev-mode": cmd_set_ev_mode,
        "set-ev-target-soc": cmd_set_ev_target_soc,
        "set-ev-departure": cmd_set_ev_departure,
        "price-config": cmd_price_config,
        "comparison-price": cmd_comparison_price,
        "price-guarantee": cmd_price_guarantee,
        "wallboxes": cmd_wallboxes,
        "smart-meter": cmd_smart_meter,
        "monthly-trading": cmd_monthly_trading,
        "ai-decisions": cmd_ai_decisions,
        "site-details": cmd_site_details,
        "customer": cmd_customer,
        "subscriptions": cmd_subscriptions,
        "notifications": cmd_notifications,
        "notification-settings": cmd_notification_settings,
        "versions": cmd_versions,
        "me": cmd_me,
        "impact": cmd_impact,
        "trader": cmd_trader,
        "ai-summary": cmd_ai_summary,
        "heartbeat-prices": cmd_heartbeat_prices,
        "savings": cmd_savings,
        "energy-today": cmd_energy_today,
        "energy-historical": cmd_energy_historical,
        "optimizations": cmd_optimizations,
        "ems": cmd_ems,
        "set-ems": cmd_set_ems,
    }[args.command](args)


if __name__ == "__main__":
    main()
