"""Pytest configuration for the test suite.

Currently only holds an aiohttp-3.14 compatibility shim for aioresponses.
"""

from __future__ import annotations

import inspect
from typing import Any
from unittest.mock import Mock

import aiohttp
import pytest

# aiohttp 3.14 added a required keyword-only ``stream_writer`` argument to
# ``ClientResponse.__init__``. aioresponses (<=0.7.8) builds mocked responses
# without it, so every mocked request raises
# ``TypeError: ... missing 1 required keyword-only argument: 'stream_writer'``.
# aiohttp only reads ``stream_writer.output_size`` on Mock responses, so a
# ``Mock(output_size=0)`` suffices.
#
# Mirrors the upstream fix (aioresponses#288, tracking aioresponses#289) and
# the same shim used in https://github.com/j7an/dep-rank/pull/123. The
# signature guard makes this a no-op on aiohttp < 3.14 or once aioresponses
# ships a release that supplies the argument itself. Remove this block then;
# tracked in issue #21.
_response_init = aiohttp.ClientResponse.__init__
if "stream_writer" in inspect.signature(_response_init).parameters:

    def _patched_response_init(
        self: aiohttp.ClientResponse, *args: Any, **kwargs: Any
    ) -> None:
        kwargs.setdefault("stream_writer", Mock(output_size=0))
        _response_init(self, *args, **kwargs)

    aiohttp.ClientResponse.__init__ = _patched_response_init  # type: ignore[method-assign]


@pytest.fixture(autouse=True)
def _direct_gateway(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Keep the suite's mocked per-service URLs valid.

    The client defaults to the BFF gateway; most tests mock the direct
    ``/api/vN`` URLs. ``TestGateway`` removes the variable to exercise the
    real default; the live integration tests keep the default route.
    """
    if request.module.__name__.endswith("test_integration"):
        return
    monkeypatch.setenv("ONEKOMMAFIVE_GATEWAY", "direct")
