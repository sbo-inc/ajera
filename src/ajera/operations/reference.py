from ajera.operations.generic import Operation, flatten
from ajera.schemas.reference import (
    Activity,
    BankAccount,
    ChargeablePhase,
    Company,
    Department,
    InvoiceFormat,
    ListActivities,
    ListActivitiesArguments,
    ListActivitiesResponse,
    ListBankAccounts,
    ListBankAccountsResponse,
    ListChargeablePhases,
    ListChargeablePhasesArguments,
    ListChargeablePhasesResponse,
    ListCompanies,
    ListCompaniesResponse,
    ListDepartments,
    ListDepartmentsResponse,
    ListInvoiceFormats,
    ListInvoiceFormatsResponse,
    ListPayrollTaxes,
    ListPayrollTaxesResponse,
    ListPays,
    ListPaysResponse,
    ListRateTables,
    ListRateTablesResponse,
    ListWageTables,
    ListWageTablesResponse,
    Pay,
    PayrollTax,
    RateTable,
    StatusFilterArguments,
    WageTable,
)

# -----------------------------------------------------------------------------
# OPERATION: list_activities
# -----------------------------------------------------------------------------


def list_activities(
    *,
    filter_by_status: list[str] | None = ["Active"],
    filter_by_description_like: str | None = None,
) -> Operation[list[Activity]]:
    """
    Build the ListActivities operation.

    Returns:
        Operation[list[Activity]]: The list activities operation.
    """
    request = ListActivities()
    request.method_arguments = ListActivitiesArguments(
        filter_by_status=filter_by_status,
        filter_by_description_like=filter_by_description_like,
    )

    return Operation(
        request=request,
        api_version=1,
        parse=flatten("Activities", ListActivitiesResponse),
    )


# -----------------------------------------------------------------------------
# OPERATION: list_bank_accounts
# -----------------------------------------------------------------------------


def list_bank_accounts(
    *,
    filter_by_status: list[str] | None = ["Active"],
) -> Operation[list[BankAccount]]:
    """
    Build the ListBankAccounts operation.

    Returns:
        Operation[list[BankAccount]]: The list bank accounts operation.
    """
    request = ListBankAccounts()
    request.method_arguments = StatusFilterArguments(filter_by_status=filter_by_status)

    return Operation(
        request=request,
        api_version=1,
        parse=flatten("BankAccounts", ListBankAccountsResponse),
    )


# -----------------------------------------------------------------------------
# OPERATION: list_companies
# -----------------------------------------------------------------------------


def list_companies(
    *,
    filter_by_status: list[str] | None = ["Active"],
) -> Operation[list[Company]]:
    """
    Build the ListCompanies operation.

    Returns:
        Operation[list[Company]]: The list companies operation.
    """
    request = ListCompanies()
    request.method_arguments = StatusFilterArguments(filter_by_status=filter_by_status)

    return Operation(
        request=request,
        api_version=1,
        parse=flatten("Companies", ListCompaniesResponse),
    )


# -----------------------------------------------------------------------------
# OPERATION: list_departments
# -----------------------------------------------------------------------------


def list_departments(
    *,
    filter_by_status: list[str] | None = ["Active"],
) -> Operation[list[Department]]:
    """
    Build the ListDepartments operation.

    Returns:
        Operation[list[Department]]: The list departments operation.
    """
    request = ListDepartments()
    request.method_arguments = StatusFilterArguments(filter_by_status=filter_by_status)

    return Operation(
        request=request,
        api_version=1,
        parse=flatten("Departments", ListDepartmentsResponse),
    )


# -----------------------------------------------------------------------------
# OPERATION: list_invoice_formats
# -----------------------------------------------------------------------------


def list_invoice_formats(
    *,
    filter_by_status: list[str] | None = ["Active"],
) -> Operation[list[InvoiceFormat]]:
    """
    Build the ListInvoiceFormats operation.

    Returns:
        Operation[list[InvoiceFormat]]: The list invoice formats operation.
    """
    request = ListInvoiceFormats()
    request.method_arguments = StatusFilterArguments(filter_by_status=filter_by_status)

    return Operation(
        request=request,
        api_version=1,
        parse=flatten("InvoiceFormats", ListInvoiceFormatsResponse),
    )


# -----------------------------------------------------------------------------
# OPERATION: list_payroll_taxes
# -----------------------------------------------------------------------------


def list_payroll_taxes(
    *,
    filter_by_status: list[str] | None = ["Active"],
) -> Operation[list[PayrollTax]]:
    """
    Build the ListPayrollTaxes operation.

    Returns:
        Operation[list[PayrollTax]]: The list payroll taxes operation.
    """
    request = ListPayrollTaxes()
    request.method_arguments = StatusFilterArguments(filter_by_status=filter_by_status)

    return Operation(
        request=request,
        api_version=1,
        parse=flatten("PayrollTaxes", ListPayrollTaxesResponse),
    )


# -----------------------------------------------------------------------------
# OPERATION: list_pays
# -----------------------------------------------------------------------------


def list_pays(
    *,
    filter_by_status: list[str] | None = ["Active"],
) -> Operation[list[Pay]]:
    """
    Build the ListPays operation.

    Returns:
        Operation[list[Pay]]: The list pays operation.
    """
    request = ListPays()
    request.method_arguments = StatusFilterArguments(filter_by_status=filter_by_status)

    return Operation(
        request=request,
        api_version=1,
        parse=flatten("Pays", ListPaysResponse),
    )


# -----------------------------------------------------------------------------
# OPERATION: list_rate_tables
# -----------------------------------------------------------------------------


def list_rate_tables(
    *,
    filter_by_status: list[str] | None = ["Active"],
) -> Operation[list[RateTable]]:
    """
    Build the ListRateTables operation.

    Returns:
        Operation[list[RateTable]]: The list rate tables operation.
    """
    request = ListRateTables()
    request.method_arguments = StatusFilterArguments(filter_by_status=filter_by_status)

    return Operation(
        request=request,
        api_version=1,
        parse=flatten("RateTables", ListRateTablesResponse),
    )


# -----------------------------------------------------------------------------
# OPERATION: list_wage_tables
# -----------------------------------------------------------------------------


def list_wage_tables(
    *,
    filter_by_status: list[str] | None = ["Active"],
) -> Operation[list[WageTable]]:
    """
    Build the ListWageTables operation.

    Returns:
        Operation[list[WageTable]]: The list wage tables operation.
    """
    request = ListWageTables()
    request.method_arguments = StatusFilterArguments(filter_by_status=filter_by_status)

    return Operation(
        request=request,
        api_version=1,
        parse=flatten("WageTables", ListWageTablesResponse),
    )


# -----------------------------------------------------------------------------
# OPERATION: list_chargeable_phases
# -----------------------------------------------------------------------------


def list_chargeable_phases(project_key: int) -> Operation[list[ChargeablePhase]]:
    """
    Build the ListChargeablePhases operation.

    Returns:
        Operation[list[ChargeablePhase]]: The list chargeable phases operation.
    """
    request = ListChargeablePhases()
    request.method_arguments = ListChargeablePhasesArguments(project_key=project_key)

    return Operation(
        request=request,
        api_version=2,
        parse=flatten("ChargeablePhases", ListChargeablePhasesResponse),
    )
