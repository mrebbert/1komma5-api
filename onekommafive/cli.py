#!/usr/bin/env python3
"""Simple CLI for the 1KOMMA5° Heartbeat API.

Usage:
    python cli.py live
    python cli.py prices [--resolution 1h|15m]
    python cli.py ev
    python cli.py ev-modes
    python cli.py set-ev-mode <mode> [--ev <ev_id>]
    python cli.py ems
    python cli.py set-ems auto|manual

Credentials are read from the environment:
    ONEKOMMAFIVE_USERNAME
    ONEKOMMAFIVE_PASSWORD

An optional ONEKOMMAFIVE_SYSTEM env var selects a system by ID;
otherwise the first system is used.
"""

from __future__ import annotations

import argparse
import datetime
import os
import sys

from onekommafive import Client, Systems
from onekommafive.models import ChargingMode, MarketPrices


def _client() -> Client:
    username = os.environ.get("ONEKOMMAFIVE_USERNAME")
    password = os.environ.get("ONEKOMMAFIVE_PASSWORD")
    if not username or not password:
        sys.exit("Error: set ONEKOMMAFIVE_USERNAME and ONEKOMMAFIVE_PASSWORD")
    return Client(username, password)


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


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

def cmd_info(args: argparse.Namespace) -> None:
    client = _client()
    system = _system(client)
    si = system.info()
    addr_parts = filter(None, [
        si.address_line1,
        si.address_line2,
        f"{si.address_zip_code} {si.address_city}".strip() or None,
        si.address_country,
    ])
    print(f"System:       {si.id}")
    print(f"Name:         {si.name or '—'}")
    print(f"Status:       {si.status or '—'}")
    print(f"Address:      {', '.join(addr_parts) or '—'}")
    if si.address_latitude is not None and si.address_longitude is not None:
        print(f"Coordinates:  {si.address_latitude:.4f}, {si.address_longitude:.4f}")
    print(f"Customer ID:  {si.customer_id or '—'}")
    print(f"Dynamic Pulse:        {'yes' if si.dynamic_pulse_compatible else 'no'}")
    print(f"Energy trading:       {'yes' if si.energy_trader_active else 'no'}")
    print(f"Electricity contract: {'yes' if si.electricity_contract_active else 'no'}")
    print(f"Created:      {si.created_at or '—'}")
    print(f"Updated:      {si.updated_at or '—'}")


def cmd_live(args: argparse.Namespace) -> None:
    client = _client()
    system = _system(client)
    ov = system.get_live_overview()
    print(f"System:       {system.id()}")
    print(f"Status:       {ov.status or '—'}")
    print(f"PV power:     {_w(ov.pv_power)}")
    print(f"Battery:      {_w(ov.battery_power)}  SoC {_pct(ov.battery_soc)}")
    print(f"Grid:         {_w(ov.grid_power)}")
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
    client = _client()
    system = _system(client)
    today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start = today
    end = today.replace(hour=23, minute=59, second=59)
    mp: MarketPrices = system.get_prices(
        start=start,
        end=end,
        resolution=args.resolution,
    )
    vat_pct = f"{mp.vat * 100:.0f}%"
    print(f"System:        {system.id()}")
    print(f"Period:        {start.date()} – {end.date()}")
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


def cmd_ev(args: argparse.Namespace) -> None:
    client = _client()
    system = _system(client)
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
    client = _client()
    system = _system(client)
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

    client = _client()
    system = _system(client)
    chargers = system.get_ev_chargers()
    if not chargers:
        sys.exit("Error: no EV chargers registered on this system")

    if args.ev:
        target = next((ev for ev in chargers if ev.id() == args.ev), None)
        if target is None:
            sys.exit(f"Error: EV charger {args.ev!r} not found")
    else:
        target = chargers[0]

    target.set_charging_mode(mode)
    print(f"EV {target.id()}: charging mode set to {mode.value}")


def cmd_ems(args: argparse.Namespace) -> None:
    client = _client()
    system = _system(client)
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
                print(f"  EV_CHARGER  {dev.charger_name or dev.id or '—'}  →  {mode}  ({ev})")
            elif dev.type == "BATTERY":
                fc = "enabled" if dev.enable_forecast_charging else "disabled"
                print(f"  BATTERY     Forecast charging: {fc}")
            elif dev.type == "HEAT_PUMP":
                surplus = f"yes  (max {dev.max_solar_surplus_usage_kw:.1f} kW)" if dev.use_solar_surplus and dev.max_solar_surplus_usage_kw is not None else ("yes" if dev.use_solar_surplus else "no")
                print(f"  HEAT_PUMP   {dev.id or '—'}  Solar surplus: {surplus}")
            else:
                print(f"  {dev.type}")


def cmd_set_ems(args: argparse.Namespace) -> None:
    auto = args.mode == "auto"
    client = _client()
    system = _system(client)
    system.set_ems_mode(auto=auto)
    print(f"System: {system.id()}")
    print(f"EMS mode set to: {'AUTO' if auto else 'MANUAL OVERRIDE'}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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
    sub.add_parser("live", help="Live power overview")

    prices_p = sub.add_parser("prices", help="Market electricity prices (yesterday) [--resolution 1h|15m]")
    prices_p.add_argument(
        "--resolution",
        metavar="RES",
        default="1h",
        choices=["1h", "15m"],
        help="Data resolution: '1h' (default) or '15m'",
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
        "live": cmd_live,
        "prices": cmd_prices,
        "ev": cmd_ev,
        "ev-modes": cmd_ev_modes,
        "set-ev-mode": cmd_set_ev_mode,
        "ems": cmd_ems,
        "set-ems": cmd_set_ems,
    }[args.command](args)


if __name__ == "__main__":
    main()
