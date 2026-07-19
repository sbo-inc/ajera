from math import ceil
from typing import Any, Literal, override

from pydantic import Field, computed_field

from ajera.schemas.generic import (
    GenericBaseModel,
    GenericRequest,
    GenericResponse,
)

# =============================================================================
# CLASS: PayRate
# =============================================================================


class PayRate(GenericBaseModel):
    pay_rate_key: int | None = Field(
        default=None,
        alias="PayRateKey",
        description="Unique pay rate key.",
    )
    start_date: str | None = Field(
        default=None,
        alias="StartDate",
        description="Start date for this pay rate.",
    )
    pay_period: str | None = Field(
        default=None,
        alias="PayPeriod",
        description="Pay period description.",
    )
    is_hourly: bool | None = Field(
        default=None,
        alias="IsHourly",
        description="Whether the employee is hourly for this rate.",
    )
    salary: float | None = Field(
        default=None,
        alias="Salary",
        description="Salary amount when applicable.",
    )
    pay_rate: float | None = Field(
        default=None,
        alias="PayRate",
        description="Base pay rate.",
    )
    overtime_markup: float | None = Field(
        default=None,
        alias="OvertimeMarkup",
        description="Overtime markup multiplier.",
    )
    include_overtime_in_salary: bool | None = Field(
        default=None,
        alias="IncludeOvertimeInSalary",
        description="Include overtime in salary flag.",
    )
    double_time_markup: float | None = Field(
        default=None,
        alias="DoubleTimeMarkup",
        description="Double time markup multiplier.",
    )
    include_double_time_in_salary: bool | None = Field(
        default=None,
        alias="IncludeDoubleTimeInSalary",
        description="Include double time in salary flag.",
    )
    other_time_markup: float | None = Field(
        default=None,
        alias="OtherTimeMarkup",
        description="Other time markup multiplier.",
    )
    include_other_time_markup_in_salary: bool | None = Field(
        default=None,
        alias="IncludeOtherTimeMarkupInSalary",
        description="Include other time markup in salary flag.",
    )

    @computed_field
    @property
    def annual_salary(self) -> int:
        if self.pay_rate:
            return ceil(self.pay_rate * 40 * 52)
        return 0


# =============================================================================
# CLASS: Contact
# =============================================================================


class Contact(GenericBaseModel):
    contact_key: int | None = Field(
        default=None,
        alias="ContactKey",
        description="Unique contact key.",
    )
    order: int | None = Field(
        default=None,
        alias="Order",
        description="Ordering value for the contact.",
    )
    text: str | None = Field(
        default=None,
        alias="Text",
        description="Free-form text for the contact.",
    )
    is_hourly: bool | None = Field(
        default=None,
        alias="IsHourly",
        description="Whether contact is hourly.",
    )
    first_name: str | None = Field(
        default=None,
        alias="FirstName",
        description="Contact first name.",
    )
    middle_name: str | None = Field(
        default=None,
        alias="MiddleName",
        description="Contact middle name.",
    )
    last_name: str | None = Field(
        default=None,
        alias="LastName",
        description="Contact last name.",
    )
    title: str | None = Field(
        default=None,
        alias="Title",
        description="Contact title.",
    )
    company: str | None = Field(
        default=None,
        alias="Company",
        description="Contact company.",
    )


# =============================================================================
# CLASS: CreditCard
# =============================================================================


class CreditCard(GenericBaseModel):
    bank_account_key: int | None = Field(
        default=None,
        alias="BankAccountKey",
        description="Bank account key tied to the card.",
    )
    order: int | None = Field(
        default=None,
        alias="Order",
        description="Ordering value for the credit card.",
    )
    cardholder_name: str | None = Field(
        default=None,
        alias="CardholderName",
        description="Cardholder full name.",
    )
    description: str | None = Field(
        default=None,
        alias="Description",
        description="Card description.",
    )


# =============================================================================
# CLASS: Employee
# =============================================================================


