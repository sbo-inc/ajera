from typing import Any, Literal, override

from pydantic import Field

from ajera.schemas.generic import (
    GenericBaseModel,
    GenericRequest,
    GenericResponse,
)

# =============================================================================
# CLASS: StatusFilterArguments
# =============================================================================


class StatusFilterArguments(GenericBaseModel):
    """
    Shared filter arguments for the simple, status-only lookup lists
    """

    filter_by_status: list[str] | None = Field(
        default=None,
        alias="FilterByStatus",
        description="Filter by status values (e.g. Active, Inactive).",
    )


# =============================================================================
# CLASS: AccountGroup
# =============================================================================


class AccountGroup(GenericBaseModel):
    """
    General ledger account group, as returned by ListAccountGroups
    """

    account_group_key: int = Field(
        default=0,
        alias="AccountGroupKey",
        description="Unique account group key.",
    )
    description: str = Field(
        default="",
        alias="Description",
        description="Account group description.",
    )
    status: str = Field(
        default="",
        alias="Status",
        description="Status (e.g. Active or Inactive).",
    )
    notes: str = Field(
        default="",
        alias="Notes",
        description="Notes.",
    )


class ListAccountGroups(GenericRequest[StatusFilterArguments]):
    """
    List Account Groups request body
    """

    method: Literal["ListAccountGroups"] = Field(
        default="ListAccountGroups",
        alias="Method",
        description="API method name to invoke.",
        frozen=True,
    )


class ListAccountGroupsResponse(GenericResponse[list[AccountGroup]]):
    """
    Response schema for ListAccountGroups
    """

    @override
    def model_post_init(self, context: Any) -> None:
        if self.content:
            self.content.sort(key=lambda item: item.description)


# =============================================================================
# CLASS: Activity
# =============================================================================


class Activity(GenericBaseModel):
    """
    Activity, as returned by ListActivities
    """

    activity_key: int = Field(
        default=0,
        alias="ActivityKey",
        description="Unique activity key.",
    )
    description: str = Field(
        default="",
        alias="Description",
        description="Activity description.",
    )
    status: str = Field(
        default="",
        alias="Status",
        description="Status (e.g. Active or Inactive).",
    )
    notes: str = Field(
        default="",
        alias="Notes",
        description="Notes.",
    )
    unit_based: bool = Field(
        default=False,
        alias="UnitBased",
        description="Whether the activity is unit based.",
    )
    unit_description: str = Field(
        default="",
        alias="UnitDescription",
        description="Unit description for unit-based activities.",
    )
    unit_cost_rate: float = Field(
        default=0.0,
        alias="UnitCostRate",
        description="Cost rate per unit.",
    )
    icr_expense: bool = Field(
        default=False,
        alias="ICRExpense",
        description="Whether the activity is an indirect cost recovery expense.",
    )


class ListActivitiesArguments(StatusFilterArguments):
    """
    Optional filter arguments for ListActivities
    """

    filter_by_description_like: str | None = Field(
        default=None,
        alias="FilterByDescriptionLike",
        description="Filter where the description contains this substring.",
    )


class ListActivities(GenericRequest[ListActivitiesArguments]):
    """
    List Activities request body
    """

    method: Literal["ListActivities"] = Field(
        default="ListActivities",
        alias="Method",
        description="API method name to invoke.",
        frozen=True,
    )


class ListActivitiesResponse(GenericResponse[list[Activity]]):
    """
    Response schema for ListActivities
    """

    @override
    def model_post_init(self, context: Any) -> None:
        if self.content:
            self.content.sort(key=lambda item: item.description)


# =============================================================================
# CLASS: BankAccount
# =============================================================================


class BankAccount(GenericBaseModel):
    """
    Bank account, as returned by ListBankAccounts
    """

    bank_account_key: int = Field(
        default=0,
        alias="BankAccountKey",
        description="Unique bank account key.",
    )
    description: str = Field(
        default="",
        alias="Description",
        description="Bank account description.",
    )
    status: str = Field(
        default="",
        alias="Status",
        description="Status (e.g. Active or Inactive).",
    )
    notes: str = Field(
        default="",
        alias="Notes",
        description="Notes.",
    )


class ListBankAccounts(GenericRequest[StatusFilterArguments]):
    """
    List Bank Accounts request body
    """

    method: Literal["ListBankAccounts"] = Field(
        default="ListBankAccounts",
        alias="Method",
        description="API method name to invoke.",
        frozen=True,
    )


class ListBankAccountsResponse(GenericResponse[list[BankAccount]]):
    """
    Response schema for ListBankAccounts
    """

    @override
    def model_post_init(self, context: Any) -> None:
        if self.content:
            self.content.sort(key=lambda item: item.description)


# =============================================================================
# CLASS: Company
# =============================================================================


