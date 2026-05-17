"""System metadata models (``/api/v4/systems/{id}`` and ``/api/v1/systems/{id}/details``)."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SystemInfo:
    """Static metadata for a 1KOMMA5° system (site).

    Populated from the ``GET /api/v4/systems/{id}`` response which is fetched
    once when the system is loaded.  Use :meth:`~onekommafive.System.info` to
    obtain an instance.
    """

    id: str
    """Unique system UUID."""

    name: str | None
    """Human-readable site name (``systemName`` in the API response)."""

    status: str | None
    """Operational status string, e.g. ``"ACTIVE"``."""

    address_line1: str | None
    """Street address, first line."""

    address_line2: str | None
    """Street address, second line (often ``None``)."""

    address_zip_code: str | None
    """Postal / ZIP code."""

    address_city: str | None
    """City name."""

    address_country: str | None
    """ISO 3166-1 alpha-2 country code, e.g. ``"DE"``."""

    address_latitude: float | None
    """Geographic latitude of the site."""

    address_longitude: float | None
    """Geographic longitude of the site."""

    customer_id: str | None
    """Internal customer identifier."""

    dynamic_pulse_compatible: bool
    """Whether the system supports Dynamic Pulse (dynamic tariff optimisation)."""

    energy_trader_active: bool | None
    """Whether the energy trading feature is active for this system (not available in API v4+)."""

    electricity_contract_active: bool | None
    """Whether an electricity contract is active for this system (not available in API v4+)."""

    created_at: str | None
    """ISO 8601 timestamp when the system was created."""

    updated_at: str | None
    """ISO 8601 timestamp of the last system update."""

    raw: dict[str, Any] = field(repr=False)
    """The complete raw API response."""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SystemInfo":
        """Construct a :class:`SystemInfo` from a raw API response dictionary."""
        return cls(
            id=data["id"],
            name=data.get("systemName"),
            status=data.get("status"),
            address_line1=data.get("addressLine1"),
            address_line2=data.get("addressLine2"),
            address_zip_code=data.get("addressZipCode"),
            address_city=data.get("addressCity"),
            address_country=data.get("addressCountry"),
            address_latitude=data.get("addressLatitude"),
            address_longitude=data.get("addressLongitude"),
            customer_id=data.get("customerId"),
            dynamic_pulse_compatible=bool(data.get("dynamicPulseCompatible", False)),
            energy_trader_active=(
                bool(data["energyTraderActive"]) if "energyTraderActive" in data else None
            ),
            electricity_contract_active=(
                bool(data["electricityContractActive"])
                if "electricityContractActive" in data
                else None
            ),
            created_at=data.get("createdAt"),
            updated_at=data.get("updatedAt"),
            raw=data,
        )


@dataclass
class SystemCustomer:
    """Customer contact details embedded in :class:`SystemDetails`.

    Returned as part of ``GET /api/v1/systems/{id}/details``.
    """

    id: str
    """Customer UUID."""

    first_name: str | None
    """Customer's first name."""

    last_name: str | None
    """Customer's last name."""

    email: str | None
    """Customer's email address."""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SystemCustomer":
        """Construct a :class:`SystemCustomer` from a raw API response dictionary."""
        return cls(
            id=data["id"],
            first_name=data.get("firstName"),
            last_name=data.get("lastName"),
            email=data.get("email"),
        )


@dataclass
class DeviceGateway:
    """A device gateway (e.g. GridX box) registered to a system.

    Returned as part of :class:`SystemDetails`.
    """

    id: str
    """Gateway UUID."""

    gridx_start_code: str | None
    """GridX activation / pairing code."""

    serial_number: str | None
    """Hardware serial number of the gateway device."""

    installation_date: str | None
    """ISO-8601 date (``YYYY-MM-DD``) when the gateway was installed."""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DeviceGateway":
        """Construct a :class:`DeviceGateway` from a raw API response dictionary."""
        return cls(
            id=data["id"],
            gridx_start_code=data.get("gridxStartCode"),
            serial_number=data.get("serialNumber"),
            installation_date=data.get("installationDate"),
        )


