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
    SiteStatus,
    SystemDetails,
    SystemInfo,
    WeatherData,
)

if TYPE_CHECKING:
    from .client import Client
    from .ev_charger import EVCharger


class System:
    """A single 1KOMMA5° energy system (site).

    Obtain via :class:`~onekommafive.Systems` rather than constructing directly.
    """

    def __init__(self, client: Client, data: dict[str, Any]) -> None:
        self._client = client
        self._data = data

    # ------------------------------------------------------------------
    # URL helpers
    # ------------------------------------------------------------------

    def _systems_url(self, version: str, *parts: str) -> str:
        base = f"{self._client.HEARTBEAT_API}/api/{version}/systems/{self.id()}"
        return base + ("/" + "/".join(parts) if parts else "")

    def _sites_url(self, version: str, *parts: str) -> str:
        base = f"{self._client.HEARTBEAT_API}/api/{version}/sites/{self.id()}"
        return base + ("/" + "/".join(parts) if parts else "")

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    def id(self) -> str:
        return self._data["id"]

    def info(self) -> SystemInfo:
        """Return static metadata for this system (``GET /api/v4/systems/{id}``)."""
        data = self._client._request(
            "GET", self._systems_url("v4"), error_label="Failed to get system info",
        )
        return SystemInfo.from_dict(data)

    def get_details(self) -> SystemDetails:
        """Return extended metadata (``GET /api/v1/systems/{id}/details``).

        Richer than :meth:`info`: includes EMP type, technical contact,
        embedded customer details, smart-meter status, earliest measurement
        date, and installed device gateways.
        """
        data = self._client._request(
            "GET", self._systems_url("v1", "details"), error_label="Failed to get system details",
        )
        return SystemDetails.from_dict(data)

    def get_status_and_assets(self) -> SiteStatus:
        """Return site connection status and installed asset inventory."""
        data = self._client._request(
            "GET",
            self._sites_url("v2", "status-and-assets"),
            error_label="Failed to get site status and assets",
        )
        return SiteStatus.from_dict(data)

    def get_active_features(self, customer_id: str) -> list[str]:
        """Return active feature flags for this site (e.g. ``"DYNAMIC_TARIFF"``).

        ``customer_id`` is available via :meth:`get_details`
        (``SystemDetails.customer_id``).
        """
        data = self._client._request(
            "GET",
            f"{self._client.IDENTITY_API}/api/v1/customers/{customer_id}/sites/{self.id()}/active-features",
            error_label="Failed to get active features",
        )
        return list(data.get("features", []))

    # ------------------------------------------------------------------
    # Live data
    # ------------------------------------------------------------------

    def get_live_overview(self) -> LiveOverview:
        """Fetch the current real-time energy overview for this system."""
        data = self._client._request(
            "GET", self._systems_url("v3", "live-overview"),
            error_label="Failed to get live overview",
        )
        return LiveOverview.from_dict(data)

    # ------------------------------------------------------------------
    # EV chargers
    # ------------------------------------------------------------------

    def get_displayed_ev_charging_modes(self) -> list[ChargingMode]:
        """Fetch the EV charging modes available (and enabled) for this site."""
        data = self._client._request(
            "GET",
            self._sites_url("v1", "assets", "evs", "displayed-ev-charging-modes"),
            error_label="Failed to get displayed EV charging modes",
        )
        return [
            ChargingMode(entry["type"])
            for entry in data.get("displayedEvChargingModes", [])
            if not entry.get("disabled", False)
        ]

    def get_ev_chargers(self) -> list[EVCharger]:
        """Retrieve all EV charger devices registered to this system."""
        from .ev_charger import EVCharger

        data = self._client._request(
            "GET", self._systems_url("v1", "devices", "evs"),
            error_label="Failed to get EV chargers",
        )
        return [EVCharger(self._client, self, ev) for ev in data]

    # ------------------------------------------------------------------
    # Energy data
    # ------------------------------------------------------------------

    def get_energy_today(self, resolution: str = "1h") -> EnergyData:
        """Fetch today's energy production and consumption (``resolution``: ``"1h"`` or ``"15m"``)."""
        data = self._client._request(
            "GET", self._systems_url("v2", "energy-today"),
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
        """Fetch historical energy data for an inclusive date range.

        For ``resolution="15m"`` both dates must be the same day; for ``"1h"``
        ``to_date`` may be at most one day after ``from_date``.
        """
        data = self._client._request(
            "GET", self._systems_url("v3", "energy-historical"),
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
        """Fetch the current energy-management system settings."""
        data = self._client._request(
            "GET", self._systems_url("v1", "ems", "actions", "get-settings"),
            error_label="Failed to get EMS settings",
        )
        return EmsSettings.from_dict(data)

    def set_ems_mode(self, auto: bool) -> None:
        """Switch the EMS between auto (``True``) and manual override (``False``)."""
        self._client._request(
            "POST",
            self._systems_url("v1", "ems", "actions", "set-manual-override"),
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
        """Fetch market electricity prices for ``[start, end]`` (``"1h"`` or ``"15m"``)."""
        data = self._client._request(
            "GET", self._systems_url("v4", "charts", "market-prices"),
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
        """Fetch the weather forecast: today + tomorrow summaries, plus 48 h of 3 h slots."""
        data = self._client._request(
            "GET", self._systems_url("v1", "weather"),
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
        """Fetch AI optimisation decisions for ``[start, end]`` (inclusive)."""
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
