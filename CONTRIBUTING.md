# Contributing

Thanks for taking the time to contribute. This is a small,
hobby-maintained project — issues and pull requests are very welcome.

## Setup

```bash
git clone https://github.com/mrebbert/1komma5-api.git
cd 1komma5-api
python3.11 -m venv venv
./venv/bin/pip install -e ".[dev]"
./venv/bin/pre-commit install
```

## Running tests

```bash
PYTHONPATH=. ./venv/bin/pytest tests/ -v
```

Unit tests use the [`responses`](https://pypi.org/project/responses/)
library and do not hit the network.

The integration tests in `tests/test_integration.py` make real calls
against the 1KOMMA5° API and require credentials in environment variables:

```bash
export ONEKOMMAFIVE_USERNAME=you@example.com
export ONEKOMMAFIVE_PASSWORD=...
PYTHONPATH=. ./venv/bin/pytest tests/test_integration.py -v
```

## Linting

```bash
./venv/bin/ruff check onekommafive/ tests/
```

`pre-commit` runs ruff automatically before each commit; please don't
bypass hooks (`--no-verify`).

## Pull requests

- Keep changes focused. One feature or fix per PR.
- Add or update tests for the behaviour you change.
- Run the full test suite and ruff before pushing.
- Match existing code style (line length 120, type hints, dataclasses
  with `from_dict` constructors).
- Reference the API endpoint or response payload in the PR description
  when adding support for new fields, so reviewers can cross-check.

## Adding a new API endpoint

1. Add the resource method to `system.py` (or the appropriate module),
   going through `Client._request` for the HTTP call.
2. Add a typed dataclass in `models.py` with a `from_dict` classmethod.
3. Re-export public types from `onekommafive/__init__.py`.
4. Add tests in `tests/test_<module>.py` using `responses`.
5. Update the API endpoint table in `README.md` if the new endpoint is
   user-visible.

## Reporting bugs

Please open an issue with a minimal reproduction. Include Python
version, library version (`pip show onekommafive`), and any relevant
API response snippet (with personal data redacted).

## Security issues

Please do **not** open a public issue for security problems. See
[SECURITY.md](SECURITY.md) for the private reporting channel.
