# Changelog

All notable changes to **onekommafive** are recorded here. Format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Full per-commit history: <https://github.com/mrebbert/1komma5-api/commits/main>.

## [Unreleased]

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

[Unreleased]: https://github.com/mrebbert/1komma5-api/compare/v1.1.9...HEAD
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
