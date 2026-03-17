"""System resource for the 1KOMMA5° Heartbeat API."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any

import requests

from .errors import RequestError
from .ev_charger import EVCharger
from .models import ChargingMode, EmsSettings, EnergyData, LiveOverview, MarketPrices, SystemInfo

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

    def info(self) -> SystemInfo:
        """Return static metadata for this system.

        Fetches the full system detail from ``/api/v4/systems/{id}``.

        Returns:
            A :class:`~onekommafive.models.SystemInfo` instance.

        Raises:
            RequestError: If the server returns a non-200 response.
        """
        url = f"{self._client.HEARTBEAT_API}/api/v4/systems/{self.id()}"
        response = requests.get(url=url, headers=self._client._auth_headers(), timeout=30)
        if response.status_code != 200:
            raise RequestError(f"Failed to get system info: {response.text}")
        return SystemInfo.from_dict(response.json())

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
        url = f"{self._client.HEARTBEAT_API}/api/v3/systems/{self.id()}/live-overview"
        response = requests.get(url=url, headers=self._client._auth_headers(), timeout=30)
        if response.status_code != 200:
            raise RequestError(f"Failed to get live overview: {response.text}")
        return LiveOverview.from_dict(response.json())

    # ------------------------------------------------------------------
    # EV chargers
    # ------------------------------------------------------------------

    def get_displayed_ev_charging_modes(self) -> list[ChargingMode]:
        """Fetch the EV charging modes that are available for this site.

        Returns:
            A list of enabled :class:`~onekommafive.models.ChargingMode` values.

        Raises:
            RequestError: If the server returns a non-200 response.
        """
        url = (
            f"{self._client.HEARTBEAT_API}"
            f"/api/v1/sites/{self.id()}/assets/evs/displayed-ev-charging-modes"
        )
        response = requests.get(url=url, headers=self._client._auth_headers(), timeout=30)
        if response.status_code != 200:
            raise RequestError(f"Failed to get displayed EV charging modes: {response.text}")
        data = response.json()
        return [
            ChargingMode(entry["type"])
            for entry in data.get("displayedEvChargingModes", [])
            if not entry.get("disabled", False)
        ]

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
    # Energy data
    # ------------------------------------------------------------------

    def get_energy_today(self, resolution: str = "1h") -> EnergyData:
        """Fetch energy production and consumption data for today.

        Args:
            resolution: Data resolution; ``"1h"`` (default) or ``"15m"``.

        Returns:
            An :class:`~onekommafive.models.EnergyData` instance.

        Raises:
            RequestError: If the server returns a non-200 response.
        """
        url = f"{self._client.HEARTBEAT_API}/api/v2/systems/{self.id()}/energy-today"
        response = requests.get(
            url=url,
            params={"resolution": resolution},
            headers=self._client._auth_headers(),
            timeout=30,
        )
        if response.status_code != 200:
            raise RequestError(f"Failed to get energy today: {response.text}")
        return EnergyData.from_dict(response.json())

    def get_energy_historical(
        self,
        from_date: datetime.date,
        to_date: datetime.date,
        resolution: str = "1h",
    ) -> EnergyData:
        """Fetch historical energy data for a date range.

        For ``resolution="15m"`` ``from_date`` and ``to_date`` must be the same day.
        For ``resolution="1h"`` ``to_date`` may be at most one day after ``from_date``.

        Args:
            from_date: Start date (inclusive).
            to_date: End date (inclusive).
            resolution: Data resolution; ``"1h"`` (default) or ``"15m"``.

        Returns:
            An :class:`~onekommafive.models.EnergyData` instance.

        Raises:
            RequestError: If the server returns a non-200 response.
        """
        url = f"{self._client.HEARTBEAT_API}/api/v3/systems/{self.id()}/energy-historical"
        response = requests.get(
            url=url,
            params={
                "from": from_date.isoformat(),
                "to": to_date.isoformat(),
                "resolution": resolution,
            },
            headers=self._client._auth_headers(),
            timeout=30,
        )
        if response.status_code != 200:
            raise RequestError(f"Failed to get historical energy data: {response.text}")
        return EnergyData.from_dict(response.json())

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
        resolution: str = "1h",
    ) -> MarketPrices:
        """Fetch market electricity prices for a given date range.

        Args:
            start: The start of the requested interval (inclusive).
            end: The end of the requested interval (inclusive).
            resolution: Data resolution string; must be ``"1h"`` or ``"15m"``.
                Defaults to ``"1h"``.

        Returns:
            A :class:`~onekommafive.models.MarketPrices` instance.

        Raises:
            RequestError: If the server returns a non-200 response.
        """
        url = (
            f"{self._client.HEARTBEAT_API}"
            f"/api/v4/systems/{self.id()}/charts/market-prices"
        )
        params: dict[str, str] = {
            "from": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "to": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "resolution": resolution,
        }
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