class Employee(GenericBaseModel):
    """
    Employee schema for ListEmployees response
    """

    employee_key: int = Field(
        default=0,
        alias="EmployeeKey",
        description="Unique employee key.",
    )
    first_name: str = Field(
        default="",
        alias="FirstName",
        description="Employee first name.",
    )
    middle_name: str = Field(
        default="",
        alias="MiddleName",
        description="Employee middle name.",
    )
    last_name: str = Field(
        default="",
        alias="LastName",
        description="Employee last name.",
    )
    company: int = Field(
        default=-1,
        alias="Company",
        description="Company identifier.",
    )
    department: int = Field(
        default=-1,
        alias="Department",
        description="Department identifier.",
    )
    restrict_to_own_company: bool = Field(
        default=False,
        alias="RestrictToOwnCompany",
        description="Whether the employee is restricted to their own company.",
    )
    restrict_to_own_department: bool = Field(
        default=False,
        alias="RestrictToOwnDepartment",
        description="Whether the employee is restricted to their own department.",
    )


# =============================================================================
# CLASS: EmployeeDetails
# =============================================================================


class EmployeeDetails(GenericBaseModel):
    """
    Detailed Employee schema for GetEmployees response
    """

    employee_key: int = Field(
        alias="EmployeeKey",
        description="Employee key.",
    )
    last_modified_date: str | None = Field(
        default="",
        alias="LastModifiedDate",
        description="Last modified date.",
    )
    first_name: str = Field(
        default="",
        alias="FirstName",
        description="First name.",
    )
    middle_name: str = Field(
        default="",
        alias="MiddleName",
        description="Middle name.",
    )
    last_name: str = Field(
        default="",
        alias="LastName",
        description="Last name.",
    )
    title: str = Field(
        default="",
        alias="Title",
        description="Title.",
    )
    status: str = Field(
        default="",
        alias="Status",
        description="Status.",
    )
    company_key: int = Field(
        default=-1,
        alias="CompanyKey",
        description="Company key.",
    )
    department_key: int = Field(
        default=-1,
        alias="DepartmentKey",
        description="Department key.",
    )
    is_principal: bool = Field(
        default=False,
        alias="IsPrincipal",
        description="Is principal flag.",
    )
    is_supervisor: bool = Field(
        default=False,
        alias="IsSupervisor",
        description="Is supervisor flag.",
    )
    is_project_manager: bool = Field(
        default=False,
        alias="IsProjectManager",
        description="Is project manager.",
    )
    is_accounting_manager: bool = Field(
        default=False,
        alias="IsAccountingManager",
        description="Is accounting manager.",
    )
    is_marketing_contact: bool = Field(
        default=False,
        alias="IsMarketingContact",
        description="Is marketing contact.",
    )
    supervisor_key: int | None = Field(
        default=None,
        alias="SupervisorKey",
        description="Supervisor key.",
    )
    pay_rates: list[PayRate] = Field(
        default=[],
        alias="PayRates",
        description="List of pay rates.",
    )
    fax_number: str = Field(
        default="",
        alias="FaxNumber",
        description="Fax number.",
    )
    fax_description: str = Field(
        default="",
        alias="FaxDescription",
        description="Fax description.",
    )
    email: str = Field(
        default="",
        alias="Email",
        description="Email.",
    )
    website: str = Field(
        default="",
        alias="Website",
        description="Website URL.",
    )
    allow_changes_after_processed: bool = Field(
        default=False,
        alias="AllowChangesAfterProcessed",
        description="Allow changes after processed flag.",
    )
    text: str = Field(
        default="",
        alias="Text",
        description="Notes text.",
    )
    primary_address_line_one: str = Field(
        default="",
        alias="PrimaryAddressLineOne",
        description="Address line 1.",
    )
    primary_address_line_two: str = Field(
        default="",
        alias="PrimaryAddressLineTwo",
        description="Address line 2.",
    )
    primary_address_line_three: str = Field(
        default="",
        alias="PrimaryAddressLineThree",
        description="Address line 3.",
    )
    primary_address_city: str = Field(
        default="",
        alias="PrimaryAddressCity",
        description="City.",
    )
    primary_address_zip: str = Field(
        default="",
        alias="PrimaryAddressZip",
        description="ZIP/Postal code.",
    )
    primary_address_state: str = Field(
        default="",
        alias="PrimaryAddressState",
        description="State/Province.",
    )
    primary_address_country: str = Field(
        default="",
        alias="PrimaryAddressCountry",
        description="Country.",
    )
    mailing_address_same_as_primary: bool = Field(
        default=True,
        alias="MailingAddressSameAsPrimary",
        description="Mailing address same as primary flag.",
    )
    mailing_address_line_one: str = Field(
        default="",
        alias="MailingAddressLineOne",
        description="Address line 1.",
    )
    mailing_address_line_two: str = Field(
        default="",
        alias="MailingAddressLineTwo",
        description="Address line 2.",
    )
    mailing_address_line_three: str = Field(
        default="",
        alias="MailingAddressLineThree",
        description="Address line 3.",
    )
    mailing_address_city: str = Field(
        default="",
        alias="MailingAddressCity",
        description="City.",
    )
    mailing_address_zip: str = Field(
        default="",
        alias="MailingAddressZip",
        description="ZIP/Postal code.",
    )
    mailing_address_state: str = Field(
        default="",
        alias="MailingAddressState",
        description="State/Province.",
    )
    mailing_address_country: str = Field(
        default="",
        alias="MailingAddressCountry",
        description="Country.",
    )
    primary_phone_number: str = Field(
        default="",
        alias="PrimaryPhoneNumber",
        description="Primary phone.",
    )
    primary_phone_description: str = Field(
        default="",
        alias="PrimaryPhoneDescription",
        description="Primary phone description.",
    )
    secondary_phone_number: str = Field(
        default="",
        alias="SecondaryPhoneNumber",
        description="Secondary phone.",
    )
    secondary_phone_description: str = Field(
        default="",
        alias="SecondaryPhoneDescription",
        description="Secondary phone description.",
    )
    tertiary_phone_number: str = Field(
        default="",
        alias="TertiaryPhoneNumber",
        description="Tertiary phone.",
    )
    tertiary_phone_description: str = Field(
        default="",
        alias="TertiaryPhoneDescription",
        description="Tertiary phone description.",
    )
    employee_type_key: int | None = Field(
        default=None,
        alias="EmployeeTypeKey",
        description="Employee type key.",
    )
    employee_type_description: str = Field(
        default="",
        alias="EmployeeTypeDescription",
        description="Employee type description.",
    )
    employee_type_notes: str = Field(
        default="",
        alias="EmployeeTypeNotes",
        description="Employee type notes.",
    )

    contacts: list[Contact] | Contact | None = Field(
        default=None,
        alias="Contacts",
        description="List of contacts.",
    )
    gender: str = Field(
        default="",
        alias="Gender",
        description="Gender.",
    )
    birth_date: str | None = Field(
        default=None,
        alias="BirthDate",
        description="Birth date.",
    )
    date_hired: str | None = Field(
        default=None,
        alias="DateHired",
        description="Date hired.",
    )
    date_rehired: str | None = Field(
        default=None,
        alias="DateRehired",
        description="Date rehired.",
    )
    date_terminated: str | None = Field(
        default=None,
        alias="DateTerminated",
        description="Date terminated.",
    )
    billable_percent: int | None = Field(
        default=None,
        alias="BillablePercent",
        description="Billable percent.",
    )
    social_security_number: str = Field(
        default="",
        alias="SocialSecurityNumber",
        description="Social Security Number.",
    )
    payroll_service_id: str = Field(
        default="",
        alias="PayrollServiceID",
        description="Payroll service ID.",
    )
    overhead_group_key: int | None = Field(
        default=None,
        alias="OverheadGroupKey",
        description="Overhead group key.",
    )
    use_employees: bool | None = Field(
        default=None,
        alias="UseEmployees",
        description="Use employees flag.",
    )
    credit_cards: list[CreditCard] | CreditCard | None = Field(
        default=None,
        alias="CreditCards",
        description="List of credit cards.",
    )
    calculate_payment_date_method: str = Field(
        default="",
        alias="CalculatePaymentDateMethod",
        description="Payment date calculation method.",
    )
    number_of_days_from_invoice_date: int | None = Field(
        default=None,
        alias="NumberOfDaysFromInvoiceDate",
        description="Number of days from invoice date.",
    )
    day_of_the_month_to_pay: int | None = Field(
        default=None,
        alias="DayOfTheMonthToPay",
        description="Day of the month to pay.",
    )
    notes: str = Field(
        default="",
        alias="Notes",
        description="Notes.",
    )


