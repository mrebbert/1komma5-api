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
from .models import ChargingMode, EmsManualDevice, EmsSettings, LiveOverview, MarketPrices, SystemInfo, User
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
    "MarketPrices",
    "SystemInfo",
    "User",
    "ApiError",
    "AuthenticationError",
    "RequestError",
]
