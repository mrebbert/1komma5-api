#!/usr/bin/env python3
"""Simple CLI for the 1KOMMA5° Heartbeat API.

Usage:
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
    if si.energy_trader_active is not None:
        print(f"Energy trading:       {'yes' if si.energy_trader_active else 'no'}")
    if si.electricity_contract_active is not None:
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


def cmd_energy_today(args: argparse.Namespace) -> None:
    client = _client()
    system = _system(client)
    ed = system.get_energy_today(resolution=args.resolution)
    _print_energy(system.id(), ed, args.resolution)


def cmd_energy_historical(args: argparse.Namespace) -> None:
    import datetime as dt
    try:
        from_date = dt.date.fromisoformat(args.from_date)
        to_date = dt.date.fromisoformat(args.to_date)
    except ValueError as e:
        sys.exit(f"Error: invalid date — {e}")
    client = _client()
    system = _system(client)
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


def _resolve_ev(args):
    """Return the targeted EVCharger from args (--ev or first charger)."""
    client = _client()
    system = _system(client)
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


def cmd_weather(args: argparse.Namespace) -> None:
    from onekommafive.models import WEATHER_SYMBOLS
    client = _client()
    system = _system(client)
    w = system.get_weather()

    def _day_label(d) -> str:
        symbol = WEATHER_SYMBOLS.get(d.weather_symbol_id, f"Symbol {d.weather_symbol_id}") if d.weather_symbol_id else "—"
        sun_h = f"{d.sunshine_minutes / 60:.1f} h" if d.sunshine_minutes is not None else "—"
        rain = f"{d.precipitation_mm:.1f} mm" if d.precipitation_mm is not None else "—"
        prob = f"{d.precipitation_probability:.0f}%" if d.precipitation_probability is not None else "—"
        temp = f"{d.temperature_celsius:.1f} °C" if d.temperature_celsius is not None else "—"
        rise = d.sunrise[:16].replace("T", " ") if d.sunrise else "—"
        sset = d.sunset[:16].replace("T", " ") if d.sunset else "—"
        return f"{symbol:<28}  {temp}  ☀ {sun_h}  🌧 {rain} ({prob})  ↑{rise}  ↓{sset}"

    print(f"System:   {system.id()}")
    print(f"Heute:    {_day_label(w.today)}")
    print(f"Morgen:   {_day_label(w.tomorrow)}")

    if args.forecasts and w.forecasts:
        print()
        print(f"{'Zeit (UTC)':<18}  {'Wetter':<28}  {'Temp':>6}  {'Wind':>6}  {'Regen':>8}  {'Prob':>5}  {'Sonne':>6}")
        print("-" * 92)
        for slot in w.forecasts:
            ts = slot.period_start[:16].replace("T", " ")
            desc = WEATHER_SYMBOLS.get(slot.weather_symbol_id, f"Symbol {slot.weather_symbol_id}") if slot.weather_symbol_id else "—"
            temp = f"{slot.temperature_celsius:.1f}°C" if slot.temperature_celsius is not None else "—"
            wind = f"{slot.wind_speed:.1f} m/s" if slot.wind_speed is not None else "—"
            rain = f"{slot.precipitation_mm:.1f} mm" if slot.precipitation_mm is not None else "—"
            prob = f"{slot.precipitation_probability:.0f}%" if slot.precipitation_probability is not None else "—"
            sun = f"{slot.sunshine_minutes:.0f} min" if slot.sunshine_minutes is not None else "—"
            print(f"{ts:<18}  {desc:<28}  {temp:>6}  {wind:>6}  {rain:>8}  {prob:>5}  {sun:>6}")


def _parse_dt(value: str, end_of_day: bool) -> "datetime.datetime":
    """Parse a date or datetime string; fill missing time with start/end of day."""
    import datetime as dt
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            parsed = dt.datetime.strptime(value, fmt)
            if fmt == "%Y-%m-%d":
                if end_of_day:
                    parsed = parsed.replace(hour=23, minute=59, second=59)
            return parsed
        except ValueError:
            continue
    raise ValueError(f"unrecognised date/time format: {value!r}  (expected YYYY-MM-DD or YYYY-MM-DD HH:MM)")


def cmd_optimizations(args: argparse.Namespace) -> None:
    import datetime as dt
    today = dt.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    try:
        start = _parse_dt(args.from_date, end_of_day=False) if args.from_date else today
        end = _parse_dt(args.to_date, end_of_day=True) if args.to_date else today.replace(hour=23, minute=59, second=59)
    except ValueError as e:
        sys.exit(f"Error: invalid date — {e}")

    client = _client()
    system = _system(client)
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
    client = _client()
    system = _system(client)
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
    sub.add_parser("live", help="Live power overview")

    prices_p = sub.add_parser("prices", help="Market electricity prices (yesterday) [--resolution 1h|15m]")
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
        "live": cmd_live,
        "weather": cmd_weather,
        "prices": cmd_prices,
        "ev": cmd_ev,
        "ev-modes": cmd_ev_modes,
        "set-ev-mode": cmd_set_ev_mode,
        "set-ev-target-soc": cmd_set_ev_target_soc,
        "set-ev-departure": cmd_set_ev_departure,
        "energy-today": cmd_energy_today,
        "energy-historical": cmd_energy_historical,
        "optimizations": cmd_optimizations,
        "ems": cmd_ems,
        "set-ems": cmd_set_ems,
    }[args.command](args)


if __name__ == "__main__":
    main()