# =============================================================================
# CLASS: ListEmployeesArguments
# =============================================================================


class ListEmployeesArguments(GenericBaseModel):
    """
    Optional filter arguments for ListEmployees
    """

    filter_by_company: list[int] | None = Field(
        default=None,
        alias="FilterByCompany",
        description="Filter employees by company keys.",
    )
    filter_by_status: list[str] | None = Field(
        default=None,
        alias="FilterByStatus",
        description="Filter employees by status values.",
    )
    filter_by_name_like: str | None = Field(
        default=None,
        alias="FilterByNameLike",
        description="Filter employees where the name contains the given substring.",
    )
    filter_by_employee_type: list[int] | None = Field(
        default=None,
        alias="FilterByEmployeeType",
        description="Filter employees by employee type keys.",
    )
    filter_by_earliest_modified_date: str | None = Field(
        default=None,
        alias="FilterByEarliestModifiedDate",
        description="Earliest modified date filter (e.g., YYYY-MM-DD or ISO 8601).",
    )
    filter_by_latest_modified_date: str | None = Field(
        default=None,
        alias="FilterByLatestModifiedDate",
        description="Latest modified date filter (e.g., YYYY-MM-DD or ISO 8601).",
    )


# =============================================================================
# CLASS: ListEmployees
# =============================================================================


