"""EV charger resource for the 1KOMMA5° Heartbeat API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import requests

from .errors import RequestError
from .models import ChargingMode

if TYPE_CHECKING:
    from .client import Client
    from .system import System


class EVCharger:
    """Represents a single EV charger device within a 1KOMMA5° system.

    Instances should be obtained through :meth:`~onekommafive.System.get_ev_chargers`
    rather than constructed directly.

    Args:
        client: An authenticated :class:`~onekommafive.Client`.
        system: The :class:`~onekommafive.System` this charger belongs to.
        data: Raw device dictionary as returned by the Heartbeat API.
    """

    def __init__(self, client: "Client", system: "System", data: dict[str, Any]) -> None:
        self._client = client
        self._system = system
        self._data = data

    # ------------------------------------------------------------------
    # Read-only properties
    # ------------------------------------------------------------------

    def id(self) -> str:
        """Return the unique device identifier."""
        return self._data["id"]

    def name(self) -> str | None:
        """Return the human-readable name configured in the app, or ``None``."""
        return (self._data.get("profile") or {}).get("name")

    def manufacturer(self) -> str | None:
        """Return the vehicle manufacturer name (whitespace-stripped), or ``None``."""
        value = (self._data.get("profile") or {}).get("manufacturer")
        return value.strip() if value else None

    def model(self) -> str | None:
        """Return the vehicle model name, or ``None``."""
        return (self._data.get("profile") or {}).get("model")

    def capacity_wh(self) -> float | None:
        """Return the battery capacity in Wh, or ``None``."""
        cap = (self._data.get("profile") or {}).get("capacity")
        return float(cap["value"]) if cap else None

    def min_charging_current_a(self) -> float | None:
        """Return the minimum charging current in A, or ``None``."""
        node = (self._data.get("profile") or {}).get("minChargingCurrent")
        return float(node["value"]) if node else None

    def safety_range_km(self) -> float | None:
        """Return the safety range buffer in km, or ``None``."""
        node = (self._data.get("profile") or {}).get("safetyRange")
        return float(node["value"]) if node else None

    def assigned_charger_id(self) -> str | None:
        """Return the ID of the physical wallbox assigned to this vehicle, or ``None``."""
        return self._data.get("assignedChargerId")

    def manual_soc_timestamp(self) -> str | None:
        """Return the ISO-8601 timestamp of the last manual SoC update, or ``None``."""
        return self._data.get("manualSocTimestamp")

    def updated_at(self) -> str | None:
        """Return the ISO-8601 timestamp of the last record update, or ``None``."""
        return self._data.get("updatedAt")

    def charging_mode(self) -> ChargingMode:
        """Return the currently active :class:`~onekommafive.models.ChargingMode`."""
        return ChargingMode(self._data["chargeSettings"]["chargingMode"])

    def charging_mode_updated_at(self) -> str | None:
        """Return the ISO-8601 timestamp when the charging mode was last changed, or ``None``."""
        return (self._data.get("chargeSettings") or {}).get("chargingModeUpdatedAt")

    def default_soc(self) -> float | None:
        """Return the default target SoC as a percentage (0–100), or ``None``."""
        val = (self._data.get("chargeSettings") or {}).get("defaultSoc")
        return float(val * 100) if val is not None else None

    def target_soc(self) -> float | None:
        """Return the user-selected target SoC as a percentage (0–100), or ``None``."""
        val = (self._data.get("chargeSettings") or {}).get("targetSoc")
        return float(val * 100) if val is not None else None

    def primary_schedule_days(self) -> list[str]:
        """Return the list of days (e.g. ``['MONDAY', 'FRIDAY']``) in the primary schedule."""
        return (self._data.get("chargeSettings") or {}).get("primaryScheduleDays") or []

    def primary_schedule_departure_time(self) -> str | None:
        """Return the primary departure time as ``'HH:MM'``, or ``None``."""
        return (self._data.get("chargeSettings") or {}).get("primaryScheduleDepartureTime")

    def primary_schedule_departure_soc(self) -> float | None:
        """Return the primary schedule target departure SoC as a percentage (0–100), or ``None``."""
        val = (self._data.get("chargeSettings") or {}).get("primaryScheduleDepartureSoc")
        return float(val * 100) if val is not None else None

    def secondary_schedule_departure_time(self) -> str | None:
        """Return the secondary departure time as ``'HH:MM'``, or ``None``."""
        return (self._data.get("chargeSettings") or {}).get("secondaryScheduleDepartureTime")

    def secondary_schedule_departure_soc(self) -> float | None:
        """Return the secondary schedule target departure SoC as a percentage (0–100), or ``None``."""
        val = (self._data.get("chargeSettings") or {}).get("secondaryScheduleDepartureSoc")
        return float(val * 100) if val is not None else None

    def current_soc(self) -> float | None:
        """Return the manually set target state-of-charge as a percentage (0–100).

        Returns ``None`` when the charger is not in
        :attr:`~onekommafive.models.ChargingMode.SMART_CHARGE` mode or when no
        target SoC has been configured.
        """
        if self.charging_mode() != ChargingMode.SMART_CHARGE:
            return None
        manual_soc = self._data.get("manualSoc")
        if manual_soc is None:
            return None
        return float(manual_soc * 100.0)

    # ------------------------------------------------------------------
    # Mutating operations
    # ------------------------------------------------------------------

    def set_charging_mode(self, mode: ChargingMode) -> None:
        """Change the charging strategy of this EV charger.

        No-ops silently when *mode* matches the currently active mode.

        Args:
            mode: The desired :class:`~onekommafive.models.ChargingMode`.

        Raises:
            RequestError: If the server returns a non-200 response.
        """
        if self.charging_mode() == mode:
            return

        url = (
            f"{self._client.HEARTBEAT_API}"
            f"/api/v1/systems/{self._system.id()}"
            f"/devices/evs/{self.id()}"
        )
        response = requests.patch(
            url=url,
            json={"chargeSettings": {"chargingMode": mode.value}},
            headers=self._client._auth_headers(),
            timeout=30,
        )
        if response.status_code != 200:
            raise RequestError(f"Failed to set charging mode: {response.text}")

        self._data["chargeSettings"]["chargingMode"] = mode.value

    def set_current_soc(self, soc: float) -> None:
        """Set the manually controlled target state-of-charge.

        Only effective in :attr:`~onekommafive.models.ChargingMode.SMART_CHARGE`
        mode; silently ignores calls in other modes.

        Args:
            soc: Target SoC as a percentage between 0 and 100 (inclusive).

        Raises:
            RequestError: If the server returns a non-200 response.
        """
        if self.charging_mode() != ChargingMode.SMART_CHARGE:
            return

        soc_decimal = float(soc / 100.0) if soc > 0 else 0.0

        url = (
            f"{self._client.HEARTBEAT_API}"
            f"/api/v1/systems/{self._system.id()}"
            f"/devices/evs/{self.id()}"
        )
        response = requests.patch(
            url=url,
            json={"id": self.id(), "manualSoc": soc_decimal},
            headers=self._client._auth_headers(),
            timeout=30,
        )
        if response.status_code != 200:
            raise RequestError(f"Failed to set state of charge: {response.text}")

        self._data["manualSoc"] = soc_decimal

    def set_target_soc(self, soc: float) -> None:
        """Set the target state-of-charge for SMART_CHARGE mode.

        No-ops silently when *soc* matches the current target.

        Args:
            soc: Target SoC as a percentage between 0 and 100 (inclusive).

        Raises:
            RequestError: If the server returns a non-200 response.
        """
        if self.target_soc() == soc:
            return

        soc_decimal = soc / 100.0
        url = (
            f"{self._client.HEARTBEAT_API}"
            f"/api/v1/systems/{self._system.id()}"
            f"/devices/evs/{self.id()}"
        )
        response = requests.patch(
            url=url,
            json={"chargeSettings": {"targetSoc": soc_decimal}},
            headers=self._client._auth_headers(),
            timeout=30,
        )
        if response.status_code != 200:
            raise RequestError(f"Failed to set target state of charge: {response.text}")

        self._data["chargeSettings"]["targetSoc"] = soc_decimal

    def set_primary_departure_time(self, time: str) -> None:
        """Set the primary schedule departure time.

        No-ops silently when *time* matches the current departure time.

        Args:
            time: Departure time as ``'HH:MM'``, e.g. ``'06:00'``.

        Raises:
            RequestError: If the server returns a non-200 response.
        """
        if self.primary_schedule_departure_time() == time:
            return

        url = (
            f"{self._client.HEARTBEAT_API}"
            f"/api/v1/systems/{self._system.id()}"
            f"/devices/evs/{self.id()}"
        )
        response = requests.patch(
            url=url,
            json={"chargeSettings": {"primaryScheduleDepartureTime": time}},
            headers=self._client._auth_headers(),
            timeout=30,
        )
        if response.status_code != 200:
            raise RequestError(f"Failed to set primary departure time: {response.text}")

        self._data["chargeSettings"]["primaryScheduleDepartureTime"] = time

    def __repr__(self) -> str:
        return f"EVCharger(id={self.id()!r}, name={self.name()!r}, mode={self.charging_mode().value!r})"
