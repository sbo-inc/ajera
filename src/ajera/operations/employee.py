from typing import Any

from ajera.operations.generic import Operation, flatten, items
from ajera.schemas.deduction import (
    Deduction,
    ListDeductions,
    ListDeductionsArguments,
    ListDeductionsResponse,
)
from ajera.schemas.employee import (
    Employee,
    EmployeeDetails,
    EmployeeType,
    GetEmployees,
    GetEmployeesArguments,
    ListEmployees,
    ListEmployeesArguments,
    ListEmployeesResponse,
    ListEmployeeTypes,
    ListEmployeeTypesArguments,
    ListEmployeeTypesResponse,
    UpdatedEmployeeResult,
    UpdateEmployees,
    UpdateEmployeesArguments,
    UpdateEmployeesResponse,
)
from ajera.schemas.fringe import (
    Fringe,
    ListFringes,
    ListFringesArguments,
    ListFringesResponse,
)

# The read-only PayRate.annual_salary is a computed field, so it serializes
# into the request body; the API rejects it. Dropping it here keeps it visible
# on reads.
PAY_RATE_EXCLUDE: dict[str, Any] = {"pay_rates": {"__all__": {"annual_salary"}}}


# -----------------------------------------------------------------------------
# OPERATION: list_employees
# -----------------------------------------------------------------------------


def list_employees(
    *,
    filter_by_company: list[int] | None = None,
    filter_by_status: list[str] | None = ["Active"],
    filter_by_name_like: str | None = None,
    filter_by_employee_type: list[int] | None = None,
    filter_by_earliest_modified_date: str | None = None,
    filter_by_latest_modified_date: str | None = None,
) -> Operation[list[Employee]]:
    """
    Build the ListEmployees operation.

    Returns:
        Operation[list[Employee]]: The list employees operation.
    """
    request = ListEmployees()
    request.method_arguments = ListEmployeesArguments(
        filter_by_company=filter_by_company,
        filter_by_status=filter_by_status,
        filter_by_name_like=filter_by_name_like,
        filter_by_employee_type=filter_by_employee_type,
        filter_by_earliest_modified_date=filter_by_earliest_modified_date,
        filter_by_latest_modified_date=filter_by_latest_modified_date,
    )

    return Operation(
        request=request,
        api_version=1,
        parse=flatten("Employees", ListEmployeesResponse),
    )


# -----------------------------------------------------------------------------
# OPERATION: get_employees
# -----------------------------------------------------------------------------


def get_employees(employee_keys: list[int]) -> Operation[list[EmployeeDetails]]:
    """
    Build the GetEmployees operation.

    Returns:
        Operation[list[EmployeeDetails]]: The get employees operation.
    """
    request = GetEmployees()
    request.method_arguments = GetEmployeesArguments(requested_employees=employee_keys)

    return Operation(
        request=request,
        api_version=1,
        parse=items("Employees", EmployeeDetails),
    )


# -----------------------------------------------------------------------------
# OPERATION: list_employee_types
# -----------------------------------------------------------------------------


def list_employee_types(
    *,
    filter_by_status: list[str] | None = ["Active"],
) -> Operation[list[EmployeeType]]:
    """
    Build the ListEmployeeTypes operation.

    Returns:
        Operation[list[EmployeeType]]: The list employee types operation.
    """
    request = ListEmployeeTypes()
    request.method_arguments = ListEmployeeTypesArguments(
        filter_by_status=filter_by_status,
    )

    return Operation(
        request=request,
        api_version=1,
        parse=flatten("EmployeeTypes", ListEmployeeTypesResponse),
    )


# -----------------------------------------------------------------------------
# OPERATION: list_deductions
# -----------------------------------------------------------------------------


