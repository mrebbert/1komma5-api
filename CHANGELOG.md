# Changelog

All notable changes to **onekommafive** are recorded here. Format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Full per-commit history: <https://github.com/mrebbert/1komma5-api/commits/main>.

## [Unreleased]

## [1.2.1] - 2026-10-24

Follow-up to v1.2.0 that surfaces the new §14a fields in the CLI
and the shipped reference docs. No library-API change.

### Added
- `1k5 prices` output grows an optional `§14a` column: the
  VAT-inclusive Modul-1 Netzentgelt per slot (EUR/kWh). Hidden
  when the account carries no Modul-1 data, so most tenants see
  the same compact table as in v1.2.0.
- `docs/enwg14a.md` gains a "Per-slot Netzentgelt on
  MarketPrices" section documenting the two new mapping
  attributes and when to use them vs. the window-aggregated
  Modul-1 fields on `HeartbeatPriceWindow`.

### Changed
- Postman collection `Get market prices` request path updated to
  v5 with a description note on the two new per-slot fields.
- `API.md` cross-link for `enwg14aModule` now points at the
  correct `#site-system-info` anchor so `mkdocs --strict` is
  warning-free.

## [1.2.0] - 2026-10-24

Public-API change: :meth:`System.get_prices` moves to the v5
endpoint and :class:`MarketPrices` exposes the two new §14a EnWG
Modul-1 Netzentgelt fields per timeseries slot. Backwards
compatible for callers that did not reach into the raw payload;
callers that iterated the raw timeseries will see the two
additional keys ``enwg14aGridFee`` / ``enwg14aGridFeeWithVat``.

### Added
- `MarketPrices.enwg14a_grid_fee` and
  `MarketPrices.enwg14a_grid_fee_with_vat`: per-slot §14a EnWG
  Modul-1 Netzentgelt mappings, in EUR/kWh. Empty when the
  operator has not provisioned Modul 1 for the site; populated
  per slot once ``enwg14aModule`` is active in
  ``/api/v1/sites/{id}/system-info``.

### Changed
- `System.get_prices` now calls `/api/v5/systems/{id}/charts/market-prices`
  (previously v4). v5 reuses the v4 request contract — same
  ``from`` / ``to`` / ``resolution`` parameters, same enum
  ``"1h"`` / ``"15m"`` — and adds the two timeseries fields.
- Fixture `make_price_data()` and all v4 URL mocks in
  `tests/test_system.py` updated to the v5 path.
- The timeseries unpack helper now skips slots whose value is
  JSON `null`, so a nullable field like `enwg14aGridFee`
  (populated per slot, absent for others) no longer raises on
  parse.

## [1.1.11] - 2026-10-18

Maintenance release. Pure dependency and CI-toolchain upgrades,
no changes to the installed `onekommafive` package behavior. Safe
to upgrade.

### Changed
- Runtime: `aiohttp` 3.14.4 → 3.14.5 (patch).
- Dev tooling: `ruff` 0.16.10 → 0.17.0, `pre-commit` 4.6.2 → 4.7.0.
- CI actions: `astral-sh/setup-uv` v6 → v7 (all workflows), `actions/github-script` v8 → v9, `softprops/action-gh-release` v2 → v3, `actions/upload-artifact` v4 → v7, `actions/download-artifact` v4 → v8. Release workflow now runs on a consistent Node 24 action set with digest-mismatch fail-fast on artifact downloads.

## [1.1.10] - 2026-10-16

Maintenance release. No changes to the installed `onekommafive`
package; CI, tests and developer tooling only. Safe to upgrade.

### Added
- `tests/test_cli_snapshots.py`: syrupy snapshot tests for seven CLI
  subcommands (`info`, `live`, `weather`, `system-info` enrolled +
  blank, `heartbeat-prices`, `ems`).
- `tests/test_failure_paths.py`: named failure-path suite collecting
  the SDK's resilience contract (error hierarchy, token-refresh
  fallback, `_request` status/body contract, resource-method labels).
- `.github/workflows/nightly.yml`: 05:17 UTC compatibility matrix
  across Python 3.13/3.14 against aiohttp latest and the locked
  version, opens an issue with the `nightly-failure` label on fail.
