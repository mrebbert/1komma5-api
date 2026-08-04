"""Customer subscription / contract models (``/api/v1/customers/{cid}/subscriptions``)."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Subscription:
    """One customer contract — a subscription to a 1KOMMA5° service.

    Returned as part of :class:`SubscriptionsList` by
    :meth:`~onekommafive.System.get_subscriptions`.

    **Scope note**: this wrapper maps only the universal contract
    metadata that's useful for dashboards and monitoring (type, status,
    price, dates, notice period, terms link) plus a small set of
    non-PII DYNAMIC_PULSE contract-identity fields.

    The raw response also carries the payment IBAN, delivery / billing
    addresses, CRM identifiers (Zoho / Lumenaza), an embedded
    ``metadata.payload`` block with the full Zoho booking record, and a
    ``statusHistory`` list — **all sensitive PII**. Those fields are
    deliberately not mapped to attributes and stay accessible via
    :attr:`raw` for callers who genuinely need them.

    Observed subscription types (extensible):

    - ``DYNAMIC_PULSE`` — electricity contract (variable price)
    - ``SMART_METER`` — metering-service contract (24-month notice period)
    - ``HEARTBEAT`` — platform-access contract (0 EUR)
    - ``ENERGY_TRADER`` — trading service (typ. 14.99 EUR / month)
    """

    id: str
    """Subscription UUID."""

    type: str
    """Contract type, see class docstring for observed values."""

    status: str
    """Contract status, e.g. ``"ACTIVE"``."""

    site_id: str | None
    """UUID of the site this contract applies to."""

    customer_id: str | None
    """UUID of the owning customer."""

    price_eur: float | None
    """Monthly price in EUR. ``0`` for platform contracts, ``None`` for
    SMART_METER (billed differently)."""

    currency: str | None
    """Currency code — ``"EURO"`` observed."""

    billing_frequency: str | None
    """Billing frequency, e.g. ``"MONTHLY"``."""

    start_date: str | None
    """Contract start (ISO-8601 or ``None`` for SMART_METER)."""

    end_date: str | None
    """Contract end (``None`` when open-ended)."""

    signed_date: str | None
    """Signature date (ISO-8601)."""

    created_at: str | None
    updated_at: str | None

    notice_period_interval: str | None
    """Notice-period unit, e.g. ``"MONTHS"``."""

    notice_period_number: int | None
    """Notice-period value (e.g. ``1`` or ``24``)."""

    renewal: str | None
    """Renewal mode, e.g. ``"AUTOMATIC"`` / ``"MANUAL"``."""

    payment_method: str | None
    """Payment method enum, e.g. ``"DIRECT_DEBIT"`` / ``"NO_PAYMENT"``.
    **Only the method enum is mapped — the actual IBAN and payment
    contact are kept in :attr:`raw` (PII).**"""

    country_code: str | None
    """ISO country code, e.g. ``"DE"``."""

    # DYNAMIC_PULSE-only contract-identity fields
    electricity_contract_number: str | None
    """Electricity contract number (DYNAMIC_PULSE only)."""

    market_location_id: str | None
    """German market location ID (MaLo) — DYNAMIC_PULSE only."""

    price_guarantee_value: float | None
    """Guaranteed price value (DYNAMIC_PULSE only)."""

    price_guarantee_unit: str | None
    """Unit for the guaranteed price, e.g. ``"ct/kWh"``."""

    price_guarantee_version: str | None
    """Guarantee scheme identifier, e.g. ``"DE_PRICE_GUARANTEE_V2"``."""

    terms_and_conditions_url: str | None
    """User-facing terms-and-conditions URL for this contract."""

    raw: dict[str, Any] = field(repr=False)
    """The full raw contract record, including all PII-heavy fields
    (paymentIban, addresses, CRM IDs, metadata.payload, statusHistory)."""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Subscription":
        return cls(
            id=data["id"],
            type=data.get("type", ""),
            status=data.get("status", ""),
            site_id=data.get("siteId"),
            customer_id=data.get("customerId"),
            price_eur=data.get("price"),
            currency=data.get("currency"),
            billing_frequency=data.get("billingFrequency"),
            start_date=data.get("startDate"),
            end_date=data.get("endDate"),
            signed_date=data.get("signedDate"),
            created_at=data.get("createdAt"),
            updated_at=data.get("updatedAt"),
            notice_period_interval=data.get("noticePeriodInterval"),
            notice_period_number=data.get("noticePeriodNumber"),
            renewal=data.get("renewal"),
            payment_method=data.get("paymentMethod"),
            country_code=data.get("countryCode"),
            electricity_contract_number=data.get("electricityContractNumber"),
            market_location_id=data.get("marketLocationId"),
            price_guarantee_value=data.get("priceGuaranteeValue"),
            price_guarantee_unit=data.get("priceGuaranteeUnit"),
            price_guarantee_version=data.get("priceGuaranteeVersion"),
            terms_and_conditions_url=data.get("termsAndConditionsLink"),
            raw=data,
        )


@dataclass
class SubscriptionsList:
    """All customer subscriptions with pagination metadata.

    Returned by :meth:`~onekommafive.System.get_subscriptions`
    (``GET /api/v1/customers/{cid}/subscriptions`` on the
    ``customer-identity`` host).
    """

    subscriptions: list[Subscription]
    """Individual contracts (usually one per service type)."""

    total_items: int
    page_index: int
    page_size: int
    total_pages: int

    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SubscriptionsList":
        return cls(
            subscriptions=[Subscription.from_dict(s) for s in data.get("data") or []],
            total_items=int(data.get("totalItems", 0)),
            page_index=int(data.get("pageIndex", 0)),
            page_size=int(data.get("pageSize", 0)),
            total_pages=int(data.get("totalPages", 0)),
            raw=data,
        )
