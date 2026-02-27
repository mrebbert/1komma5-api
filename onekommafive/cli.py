#!/usr/bin/env python3
"""Simple CLI for the 1KOMMA5° Heartbeat API.

Usage:
    python cli.py live
    python cli.py prices [--resolution 1h]
    python cli.py ev
    python cli.py ems

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
from onekommafive.models import MarketPrices


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

def cmd_live(args: argparse.Namespace) -> None:
    client = _client()
    system = _system(client)
    ov = system.get_live_overview()
    print(f"System:       {system.id()}")
    print(f"PV power:     {_w(ov.pv_power)}")
    print(f"Battery:      {_w(ov.battery_power)}  SoC {_pct(ov.battery_soc)}")
    print(f"Grid:         {_w(ov.grid_power)}")
    print(f"Consumption:  {_w(ov.consumption_power)}")


def cmd_prices(args: argparse.Namespace) -> None:
    client = _client()
    system = _system(client)
    today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start = today - datetime.timedelta(days=1)
    end = today
    mp: MarketPrices = system.get_prices(
        start=start,
        end=end,
        resolution=args.resolution or None,
    )
    print(f"System:        {system.id()}")
    print(f"Period:        {start.date()} – {end.date()}")
    print(f"Average price: {mp.average_price:.4f} ct/kWh")
    print(f"Highest price: {mp.highest_price:.4f} ct/kWh")
    print(f"Lowest price:  {mp.lowest_price:.4f} ct/kWh")
    print(f"Grid costs:    {mp.grid_costs_total:.4f} ct/kWh  (VAT {mp.vat * 100:.0f}%)")
    print()
    print(f"{'Timestamp':<25}  {'Spot':>10}  {'Incl. grid':>12}")
    print("-" * 52)
    for ts in sorted(mp.prices):
        spot = mp.prices[ts]
        total = mp.prices_with_grid_costs.get(ts, float("nan"))
        print(f"{ts:<25}  {spot:>9.4f}  {total:>11.4f}")


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
        print(f"  {ev.id()}")
        print(f"    Name:  {ev.name() or '—'}")
        print(f"    Mode:  {ev.charging_mode().value}")
        print(f"    SoC:   {soc}")


def cmd_ems(args: argparse.Namespace) -> None:
    client = _client()
    system = _system(client)
    settings = system.get_ems_settings()
    print(f"System: {system.id()}")
    print(f"EMS mode: {'AUTO' if settings.auto_mode else 'MANUAL OVERRIDE'}")


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

    sub.add_parser("live", help="Live power overview")

    prices_p = sub.add_parser("prices", help="Market electricity prices (yesterday)")
    prices_p.add_argument(
        "--resolution",
        metavar="RES",
        default="1h",
        help="Data resolution, e.g. '1h' (default). Omit for daily aggregation.",
    )

    sub.add_parser("ev", help="EV charger status")
    sub.add_parser("ems", help="EMS mode")

    args = parser.parse_args()
    {
        "live": cmd_live,
        "prices": cmd_prices,
        "ev": cmd_ev,
        "ems": cmd_ems,
    }[args.command](args)


if __name__ == "__main__":
    main()
