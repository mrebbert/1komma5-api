"""System resource for the 1KOMMA5° Heartbeat API."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any

from .models import (
    ChargingMode,
    EmsSettings,
    EnergyData,
    LiveOverview,
    MarketPrices,
    OptimizationEvents,
    SystemInfo,
    WeatherData,
)

if TYPE_CHECKING:
    from .client import Client
    from .ev_charger import EVCharger


class System:
    """Represents a single 1KOMMA5° energy system (site).

    Instances should be obtained through :class:`~onekommafive.Systems` rather
    than constructed directly.

    Args:
        client: An authenticated :class:`~onekommafive.Client`.
        data: Raw system dictionary as returned by the Heartbeat API.
    """

    def __init__(self, client: Client, data: dict[str, Any]) -> None:
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
        data = self._client._request(
            "GET",
            f"{self._client.HEARTBEAT_API}/api/v4/systems/{self.id()}",
            error_label="Failed to get system info",
        )
        return SystemInfo.from_dict(data)

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
        data = self._client._request(
            "GET",
            f"{self._client.HEARTBEAT_API}/api/v3/systems/{self.id()}/live-overview",
            error_label="Failed to get live overview",
        )
        return LiveOverview.from_dict(data)

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
        data = self._client._request(
            "GET",
            f"{self._client.HEARTBEAT_API}/api/v1/sites/{self.id()}/assets/evs/displayed-ev-charging-modes",
            error_label="Failed to get displayed EV charging modes",
        )
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
        from .ev_charger import EVCharger

        data = self._client._request(
            "GET",
            f"{self._client.HEARTBEAT_API}/api/v1/systems/{self.id()}/devices/evs",
            error_label="Failed to get EV chargers",
        )
        return [EVCharger(self._client, self, ev) for ev in data]

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
        data = self._client._request(
            "GET",
            f"{self._client.HEARTBEAT_API}/api/v2/systems/{self.id()}/energy-today",
            params={"resolution": resolution},
            error_label="Failed to get energy today",
        )
        return EnergyData.from_dict(data)

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
        data = self._client._request(
            "GET",
            f"{self._client.HEARTBEAT_API}/api/v3/systems/{self.id()}/energy-historical",
            params={
                "from": from_date.isoformat(),
                "to": to_date.isoformat(),
                "resolution": resolution,
            },
            error_label="Failed to get historical energy data",
        )
        return EnergyData.from_dict(data)

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
        data = self._client._request(
            "GET",
            f"{self._client.HEARTBEAT_API}/api/v1/systems/{self.id()}/ems/actions/get-settings",
            error_label="Failed to get EMS settings",
        )
        return EmsSettings.from_dict(data)

    def set_ems_mode(self, auto: bool) -> None:
        """Switch the energy-management system between auto and manual mode.

        Args:
            auto: Pass ``True`` to enable EMS automatic optimisation, ``False``
                to enable manual override.

        Raises:
            RequestError: If the server returns a non-201 response.
        """
        self._client._request(
            "POST",
            f"{self._client.HEARTBEAT_API}/api/v1/systems/{self.id()}/ems/actions/set-manual-override",
            json={"manualSettings": {}, "overrideAutoSettings": not auto},
            expected_status=201,
            error_label="Failed to set EMS mode",
        )

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
        data = self._client._request(
            "GET",
            f"{self._client.HEARTBEAT_API}/api/v4/systems/{self.id()}/charts/market-prices",
            params={
                "from": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "to": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "resolution": resolution,
            },
            error_label="Failed to get prices",
        )
        return MarketPrices.from_dict(data)

    # ------------------------------------------------------------------
    # Weather
    # ------------------------------------------------------------------

    def get_weather(self) -> WeatherData:
        """Fetch the weather forecast for this system's site location.

        Returns daily summaries for today and tomorrow plus 3-hour slots
        covering the next 48 hours.

        Returns:
            A :class:`~onekommafive.models.WeatherData` instance.

        Raises:
            RequestError: If the server returns a non-200 response.
        """
        data = self._client._request(
            "GET",
            f"{self._client.HEARTBEAT_API}/api/v1/systems/{self.id()}/weather",
            error_label="Failed to get weather",
        )
        return WeatherData.from_dict(data)

    # ------------------------------------------------------------------
    # AI optimisations
    # ------------------------------------------------------------------

    def get_optimizations(
        self,
        start: datetime.datetime,
        end: datetime.datetime,
    ) -> OptimizationEvents:
        """Fetch AI optimisation decisions for a time range.

        Args:
            start: Start of the requested interval (inclusive).
            end: End of the requested interval (inclusive).

        Returns:
            An :class:`~onekommafive.models.OptimizationEvents` instance.

        Raises:
            RequestError: If the server returns a non-200 response.
        """
        data = self._client._request(
            "GET",
            f"{self._client.HEARTBEAT_API}/api/v1/heartbeat-ai/optimizations",
            params={
                "siteId": self.id(),
                "from": start.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "to": end.strftime("%Y-%m-%dT%H:%M:%S.999Z"),
            },
            error_label="Failed to get optimizations",
        )
        return OptimizationEvents.from_dict(data)

    def __repr__(self) -> str:
        return f"System(id={self.id()!r})"
