"""Systems collection resource for the 1KOMMA5° Heartbeat API."""

from __future__ import annotations

from typing import TYPE_CHECKING

import requests

from .errors import RequestError
from .system import System

if TYPE_CHECKING:
    from .client import Client

# The API returns this sentinel UUID for placeholder / inactive systems that
# should be filtered out before presenting results to callers.
_NULL_SYSTEM_ID = "00000000-0000-0000-0000-000000000000"


class Systems:
    """Entry point for listing and retrieving 1KOMMA5° energy systems.

    Args:
        client: An authenticated :class:`~onekommafive.Client`.

    Example::

        from onekommafive import Client, Systems

        client = Client("user@example.com", "s3cr3t")
        systems = Systems(client).get_systems()
        for system in systems:
            overview = system.get_live_overview()
            print(system.id(), overview.pv_power)
    """

    def __init__(self, client: "Client") -> None:
        self._client = client

    def get_systems(self) -> list[System]:
        """Return all active systems accessible to the authenticated user.

        Placeholder systems with the nil UUID are filtered out automatically.

        Returns:
            A list of :class:`~onekommafive.System` instances.

        Raises:
            RequestError: If the server returns a non-200 response.
        """
        url = f"{self._client.HEARTBEAT_API}/api/v2/systems"
        response = requests.get(url=url, headers=self._client._auth_headers(), timeout=30)
        if response.status_code != 200:
            raise RequestError(f"Failed to get systems: {response.text}")

        raw_systems: list[dict] = response.json().get("data", [])
        active = [s for s in raw_systems if s.get("id") != _NULL_SYSTEM_ID]
        return [System(self._client, s) for s in active]

    def get_system(self, system_id: str) -> System:
        """Retrieve a single system by its UUID.

        Args:
            system_id: The UUID of the target system.

        Returns:
            A :class:`~onekommafive.System` instance.

        Raises:
            RequestError: If the server returns a non-200 response.
        """
        url = f"{self._client.HEARTBEAT_API}/api/v2/systems/{system_id}"
        response = requests.get(url=url, headers=self._client._auth_headers(), timeout=30)
        if response.status_code != 200:
            raise RequestError(f"Failed to get system {system_id!r}: {response.text}")
        return System(self._client, response.json())