def list_deductions(
    *,
    filter_by_status: list[str] | None = ["Active"],
) -> Operation[list[Deduction]]:
    """
    Build the ListDeductions operation.

    Returns:
        Operation[list[Deduction]]: The list deductions operation.
    """
    request = ListDeductions()
    request.method_arguments = ListDeductionsArguments(
        filter_by_status=filter_by_status,
    )

    return Operation(
        request=request,
        api_version=1,
        parse=flatten("Deductions", ListDeductionsResponse),
    )


# -----------------------------------------------------------------------------
# OPERATION: list_fringes
# -----------------------------------------------------------------------------


def list_fringes(
    *,
    filter_by_status: list[str] | None = ["Active"],
) -> Operation[list[Fringe]]:
    """
    Build the ListFringes operation.

    Returns:
        Operation[list[Fringe]]: The list fringes operation.
    """
    request = ListFringes()
    request.method_arguments = ListFringesArguments(
        filter_by_status=filter_by_status,
    )

    return Operation(
        request=request,
        api_version=1,
        parse=flatten("Fringes", ListFringesResponse),
    )


# -----------------------------------------------------------------------------
# FUNCTION: apply_employee_edits
# -----------------------------------------------------------------------------


def apply_employee_edits(
    baseline: EmployeeDetails,
    *,
    first_name: str | None = None,
    middle_name: str | None = None,
    last_name: str | None = None,
    title: str | None = None,
    email: str | None = None,
    website: str | None = None,
    primary_phone_number: str | None = None,
    secondary_phone_number: str | None = None,
    tertiary_phone_number: str | None = None,
    fax_number: str | None = None,
) -> EmployeeDetails:
    """
    Apply the non-None edits to a deep copy of the baseline record.

    Returns:
        EmployeeDetails: The edited copy, which equals the baseline if nothing
            changed.
    """
    modified = baseline.model_copy(deep=True)
    if first_name is not None:
        modified.first_name = first_name
    if middle_name is not None:
        modified.middle_name = middle_name
    if last_name is not None:
        modified.last_name = last_name
    if title is not None:
        modified.title = title
    if email is not None:
        modified.email = email
    if website is not None:
        modified.website = website
    if primary_phone_number is not None:
        modified.primary_phone_number = primary_phone_number
    if secondary_phone_number is not None:
        modified.secondary_phone_number = secondary_phone_number
    if tertiary_phone_number is not None:
        modified.tertiary_phone_number = tertiary_phone_number
    if fax_number is not None:
        modified.fax_number = fax_number

    return modified


# -----------------------------------------------------------------------------
# FUNCTION: unchanged_employee_result
# -----------------------------------------------------------------------------


def unchanged_employee_result(baseline: EmployeeDetails) -> UpdatedEmployeeResult:
    """
    Represent an untouched record as an update result.

    The API rejects no-op updates, so an edit that changes nothing is answered
    from the baseline instead of being sent.

    Returns:
        UpdatedEmployeeResult: The current record, as an update result.
    """
    return UpdatedEmployeeResult.model_validate(baseline.model_dump(by_alias=True))


# -----------------------------------------------------------------------------
# OPERATION: update_employee
# -----------------------------------------------------------------------------


def update_employee(
    baseline: EmployeeDetails, modified: EmployeeDetails
) -> Operation[UpdatedEmployeeResult]:
    """
    Build the UpdateEmployees operation for one edited record.

    Returns:
        Operation[UpdatedEmployeeResult]: The update employee operation.
    """
    request = UpdateEmployees(
        method_arguments=UpdateEmployeesArguments(
            updated_employees=[modified],
            unchanged_employees=[baseline],
        )
    )

    def parse(data: dict[str, Any]) -> UpdatedEmployeeResult:
        results = UpdateEmployeesResponse.model_validate(data).content.employees
        if not results:
            raise Exception("UpdateEmployees returned no employee records")
        return results[0]

    return Operation(
        request=request,
        api_version=1,
        parse=parse,
        exclude={
            "method_arguments": {
                "updated_employees": {"__all__": PAY_RATE_EXCLUDE},
                "unchanged_employees": {"__all__": PAY_RATE_EXCLUDE},
            }
        },
    )
