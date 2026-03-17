#!/usr/bin/env python3
"""
Probe for newer API versions than currently used in the client.

Usage:
    ONEKOMMAFIVE_USERNAME=... ONEKOMMAFIVE_PASSWORD=... python scripts/probe_versions.py

Or with an existing bearer token:
    BEARER_TOKEN=... ONEKOMMAFIVE_SYSTEM=... python scripts/probe_versions.py
"""
import os
import re
import sys
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

HEARTBEAT_BASE = "https://heartbeat.1komma5grad.com"
IDENTITY_BASE = "https://customer-identity.1komma5grad.com"
MAX_VERSION = 7  # probe up to this version number
SOURCE_DIR = Path(__file__).parent.parent / "onekommafive"

# ---------------------------------------------------------------------------
# Step 1: Parse current versions from source files
# ---------------------------------------------------------------------------

# Regex: capture version number and the full path after /api/vN/
# The path may contain f-string placeholders like {self.id()} — we capture them too.
VERSION_RE = re.compile(r"/api/(v\d+)/((?:[^\s\"'])+)")


def _normalise(path: str) -> str:
    """Replace f-string expressions and bare variable names with a stable placeholder."""
    # {self.id()}, {self._system.id()}, {system_id}, {ev_id}, {s}, etc.
    path = re.sub(r"\{[^}]+\}", "{id}", path)
    return path.rstrip("/")


def parse_client_versions() -> dict[str, tuple[str, str, str]]:
    """
    Returns a dict keyed by normalised path template:
        path_template -> (version_str, raw_path, source_file)

    When multiple files define the same path, the highest version wins
    (shouldn't happen, but guards against stale copies).
    """
    found: dict[str, tuple[str, str, str]] = {}
    for src in SOURCE_DIR.glob("*.py"):
        for lineno, line in enumerate(src.read_text().splitlines(), 1):
            # Skip comments and docstrings (lines that are pure documentation)
            stripped = line.lstrip()
            if stripped.startswith("#") or stripped.startswith("``"):
                continue
            for m in VERSION_RE.finditer(line):
                ver, rest = m.group(1), m.group(2)
                # Strip trailing backticks, quotes, or punctuation from docstring leakage
                rest = re.sub(r"[`\"']+$", "", rest)
                normalised = _normalise(rest)
                if not normalised:
                    continue
                if normalised not in found or int(ver[1:]) > int(found[normalised][0][1:]):
                    found[normalised] = (ver, rest, src.name)
    return found


# ---------------------------------------------------------------------------
# Step 2: Obtain Bearer token + system ID
# ---------------------------------------------------------------------------

def get_credentials() -> tuple[str, str]:
    token = os.environ.get("BEARER_TOKEN")
    system = os.environ.get("ONEKOMMAFIVE_SYSTEM")

    if not token:
        username = os.environ.get("ONEKOMMAFIVE_USERNAME")
        password = os.environ.get("ONEKOMMAFIVE_PASSWORD")
        if not username or not password:
            print(
                "Error: set BEARER_TOKEN or (ONEKOMMAFIVE_USERNAME + ONEKOMMAFIVE_PASSWORD)",
                file=sys.stderr,
            )
            sys.exit(1)
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from onekommafive import Client  # noqa: PLC0415
        from onekommafive.systems import Systems  # noqa: PLC0415
        client = Client(username, password)
        token = client.get_token()
        if not system:
            systems = Systems(client).get_systems()
            system = systems[0].id() if systems else ""

    if not system:
        print("Error: set ONEKOMMAFIVE_SYSTEM", file=sys.stderr)
        sys.exit(1)

    return token, system


# ---------------------------------------------------------------------------
# Step 3: Probe higher versions
# ---------------------------------------------------------------------------

def _make_url(v: int, path_template: str, system_id: str) -> str:
    path = path_template.replace("{id}", system_id)
    base = IDENTITY_BASE if "users/me" in path else HEARTBEAT_BASE
    return f"{base}/api/v{v}/{path}"


