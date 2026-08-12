"""System resource for the 1KOMMA5° Heartbeat API."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any

from .models import (
    ChargingMode,
    ComparisonPrice,
    Customer,
    EmsSettings,
    EnergyData,
    EnergyTrader,
    HeartbeatAiSummary,
    HeartbeatPrices,
    HeartbeatSavings,
    ImpactOverview,
    LiveOverview,
    MarketPrices,
    MonthlyTradingSavings,
    NotificationSettings,
    NotificationsList,
    OptimizationEvents,
    PriceCustomizations,
    PriceGuarantee,
    SelfSufficiencyEvents,
    SiteDetails,
    SiteStatus,
    SmartMeter,
    SubscriptionsList,
    SystemDetails,
    SystemInfo,
    Wallbox,
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
            self._sites_url("v3", "status-and-assets"),
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

    def get_energy_savings(
        self,
        from_date: datetime.date | None = None,
        to_date: datetime.date | None = None,
    ) -> HeartbeatSavings:
        """Fetch aggregated Heartbeat savings for an inclusive date range.

        When both dates are omitted the API returns its default rolling
        window (undocumented). Dates must be date-only (``YYYY-MM-DD``);
        passing ISO datetimes with a time component is rejected by the API.
        """
        params: dict[str, str] = {}
        if from_date is not None:
            params["from"] = from_date.isoformat()
        if to_date is not None:
            params["to"] = to_date.isoformat()
        data = self._client._request(
            "GET", self._systems_url("v1", "energy-savings"),
            params=params or None,
            error_label="Failed to get energy savings",
        )
        return HeartbeatSavings.from_dict(data)

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
    # Prices — customizations, comparison, guarantee
    # ------------------------------------------------------------------

    def get_price_customizations(self) -> PriceCustomizations:
        """Fetch user-configured energy prices (grid, comparison, monthly base)."""
        data = self._client._request(
            "GET", self._systems_url("v2", "price-customizations"),
            error_label="Failed to get price customizations",
        )
        return PriceCustomizations.from_dict(data)

    def get_comparison_price(self) -> ComparisonPrice:
        """Fetch the site's grid-supplier comparison price (EUR/kWh)."""
        data = self._client._request(
            "GET",
            f"{self._client.HEARTBEAT_API}/api/v2/comparison-price",
            params={"siteId": self.id()},
            error_label="Failed to get comparison price",
        )
        return ComparisonPrice.from_dict(data)

    def get_price_guarantee(self, customer_id: str) -> PriceGuarantee:
        """Fetch the contractual electricity-price guarantee for this customer.

        ``customer_id`` is available via :meth:`get_details`
        (``SystemDetails.customer_id``). Sits on the ``customer-identity``
        host and requires ``systemId`` as a query parameter (server quirk —
        the customer scope alone is not sufficient).
        """
        data = self._client._request(
            "GET",
            f"{self._client.IDENTITY_API}/api/v1/customers/{customer_id}/price-guarantee",
            params={"systemId": self.id()},
            error_label="Failed to get price guarantee",
        )
        return PriceGuarantee.from_dict(data)

    # ------------------------------------------------------------------
    # Wallboxes (physical charging hardware) and smart meter
    # ------------------------------------------------------------------

    def get_wallboxes(self) -> list[Wallbox]:
        """Fetch physical wallbox hardware for this system.

        Complements :meth:`get_ev_chargers` which returns the vehicle-side
        charging profiles.
        """
        data = self._client._request(
            "GET", self._systems_url("v1", "devices", "ev-chargers"),
            error_label="Failed to get wallboxes",
        )
        return [Wallbox.from_dict(w) for w in data or []]

    def get_smart_meter(self) -> SmartMeter:
        """Fetch smart-meter registration details for this site (EIC, DSO code, concession fee)."""
        data = self._client._request(
            "GET", self._sites_url("v1", "smart-meter"),
            error_label="Failed to get smart meter",
        )
        return SmartMeter.from_dict(data)

    # ------------------------------------------------------------------
    # Analytics — CO2, trading, and AI-summary
    # ------------------------------------------------------------------

    def get_impact_overview(self) -> ImpactOverview:
        """Fetch lifetime CO2-savings figures for this site.

        Ignores any query params; the response is always lifetime totals.
        """
        data = self._client._request(
            "GET", self._systems_url("v2", "impact-overview"),
            error_label="Failed to get impact overview",
        )
        return ImpactOverview.from_dict(data)

    def get_energy_trader(self) -> EnergyTrader:
        """Fetch lifetime energy-trading statistics for this site.

        Uses the account-wide endpoint ``/api/v2/energy-trader`` with the
        site ID passed as a ``siteId`` query parameter (not a path segment).
        """
        data = self._client._request(
            "GET",
            f"{self._client.HEARTBEAT_API}/api/v2/energy-trader",
            params={"siteId": self.id()},
            error_label="Failed to get energy trader",
        )
        return EnergyTrader.from_dict(data)

    def get_heartbeat_prices(self) -> HeartbeatPrices:
        """Fetch the site's financial breakdown across five aggregation windows.

        ``GET /api/v3/heartbeat-prices?siteId={id}`` — for each of
        ``day`` / ``week`` / ``month`` / ``halfYear`` / ``year`` returns
        PV production, grid feed-in, grid consumption, site totals, and
        the effective per-kWh Heartbeat price.

        See :class:`~onekommafive.HeartbeatPriceWindow` for the VAT
        convention (**most likely gross**, matching the German consumer
        UI) and the three distinct price semantics (PV valuation,
        feed-in tariff, grid consumption price, effective Heartbeat
        price, comparison tariff).
        """
        data = self._client._request(
            "GET",
            f"{self._client.HEARTBEAT_API}/api/v3/heartbeat-prices",
            params={"siteId": self.id()},
            error_label="Failed to get heartbeat prices",
        )
        return HeartbeatPrices.from_dict(data)

    def get_monthly_trading_savings(self) -> MonthlyTradingSavings:
        """Fetch the average monthly savings from Energy Trader activity.

        Uses ``/api/v1/energy-trader-savings/{site_id}/month`` with the
        site (not customer) ID as the path segment — verified live.
        """
        data = self._client._request(
            "GET",
            f"{self._client.HEARTBEAT_API}/api/v1/energy-trader-savings/{self.id()}/month",
            error_label="Failed to get monthly trading savings",
        )
        return MonthlyTradingSavings.from_dict(data)

    def get_heartbeat_ai_summary(self, resolution: str = "1M") -> HeartbeatAiSummary:
        """Fetch aggregated Heartbeat-AI metrics for a resolution window.

        ``resolution`` must be one of ``"1W"``, ``"1M"``, or ``"1Y"``.
        ``"1W"`` and ``"1Y"`` return only CO2/production figures; the
        self-sufficiency and earnings fields are ``None`` in those cases.
        """
        data = self._client._request(
            "GET",
            f"{self._client.HEARTBEAT_API}/api/v2/heartbeat-ai/summary",
            params={"siteId": self.id(), "resolution": resolution},
            error_label="Failed to get Heartbeat AI summary",
        )
        return HeartbeatAiSummary.from_dict(resolution, data)

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

    def get_self_sufficiency_events(
        self,
        start: datetime.datetime,
        end: datetime.datetime,
    ) -> SelfSufficiencyEvents:
        """Fetch AI self-sufficiency events for ``[start, end]`` (inclusive).

        Same payload shape as :meth:`get_optimizations` but a different
        endpoint that surfaces a **different subset** of AI activity
        (typically the granular battery-discharge trace).
        """
        data = self._client._request(
            "GET",
            f"{self._client.HEARTBEAT_API}/api/v1/heartbeat-ai/self-sufficiency",
            params={
                "siteId": self.id(),
                "from": start.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "to": end.strftime("%Y-%m-%dT%H:%M:%S.999Z"),
            },
            error_label="Failed to get self-sufficiency events",
        )
        return SelfSufficiencyEvents.from_dict(data)

    # ------------------------------------------------------------------
    # Site details, customer, notifications
    # ------------------------------------------------------------------

    def get_site_details(self) -> SiteDetails:
        """Fetch extended site metadata (``GET /api/v3/sites/{id}/details``).

        Superset of :meth:`info`/:meth:`get_details`: adds bidding zone,
        EMP connection block and — most useful — the current EMS runtime
        state (``ems_mode``, ``ems_state``, ``ems_state_reasons``).
        """
        data = self._client._request(
            "GET", self._sites_url("v3", "details"),
            error_label="Failed to get site details",
        )
        return SiteDetails.from_dict(data)

    def get_customer(self, customer_id: str) -> Customer:
        """Fetch the full customer record (``GET /api/v3/customers/{id}``, IDENTITY host).

        Superset of the embedded :class:`~onekommafive.SystemCustomer`
        (which only exposes id/name/email). ``customer_id`` is available
        via :meth:`get_details`.
        """
        data = self._client._request(
            "GET", f"{self._client.IDENTITY_API}/api/v3/customers/{customer_id}",
            error_label="Failed to get customer",
        )
        return Customer.from_dict(data)

    def get_subscriptions(self, customer_id: str) -> SubscriptionsList:
        """Fetch all customer subscriptions / contracts.

        ``GET /api/v1/customers/{cid}/subscriptions`` (IDENTITY host).
        Returns all active contracts for a customer — electricity
        (``DYNAMIC_PULSE``), smart-meter (``SMART_METER``), platform
        (``HEARTBEAT``), trading (``ENERGY_TRADER``) — with universal
        contract metadata mapped and PII-heavy fields (IBAN, addresses,
        CRM IDs, ``metadata.payload``, ``statusHistory``) retained only
        in :attr:`~onekommafive.Subscription.raw`.

        See :class:`~onekommafive.Subscription` for the mapped subset
        and PII handling.

        ``customer_id`` is available via :meth:`get_details` — same
        pattern as :meth:`get_customer`.
        """
        data = self._client._request(
            "GET",
            f"{self._client.IDENTITY_API}/api/v1/customers/{customer_id}/subscriptions",
            error_label="Failed to get subscriptions",
        )
        return SubscriptionsList.from_dict(data)

    def get_notifications(self) -> NotificationsList:
        """Fetch recent push/in-app notifications for the authenticated user.

        ``GET /api/v1/users/{uid}/notifications/latest?systemId={id}``.
        The user id is looked up lazily via :meth:`~onekommafive.Client.get_user`.
        """
        user = self._client.get_user()
        data = self._client._request(
            "GET",
            f"{self._client.HEARTBEAT_API}/api/v1/users/{user.id}/notifications/latest",
            params={"systemId": self.id()},
            error_label="Failed to get notifications",
        )
        return NotificationsList.from_dict(data)

    def get_notification_settings(self) -> NotificationSettings:
        """Fetch the user's notification preferences for this system.

        ``GET /api/v1/systems/{id}/users/{uid}/notifications/settings``.
        The user id is looked up lazily via :meth:`~onekommafive.Client.get_user`.
        """
        user = self._client.get_user()
        data = self._client._request(
            "GET",
            self._systems_url("v1", "users", user.id, "notifications", "settings"),
            error_label="Failed to get notification settings",
        )
        return NotificationSettings.from_dict(data)

    def __repr__(self) -> str:
        return f"System(id={self.id()!r})"
