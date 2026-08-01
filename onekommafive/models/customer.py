"""Full customer record (``/api/v3/customers/{id}``)."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Customer:
    """Full customer profile as returned by ``GET /api/v3/customers/{id}``.

    Sits on the ``customer-identity`` host and returns a superset of the
    embedded :class:`~onekommafive.SystemCustomer` (which only carries
    ``id``, ``firstName``, ``lastName``, ``email``).

    Retrieved via :meth:`~onekommafive.System.get_customer`.
    """

    id: str
    """Customer UUID."""

    first_name: str | None
    last_name: str | None
    contact_email: str | None
    """API field: ``contactEmail`` (v3 uses this name; the embedded customer uses plain ``email``)."""

    contact_phone: str | None
    company_name: str | None
    company_tax_id: str | None

    address_name: str | None
    address_line1: str | None
    address_line2: str | None
    address_zip_code: str | None
    address_city: str | None
    address_country: str | None

    customer_type: str | None
    """Customer classification, e.g. ``"UNKNOWN"``, ``"PRIVATE"``, ``"BUSINESS"``."""

    title: str | None
    crm_contact_id: str | None
    crm_branch_location: str | None
    """Assigned 1KOMMA5° branch, e.g. ``"1KOMMA5° Moers"``."""

    created_at: str | None
    updated_at: str | None

    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Customer":
        return cls(
            id=data["id"],
            first_name=data.get("firstName"),
            last_name=data.get("lastName"),
            contact_email=data.get("contactEmail"),
            contact_phone=data.get("contactPhone"),
            company_name=data.get("companyName"),
            company_tax_id=data.get("companyTaxId"),
            address_name=data.get("addressName"),
            address_line1=data.get("addressLine1"),
            address_line2=data.get("addressLine2"),
            address_zip_code=data.get("addressZipCode"),
            address_city=data.get("addressCity"),
            address_country=data.get("addressCountry"),
            customer_type=data.get("customerType"),
            title=data.get("title"),
            crm_contact_id=data.get("crmContactId"),
            crm_branch_location=data.get("crmBranchLocation"),
            created_at=data.get("createdAt"),
            updated_at=data.get("updatedAt"),
            raw=data,
        )
