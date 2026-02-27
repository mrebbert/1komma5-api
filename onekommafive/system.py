"""System resource for the 1KOMMA5° Heartbeat API."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any

import requests

from .errors import RequestError
from .ev_charger import EVCharger
from .models import EmsSettings, LiveOverview, MarketPrices

if TYPE_CHECKING:
    from .client import Client


class System:
    """Represents a single 1KOMMA5° energy system (site).

    Instances should be obtained through :class:`~onekommafive.Systems` rather
    than constructed directly.

    Args:
        client: An authenticated :class:`~onekommafive.Client`.
        data: Raw system dictionary as returned by the Heartbeat API.
    """

    def __init__(self, client: "Client", data: dict[str, Any]) -> None:
        self._client = client
        self._data = data

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    def id(self) -> str:
        """Return the unique system identifier (UUID)."""
        return self._data["id"]

    # ------------------------------------------------------------------
    # Live data
    # ------------------------------------------------------------------

    def get_live_overview(self) -> LiveOverview:
        """Fetch the current real-time energy overview for this system.

        Returns:
            A :class:`~onekommafive.models.LiveOverview` with the latest
            power and state-of-charge values.

        Raises:
            RequestError: If the server returns a non-200 response.
        """
        url = f"{self._client.HEARTBEAT_API}/api/v1/systems/{self.id()}/live-overview"
        response = requests.get(url=url, headers=self._client._auth_headers(), timeout=30)
        if response.status_code != 200:
            raise RequestError(f"Failed to get live overview: {response.text}")
        return LiveOverview.from_dict(response.json())

    # ------------------------------------------------------------------
    # EV chargers
    # ------------------------------------------------------------------

    def get_ev_chargers(self) -> list[EVCharger]:
        """Retrieve all EV charger devices registered to this system.

        Returns:
            A list of :class:`~onekommafive.EVCharger` instances (may be empty).

        Raises:
            RequestError: If the server returns a non-200 response.
        """
        url = f"{self._client.HEARTBEAT_API}/api/v1/systems/{self.id()}/devices/evs"
        response = requests.get(url=url, headers=self._client._auth_headers(), timeout=30)
        if response.status_code != 200:
            raise RequestError(f"Failed to get EV chargers: {response.text}")
        return [EVCharger(self._client, self, ev) for ev in response.json()]

    # ------------------------------------------------------------------
    # EMS
    # ------------------------------------------------------------------

    def get_ems_settings(self) -> EmsSettings:
        """Fetch the current energy-management system settings.

        Returns:
            An :class:`~onekommafive.models.EmsSettings` instance.

        Raises:
            RequestError: If the server returns a non-200 response.
        """
        url = (
            f"{self._client.HEARTBEAT_API}"
            f"/api/v1/systems/{self.id()}/ems/actions/get-settings"
        )
        response = requests.get(url=url, headers=self._client._auth_headers(), timeout=30)
        if response.status_code != 200:
            raise RequestError(f"Failed to get EMS settings: {response.text}")
        return EmsSettings.from_dict(response.json())

    def set_ems_mode(self, auto: bool) -> None:
        """Switch the energy-management system between auto and manual mode.

        Args:
            auto: Pass ``True`` to enable EMS automatic optimisation, ``False``
                to enable manual override.

        Raises:
            RequestError: If the server returns a non-201 response.
        """
        url = (
            f"{self._client.HEARTBEAT_API}"
            f"/api/v1/systems/{self.id()}/ems/actions/set-manual-override"
        )
        response = requests.post(
            url=url,
            json={"manualSettings": {}, "overrideAutoSettings": not auto},
            headers=self._client._auth_headers(),
            timeout=30,
        )
        if response.status_code != 201:
            raise RequestError(f"Failed to set EMS mode: {response.text}")

    # ------------------------------------------------------------------
    # Prices
    # ------------------------------------------------------------------

    def get_prices(
        self,
        start: datetime.datetime,
        end: datetime.datetime,
        resolution: str | None = None,
    ) -> MarketPrices:
        """Fetch market electricity prices for a given date range.

        Args:
            start: The start of the requested interval (inclusive).
            end: The end of the requested interval (inclusive).
            resolution: Data resolution string, e.g. ``"1h"`` for hourly data.
                When omitted the API returns one aggregated entry per day, which
                allows multi-day ranges.  When set to ``"1h"`` the range must
                span at most one day.

        Returns:
            A :class:`~onekommafive.models.MarketPrices` instance.

        Raises:
            RequestError: If the server returns a non-200 response.
        """
        url = (
            f"{self._client.HEARTBEAT_API}"
            f"/api/v2/systems/{self.id()}/charts/market-prices"
        )
        params: dict[str, str] = {
            "from": start.strftime("%Y-%m-%d"),
            "to": end.strftime("%Y-%m-%d"),
        }
        if resolution is not None:
            params["resolution"] = resolution
        response = requests.get(
            url=url,
            params=params,
            headers=self._client._auth_headers(),
            timeout=30,
        )
        if response.status_code != 200:
            raise RequestError(f"Failed to get prices: {response.text}")
        return MarketPrices.from_dict(response.json())

    def __repr__(self) -> str:
        return f"System(id={self.id()!r})"
