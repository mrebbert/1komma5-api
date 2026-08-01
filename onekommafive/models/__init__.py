"""Typed data models returned by the 1KOMMA5° API.

This package re-exports all model classes so existing
``from onekommafive.models import X`` imports continue to work after the
domain-based split introduced in this refactor.
"""

from .analytics import EnergyTrader, HeartbeatAiSummary, ImpactOverview, MonthlyTradingSavings
from .customer import Customer
from .ems import EmsManualDevice, EmsSettings
from .energy import EnergyData, EnergySlot, HeartbeatSavings
from .ev import ChargingMode, Wallbox
from .live import LiveOverview
from .meta import SupportedVersions, VersionInfo
from .notifications import (
    Notification,
    NotificationChannelSettings,
    NotificationSettings,
    NotificationsList,
)
from .optimizations import OptimizationEvent, OptimizationEvents, SelfSufficiencyEvents
from .prices import ComparisonPrice, MarketPrices, PriceCustomizations, PriceGuarantee
from .sites import Asset, SiteDetails, SiteStatus, SmartMeter
from .system import DeviceGateway, SystemCustomer, SystemDetails, SystemInfo
from .user import User
from .weather import WEATHER_SYMBOLS, WeatherData, WeatherDay, WeatherSlot

__all__ = [
    "WEATHER_SYMBOLS",
    "Asset",
    "ChargingMode",
    "ComparisonPrice",
    "Customer",
    "DeviceGateway",
    "EmsManualDevice",
    "EmsSettings",
    "EnergyData",
    "EnergySlot",
    "EnergyTrader",
    "HeartbeatAiSummary",
    "HeartbeatSavings",
    "ImpactOverview",
    "LiveOverview",
    "MarketPrices",
    "MonthlyTradingSavings",
    "Notification",
    "NotificationChannelSettings",
    "NotificationSettings",
    "NotificationsList",
    "OptimizationEvent",
    "OptimizationEvents",
    "PriceCustomizations",
    "PriceGuarantee",
    "SelfSufficiencyEvents",
    "SiteDetails",
    "SiteStatus",
    "SmartMeter",
    "SupportedVersions",
    "SystemCustomer",
    "SystemDetails",
    "SystemInfo",
    "User",
    "VersionInfo",
    "Wallbox",
    "WeatherData",
    "WeatherDay",
    "WeatherSlot",
]