def probe(token: str, system_id: str, path_template: str, current_ver: str) -> list[tuple[int, int]]:
    """
    Try versions current+1 .. MAX_VERSION for the given path template.
    Returns list of (version, http_status) for responses that look valid
    (i.e. not 404 / 405 / 401 / 403).
    """
    headers = {"Authorization": f"Bearer {token}"}
    current_n = int(current_ver[1:])
    hits = []
    for v in range(current_n + 1, MAX_VERSION + 1):
        try:
            r = requests.get(_make_url(v, path_template, system_id), headers=headers, timeout=6)
            if r.status_code not in (404, 405, 401, 403):
                hits.append((v, r.status_code))
        except requests.RequestException:
            pass
    return hits


# ---------------------------------------------------------------------------
# Step 4: Compare two versions and summarise differences
# ---------------------------------------------------------------------------

def _flatten_keys(obj: object, prefix: str = "") -> set[str]:
    """Recursively collect all dot-separated key paths from a JSON object."""
    keys: set[str] = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            full = f"{prefix}.{k}" if prefix else k
            keys.add(full)
            keys |= _flatten_keys(v, full)
    elif isinstance(obj, list) and obj:
        keys |= _flatten_keys(obj[0], f"{prefix}[]")
    return keys


def diff_summary(token: str, system_id: str, path_template: str, old_ver: str, new_ver: int) -> str:
    """Fetch both versions and return a human-readable diff summary."""
    headers = {"Authorization": f"Bearer {token}"}
    old_n = int(old_ver[1:])

    try:
        r_old = requests.get(_make_url(old_n, path_template, system_id), headers=headers, timeout=6)
        r_new = requests.get(_make_url(new_ver, path_template, system_id), headers=headers, timeout=6)
        old_json = r_old.json()
        new_json = r_new.json()
    except Exception as e:
        return f"(could not compare: {e})"

    old_keys = _flatten_keys(old_json)
    new_keys = _flatten_keys(new_json)

    added   = sorted(new_keys - old_keys)
    removed = sorted(old_keys - new_keys)

    parts = []
    if added:
        parts.append("new fields: " + ", ".join(f"`{k}`" for k in added))
    if removed:
        parts.append("removed fields: " + ", ".join(f"`{k}`" for k in removed))
    if not parts:
        # Same structure — check for top-level value changes
        if old_json == new_json:
            parts.append("identical response")
        else:
            parts.append("same fields, different values")

    return "; ".join(parts)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("Parsing current API versions from source …")
    client_versions = parse_client_versions()

    if not client_versions:
        print("No versioned API paths found in source.", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(client_versions)} distinct endpoint paths in client.\n")
    print("Obtaining credentials …")
    token, system_id = get_credentials()
    print(f"System ID: {system_id}\n")

    upgrades: list[tuple[str, str, list[tuple[int, int]], str]] = []

    print(f"{'Path':<55} {'Current':>8}  Probing …")
    print("-" * 75)
    for normalised, (ver, _raw, src) in sorted(client_versions.items()):
        label = f"/{normalised}"
        print(f"{label:<55} {ver:>8}  ", end="", flush=True)
        hits = probe(token, system_id, normalised, ver)
        if hits:
            summary = ", ".join(f"v{v}={s}" for v, s in hits)
            print(f"*** {summary}")
            upgrades.append((normalised, ver, hits, src))
        else:
            print("ok")

    print()
    if upgrades:
        print("=" * 75)
        print("POSSIBLE NEW VERSIONS FOUND:")
        print("=" * 75)
        for normalised, current, hits, src in upgrades:
            best_v, best_s = hits[-1]
            print(
                f"  /{normalised}\n"
                f"    current: {current}  (defined in {src})\n"
                f"    newer:   " + ", ".join(f"v{v} → HTTP {s}" for v, s in hits)
            )
            summary = diff_summary(token, system_id, normalised, current, best_v)
            print(f"    diff:    {summary}")
            print()
    else:
        print("No newer versions found. Client is up to date.")


if __name__ == "__main__":
    main()
