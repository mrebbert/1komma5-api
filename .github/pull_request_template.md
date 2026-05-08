## Summary

<!-- What does this PR change and why? One or two sentences. -->

## Related issue

<!-- "Fixes #123" or "Refs #123", or "n/a" if there's no issue. -->

## Changes

<!-- Bullet list of the concrete changes. -->

-

## Test plan

- [ ] `PYTHONPATH=. ./venv/bin/pytest tests/ -v` passes locally
- [ ] `./venv/bin/ruff check onekommafive/ tests/` passes
- [ ] Added or updated tests for the changed behaviour
- [ ] Manually verified against a live system (if applicable)

## API notes (if applicable)

<!--
For new endpoints or response fields: paste the request URL, params,
and a redacted example response.
-->

## Checklist

- [ ] Code follows existing style (line length 120, type hints, dataclasses with `from_dict`)
- [ ] Public API additions are re-exported from `onekommafive/__init__.py`
- [ ] Docstrings added for new public methods and classes
- [ ] `README.md` updated if the change is user-visible