class Company(GenericBaseModel):
    """
    Company, as returned by ListCompanies
    """

    company_key: int = Field(
        default=0,
        alias="CompanyKey",
        description="Unique company key.",
    )
    description: str = Field(
        default="",
        alias="Description",
        description="Company description.",
    )
    status: str = Field(
        default="",
        alias="Status",
        description="Status (e.g. Active or Inactive).",
    )
    notes: str = Field(
        default="",
        alias="Notes",
        description="Notes.",
    )


class ListCompanies(GenericRequest[StatusFilterArguments]):
    """
    List Companies request body
    """

    method: Literal["ListCompanies"] = Field(
        default="ListCompanies",
        alias="Method",
        description="API method name to invoke.",
        frozen=True,
    )


class ListCompaniesResponse(GenericResponse[list[Company]]):
    """
    Response schema for ListCompanies
    """

    @override
    def model_post_init(self, context: Any) -> None:
        if self.content:
            self.content.sort(key=lambda item: item.description)


# =============================================================================
# CLASS: Department
# =============================================================================


class Department(GenericBaseModel):
    """
    Department, as returned by ListDepartments
    """

    department_key: int = Field(
        default=0,
        alias="DepartmentKey",
        description="Unique department key.",
    )
    department: str = Field(
        default="",
        alias="Department",
        description="Department name.",
    )
    status: str = Field(
        default="",
        alias="Status",
        description="Status (e.g. Active or Inactive).",
    )
    notes: str = Field(
        default="",
        alias="Notes",
        description="Notes.",
    )
    dpe_percent: float = Field(
        default=0.0,
        alias="DPEPercent",
        description="Direct personnel expense (DPE) percent.",
    )
    overhead_percent: float = Field(
        default=0.0,
        alias="OverheadPercent",
        description="Overhead percent.",
    )


class ListDepartments(GenericRequest[StatusFilterArguments]):
    """
    List Departments request body
    """

    method: Literal["ListDepartments"] = Field(
        default="ListDepartments",
        alias="Method",
        description="API method name to invoke.",
        frozen=True,
    )


class ListDepartmentsResponse(GenericResponse[list[Department]]):
    """
    Response schema for ListDepartments
    """

    @override
    def model_post_init(self, context: Any) -> None:
        if self.content:
            self.content.sort(key=lambda item: item.department)


# =============================================================================
# CLASS: InvoiceFormat
# =============================================================================


class InvoiceFormat(GenericBaseModel):
    """
    Invoice format, as returned by ListInvoiceFormats
    """

    invoice_format_key: int = Field(
        default=0,
        alias="InvoiceFormatKey",
        description="Unique invoice format key.",
    )
    description: str = Field(
        default="",
        alias="Description",
        description="Invoice format description.",
    )
    status: str = Field(
        default="",
        alias="Status",
        description="Status (e.g. Active or Inactive).",
    )
    notes: str = Field(
        default="",
        alias="Notes",
        description="Notes.",
    )


class ListInvoiceFormats(GenericRequest[StatusFilterArguments]):
    """
    List Invoice Formats request body
    """

    method: Literal["ListInvoiceFormats"] = Field(
        default="ListInvoiceFormats",
        alias="Method",
        description="API method name to invoke.",
        frozen=True,
    )


class ListInvoiceFormatsResponse(GenericResponse[list[InvoiceFormat]]):
    """
    Response schema for ListInvoiceFormats
    """

    @override
    def model_post_init(self, context: Any) -> None:
        if self.content:
            self.content.sort(key=lambda item: item.description)


# =============================================================================
# CLASS: PayrollTax
# =============================================================================


class PayrollTax(GenericBaseModel):
    """
    Payroll tax, as returned by ListPayrollTaxes
    """

    payroll_tax_key: int = Field(
        default=0,
        alias="PayrollTaxKey",
        description="Unique payroll tax key.",
    )
    description: str = Field(
        default="",
        alias="Description",
        description="Payroll tax description.",
    )
    status: str = Field(
        default="",
        alias="Status",
        description="Status (e.g. Active or Inactive).",
    )
    notes: str = Field(
        default="",
        alias="Notes",
        description="Notes.",
    )


class ListPayrollTaxes(GenericRequest[StatusFilterArguments]):
    """
    List Payroll Taxes request body
    """

    method: Literal["ListPayrollTaxes"] = Field(
        default="ListPayrollTaxes",
        alias="Method",
        description="API method name to invoke.",
        frozen=True,
    )


class ListPayrollTaxesResponse(GenericResponse[list[PayrollTax]]):
    """
    Response schema for ListPayrollTaxes
    """

    @override
    def model_post_init(self, context: Any) -> None:
        if self.content:
            self.content.sort(key=lambda item: item.description)


# =============================================================================
# CLASS: Pay
# =============================================================================