class ListEmployees(GenericRequest[ListEmployeesArguments]):
    """
    List Employees request body
    """

    method: Literal["ListEmployees"] = Field(
        default="ListEmployees",
        alias="Method",
        description="API method name to invoke.",
        frozen=True,
    )


# =============================================================================
# CLASS: ListEmployeesResponse
# =============================================================================


class ListEmployeesResponse(GenericResponse[list[Employee]]):
    """
    Response schema for ListEmployees
    """

    @override
    def model_post_init(self, context: Any) -> None:
        if self.content:
            self.content.sort(key=lambda emp: (emp.last_name, emp.first_name))


# =============================================================================
# CLASS: GetEmployeesArguments
# =============================================================================


class GetEmployeesArguments(GenericBaseModel):
    """
    Optional filter arguments for GetEmployees
    """

    requested_employees: list[int] = Field(
        alias="RequestedEmployees",
        description="List of employee keys to retrieve.",
    )


# =============================================================================
# CLASS: GetEmployees
# =============================================================================


class GetEmployees(GenericRequest[GetEmployeesArguments]):
    """
    Get Employees request body
    """

    method: Literal["GetEmployees"] = Field(
        default="GetEmployees",
        alias="Method",
        description="API method name to invoke.",
        frozen=True,
    )


# =============================================================================
# CLASS: EmployeeType
# =============================================================================


class EmployeeType(GenericBaseModel):
    """
    Employee type schema for ListEmployeeTypes response
    """

    employee_type_key: int = Field(
        default=0,
        alias="EmployeeTypeKey",
        description="Unique employee type key.",
    )
    description: str = Field(
        default="",
        alias="Description",
        description="Employee type description.",
    )
    status: str = Field(
        default="",
        alias="Status",
        description="Status (e.g. Active or Inactive).",
    )
    billable_percent: float = Field(
        default=0.0,
        alias="BillablePercent",
        description="Default billable percent for the employee type.",
    )
    budget_cost_rate: float = Field(
        default=0.0,
        alias="BudgetCostRate",
        description="Budget cost rate for the employee type.",
    )
    budget_bill_rate: float = Field(
        default=0.0,
        alias="BudgetBillRate",
        description="Budget bill rate for the employee type.",
    )
    notes: str = Field(
        default="",
        alias="Notes",
        description="Notes.",
    )


