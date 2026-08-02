"""Site status and asset inventory models (``/api/v2/sites/{id}/status-and-assets``)."""

from dataclasses import dataclass, field
from typing import Any

from .system import SystemCustomer


@dataclass
class Asset:
    """One hardware asset (inverter, heat pump, meter, EV charger, …) at a site.

    Returned as part of :class:`SiteStatus` by
    :meth:`~onekommafive.System.get_status_and_assets`.

    The ``connection_status`` and ``network_address`` fields are flattened from
    the nested ``connectionStatus.status`` / ``network.address`` objects in the
    raw response.
    """

    id: str
    """Asset UUID."""

    type: str
    """Asset type, e.g. ``"HYBRID"``, ``"HEAT_PUMP"``, ``"METER"``, ``"EV_CHARGER"``."""

    emp_type: str | None
    """Energy management provider type, e.g. ``"GRIDX"``."""

    name: str | None
    """Human-readable display name (typically only set for EV chargers / wallboxes)."""

    connection_status: str | None
    """Flattened from ``connectionStatus.status`` — e.g. ``"CONNECTED"``."""

    manufacturer: str | None
    """Hardware manufacturer, e.g. ``"Sungrow"``."""

    model: str | None
    """Hardware model identifier, e.g. ``"SH6.0RT-V112"``."""

    serial_number: str | None
    """Hardware serial number (API field: ``serialnumber``, lowercase ``n``)."""

    firmware: str | None
    """Firmware version string (often ``None`` for meters)."""

    network_address: str | None
    """Flattened from ``network.address`` — usually a local IPv4 address."""

    heat_pump_meter_type: str | None
    """Heat-pump meter classification, e.g. ``"HOUSEHOLD"`` (only on ``HEAT_PUMP`` assets)."""

    raw: dict[str, Any] = field(repr=False)
    """The complete raw API asset dictionary."""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Asset":
        """Construct an :class:`Asset` from a raw API asset dictionary."""
        return cls(
            id=data["id"],
            type=data.get("type", ""),
            emp_type=data.get("empType"),
            name=data.get("name"),
            connection_status=(data.get("connectionStatus") or {}).get("status"),
            manufacturer=data.get("manufacturer"),
            model=data.get("model"),
            serial_number=data.get("serialnumber"),
            firmware=data.get("firmware"),
            network_address=(data.get("network") or {}).get("address"),
            heat_pump_meter_type=data.get("heatPumpMeterType"),
            raw=data,
        )


@dataclass
class SmartMeter:
    """Smart-meter registration details for a site.

    Returned by :meth:`~onekommafive.System.get_smart_meter`
    (``GET /api/v1/sites/{id}/smart-meter``).

    The API exposes ``dsoBdewCode`` and ``concessionFeeEURperkWh`` as
    arrays of historic entries with ``validFromDate``/``validUntilDate``.
    This wrapper flattens each to its **first** entry (typically the most
    recent). For historic values inspect :attr:`raw`.
    """

    site_id: str | None
    """Site UUID as returned by the endpoint (redundant to the caller)."""

    control_area_eic: str | None
    """ENTSO-E control-area EIC code, e.g. ``"10YDE-RWENET---I"``."""

    dso_bdew_code: str | None
    """Distribution System Operator's BDEW code (13-digit), latest entry."""

    concession_fee_eur_per_kwh: float | None
    """Municipality concession fee in EUR/kWh, latest entry."""

    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SmartMeter":
        def _first(nodes: Any, key: str) -> Any:
            if isinstance(nodes, list) and nodes:
                return nodes[0].get(key)
            return None

        fee = _first(data.get("concessionFeeEURperkWh"), "value")
        return cls(
            site_id=data.get("siteId"),
            control_area_eic=data.get("controlAreaEIC"),
            dso_bdew_code=_first(data.get("dsoBdewCode"), "reference"),
            concession_fee_eur_per_kwh=float(fee) if fee is not None else None,
            raw=data,
        )