class Pay(GenericBaseModel):
    """
    Pay type, as returned by ListPays
    """

    pay_key: int = Field(
        default=0,
        alias="PayKey",
        description="Unique pay key.",
    )
    description: str = Field(
        default="",
        alias="Description",
        description="Pay type description.",
    )
    status: str = Field(
        default="",
        alias="Status",
        description="Status (e.g. Active or Inactive).",
    )
    notes: str = Field(
        default="",
        alias="Notes",
        description="Notes.",
    )


class ListPays(GenericRequest[StatusFilterArguments]):
    """
    List Pays request body
    """

    method: Literal["ListPays"] = Field(
        default="ListPays",
        alias="Method",
        description="API method name to invoke.",
        frozen=True,
    )


class ListPaysResponse(GenericResponse[list[Pay]]):
    """
    Response schema for ListPays
    """

    @override
    def model_post_init(self, context: Any) -> None:
        if self.content:
            self.content.sort(key=lambda item: item.description)


# =============================================================================
# CLASS: RateTable
# =============================================================================


class RateTable(GenericBaseModel):
    """
    Rate table, as returned by ListRateTables
    """

    rate_table_key: int = Field(
        default=0,
        alias="RateTableKey",
        description="Unique rate table key.",
    )
    description: str = Field(
        default="",
        alias="Description",
        description="Rate table description.",
    )
    status: str = Field(
        default="",
        alias="Status",
        description="Status (e.g. Active or Inactive).",
    )
    notes: str = Field(
        default="",
        alias="Notes",
        description="Notes.",
    )


class ListRateTables(GenericRequest[StatusFilterArguments]):
    """
    List Rate Tables request body
    """

    method: Literal["ListRateTables"] = Field(
        default="ListRateTables",
        alias="Method",
        description="API method name to invoke.",
        frozen=True,
    )


class ListRateTablesResponse(GenericResponse[list[RateTable]]):
    """
    Response schema for ListRateTables
    """

    @override
    def model_post_init(self, context: Any) -> None:
        if self.content:
            self.content.sort(key=lambda item: item.description)


# =============================================================================
# CLASS: WageTable
# =============================================================================


class WageTable(GenericBaseModel):
    """
    Wage table, as returned by ListWageTables
    """

    wage_table_key: int = Field(
        default=0,
        alias="WageTableKey",
        description="Unique wage table key.",
    )
    description: str = Field(
        default="",
        alias="Description",
        description="Wage table description.",
    )
    status: str = Field(
        default="",
        alias="Status",
        description="Status (e.g. Active or Inactive).",
    )
    notes: str = Field(
        default="",
        alias="Notes",
        description="Notes.",
    )


class ListWageTables(GenericRequest[StatusFilterArguments]):
    """
    List Wage Tables request body
    """

    method: Literal["ListWageTables"] = Field(
        default="ListWageTables",
        alias="Method",
        description="API method name to invoke.",
        frozen=True,
    )


class ListWageTablesResponse(GenericResponse[list[WageTable]]):
    """
    Response schema for ListWageTables
    """

    @override
    def model_post_init(self, context: Any) -> None:
        if self.content:
            self.content.sort(key=lambda item: item.description)


# =============================================================================
# CLASS: ChargeablePhase
# =============================================================================


class ChargeablePhase(GenericBaseModel):
    """
    A phase of a project that can be charged to, from ListChargeablePhases
    """

    key: int = Field(
        default=0,
        alias="Key",
        description="Phase key.",
    )
    description: str = Field(
        default="",
        alias="Description",
        description="Phase description.",
    )
    level: int = Field(
        default=0,
        alias="Level",
        description="Depth level within the work breakdown structure.",
    )
    enabled: bool = Field(
        default=False,
        alias="Enabled",
        description="Whether the phase can currently be charged to.",
    )
    wbs: str = Field(
        default="",
        alias="WBS",
        description="Work breakdown structure label.",
    )
    require_notes: bool = Field(
        default=False,
        alias="RequireNotes",
        description="Whether notes are required when charging to this phase.",
    )


# =============================================================================
# CLASS: ListChargeablePhasesArguments
# =============================================================================


class ListChargeablePhasesArguments(GenericBaseModel):
    """
    Arguments for ListChargeablePhases
    """

    project_key: int = Field(
        alias="ProjectKey",
        description="The project whose chargeable phases to list.",
    )


class ListChargeablePhases(GenericRequest[ListChargeablePhasesArguments]):
    """
    List Chargeable Phases request body
    """

    method: Literal["ListChargeablePhases"] = Field(
        default="ListChargeablePhases",
        alias="Method",
        description="API method name to invoke.",
        frozen=True,
    )


class ListChargeablePhasesResponse(GenericResponse[list[ChargeablePhase]]):
    """
    Response schema for ListChargeablePhases
    """