# =============================================================================
# CLASS: ListEmployeeTypesArguments
# =============================================================================


class ListEmployeeTypesArguments(GenericBaseModel):
    """
    Optional filter arguments for ListEmployeeTypes
    """

    filter_by_status: list[str] | None = Field(
        default=None,
        alias="FilterByStatus",
        description="Filter employee types by status values (e.g. Active, Inactive).",
    )


# =============================================================================
# CLASS: ListEmployeeTypes
# =============================================================================


class ListEmployeeTypes(GenericRequest[ListEmployeeTypesArguments]):
    """
    List Employee Types request body
    """

    method: Literal["ListEmployeeTypes"] = Field(
        default="ListEmployeeTypes",
        alias="Method",
        description="API method name to invoke.",
        frozen=True,
    )


# =============================================================================
# CLASS: ListEmployeeTypesResponse
# =============================================================================


class ListEmployeeTypesResponse(GenericResponse[list[EmployeeType]]):
    """
    Response schema for ListEmployeeTypes
    """

    @override
    def model_post_init(self, context: Any) -> None:
        if self.content:
            self.content.sort(key=lambda emp_type: emp_type.description)


# =============================================================================
# CLASS: UpdatedEmployeeResult
# =============================================================================


class UpdatedEmployeeResult(EmployeeDetails):
    """
    Employee record returned by UpdateEmployees.

    Extends the standard employee detail with the two fields the API only
    populates on a write: `OriginalEmployeeKey` (when a record was created)
    and `Deleted` (when a record was deleted).
    """

    original_employee_key: int | None = Field(
        default=None,
        alias="OriginalEmployeeKey",
        description="Negative key supplied on create, echoed back with the new key.",
    )
    deleted: bool | None = Field(
        default=None,
        alias="Deleted",
        description="Whether the record was deleted.",
    )


# =============================================================================
# CLASS: UpdateEmployeesArguments
# =============================================================================


class UpdateEmployeesArguments(GenericBaseModel):
    """
    Method arguments for UpdateEmployees.

    Both `UpdatedEmployees` and `UnchangedEmployees` are required by the API:
    the unchanged set is the baseline (e.g. from GetEmployees) and the updated
    set is the same baseline with the desired edits applied. (Despite the
    published docs, these are NOT wrapped in a `Content` object.)
    """

    updated_employees: list[EmployeeDetails] = Field(
        default=[],
        alias="UpdatedEmployees",
        description="Employees with edits applied (negative key requests creation).",
    )
    unchanged_employees: list[EmployeeDetails] = Field(
        default=[],
        alias="UnchangedEmployees",
        description="Baseline employee records, left untouched.",
    )
    use_single_transaction: bool = Field(
        default=False,
        alias="UseSingleTransaction",
        description="Apply all updates in one transaction; any failure rejects all.",
    )


# =============================================================================
# CLASS: UpdateEmployees
# =============================================================================


class UpdateEmployees(GenericRequest[UpdateEmployeesArguments]):
    """
    Update Employees request body
    """

    method: Literal["UpdateEmployees"] = Field(
        default="UpdateEmployees",
        alias="Method",
        description="API method name to invoke.",
        frozen=True,
    )


# =============================================================================
# CLASS: UpdateEmployeesResponseContent
# =============================================================================


class UpdateEmployeesResponseContent(GenericBaseModel):
    """
    Content payload returned by UpdateEmployees.
    """

    employees: list[UpdatedEmployeeResult] = Field(
        default=[],
        alias="Employees",
        description="The resulting employee records.",
    )
    number_of_employees_updated: int = Field(
        default=0,
        alias="NumberOfEmployeesUpdated",
        description="Count of employees updated.",
    )


# =============================================================================
# CLASS: UpdateEmployeesResponse
# =============================================================================


class UpdateEmployeesResponse(GenericResponse[UpdateEmployeesResponseContent]):
    """
    Response schema for UpdateEmployees
    """