@dataclass
class SiteDetails:
    """Extended site metadata — a superset of :class:`~onekommafive.SystemInfo`.

    Returned by :meth:`~onekommafive.System.get_site_details`
    (``GET /api/v2/sites/{id}/details``). Adds bidding-zone, EMP-connection
    details, and — most useful — the current EMS runtime state
    (``ems_mode``, ``ems_state``, ``ems_state_reasons``) that
    :class:`~onekommafive.SystemInfo`/:class:`~onekommafive.SystemDetails`
    do not expose.

    ``deviceGateways`` is not in this response — use
    :meth:`~onekommafive.System.get_details` for those.
    """

    id: str
    """Site UUID."""

    name: str | None
    """Site display name (API field: ``siteName``)."""

    status: str | None
    """Site status, e.g. ``"ACTIVE"``."""

    emp_type: str | None
    """Energy-management provider, typically ``"GRIDX"``."""

    bidding_zone: str | None
    """ENTSO-E bidding zone code, e.g. ``"DE_LU"``."""

    bidding_zone_eic: str | None
    """ENTSO-E identifier of the bidding zone, e.g. ``"10Y1001A1001A82H"``."""

    ems_mode: str | None
    """Current EMS operating mode, e.g. ``"TOU"`` (time-of-use)."""

    ems_state: str | None
    """Current EMS runtime state, e.g. ``"OPERATIONAL"``."""

    ems_state_reasons: list[str]
    """Machine-readable reason codes explaining the current EMS state (may be empty)."""

    dynamic_pulse_compatible: bool
    """True when the site is compatible with the Dynamic Pulse tariff."""

    address_line1: str | None
    address_line2: str | None
    address_zip_code: str | None
    address_city: str | None
    address_country: str | None
    address_latitude: float | None
    address_longitude: float | None

    customer_id: str | None
    """UUID of the owning customer (matches :attr:`SystemDetails.customer_id`)."""

    customer: SystemCustomer | None
    """Embedded customer contact block (id/firstName/lastName/email). ``None`` when the
    API omits the block. For the full customer profile, use
    :meth:`~onekommafive.System.get_customer`."""

    technical_contact_id: str | None
    technical_contact_name: str | None

    earliest_measurement: str | None
    """ISO-8601 date (``YYYY-MM-DD``) of the earliest available measurement.
    Matches :attr:`SystemDetails.earliest_measurement`."""

    energy_trader_active: bool | None
    """Whether Energy Trader is active for this site. ``None`` when the API omits
    the flag entirely (matches :attr:`SystemDetails.energy_trader_active`)."""

    electricity_contract_active: bool | None
    """Whether the electricity contract is active. ``None`` when the API omits
    the flag entirely (matches :attr:`SystemDetails.electricity_contract_active`)."""

    impacted_by_enwg: bool | None
    """German regulatory flag related to the Energiewirtschaftsgesetz (EnWG).
    ``None`` when the field is absent.

    **Semantic caveat**: the exact meaning is not documented by the API.
    Most plausible interpretation is ``§14a EnWG``, which since 2024-01-01
    lets DSOs remotely reduce controllable consumption devices (heat pump /
    wallbox / battery storage / AC ≥ 4.2 kW) during grid stress, in exchange
    for reduced grid fees. A ``true`` value would presumably mean the site
    has at least one such device registered under §14a. Other EnWG paragraphs
    (§17c smart meters, §41d dynamic tariffs) are less likely because the
    client already exposes dedicated flags for those (``hasThirdPartySmartMeter``,
    ``dynamicPulseCompatible``)."""

    emp_reference_id: str | None
    """Additional Energy-Management-Provider reference identifier (opaque)."""

    grid_connection_point_phases: int | None
    """Number of phases of the grid connection (typically ``3`` for a
    standard German household). ``None`` when the API returns null."""

    max_current_per_phase_ampere: float | None
    """Maximum current per phase in **amperes** (typical residential values:
    ``32``, ``63``, ``80``). ``None`` when the API returns null."""

    created_at: str | None
    updated_at: str | None

    emp_details: dict[str, Any] | None
    """Raw EMP connection block (contains gateway serial number, GridX start code,
    installation date — sensitive pairing data, hence kept as a dict)."""

    physical_attributes: dict[str, Any] | None
    """Site-level physical attributes as delivered by the API."""

    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SiteDetails":
        customer_data = data.get("customer")
        return cls(
            id=data["id"],
            name=data.get("siteName"),
            status=data.get("status"),
            emp_type=data.get("empType"),
            bidding_zone=data.get("biddingZone"),
            bidding_zone_eic=data.get("biddingZoneEic"),
            ems_mode=data.get("emsMode"),
            ems_state=data.get("emsState"),
            ems_state_reasons=list(data.get("emsStateReasons") or []),
            dynamic_pulse_compatible=bool(data.get("dynamicPulseCompatible")),
            address_line1=data.get("addressLine1"),
            address_line2=data.get("addressLine2"),
            address_zip_code=data.get("addressZipCode"),
            address_city=data.get("addressCity"),
            address_country=data.get("addressCountry"),
            address_latitude=data.get("addressLatitude"),
            address_longitude=data.get("addressLongitude"),
            customer_id=data.get("customerId"),
            customer=SystemCustomer.from_dict(customer_data) if customer_data else None,
            technical_contact_id=data.get("technicalContactId"),
            technical_contact_name=data.get("technicalContactName"),
            earliest_measurement=data.get("earliestMeasurement"),
            energy_trader_active=(
                bool(data["energyTraderActive"]) if "energyTraderActive" in data else None
            ),
            electricity_contract_active=(
                bool(data["electricityContractActive"])
                if "electricityContractActive" in data
                else None
            ),
            impacted_by_enwg=(
                bool(data["impactedByEnwg"]) if "impactedByEnwg" in data else None
            ),
            emp_reference_id=data.get("empReferenceId"),
            grid_connection_point_phases=data.get("gridConnectionPointPhases"),
            max_current_per_phase_ampere=data.get("maxCurrentPerPhaseAmpere"),
            created_at=data.get("createdAt"),
            updated_at=data.get("updatedAt"),
            emp_details=data.get("empDetails"),
            physical_attributes=data.get("physicalAttributes"),
            raw=data,
        )


@dataclass
class SiteStatus:
    """Overall connection status and asset inventory for a site.

    Returned by :meth:`~onekommafive.System.get_status_and_assets`
    (``GET /api/v2/sites/{id}/status-and-assets``).
    """

    status: str | None
    """Overall site connection status, e.g. ``"CONNECTED"``."""

    assets: list[Asset]
    """All hardware assets installed at the site (inverter, meter, heat pump, EV charger, …)."""

    raw: dict[str, Any] = field(repr=False)
    """The complete raw API response."""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SiteStatus":
        """Construct a :class:`SiteStatus` from a raw API response dictionary."""
        return cls(
            status=data.get("status"),
            assets=[Asset.from_dict(a) for a in data.get("assets") or []],
            raw=data,
        )
