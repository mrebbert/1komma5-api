"""EV charger resource for the 1KOMMA5° Heartbeat API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

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

    def __init__(self, client: Client, system: System, data: dict[str, Any]) -> None:
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
        return self._data.get("name")

    def manufacturer(self) -> str | None:
        """Return the vehicle manufacturer name (whitespace-stripped), or ``None``."""
        value = self._data.get("manufacturer")
        return value.strip() if value else None

    def model(self) -> str | None:
        """Return the vehicle model name, or ``None``."""
        return self._data.get("model")

    def capacity_wh(self) -> float | None:
        """Return the battery capacity in Wh, or ``None``.

        The site-scoped v2 API surfaces ``capacity`` in either ``Wh`` or
        ``kWh`` depending on the user's setup. This method normalises
        to Wh so the returned value is consistent.
        """
        cap = self._data.get("capacity")
        if not cap:
            return None
        value = float(cap["value"])
        if cap.get("unit") == "kWh":
            value *= 1000
        return value

    def min_charging_current_a(self) -> float | None:
        """Return the minimum charging current in A, or ``None``."""
        node = self._data.get("minChargingCurrent")
        return float(node["value"]) if node else None

    def safety_range_km(self) -> float | None:
        """Return the safety range buffer in km, or ``None``.

        Not surfaced by the site-scoped v2 API; always returns ``None``
        in v0.2.0+.
        """
        return None

    def assigned_charger_id(self) -> str | None:
        """Return the ID of the physical wallbox assigned to this vehicle, or ``None``."""
        return self._data.get("chargerId")

    def manual_soc_timestamp(self) -> str | None:
        """Return the ISO-8601 timestamp of the last manual SoC update, or ``None``."""
        return self._data.get("manualSocTimestamp")

    def updated_at(self) -> str | None:
        """Return the ISO-8601 timestamp of the last record update, or ``None``.

        Not surfaced by the site-scoped v2 API; always returns ``None``
        in v0.2.0+.
        """
        return None

    def charging_mode(self) -> ChargingMode:
        """Return the currently active :class:`~onekommafive.models.ChargingMode`."""
        return ChargingMode(self._data["chargingMode"])

    def charging_mode_updated_at(self) -> str | None:
        """Return the ISO-8601 timestamp when the charging mode was last changed, or ``None``.

        Not surfaced by the site-scoped v2 API; always returns ``None``
        in v0.2.0+.
        """
        return None

    def default_soc(self) -> float | None:
        """Return the default target SoC as a percentage (0–100), or ``None``."""
        val = self._data.get("defaultSoc")
        return float(val * 100) if val is not None else None

    def target_soc(self) -> float | None:
        """Return the user-selected target SoC as a percentage (0–100), or ``None``."""
        val = self._data.get("targetSoc")
        return float(val * 100) if val is not None else None

    def primary_schedule_days(self) -> list[str]:
        """Return the list of days (e.g. ``['MONDAY', 'FRIDAY']``) in the primary schedule.

        Not surfaced by the site-scoped v2 API; always returns ``[]``
        in v0.2.0+.
        """
        return []

    def primary_schedule_departure_time(self) -> str | None:
        """Return the scheduled departure time as ``'HH:MM'``, or ``None``.

        The site-scoped v2 API has a single departure-time slot per
        vehicle (the ``primary``/``secondary`` distinction is a v1
        anachronism); this reader keeps its historical name.
        """
        return self._data.get("departureTime")

    def primary_schedule_departure_soc(self) -> float | None:
        """Return the departure-time target SoC as a percentage (0–100), or ``None``.

        In the site-scoped v2 API this concept was consolidated with
        ``targetSoc`` (the app uses a single SoC value for scheduled
        departure). Returns the same value as :meth:`target_soc`.
        """
        return self.target_soc()

    def secondary_schedule_departure_time(self) -> str | None:
        """Return the secondary departure time as ``'HH:MM'``, or ``None``.

        Not surfaced by the site-scoped v2 API; always returns ``None``
        in v0.2.0+.
        """
        return None

    def secondary_schedule_departure_soc(self) -> float | None:
        """Return the secondary schedule target departure SoC as a percentage (0–100), or ``None``.

        Not surfaced by the site-scoped v2 API; always returns ``None``
        in v0.2.0+.
        """
        return None

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

    def _url(self) -> str:
        """Return the device endpoint URL for this charger."""
        return (
            f"{self._client.HEARTBEAT_API}"
            f"/api/v2/sites/{self._system.id()}"
            f"/assets/evs/{self.id()}"
        )

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

        self._client._request(
            "PATCH",
            self._url(),
            json={"chargingMode": mode.value},
            error_label="Failed to set charging mode",
        )
        self._data["chargingMode"] = mode.value

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

        self._client._request(
            "PATCH",
            self._url(),
            json={"manualSoc": soc_decimal},
            error_label="Failed to set state of charge",
        )
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
        self._client._request(
            "PATCH",
            self._url(),
            json={"targetSoc": soc_decimal},
            error_label="Failed to set target state of charge",
        )
        self._data["targetSoc"] = soc_decimal

    def set_primary_departure_time(self, time: str) -> None:
        """Set the scheduled departure time.

        No-ops silently when *time* matches the current departure time.
        The method name keeps its ``primary`` prefix for backwards
        compatibility (v1 API had ``primary``/``secondary`` slots; v2
        has a single slot).

        Args:
            time: Departure time as ``'HH:MM'``, e.g. ``'06:00'``.

        Raises:
            RequestError: If the server returns a non-200 response.
        """
        if self.primary_schedule_departure_time() == time:
            return

        self._client._request(
            "PATCH",
            self._url(),
            json={"departureTime": time},
            error_label="Failed to set departure time",
        )
        self._data["departureTime"] = time

    def __repr__(self) -> str:
        return f"EVCharger(id={self.id()!r}, name={self.name()!r}, mode={self.charging_mode().value!r})"