- `.github/workflows/mutation.yml`: opt-in mutmut on `analytics.py` /
  `prices.py`, triggered on direct pushes to those files or via
  `workflow_dispatch`.
- `[tool.mutmut]` + `[tool.interrogate]` config in `pyproject.toml`,
  `test-mutation` opt-in extra (`mutmut>=3.0,<4`), interrogate 85 %
  docstring-coverage gate wired into `lint.yml`.
- `[dependency-groups] dev` (PEP 735): `uv sync` without flags now
  installs the full test toolbelt (aioresponses, hypothesis, pytest,
  syrupy, mypy, ruff ...). Pip's `.[dev]` extra kept for CI parity.

### Changed
- pytest `addopts = "--cov --cov-report=term-missing -ra
  --strict-markers"`: typos in `@pytest.mark.*` decorators now fail
  the run instead of being silently ignored.
- syrupy pin lifted to `>=6.0` to match the serializer format CI has
  been running since PR #55.
- `README.md` and `docs/development.md` drop `--all-extras` from the
  setup snippet; the dev group is picked up by default.

### Fixed
- CodeQL `py/unnecessary-lambda` on `test_models_properties.py`:
  dropped the zero-arg lambda wrapper around `make_system_info_data`.

## [1.1.9] - 2026-10-16

Maintenance release. No changes to the installed `onekommafive`
package; CI, docs and tests only. Safe to upgrade.

### Added
- `CHANGELOG.md` seeded from `v1.0.0..v1.1.8` git history.
- `docs/development.md` as the single-source-of-truth developer guide
  (setup, tests, lint, mypy, probe-versions, release), linked from
  `README.md`, `CONTRIBUTING.md` and the mkdocs nav.
- Landing page (`docs/index.md`) now carries the feature overview
  instead of punting to the GitHub README.
- FAQ entry explaining why `/ev-charging-sessions/active` returns an
  empty list on accounts whose EV asset has `dataSource = USER_INPUT`.
- `API.md` section `Endpoints observed but not wrapped` documenting
  the two deliberately-skipped endpoints
  (`ev-charging-sessions/active`, `whats-new/updates/improvements`).
- `.github/workflows/release.yml`: tag-driven release via PyPI
  Trusted Publishing (OIDC). No secrets in the repo.
- `tests/test_models_properties.py`: hypothesis-based robustness
  suite exercising every representative `from_dict` against random
  subsets of its reference payload.
