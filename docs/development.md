# Development

Everything a contributor or packager needs to run tests, lint, type-check
and probe the live API against this repository.

## Prerequisites

- **Python 3.13+** (SDK target; CI covers 3.13 and 3.14).
- **[uv](https://docs.astral.sh/uv/)** recommended for environment and
  dependency management (uses the checked-in `uv.lock` for reproducible
  installs). Plain `pip` works too.
- **Git** with signed commits (`commit.gpgsign = true` is the author's
  default; CI does not enforce signing on PRs).

## Setup

### With uv (recommended)

```bash
git clone https://github.com/mrebbert/1komma5-api.git
cd 1komma5-api
uv sync --all-extras
uv run pre-commit install
```

### With pip

```bash
git clone https://github.com/mrebbert/1komma5-api.git
cd 1komma5-api
python3.13 -m venv .venv
./.venv/bin/pip install -e ".[dev]"
./.venv/bin/pre-commit install
```

## Day-to-day commands

| Task | uv | pip (venv activated) |
|---|---|---|
| Run unit + mocked tests | `uv run pytest` | `pytest` |
| Run with coverage report | `uv run pytest --cov --cov-report=term-missing` | `pytest --cov --cov-report=term-missing` |
| Run a single test | `uv run pytest tests/test_system.py::test_get_system_info` | `pytest tests/test_system.py::test_get_system_info` |
| Lint | `uv run ruff check .` | `ruff check .` |
| Format | `uv run ruff format .` | `ruff format .` |
| Type-check (strict) | `uv run mypy onekommafive` | `mypy onekommafive` |
| Full pre-commit sweep | `uv run pre-commit run --all-files` | `pre-commit run --all-files` |

Coverage gate: `fail_under = 95` in `pyproject.toml`. The project ships
with ~95% coverage; keep an eye on `--cov-report=term-missing` when
adding code.

## Integration tests (require credentials)

`tests/test_integration.py` makes real calls against the 1KOMMA5° API,
read-only, no mutations. Credentials come from environment variables and
are **never** committed to the repo.

```bash
export ONEKOMMAFIVE_USERNAME=you@example.com
export ONEKOMMAFIVE_PASSWORD=...
uv run pytest tests/test_integration.py -v
```

Omit the variables and the test module auto-skips.

## Probing for new API versions

`scripts/probe_versions.py` walks every endpoint the client wraps and
asks `v{N+1}..v{N+5}` for each path. Run it after a 1KOMMA5° app update
to catch version bumps early:

```bash
export ONEKOMMAFIVE_USERNAME=you@example.com
export ONEKOMMAFIVE_PASSWORD=...
PYTHONPATH=. uv run python scripts/probe_versions.py
```

Full script contract: [`scripts/probe_versions.md`](https://github.com/mrebbert/1komma5-api/blob/main/scripts/probe_versions.md).

The probe is deliberately not wired into CI (CI never sees API
credentials). A separate "observatory" diff runs out of tree and tracks
response-shape changes daily; its findings land in [API.md](api.md) and
the repo's commit history.

## Adding a new API endpoint

The repeating recipe:

1. Add the resource method on `System`, `Systems`, `EVCharger` or a new
   module next to them. Prefer the `_sites_url(version, *parts)` /
   `_systems_url(version, *parts)` helpers over inline f-strings.
2. Add a typed dataclass in `onekommafive/models/<domain>.py` with a
   `from_dict(cls, data: dict[str, Any])` classmethod. Keep `raw` as the
   escape hatch for unmapped fields.
3. Re-export public types from `onekommafive/__init__.py` and the
   relevant `onekommafive/models/__init__.py` section.
4. Add tests in `tests/test_<module>.py` using `aioresponses`. Share
   fixtures via `tests/fixtures.py`.
5. Update [API.md](api.md) with URL, request parameters, response JSON
   and known quirks; mirror the entry into the Postman collection in
   `postman/`.
6. Add a CLI command if the endpoint is user-visible (`onekommafive/cli.py`).

## Code style

Enforced by `ruff format` (line length 88) and `ruff check` with
`select = ["E", "W", "F", "I", "B", "UP", "C4", "SIM"]`.

- `_LOGGER = logging.getLogger(__name__)` as module constant, `%s`
  formatting (no f-strings in log calls), no period at end of log
  messages.
- `mypy --strict` passes on `onekommafive/` (CI checks this).
- Reformat-only commits are listed in `.git-blame-ignore-revs`; run
  `git config blame.ignoreRevsFile .git-blame-ignore-revs` once after
  cloning so `git blame` skips them.

## Release

Tag-driven. See [`CHANGELOG.md`](https://github.com/mrebbert/1komma5-api/blob/main/CHANGELOG.md)
for the version history and
[`.github/workflows/release.yml`](https://github.com/mrebbert/1komma5-api/blob/main/.github/workflows/release.yml)
for the automation that publishes to PyPI via Trusted Publishing when a
`v*` tag is pushed.
