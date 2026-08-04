"""1KOMMA5° Heartbeat API client.

Provides typed Python bindings for the 1KOMMA5° Heartbeat REST API, including
OAuth2 authentication with automatic token refresh, system monitoring, EV
charger control, and electricity price retrieval.

Typical usage::

    from onekommafive import Client, Systems

    client = Client("user@example.com", "s3cr3t")
    all_systems = Systems(client).get_systems()

    for system in all_systems:
        overview = system.get_live_overview()
        print(f"PV power: {overview.pv_power} W")

        for charger in system.get_ev_chargers():
            print(f"Charger {charger.name()}: {charger.charging_mode().value}")
"""

from .client import Client
from .errors import ApiError, AuthenticationError, RequestError
from .ev_charger import EVCharger
from .models import (
    WEATHER_SYMBOLS,
    Asset,
    ChargingMode,
    ComparisonPrice,
    ConnectedSystem,
    Customer,
    DeviceGateway,
    EmsManualDevice,
    EmsSettings,
    EnergyData,
    EnergySlot,
    EnergyTrader,
    HeartbeatAiSummary,
    HeartbeatPrices,
    HeartbeatPriceWindow,
    HeartbeatSavings,
    ImpactOverview,
    LiveOverview,
    MarketPrices,
    MonthlyTradingSavings,
    Notification,
    NotificationChannelSettings,
    NotificationSettings,
    NotificationsList,
    OptimizationEvent,
    OptimizationEvents,
    PriceCustomizations,
    PriceGuarantee,
    SelfSufficiencyEvents,
    SiteDetails,
    SiteStatus,
    SmartMeter,
    Subscription,
    SubscriptionsList,
    SupportedVersions,
    SystemCustomer,
    SystemDetails,
    SystemInfo,
    User,
    VersionInfo,
    Wallbox,
    WeatherData,
    WeatherDay,
    WeatherSlot,
)
from .system import System
from .systems import Systems

__all__ = [
    "Client",
    "Systems",
    "System",
    "EVCharger",
    "ChargingMode",
    "LiveOverview",
    "EmsManualDevice",
    "EmsSettings",
    "EnergyData",
    "EnergySlot",
    "EnergyTrader",
    "HeartbeatAiSummary",
    "HeartbeatPrices",
    "HeartbeatPriceWindow",
    "HeartbeatSavings",
    "ImpactOverview",
    "MarketPrices",
    "MonthlyTradingSavings",
    "OptimizationEvent",
    "OptimizationEvents",
    "ComparisonPrice",
    "PriceCustomizations",
    "PriceGuarantee",
    "SelfSufficiencyEvents",
    "SmartMeter",
    "SiteDetails",
    "Subscription",
    "SubscriptionsList",
    "ConnectedSystem",
    "SupportedVersions",
    "VersionInfo",
    "Customer",
    "Notification",
    "NotificationChannelSettings",
    "NotificationSettings",
    "NotificationsList",
    "Wallbox",
    "WeatherData",
    "WeatherDay",
    "WeatherSlot",
    "WEATHER_SYMBOLS",
    "SystemInfo",
    "SystemDetails",
    "SystemCustomer",
    "DeviceGateway",
    "SiteStatus",
    "Asset",
    "User",
    "ApiError",
    "AuthenticationError",
    "RequestError",
]
