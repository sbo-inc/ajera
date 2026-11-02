"""
The REST client's list methods, answered from the database.

Each method takes the same arguments as its `AjeraClient` namesake and
returns the same models in the same order, so a caller can move a read from
the API to the database without touching the code that consumes it. The live
suite compares every one against the REST API.
"""

from typing import Any, cast

from ajera.odbc.queries.generic import Query
from ajera.odbc.queries.mirror import MIRRORS, mirror_list
from ajera.schemas.client import ClientType
from ajera.schemas.contact import ContactType
from ajera.schemas.deduction import Deduction
from ajera.schemas.employee import EmployeeType
from ajera.schemas.fringe import Fringe
from ajera.schemas.project import ProjectType
from ajera.schemas.reference import (
    AccountGroup,
    Activity,
    BankAccount,
    Company,
    InvoiceFormat,
    Pay,
    PayrollTax,
    RateTable,
    WageTable,
)
from ajera.schemas.vendor import VendorType

ACTIVE = ["Active"]


# =============================================================================
# CLASS: RestReads
# =============================================================================


class RestReads:
    """REST-shaped list reads, one per mirrored `AjeraClient` method."""

    def _run[T](self, query: Query[T]) -> T:
        raise NotImplementedError

    def _mirror(self, method: str, **arguments: object) -> list[Any]:
        status = arguments.pop("filter_by_status", None)
        query: Query[list[Any]] = mirror_list(
            MIRRORS[method],
            filter_by_status=cast(list[str] | None, status),
            **arguments,
        )
        return self._run(query)

    def list_account_groups(
        self, *, filter_by_status: list[str] | None = ACTIVE
    ) -> list[AccountGroup]:
        """List GL account groups, as `AjeraClient.list_account_groups` does."""
        return self._mirror("list_account_groups", filter_by_status=filter_by_status)

    def list_activities(
        self,
        *,
        filter_by_status: list[str] | None = ACTIVE,
        filter_by_description_like: str | None = None,
    ) -> list[Activity]:
        """List activities, as `AjeraClient.list_activities` does."""
        return self._mirror(
            "list_activities",
            filter_by_status=filter_by_status,
            filter_by_description_like=filter_by_description_like,
        )

    def list_bank_accounts(
        self, *, filter_by_status: list[str] | None = ACTIVE
    ) -> list[BankAccount]:
        """List bank accounts, as `AjeraClient.list_bank_accounts` does."""
        return self._mirror("list_bank_accounts", filter_by_status=filter_by_status)

    def list_client_types(
        self, *, filter_by_status: list[str] | None = ACTIVE
    ) -> list[ClientType]:
        """List client types, as `AjeraClient.list_client_types` does."""
        return self._mirror("list_client_types", filter_by_status=filter_by_status)

    def list_companies(
        self, *, filter_by_status: list[str] | None = ACTIVE
    ) -> list[Company]:
        """List companies, as `AjeraClient.list_companies` does."""
        return self._mirror("list_companies", filter_by_status=filter_by_status)

    def list_contact_types(
        self, *, filter_by_status: list[str] | None = ACTIVE
    ) -> list[ContactType]:
        """List contact types, as `AjeraClient.list_contact_types` does."""
        return self._mirror("list_contact_types", filter_by_status=filter_by_status)

    def list_deductions(
        self, *, filter_by_status: list[str] | None = ACTIVE
    ) -> list[Deduction]:
        """List payroll deductions, as `AjeraClient.list_deductions` does."""
        return self._mirror("list_deductions", filter_by_status=filter_by_status)

    def list_employee_types(
        self, *, filter_by_status: list[str] | None = ACTIVE
    ) -> list[EmployeeType]:
        """List employee types, as `AjeraClient.list_employee_types` does."""
        return self._mirror("list_employee_types", filter_by_status=filter_by_status)

    def list_fringes(
        self, *, filter_by_status: list[str] | None = ACTIVE
    ) -> list[Fringe]:
        """List payroll fringes, as `AjeraClient.list_fringes` does."""
        return self._mirror("list_fringes", filter_by_status=filter_by_status)

    def list_invoice_formats(
        self, *, filter_by_status: list[str] | None = ACTIVE
    ) -> list[InvoiceFormat]:
        """List invoice formats, as `AjeraClient.list_invoice_formats` does."""
        return self._mirror("list_invoice_formats", filter_by_status=filter_by_status)

    def list_payroll_taxes(
        self, *, filter_by_status: list[str] | None = ACTIVE
    ) -> list[PayrollTax]:
        """List payroll taxes, as `AjeraClient.list_payroll_taxes` does."""
        return self._mirror("list_payroll_taxes", filter_by_status=filter_by_status)

    def list_pays(self, *, filter_by_status: list[str] | None = ACTIVE) -> list[Pay]:
        """List pay types, as `AjeraClient.list_pays` does."""
        return self._mirror("list_pays", filter_by_status=filter_by_status)

    def list_project_types(
        self, *, filter_by_status: list[str] | None = ACTIVE
    ) -> list[ProjectType]:
        """List project types, as `AjeraClient.list_project_types` does."""
        return self._mirror("list_project_types", filter_by_status=filter_by_status)

    def list_rate_tables(
        self, *, filter_by_status: list[str] | None = ACTIVE
    ) -> list[RateTable]:
        """List rate tables, as `AjeraClient.list_rate_tables` does."""
        return self._mirror("list_rate_tables", filter_by_status=filter_by_status)

    def list_vendor_types(
        self,
        *,
        filter_by_status: list[str] | None = ACTIVE,
        filter_by_is_credit_card: list[bool] | None = None,
        filter_by_is_consultant: list[bool] | None = None,
    ) -> list[VendorType]:
        """List vendor types, as `AjeraClient.list_vendor_types` does."""
        return self._mirror(
            "list_vendor_types",
            filter_by_status=filter_by_status,
            filter_by_is_credit_card=filter_by_is_credit_card,
            filter_by_is_consultant=filter_by_is_consultant,
        )

    def list_wage_tables(
        self, *, filter_by_status: list[str] | None = ACTIVE
    ) -> list[WageTable]:
        """List wage tables, as `AjeraClient.list_wage_tables` does."""
        return self._mirror("list_wage_tables", filter_by_status=filter_by_status)
