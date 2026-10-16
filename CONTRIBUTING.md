# Contributing

Thanks for taking the time to contribute. This is a small,
hobby-maintained project; issues and pull requests are welcome.

Setup, test invocations, lint commands, type-check commands and the
"add a new API endpoint" recipe live on the dedicated developer page:

**<https://mrebbert.github.io/1komma5-api/development/>**
(Source: [`docs/development.md`](docs/development.md).)

## Pull-request policy

- Keep changes focused. One feature or fix per PR.
- Add or update tests for the behaviour you change. CI gates coverage
  at 95%; the project is close to the floor, so new code without
  tests tends to break the build.
- Run the full suite plus `ruff` and `mypy --strict` before pushing
  (`uv run pre-commit run --all-files` does all three in one call).
- Match existing code style: line length 88 (`ruff format`), type hints
  everywhere, dataclasses with `from_dict` constructors, structured
  logging via `_LOGGER = logging.getLogger(__name__)` with `%s`
  formatting.
- Reference the API endpoint or response payload in the PR description
  when adding support for new fields, so reviewers can cross-check.
- No `--no-verify`, no `--no-gpg-sign`. If a hook fails, fix the
  underlying issue.

## Reporting bugs

Open an issue with a minimal reproduction. Include Python version,
library version (`pip show onekommafive`), and any relevant API
response snippet with personal data redacted.

## Security issues

Please do **not** open a public issue for security problems. See
[SECURITY.md](SECURITY.md) for the private reporting channel.