- Test coverage for `client.py` JWT/JWKS pathways (`_get_jwks`,
  `_decode_token`) and `cli.py` formatters (`_kwh`, `_w`, `_pct`,
  `main`'s finally branch).

### Changed
- Project coverage 95.11 % → 96.14 %. `client.py` 90 % → 100 %,
  `cli.py` 90 % → 91 %.

## [1.1.8] - 2026-10-12

### Added
- `GET /api/v1/sites/{id}/system-info` wrapped as `System.get_system_info()`
  returning `SiteSystemInfo` with the §14a enrolment slug via
  `Enwg14aModule(value, valid_from_date)`.
- `HeartbeatPriceWindow.variable_grid_fee_eur_per_kwh` (counterpart to
  `comparison_grid_fee_eur_per_kwh`).

### Fixed
- `enwg14aModule` is an object, not a string. Earlier mapping treated it
  as `str | None`; now modelled as `Enwg14aModule | None`.

### Docs
- `docs/enwg14a.md` names both enrolment sources (`SiteSystemInfo` and
  `HeartbeatPriceWindow`) and the new `variable_grid_fee_eur_per_kwh`
  field. `README.md` lists `SiteSystemInfo` + `Enwg14aModule` in the
  models table.

## [1.1.7] - 2026-10-10

### Added
- `Notification.updated_at` (ISO-8601 timestamp of the last
  read/dismissed state change).

### Docs
- CLI reference, §14a EnWG primer and FAQ published on the mkdocs site.

## [1.1.6] - 2026-10-09

### Added
- `1k5 heartbeat-prices` surfaces a §14a section with Modul-1, Modul-3,
  combined savings and comparison grid fee for enrolled accounts.

## [1.1.5] - 2026-10-08

### Added
- §14a EnWG Modul-3 fields on `HeartbeatPriceWindow`
  (`comparison_grid_fee_eur_per_kwh`, `comparison_grid_fees_total_eur`,
  `variable_grid_fees_total_eur`, `module3_total_savings_eur`,
  `enwg14a_total_savings_eur`).

## [1.1.4] - 2026-10-04

### Added
- `externalPartnerId` on `SystemDetails` and `SiteDetails`.

## [1.1.3] - 2026-09-30

### Added
- `GET /api/v1/customers/{id}/subscriptions/eligibility` wrapped.

## [1.1.2] - 2026-09-30

### Added
- `GET /api/v1/customers/{id}/subscriptions` wrapped.

## [1.1.1] - 2026-09-28

### Added
- Modul-1 fields on `HeartbeatPriceWindow` (`module1_provisioning_date`,
  `module1_active_days`, `module1_savings_per_year_eur`,
  `module1_total_savings_eur`).
- `view` query parameter on `get_optimizations`.

## [1.1.0] - 2026-09-26

### Added
- `python-quality-baseline` compliance: ruff ruleset extended to
  `E,W,F,I,B,UP,C4,SIM`, structured logging in `client.py` and `sync.py`,
  pre-commit `ruff-format` + `check-json` hooks, coverage gate at 95%
  (`pytest-cov`, `--cov-fail-under=95`), `cli.py` type-checked under
  `mypy --strict`.
- `.git-blame-ignore-revs` for the line-length-88 reformat.

## [1.0.3] - 2026-09-26

### Changed
- Dropped the `aiohttp<3.13` upper bound; `aioresponses` compatibility
  gap bridged via a test-time `stream_writer` shim.

## [1.0.2] - 2026-09-26

### Changed
- Loosened the `aiohttp` constraint to let Home Assistant resolve
  dependencies cleanly.

## [1.0.1] - 2026-09-26

### Fixed
- `sync.Client` registers an `atexit` safety net so sync callers do not
  leak the background event loop on interpreter shutdown.

## [1.0.0] - 2026-09-26

### Changed
- Full async rewrite on `aiohttp`. Public API is now async by default;
  the legacy sync surface stays available via `onekommafive.sync`.
- Python 3.13+ required. For Python 3.11/3.12 compatibility, pin
  `onekommafive<1.0`.

[Unreleased]: https://github.com/mrebbert/1komma5-api/compare/v1.1.10...HEAD
[1.2.1]: https://github.com/mrebbert/1komma5-api/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/mrebbert/1komma5-api/compare/v1.1.11...v1.2.0
[1.1.11]: https://github.com/mrebbert/1komma5-api/compare/v1.1.10...v1.1.11
[1.1.10]: https://github.com/mrebbert/1komma5-api/compare/v1.1.9...v1.1.10
[1.1.9]: https://github.com/mrebbert/1komma5-api/compare/v1.1.8...v1.1.9
[1.1.8]: https://github.com/mrebbert/1komma5-api/compare/v1.1.7...v1.1.8
[1.1.7]: https://github.com/mrebbert/1komma5-api/compare/v1.1.6...v1.1.7
[1.1.6]: https://github.com/mrebbert/1komma5-api/compare/v1.1.5...v1.1.6
[1.1.5]: https://github.com/mrebbert/1komma5-api/compare/v1.1.4...v1.1.5
[1.1.4]: https://github.com/mrebbert/1komma5-api/compare/v1.1.3...v1.1.4
[1.1.3]: https://github.com/mrebbert/1komma5-api/compare/v1.1.2...v1.1.3
[1.1.2]: https://github.com/mrebbert/1komma5-api/compare/v1.1.1...v1.1.2
[1.1.1]: https://github.com/mrebbert/1komma5-api/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/mrebbert/1komma5-api/compare/v1.0.3...v1.1.0
[1.0.3]: https://github.com/mrebbert/1komma5-api/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/mrebbert/1komma5-api/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/mrebbert/1komma5-api/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/mrebbert/1komma5-api/releases/tag/v1.0.0