@dataclass
class SystemDetails:
    """Extended metadata for a 1KOMMA5° system (site).

    Returned by ``GET /api/v1/systems/{id}/details``.  Compared to
    :class:`SystemInfo` (which sources from ``/api/v4/systems/{id}``) this
    endpoint additionally exposes the energy management provider (``emp_type``),
    technical-contact details, customer contact details, third-party smart-meter
    metadata, the earliest available measurement date, and the list of installed
    :class:`DeviceGateway` units (e.g. GridX boxes).
    """

    id: str
    """Unique system UUID."""

    name: str | None
    """Human-readable site name (``systemName`` in the API response)."""

    status: str | None
    """Operational status string, e.g. ``"ACTIVE"``."""

    emp_type: str | None
    """Energy management provider type (e.g. ``"GRIDX"``)."""

    address_name: str | None
    """Optional address label / name (often ``None``)."""

    address_line1: str | None
    """Street address, first line."""

    address_line2: str | None
    """Street address, second line (often ``None``)."""

    address_zip_code: str | None
    """Postal / ZIP code."""

    address_city: str | None
    """City name."""

    address_country: str | None
    """ISO 3166-1 alpha-2 country code, e.g. ``"DE"``."""

    address_longitude: float | None
    """Geographic longitude of the site."""

    address_latitude: float | None
    """Geographic latitude of the site."""

    technical_contact_id: str | None
    """UUID of the technical / installation partner."""

    technical_contact_name: str | None
    """Display name of the technical / installation partner."""

    customer_id: str | None
    """Internal customer identifier."""

    customer: SystemCustomer | None
    """Customer contact details (id, name, email)."""

    dynamic_pulse_compatible: bool
    """Whether the system supports Dynamic Pulse (dynamic tariff optimisation)."""

    energy_trader_active: bool | None
    """Whether the energy trading feature is active for this system."""

    electricity_contract_active: bool | None
    """Whether an electricity contract is active for this system."""

    has_third_party_smart_meter: bool | None
    """Whether a third-party smart meter is registered for this site."""

    third_party_smart_meter_meter_id: str | None
    """Identifier of the third-party smart meter (``None`` if not installed)."""

    third_party_smart_meter_deleted_at: str | None
    """ISO-8601 timestamp when the third-party smart meter was removed."""

    third_party_smart_meter_market_location_id: str | None
    """Market location ID (Marktlokations-ID) of the third-party smart meter."""

    earliest_measurement: str | None
    """ISO-8601 date (``YYYY-MM-DD``) of the earliest available measurement."""

    created_at: str | None
    """ISO 8601 timestamp when the system was created."""

    updated_at: str | None
    """ISO 8601 timestamp of the last system update."""

    device_gateways: list[DeviceGateway]
    """Device gateways (e.g. GridX boxes) installed at the site."""

    raw: dict[str, Any] = field(repr=False)
    """The complete raw API response."""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SystemDetails":
        """Construct a :class:`SystemDetails` from a raw API response dictionary."""
        customer_raw = data.get("customer")
        gateways_raw = data.get("deviceGateways") or []
        return cls(
            id=data["id"],
            name=data.get("systemName"),
            status=data.get("status"),
            emp_type=data.get("empType"),
            address_name=data.get("addressName"),
            address_line1=data.get("addressLine1"),
            address_line2=data.get("addressLine2"),
            address_zip_code=data.get("addressZipCode"),
            address_city=data.get("addressCity"),
            address_country=data.get("addressCountry"),
            address_longitude=data.get("addressLongitude"),
            address_latitude=data.get("addressLatitude"),
            technical_contact_id=data.get("technicalContactId"),
            technical_contact_name=data.get("technicalContactName"),
            customer_id=data.get("customerId"),
            customer=SystemCustomer.from_dict(customer_raw) if customer_raw else None,
            dynamic_pulse_compatible=bool(data.get("dynamicPulseCompatible", False)),
            energy_trader_active=(
                bool(data["energyTraderActive"]) if "energyTraderActive" in data else None
            ),
            electricity_contract_active=(
                bool(data["electricityContractActive"])
                if "electricityContractActive" in data
                else None
            ),
            has_third_party_smart_meter=(
                bool(data["hasThirdPartySmartMeter"])
                if data.get("hasThirdPartySmartMeter") is not None
                else None
            ),
            third_party_smart_meter_meter_id=data.get("thirdPartySmartMeterMeterId"),
            third_party_smart_meter_deleted_at=data.get("thirdPartySmartMeterDeletedAt"),
            third_party_smart_meter_market_location_id=data.get("thirdPartySmartMeterMarketLocationId"),
            earliest_measurement=data.get("earliestMeasurement"),
            created_at=data.get("createdAt"),
            updated_at=data.get("updatedAt"),
            device_gateways=[DeviceGateway.from_dict(g) for g in gateways_raw],
            raw=data,
        )
