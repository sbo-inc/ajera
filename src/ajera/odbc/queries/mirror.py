"""
REST-shaped reads: the REST client's list methods, served from the database.

Each `Mirror` names the table behind one REST list method and maps every
property of the REST model to the column holding it, so the rows validate
into the same model through the same response class (and so sort the same
way). The live suite proves each one against the REST API on a real tenant.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from typing import Any

from pydantic import BaseModel

from ajera.odbc.queries.generic import CodeMap, Query, Record, placeholders
from ajera.odbc.queries.select import quote_name
from ajera.schemas.client import ListClientTypesResponse
from ajera.schemas.contact import ListContactTypesResponse
from ajera.schemas.deduction import ListDeductionsResponse
from ajera.schemas.employee import ListEmployeeTypesResponse
from ajera.schemas.fringe import ListFringesResponse
from ajera.schemas.generic import GenericResponse
from ajera.schemas.project import ListProjectTypesResponse
from ajera.schemas.reference import (
    ListAccountGroupsResponse,
    ListActivitiesResponse,
    ListBankAccountsResponse,
    ListCompaniesResponse,
    ListInvoiceFormatsResponse,
    ListPayrollTaxesResponse,
    ListPaysResponse,
    ListRateTablesResponse,
    ListWageTablesResponse,
)
from ajera.schemas.vendor import ListVendorTypesResponse

# The convention most status columns document ("0 = Inactive; 1 = Active").
ACTIVE_STATUS = {0: "Inactive", 1: "Active"}


# =============================================================================
# CLASS: Mirror
# =============================================================================


@dataclass(frozen=True)
class Mirror:
    """
    How one REST list method maps onto the database.

    Attributes:
        table: The table read.
        columns: REST property (alias) to the SQL expression producing it,
            usually a bare column name.
        response: The REST response class, whose `model_post_init` gives the
            rows the REST ordering.
        status: The code map for the `Status` property, if it has one.
        condition: A fixed predicate selecting the rows the method covers
            (clients among the shared party table, say).
        filters: REST filter keyword to the column it matches with `=` / `IN`.
        likes: REST `..._like` filter keyword to the column it matches.
        richer: Fields the REST list method leaves at their default (it
            reports 0 for every row) but the database fills with the real
            value. The database value is returned; the live suite compares
            everything else, and checks REST really does leave these empty.
    """

    table: str
    columns: Mapping[str, str]
    response: type[GenericResponse[Any]]
    status: Mapping[int, str] | None = None
    condition: str = ""
    filters: Mapping[str, str] = field(default_factory=dict)
    likes: Mapping[str, str] = field(default_factory=dict)
    richer: frozenset[str] = frozenset()


def _expression(column: str) -> str:
    return quote_name(column) if column.isidentifier() else column


# =============================================================================
# QUERY: mirror_list
# =============================================================================


def mirror_list[M: BaseModel](
    mirror: Mirror,
    *,
    filter_by_status: Sequence[str] | None,
    **filters: object,
) -> Query[list[M]]:
    """
    Build the read behind one REST list method.

    REST `filter_by_*` arguments arrive as keywords and are applied when not
    None: a list matches any of its values, a `..._like` filter matches as
    SQL `LIKE` with the REST API's contains semantics.

    Returns:
        Query[list[M]]: The read, validated through the REST response class.
    """
    codes = CodeMap(f"{mirror.table} status", mirror.status) if mirror.status else None
    select_list = ", ".join(
        f"{_expression(column)} AS {quote_name(alias)}"
        for alias, column in mirror.columns.items()
    )
    predicates = [mirror.condition] if mirror.condition else []
    parameters: list[object] = []

    if filter_by_status and codes is not None:
        wanted = codes.encode(list(filter_by_status))
        predicates.append(
            f"{_expression(mirror.columns['Status'])} IN ({placeholders(len(wanted))})"
        )
        parameters.extend(wanted)

    for name, value in filters.items():
        if value is None:
            continue
        if name in mirror.likes:
            predicates.append(f"{_expression(mirror.likes[name])} LIKE ?")
            parameters.append(f"%{value}%")
        elif name in mirror.filters:
            values = list(value) if isinstance(value, (list, tuple, set)) else [value]
            if not values:
                continue
            predicates.append(
                f"{_expression(mirror.filters[name])} IN ({placeholders(len(values))})"
            )
            parameters.extend(values)
        else:
            raise TypeError(f"{mirror.table} has no REST filter {name!r}")

    statement = f"SELECT {select_list} FROM [dbo].{quote_name(mirror.table)}"
    if predicates:
        statement += " WHERE " + " AND ".join(f"({p})" for p in predicates)

    def parse(records: list[Record]) -> list[M]:
        if codes is not None:
            for record in records:
                if "Status" in record:
                    record["Status"] = codes.decode(record["Status"])
        content: list[M] = mirror.response.model_validate({"Content": records}).content
        return content

    return Query(statement=statement, parse=parse, parameters=tuple(parameters))


# =============================================================================
# SPECS
# =============================================================================


def _reference(
    table: str,
    prefix: str,
    key: str,
    response: type[GenericResponse[Any]],
    **extra: str,
) -> Mirror:
    """The common shape: key, description, status, notes, plus any extras."""
    return Mirror(
        table=table,
        columns={
            key: f"{prefix}Key",
            "Description": f"{prefix}Description",
            "Status": f"{prefix}Status",
            "Notes": f"{prefix}Notes",
            **extra,
        },
        response=response,
        status=ACTIVE_STATUS,
    )


MIRRORS: dict[str, Mirror] = {
    "list_account_groups": _reference(
        "AxGLAccountGroup", "ag", "AccountGroupKey", ListAccountGroupsResponse
    ),
    # REST's Description is the bank's name; baDescription is usually blank.
    "list_bank_accounts": Mirror(
        table="AxBankAccount",
        columns={
            "BankAccountKey": "baKey",
            "Description": "baBankName",
            "Status": "baStatus",
            "Notes": "baNotes",
        },
        response=ListBankAccountsResponse,
        status=ACTIVE_STATUS,
    ),
    "list_client_types": _reference(
        "AxClientType", "ct", "ClientTypeKey", ListClientTypesResponse
    ),
    "list_companies": _reference(
        "AxCompany", "cmp", "CompanyKey", ListCompaniesResponse
    ),
    "list_contact_types": _reference(
        "AxContactType", "cntt", "ContactTypeKey", ListContactTypesResponse
    ),
    "list_deductions": _reference(
        "AxDeduction", "ded", "DeductionKey", ListDeductionsResponse
    ),
    "list_fringes": _reference("AxFringe", "frn", "FringeKey", ListFringesResponse),
    "list_invoice_formats": _reference(
        "AxInvoiceFormat", "if", "InvoiceFormatKey", ListInvoiceFormatsResponse
    ),
    "list_payroll_taxes": _reference(
        "AxTax", "tax", "PayrollTaxKey", ListPayrollTaxesResponse
    ),
    "list_pays": _reference("AxPay", "pay", "PayKey", ListPaysResponse),
    "list_project_types": _reference(
        "AxProjectType", "pt", "ProjectTypeKey", ListProjectTypesResponse
    ),
    "list_rate_tables": _reference(
        "AxRateTable", "rt", "RateTableKey", ListRateTablesResponse
    ),
    "list_vendor_types": Mirror(
        table="AxVendorType",
        columns={
            "VendorTypeKey": "vtKey",
            "Description": "vtDescription",
            "Status": "vtStatus",
            "Notes": "vtNotes",
        },
        response=ListVendorTypesResponse,
        status=ACTIVE_STATUS,
        filters={
            "filter_by_is_credit_card": "vtCreditCard",
            "filter_by_is_consultant": "vtIsConsultant",
        },
    ),
    "list_wage_tables": _reference(
        "AxWageTable", "wt", "WageTableKey", ListWageTablesResponse
    ),
    # ListEmployeeTypes reports 0 for the percent and budget rates on every
    # row; the table holds the real values, which this returns instead.
    "list_employee_types": replace(
        _reference(
            "AxEmployeeType",
            "et",
            "EmployeeTypeKey",
            ListEmployeeTypesResponse,
            BillablePercent="etBillablePercent",
            BudgetCostRate="etBudgetCostRate",
            BudgetBillRate="etBudgetBillRate",
        ),
        richer=frozenset({"billable_percent", "budget_cost_rate", "budget_bill_rate"}),
    ),
    "list_activities": Mirror(
        table="AxActivity",
        columns={
            "ActivityKey": "actKey",
            "Description": "actDescription",
            "Status": "actStatus",
            "Notes": "actNotes",
            "UnitBased": "actUnitBased",
            "UnitDescription": "actUnitDescription",
            "UnitCostRate": "actUnitCostRate",
            "ICRExpense": "actICRExpense",
        },
        response=ListActivitiesResponse,
        status=ACTIVE_STATUS,
        likes={"filter_by_description_like": "actDescription"},
    ),
}
