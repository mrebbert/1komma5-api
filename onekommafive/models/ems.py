"""Energy-management system models (``/api/v1/systems/{id}/ems/actions/get-settings``)."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class EmsManualDevice:
    """One device entry in the EMS manual settings.

    The ``type`` field determines which optional fields are populated:

    * ``EV_CHARGER`` — ``id``, ``charger_name``, ``assigned_ev_id``,
      ``assigned_ev_name``, ``active_charging_mode``
    * ``BATTERY`` — ``enable_forecast_charging``
    * ``HEAT_PUMP`` — ``id``, ``use_solar_surplus``,
      ``max_solar_surplus_usage_kw``
    """

    type: str
    """Device type: ``'EV_CHARGER'``, ``'BATTERY'``, or ``'HEAT_PUMP'``."""

    id: str | None
    """Device UUID (EV charger and heat pump only)."""

    charger_name: str | None
    """Human-readable wallbox name (EV charger only)."""

    assigned_ev_id: str | None
    """UUID of the EV assigned to this charger (EV charger only)."""

    assigned_ev_name: str | None
    """Name of the EV assigned to this charger (EV charger only)."""

    active_charging_mode: str | None
    """Active charging mode value (EV charger only)."""

    enable_forecast_charging: bool | None
    """Whether forecast-based charging is enabled (battery only)."""

    use_solar_surplus: bool | None
    """Whether solar surplus is used to power the heat pump (heat pump only)."""

    max_solar_surplus_usage_kw: float | None
    """Maximum solar surplus power used by the heat pump, in kW (heat pump only)."""

    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EmsManualDevice":
        surplus = data.get("maxSolarSurplusUsage")
        return cls(
            type=data.get("type", ""),
            id=data.get("id"),
            charger_name=data.get("chargerName"),
            assigned_ev_id=data.get("assignedEvId"),
            assigned_ev_name=data.get("assignedEvName"),
            active_charging_mode=data.get("activeChargingMode"),
            enable_forecast_charging=data.get("enableForecastCharging"),
            use_solar_surplus=data.get("useSolarSurplus"),
            max_solar_surplus_usage_kw=float(surplus["value"]) if surplus else None,
            raw=data,
        )


@dataclass
class EmsSettings:
    """Energy-management system (EMS) settings for a system."""

    auto_mode: bool
    """Whether the EMS is in automatic optimisation mode (``overrideAutoSettings`` is ``False``)."""

    system_id: str | None
    """UUID of the system these settings belong to."""

    created_at: str | None
    """ISO-8601 timestamp when this settings record was created."""

    updated_at: str | None
    """ISO-8601 timestamp of the last settings update."""

    consent_given: bool
    """Whether the user has given consent for EMS operation."""

    time_of_use_enabled: bool
    """Whether Time-of-Use optimisation is active."""

    manual_devices: list[EmsManualDevice]
    """Ordered list of devices configured in manual override mode."""

    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EmsSettings":
        """Construct an :class:`EmsSettings` from a raw API response dictionary."""
        manual_raw = data.get("manualSettings") or {}
        devices = [
            EmsManualDevice.from_dict(manual_raw[k])
            for k in sorted(manual_raw.keys(), key=lambda x: int(x) if x.isdigit() else x)
        ]
        return cls(
            auto_mode=not data.get("overrideAutoSettings", False),
            system_id=data.get("systemId"),
            created_at=data.get("createdAt"),
            updated_at=data.get("updatedAt"),
            consent_given=bool(data.get("consentGiven", False)),
            time_of_use_enabled=bool(data.get("timeOfUseEnabled", False)),
            manual_devices=devices,
            raw=data,
        )
