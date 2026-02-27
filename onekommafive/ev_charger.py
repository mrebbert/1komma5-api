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
        profile = self._data.get("profile", {})
        return profile.get("name")

    def charging_mode(self) -> ChargingMode:
        """Return the currently active :class:`~onekommafive.models.ChargingMode`."""
        return ChargingMode(self._data["chargeSettings"]["chargingMode"])

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

    def __repr__(self) -> str:
        return f"EVCharger(id={self.id()!r}, name={self.name()!r}, mode={self.charging_mode().value!r})"
