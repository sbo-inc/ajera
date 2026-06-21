import json
import logging
import os
from typing import Any, cast

import requests
from pydantic import BaseModel

from ajera.schemas.client import (
    Client,
    ClientDetails,
    ClientType,
    GetClients,
    GetClientsArguments,
    ListClients,
    ListClientsArguments,
    ListClientsResponse,
    ListClientTypes,
    ListClientTypesArguments,
    ListClientTypesResponse,
    UpdateClients,
    UpdateClientsArguments,
    UpdateClientsResponse,
    UpdatedClientResult,
)
from ajera.schemas.contact import (
    Contact,
    ContactDetails,
    ContactType,
    GetContacts,
    GetContactsArguments,
    ListContacts,
    ListContactsArguments,
    ListContactsResponse,
    ListContactTypes,
    ListContactTypesArguments,
    ListContactTypesResponse,
    UpdateContacts,
    UpdateContactsArguments,
    UpdateContactsResponse,
    UpdatedContactResult,
)
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
from ajera.schemas.ledger import (
    GetLedgerAccounts,
    GetLedgerAccountsArguments,
    LedgerAccount,
    LedgerAccountDetails,
    ListLedgerAccounts,
    ListLedgerAccountsArguments,
    ListLedgerAccountsResponse,
)
from ajera.schemas.project import (
    GetProjectTemplates,
    GetProjectTemplatesArguments,
    GetProjectTotals,
    GetProjectTotalsArguments,
    ListProjects,
    ListProjectsArguments,
    ListProjectsResponse,
    ListProjectTemplates,
    ListProjectTemplatesArguments,
    ListProjectTemplatesResponse,
    ListProjectTypes,
    ListProjectTypesArguments,
    ListProjectTypesResponse,
    Project,
    ProjectTemplate,
    ProjectTemplateDetails,
    ProjectTotalsDetails,
    ProjectType,
)
from ajera.schemas.project_v2 import (
    CreateProjects,
    CreateProjectsArguments,
    CreateProjectsResponse,
    GetProjectsArgumentsV2,
    GetProjectsResponseV2,
    GetProjectsV2,
    InvoiceGroupCreate,
    PhaseCreate,
    ProjectBundle,
    ProjectChange,
    ProjectCreate,
    UpdateProjectsArgumentsV2,
    UpdateProjectsResponseV2,
    UpdateProjectsV2,
)
from ajera.schemas.reference import (
    AccountGroup,
    Activity,
    BankAccount,
    ChargeablePhase,
    Company,
    Department,
    InvoiceFormat,
    ListAccountGroups,
    ListAccountGroupsResponse,
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
from ajera.schemas.session import APISession, CreateAPISession
from ajera.schemas.vendor import (
    GetVendors,
    GetVendorsArguments,
    ListVendors,
    ListVendorsArguments,
    ListVendorsResponse,
    ListVendorTypes,
    ListVendorTypesArguments,
    ListVendorTypesResponse,
    UpdatedVendorResult,
    UpdateVendors,
    UpdateVendorsArguments,
    UpdateVendorsResponse,
    Vendor,
    VendorDetails,
    VendorType,
)
from ajera.schemas.vendor_invoice import (
    CreateVendorInvoices,
    CreateVendorInvoicesArguments,
    CreateVendorInvoicesResponse,
    GetVendorInvoices,
    GetVendorInvoicesArguments,
    GetVendorInvoicesResponse,
    ListVendorInvoices,
    ListVendorInvoicesArguments,
    ListVendorInvoicesResponse,
    VendorInvoice,
    VendorInvoiceBundle,
    VendorInvoiceCreate,
    VendorInvoiceLineItemCreate,
)

logger = logging.getLogger("ajera")
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("ajera: %(message)s"))
logger.addHandler(console_handler)

# =============================================================================
# CLASS: AjeraClient
# =============================================================================


class AjeraClient:
    """
    Deltek Ajera Client

    https://help.deltek.com/Product/Ajera/api/index.html
    """

    url: str | None
    username: str | None
    password: str | None

    def __init__(
        self,
        url: str | None = None,
        username: str | None = None,
        password: str | None = None,
        headers: dict[str, str] = {},
        log: bool = False,
    ) -> None:
        """
        Create a new client for the Deltek Ajera API.

        Args:
            url: The base URL of the API (Environment: `AJERA_API_URL`)
            username: The username to authenticate with (Environment: `AJERA_API_USERNAME`)
            password: The password to authenticate with (Environment: `AJERA_API_PASSWORD`)
            headers: Additional headers to include in requests
            log: Enables request logging at INFO level
        """
        if log:
            logger.setLevel(logging.INFO)
        else:
            logger.setLevel(logging.CRITICAL)

        # Connection configuration
        self.url = url or os.environ.get("AJERA_API_URL")
        self.username = username or os.environ.get("AJERA_API_USERNAME")
        self.password = password or os.environ.get("AJERA_API_PASSWORD")

        # Create the client instance
        self._session = requests.Session()
        self._session.headers.update({"Content-Type": "application/json", **headers})

        # Store the session tokens for caching
        self._session_tokens: dict[int, str] = {}

    @property
    def session(self) -> requests.Session:
        return self._session

    # -------------------------------------------------------------------------
    # METHOD: _require_url
    # -------------------------------------------------------------------------

    def _require_url(self) -> str:
        """
        Return the configured API URL, raising if it was never set.

        Returns:
            str: The base URL of the API.
        """
        if not self.url:
            raise ValueError("No URL provided")
        return self.url

    # -------------------------------------------------------------------------
    # METHOD: _post
    # -------------------------------------------------------------------------

    def _post(
        self,
        request: BaseModel,
        exclude: set[str] | dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Make a POST request to the Ajera API.

        Args:
            request: The request body to send.
            exclude: Fields to omit from the serialized request body.

        Returns:
            dict[str, Any]: The decoded JSON response body.
        """
        response = self.session.post(
            url=self._require_url(),
            data=request.model_dump_json(
                exclude_none=True, by_alias=True, exclude=exclude
            ),
        )
        response.raise_for_status()
        data: dict[str, Any] = json.loads(response.text)

        if "ResponseCode" in data and data["ResponseCode"] != 200:
            code = data.get("ResponseCode", "No code")
            message = data.get("Message", "No message")
            errors: list = data.get("Errors", [])
            raise Exception(
                f"API Error (Response Code: {code})\nMessage: {message}\nErrors: {errors}"
            )

        return data

    # -------------------------------------------------------------------------
    # METHOD: get_session_token
    # -------------------------------------------------------------------------

    def get_session_token(self, api_version: int) -> str:
        """
        Get a session token for a specified API version.

        Args:
            api_version: The API version to get a session token for.

        Returns:
            str: The session token.
        """
        if api_version in self._session_tokens:
            return self._session_tokens[api_version]

        username = self.username
        password = self.password
        if not username or not password:
            raise ValueError("No username or password provided")

        request = CreateAPISession(
            username=username,
            password=password,
            api_version=api_version,
        )

        # Use the session so custom headers (e.g. an Authorization header set
        # at construction) are sent on the login request too; the session token
        # is carried in the body, not headers, so there is no reason to bypass
        # the session here.
        response = self.session.post(
            url=self._require_url(),
            data=request.model_dump_json(exclude_none=True, by_alias=True),
        )
        response.raise_for_status()
        session = APISession.model_validate_json(response.text)
        token = session.content.session_token

        if token:
            self._session_tokens[api_version] = token

        return token

    # -------------------------------------------------------------------------
    # METHOD: list_employees
    # -------------------------------------------------------------------------

    def list_employees(
        self,
        *,
        filter_by_company: list[int] | None = None,
        filter_by_status: list[str] | None = ["Active"],
        filter_by_name_like: str | None = None,
        filter_by_employee_type: list[int] | None = None,
        filter_by_earliest_modified_date: str | None = None,
        filter_by_latest_modified_date: str | None = None,
    ) -> list[Employee]:
        """
        List employees

        Supported API Versions: 1

        Returns:
            list[Employee]: The list of employees.
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

        request.session_token = self.get_session_token(api_version=1)
        data = self._post(request)

        # Simplify the response structure for easier consumption
        data["Content"] = cast(dict, data["Content"]).pop("Employees", [])

        return ListEmployeesResponse.model_validate(data).content

    # -------------------------------------------------------------------------
    # METHOD: get_employees
    # -------------------------------------------------------------------------

    def get_employees(self, employee_ids: list[int]) -> list[EmployeeDetails]:
        """
        Get employee(s) details by ID

        Supported API Versions: 1

        Returns:
            list[EmployeeDetails]: A list of employees with the specified IDs.
        """
        request = GetEmployees()
        request.session_token = self.get_session_token(api_version=1)
        request.method_arguments = GetEmployeesArguments(
            requested_employees=employee_ids
        )
        data = self._post(request)

        # Simplify the response structure for easier consumption
        content: list[Any] = cast(dict, data["Content"]).pop("Employees", [])

        return [EmployeeDetails.model_validate(e) for e in content]

    # -------------------------------------------------------------------------
    # METHOD: list_employee_types
    # -------------------------------------------------------------------------

    def list_employee_types(
        self,
        *,
        filter_by_status: list[str] | None = ["Active"],
    ) -> list[EmployeeType]:
        """
        List employee types

        Supported API Versions: 1

        Returns:
            list[EmployeeType]: The list of employee types.
        """
        request = ListEmployeeTypes()
        request.method_arguments = ListEmployeeTypesArguments(
            filter_by_status=filter_by_status,
        )

        request.session_token = self.get_session_token(api_version=1)
        data = self._post(request)

        # Simplify the response structure for easier consumption
        data["Content"] = cast(dict, data["Content"]).pop("EmployeeTypes", [])

        return ListEmployeeTypesResponse.model_validate(data).content

    # -------------------------------------------------------------------------
    # METHOD: list_deductions
    # -------------------------------------------------------------------------

    def list_deductions(
        self,
        *,
        filter_by_status: list[str] | None = ["Active"],
    ) -> list[Deduction]:
        """
        List deductions

        Supported API Versions: 1

        Returns:
            list[Deduction]: The list of deductions.
        """
        request = ListDeductions()
        request.method_arguments = ListDeductionsArguments(
            filter_by_status=filter_by_status,
        )

        request.session_token = self.get_session_token(api_version=1)
        data = self._post(request)

        # Simplify the response structure for easier consumption
        data["Content"] = cast(dict, data["Content"]).pop("Deductions", [])

        return ListDeductionsResponse.model_validate(data).content

    # -------------------------------------------------------------------------
    # METHOD: list_fringes
    # -------------------------------------------------------------------------

    def list_fringes(
        self,
        *,
        filter_by_status: list[str] | None = ["Active"],
    ) -> list[Fringe]:
        """
        List fringes

        Supported API Versions: 1

        Returns:
            list[Fringe]: The list of fringes.
        """
        request = ListFringes()
        request.method_arguments = ListFringesArguments(
            filter_by_status=filter_by_status,
        )

        request.session_token = self.get_session_token(api_version=1)
        data = self._post(request)

        # Simplify the response structure for easier consumption
        data["Content"] = cast(dict, data["Content"]).pop("Fringes", [])

        return ListFringesResponse.model_validate(data).content

    # -------------------------------------------------------------------------
    # METHOD: update_employee
    # -------------------------------------------------------------------------

    def update_employee(
        self,
        employee_key: int,
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
    ) -> UpdatedEmployeeResult:
        """
        Update simple, single-line fields on one employee.

        This is a convenience facade over the batch UpdateEmployees API. It
        fetches the current record via GetEmployees to use as the baseline,
        applies only the provided (non-None) fields to a copy, and submits the
        baseline and modified records as the API's unchanged/updated pair. A
        field left as None is unchanged.

        Structural data (pay rates, contacts, credit cards) is intentionally
        not editable here; manage those in Ajera directly.

        If the requested edits leave the record unchanged (e.g. no fields
        given, or values identical to the current ones), the current record is
        returned without calling the API, which would otherwise reject the
        request with "No valid changes to this object exist."

        Supported API Versions: 1

        Returns:
            UpdatedEmployeeResult: The resulting employee record.
        """
        # Fetch the current record to use as the unchanged baseline.
        employees = self.get_employees([employee_key])
        if not employees:
            raise ValueError(f"No employee found with key {employee_key}")
        baseline = employees[0]

        # Apply the requested edits to a copy, one property at a time.
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

        # Nothing actually changed: return the current record rather than
        # letting the API reject a no-op update.
        if modified == baseline:
            return UpdatedEmployeeResult.model_validate(
                baseline.model_dump(by_alias=True)
            )

        request = UpdateEmployees(
            method_arguments=UpdateEmployeesArguments(
                updated_employees=[modified],
                unchanged_employees=[baseline],
            )
        )
        request.session_token = self.get_session_token(api_version=1)

        # Drop the read-only computed PayRate.annual_salary from the payload.
        pay_rate_exclude = {"pay_rates": {"__all__": {"annual_salary"}}}
        data = self._post(
            request,
            exclude={
                "method_arguments": {
                    "updated_employees": {"__all__": pay_rate_exclude},
                    "unchanged_employees": {"__all__": pay_rate_exclude},
                }
            },
        )

        results = UpdateEmployeesResponse.model_validate(data).content.employees
        if not results:
            raise Exception("UpdateEmployees returned no employee records")
        return results[0]

    # -------------------------------------------------------------------------
    # METHOD: list_clients
    # -------------------------------------------------------------------------

    def list_clients(
        self,
        *,
        filter_by_company: list[int] | None = None,
        filter_by_status: list[str] | None = ["Active"],
        filter_by_name_like: str | None = None,
        filter_by_name_equals: str | None = None,
        filter_by_client_type: list[int] | None = None,
        filter_by_earliest_modified_date: str | None = None,
        filter_by_latest_modified_date: str | None = None,
    ) -> list[Client]:
        """
        List clients

        Supported API Versions: 1

        Returns:
            list[Client]: The list of clients.
        """
        request = ListClients()
        request.method_arguments = ListClientsArguments(
            filter_by_company=filter_by_company,
            filter_by_status=filter_by_status,
            filter_by_name_like=filter_by_name_like,
            filter_by_name_equals=filter_by_name_equals,
            filter_by_client_type=filter_by_client_type,
            filter_by_earliest_modified_date=filter_by_earliest_modified_date,
            filter_by_latest_modified_date=filter_by_latest_modified_date,
        )

        request.session_token = self.get_session_token(api_version=1)
        data = self._post(request)

        # Simplify the response structure for easier consumption
        data["Content"] = cast(dict, data["Content"]).pop("Clients", [])

        return ListClientsResponse.model_validate(data).content

    # -------------------------------------------------------------------------
    # METHOD: get_clients
    # -------------------------------------------------------------------------

    def get_clients(self, client_ids: list[int]) -> list[ClientDetails]:
        """
        Get client(s) details by ID

        Supported API Versions: 1

        Returns:
            list[ClientDetails]: A list of clients with the specified IDs.
        """
        request = GetClients()
        request.session_token = self.get_session_token(api_version=1)
        request.method_arguments = GetClientsArguments(requested_clients=client_ids)
        data = self._post(request)

        # Simplify the response structure for easier consumption
        content: list[Any] = cast(dict, data["Content"]).pop("Clients", [])

        return [ClientDetails.model_validate(c) for c in content]

    # -------------------------------------------------------------------------
    # METHOD: list_client_types
    # -------------------------------------------------------------------------

    def list_client_types(
        self,
        *,
        filter_by_status: list[str] | None = ["Active"],
    ) -> list[ClientType]:
        """
        List client types

        Supported API Versions: 1

        Returns:
            list[ClientType]: The list of client types.
        """
        request = ListClientTypes()
        request.method_arguments = ListClientTypesArguments(
            filter_by_status=filter_by_status,
        )

        request.session_token = self.get_session_token(api_version=1)
        data = self._post(request)

        # Simplify the response structure for easier consumption
        data["Content"] = cast(dict, data["Content"]).pop("ClientTypes", [])

        return ListClientTypesResponse.model_validate(data).content

    # -------------------------------------------------------------------------
    # METHOD: update_client
    # -------------------------------------------------------------------------

    def update_client(
        self,
        client_key: int,
        *,
        description: str | None = None,
        account_id: str | None = None,
        email: str | None = None,
        website: str | None = None,
        primary_phone_number: str | None = None,
        secondary_phone_number: str | None = None,
        tertiary_phone_number: str | None = None,
        fax_number: str | None = None,
        notes: str | None = None,
    ) -> UpdatedClientResult:
        """
        Update simple, single-line fields on one client.

        This is a convenience facade over the batch UpdateClients API. It
        fetches the current record via GetClients to use as the baseline,
        applies only the provided (non-None) fields to a copy, and submits the
        baseline and modified records as the API's unchanged/updated pair. A
        field left as None is unchanged.

        Structural data (contacts, addresses, finance-charge settings) is
        intentionally not editable here; manage those in Ajera directly.

        If the requested edits leave the record unchanged (e.g. no fields
        given, or values identical to the current ones), the current record is
        returned without calling the API, which would otherwise reject the
        request with "No valid changes to this object exist."

        Supported API Versions: 1

        Returns:
            UpdatedClientResult: The resulting client record.
        """
        # Fetch the current record to use as the unchanged baseline.
        clients = self.get_clients([client_key])
        if not clients:
            raise ValueError(f"No client found with key {client_key}")
        baseline = clients[0]

        # Apply the requested edits to a copy, one property at a time.
        modified = baseline.model_copy(deep=True)
        if description is not None:
            modified.description = description
        if account_id is not None:
            modified.account_id = account_id
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
        if notes is not None:
            modified.notes = notes

        # Nothing actually changed: return the current record rather than
        # letting the API reject a no-op update.
        if modified == baseline:
            return UpdatedClientResult.model_validate(
                baseline.model_dump(by_alias=True)
            )

        request = UpdateClients(
            method_arguments=UpdateClientsArguments(
                updated_clients=[modified],
                unchanged_clients=[baseline],
            )
        )
        request.session_token = self.get_session_token(api_version=1)
        data = self._post(request)

        results = UpdateClientsResponse.model_validate(data).content.clients
        if not results:
            raise Exception("UpdateClients returned no client records")
        return results[0]

    # -------------------------------------------------------------------------
    # METHOD: list_contacts
    # -------------------------------------------------------------------------

    def list_contacts(
        self,
        *,
        filter_by_company: list[int] | None = None,
        filter_by_status: list[str] | None = ["Active"],
        filter_by_text: str | None = None,
        filter_by_contact_type: list[int] | None = None,
        filter_by_earliest_modified_date: str | None = None,
        filter_by_latest_modified_date: str | None = None,
    ) -> list[Contact]:
        """
        List contacts

        Supported API Versions: 1

        Returns:
            list[Contact]: The list of contacts.
        """
        request = ListContacts()
        request.method_arguments = ListContactsArguments(
            filter_by_company=filter_by_company,
            filter_by_status=filter_by_status,
            filter_by_text=filter_by_text,
            filter_by_contact_type=filter_by_contact_type,
            filter_by_earliest_modified_date=filter_by_earliest_modified_date,
            filter_by_latest_modified_date=filter_by_latest_modified_date,
        )

        request.session_token = self.get_session_token(api_version=1)
        data = self._post(request)

        # Simplify the response structure for easier consumption
        data["Content"] = cast(dict, data["Content"]).pop("Contacts", [])

        return ListContactsResponse.model_validate(data).content

    # -------------------------------------------------------------------------
    # METHOD: get_contacts
    # -------------------------------------------------------------------------

    def get_contacts(self, contact_ids: list[int]) -> list[ContactDetails]:
        """
        Get contact(s) details by ID

        Supported API Versions: 1

        Returns:
            list[ContactDetails]: A list of contacts with the specified IDs.
        """
        request = GetContacts()
        request.session_token = self.get_session_token(api_version=1)
        request.method_arguments = GetContactsArguments(requested_contacts=contact_ids)
        data = self._post(request)

        # Simplify the response structure for easier consumption
        content: list[Any] = cast(dict, data["Content"]).pop("Contacts", [])

        return [ContactDetails.model_validate(c) for c in content]

    # -------------------------------------------------------------------------
    # METHOD: list_contact_types
    # -------------------------------------------------------------------------

    def list_contact_types(
        self,
        *,
        filter_by_status: list[str] | None = ["Active"],
    ) -> list[ContactType]:
        """
        List contact types

        Supported API Versions: 1

        Returns:
            list[ContactType]: The list of contact types.
        """
        request = ListContactTypes()
        request.method_arguments = ListContactTypesArguments(
            filter_by_status=filter_by_status,
        )

        request.session_token = self.get_session_token(api_version=1)
        data = self._post(request)

        # Simplify the response structure for easier consumption
        data["Content"] = cast(dict, data["Content"]).pop("ContactTypes", [])

        return ListContactTypesResponse.model_validate(data).content

    # -------------------------------------------------------------------------
    # METHOD: update_contact
    # -------------------------------------------------------------------------

    def update_contact(
        self,
        contact_key: int,
        *,
        first_name: str | None = None,
        middle_name: str | None = None,
        last_name: str | None = None,
        title: str | None = None,
        company: str | None = None,
        email: str | None = None,
        website: str | None = None,
        primary_phone_number: str | None = None,
        secondary_phone_number: str | None = None,
        tertiary_phone_number: str | None = None,
        fax_number: str | None = None,
        notes: str | None = None,
    ) -> UpdatedContactResult:
        """
        Update simple, single-line fields on one contact.

        This is a convenience facade over the batch UpdateContacts API. It
        fetches the current record via GetContacts to use as the baseline,
        applies only the provided (non-None) fields to a copy, and submits the
        baseline and modified records as the API's unchanged/updated pair. A
        field left as None is unchanged.

        Structural data (addresses, contact type) is intentionally not editable
        here; manage those in Ajera directly.

        If the requested edits leave the record unchanged (e.g. no fields
        given, or values identical to the current ones), the current record is
        returned without calling the API, which would otherwise reject the
        request with "No valid changes to this object exist."

        Supported API Versions: 1

        Returns:
            UpdatedContactResult: The resulting contact record.
        """
        # Fetch the current record to use as the unchanged baseline.
        contacts = self.get_contacts([contact_key])
        if not contacts:
            raise ValueError(f"No contact found with key {contact_key}")
        baseline = contacts[0]

        # Apply the requested edits to a copy, one property at a time.
        modified = baseline.model_copy(deep=True)
        if first_name is not None:
            modified.first_name = first_name
        if middle_name is not None:
            modified.middle_name = middle_name
        if last_name is not None:
            modified.last_name = last_name
        if title is not None:
            modified.title = title
        if company is not None:
            modified.company = company
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
        if notes is not None:
            modified.notes = notes

        # Nothing actually changed: return the current record rather than
        # letting the API reject a no-op update.
        if modified == baseline:
            return UpdatedContactResult.model_validate(
                baseline.model_dump(by_alias=True)
            )

        request = UpdateContacts(
            method_arguments=UpdateContactsArguments(
                updated_contacts=[modified],
                unchanged_contacts=[baseline],
            )
        )
        request.session_token = self.get_session_token(api_version=1)
        data = self._post(request)

        results = UpdateContactsResponse.model_validate(data).content.contacts
        if not results:
            raise Exception("UpdateContacts returned no contact records")
        return results[0]

    # -------------------------------------------------------------------------
    # METHOD: list_vendors
    # -------------------------------------------------------------------------

    def list_vendors(
        self,
        *,
        filter_by_company: list[int] | None = None,
        filter_by_status: list[str] | None = ["Active"],
        filter_by_name_like: str | None = None,
        filter_by_vendor_type: list[int] | None = None,
        filter_by_earliest_modified_date: str | None = None,
        filter_by_latest_modified_date: str | None = None,
    ) -> list[Vendor]:
        """
        List vendors

        Supported API Versions: 1

        Returns:
            list[Vendor]: The list of vendors.
        """
        request = ListVendors()
        request.method_arguments = ListVendorsArguments(
            filter_by_company=filter_by_company,
            filter_by_status=filter_by_status,
            filter_by_name_like=filter_by_name_like,
            filter_by_vendor_type=filter_by_vendor_type,
            filter_by_earliest_modified_date=filter_by_earliest_modified_date,
            filter_by_latest_modified_date=filter_by_latest_modified_date,
        )

        request.session_token = self.get_session_token(api_version=1)
        data = self._post(request)

        # Simplify the response structure for easier consumption
        data["Content"] = cast(dict, data["Content"]).pop("Vendors", [])

        return ListVendorsResponse.model_validate(data).content

    # -------------------------------------------------------------------------
    # METHOD: get_vendors
    # -------------------------------------------------------------------------

    def get_vendors(self, vendor_ids: list[int]) -> list[VendorDetails]:
        """
        Get vendor(s) details by ID

        Supported API Versions: 1

        Returns:
            list[VendorDetails]: A list of vendors with the specified IDs.
        """
        request = GetVendors()
        request.session_token = self.get_session_token(api_version=1)
        request.method_arguments = GetVendorsArguments(requested_vendors=vendor_ids)
        data = self._post(request)

        # Simplify the response structure for easier consumption
        content: list[Any] = cast(dict, data["Content"]).pop("Vendors", [])

        return [VendorDetails.model_validate(v) for v in content]

    # -------------------------------------------------------------------------
    # METHOD: list_vendor_types
    # -------------------------------------------------------------------------

    def list_vendor_types(
        self,
        *,
        filter_by_status: list[str] | None = ["Active"],
        filter_by_is_credit_card: list[bool] | None = None,
        filter_by_is_consultant: list[bool] | None = None,
    ) -> list[VendorType]:
        """
        List vendor types

        Supported API Versions: 1

        Returns:
            list[VendorType]: The list of vendor types.
        """
        request = ListVendorTypes()
        request.method_arguments = ListVendorTypesArguments(
            filter_by_status=filter_by_status,
            filter_by_is_credit_card=filter_by_is_credit_card,
            filter_by_is_consultant=filter_by_is_consultant,
        )

        request.session_token = self.get_session_token(api_version=1)
        data = self._post(request)

        # Simplify the response structure for easier consumption
        data["Content"] = cast(dict, data["Content"]).pop("VendorTypes", [])

        return ListVendorTypesResponse.model_validate(data).content

    # -------------------------------------------------------------------------
    # METHOD: update_vendor
    # -------------------------------------------------------------------------

    def update_vendor(
        self,
        vendor_key: int,
        *,
        name: str | None = None,
        vendor_account_id: str | None = None,
        email: str | None = None,
        website: str | None = None,
        primary_phone_number: str | None = None,
        secondary_phone_number: str | None = None,
        tertiary_phone_number: str | None = None,
        fax_number: str | None = None,
        notes: str | None = None,
    ) -> UpdatedVendorResult:
        """
        Update simple, single-line fields on one vendor.

        This is a convenience facade over the batch UpdateVendors API. It
        fetches the current record via GetVendors to use as the baseline,
        applies only the provided (non-None) fields to a copy, and submits the
        baseline and modified records as the API's unchanged/updated pair. A
        field left as None is unchanged.

        Structural data (contacts, addresses, 1099/W-9 settings, payment
        scheduling) is intentionally not editable here; manage those in Ajera
        directly.

        If the requested edits leave the record unchanged (e.g. no fields
        given, or values identical to the current ones), the current record is
        returned without calling the API, which would otherwise reject the
        request with "No valid changes to this object exist."

        Supported API Versions: 1

        Returns:
            UpdatedVendorResult: The resulting vendor record.
        """
        # Fetch the current record to use as the unchanged baseline.
        vendors = self.get_vendors([vendor_key])
        if not vendors:
            raise ValueError(f"No vendor found with key {vendor_key}")
        baseline = vendors[0]

        # Apply the requested edits to a copy, one property at a time.
        modified = baseline.model_copy(deep=True)
        if name is not None:
            modified.name = name
        if vendor_account_id is not None:
            modified.vendor_account_id = vendor_account_id
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
        if notes is not None:
            modified.notes = notes

        # Nothing actually changed: return the current record rather than
        # letting the API reject a no-op update.
        if modified == baseline:
            return UpdatedVendorResult.model_validate(
                baseline.model_dump(by_alias=True)
            )

        request = UpdateVendors(
            method_arguments=UpdateVendorsArguments(
                updated_vendors=[modified],
                unchanged_vendors=[baseline],
            )
        )
        request.session_token = self.get_session_token(api_version=1)
        data = self._post(request)

        results = UpdateVendorsResponse.model_validate(data).content.vendors
        if not results:
            raise Exception("UpdateVendors returned no vendor records")
        return results[0]

    # -------------------------------------------------------------------------
    # METHOD: list_vendor_invoices
    # -------------------------------------------------------------------------

    def list_vendor_invoices(
        self,
        *,
        filter_by_vendor: list[int] | None = None,
        filter_by_company: int | None = None,
        filter_by_vendor_type: int | None = None,
        filter_by_paid: bool | None = None,
        filter_by_unpaid: bool | None = None,
        filter_by_voided: bool | None = None,
        filter_by_earliest_invoice_date: str | None = None,
        filter_by_latest_invoice_date: str | None = None,
        filter_by_earliest_accounting_date: str | None = None,
        filter_by_latest_accounting_date: str | None = None,
        filter_by_earliest_invoice_date_to_pay: str | None = None,
        filter_by_latest_date_to_pay: str | None = None,
        filter_by_greater_than_amount: float | None = None,
        filter_by_less_than_amount: float | None = None,
        filter_by_equal_to_amount: float | None = None,
    ) -> list[VendorInvoice]:
        """
        List vendor invoices

        Supported API Versions: 2

        Returns:
            list[VendorInvoice]: The matching vendor invoice headers.
        """
        request = ListVendorInvoices()
        request.method_arguments = ListVendorInvoicesArguments(
            filter_by_vendor=filter_by_vendor,
            filter_by_company=filter_by_company,
            filter_by_vendor_type=filter_by_vendor_type,
            filter_by_paid=filter_by_paid,
            filter_by_unpaid=filter_by_unpaid,
            filter_by_voided=filter_by_voided,
            filter_by_earliest_invoice_date=filter_by_earliest_invoice_date,
            filter_by_latest_invoice_date=filter_by_latest_invoice_date,
            filter_by_earliest_accounting_date=filter_by_earliest_accounting_date,
            filter_by_latest_accounting_date=filter_by_latest_accounting_date,
            filter_by_earliest_invoice_date_to_pay=(
                filter_by_earliest_invoice_date_to_pay
            ),
            filter_by_latest_date_to_pay=filter_by_latest_date_to_pay,
            filter_by_greater_than_amount=filter_by_greater_than_amount,
            filter_by_less_than_amount=filter_by_less_than_amount,
            filter_by_equal_to_amount=filter_by_equal_to_amount,
        )

        request.session_token = self.get_session_token(api_version=2)
        data = self._post(request)

        # Simplify the response structure for easier consumption. The list call
        # also returns an (empty) VendorInvoicesDetails array, which we drop.
        data["Content"] = cast(dict, data["Content"]).pop("VendorInvoices", [])

        return ListVendorInvoicesResponse.model_validate(data).content

    # -------------------------------------------------------------------------
    # METHOD: get_vendor_invoices
    # -------------------------------------------------------------------------

    def get_vendor_invoices(self, invoice_ids: list[int]) -> VendorInvoiceBundle:
        """
        Get vendor invoice(s) by key, with their line items

        Returns a bundle of invoice headers and line items; line items are
        linked to their header by VendorInvoiceKey.

        Supported API Versions: 2

        Returns:
            VendorInvoiceBundle: The invoice headers and line items.
        """
        request = GetVendorInvoices()
        request.session_token = self.get_session_token(api_version=2)
        request.method_arguments = GetVendorInvoicesArguments(
            requested_vendor_invoices=invoice_ids
        )
        data = self._post(request)

        return GetVendorInvoicesResponse.model_validate(data).content

    # -------------------------------------------------------------------------
    # METHOD: create_vendor_invoice
    # -------------------------------------------------------------------------

    def create_vendor_invoice(
        self,
        *,
        vendor_key: int,
        company_key: int,
        amount: float,
        line_items: list[VendorInvoiceLineItemCreate],
        number: str | None = None,
        description: str | None = None,
        date: str | None = None,
        accounting_date: str | None = None,
        notes: str | None = None,
    ) -> VendorInvoiceBundle:
        """
        Create a single vendor invoice with its line items.

        Note: the API exposes no method to delete or void a vendor invoice, so
        a created invoice is a permanent accounting record. `amount` should
        equal the sum of the line item cost amounts.

        Supported API Versions: 2

        Returns:
            VendorInvoiceBundle: The created invoice header and line items.
        """
        request = CreateVendorInvoices(
            method_arguments=CreateVendorInvoicesArguments(
                vendor_invoices=[
                    VendorInvoiceCreate(
                        vendor_key=vendor_key,
                        company_key=company_key,
                        amount=amount,
                        line_items=line_items,
                        number=number,
                        description=description,
                        date=date,
                        accounting_date=accounting_date,
                        notes=notes,
                    )
                ],
            )
        )
        request.session_token = self.get_session_token(api_version=2)
        data = self._post(request)

        return CreateVendorInvoicesResponse.model_validate(data).content

    # -------------------------------------------------------------------------
    # METHOD: list_projects
    # -------------------------------------------------------------------------

    def list_projects(
        self,
        *,
        filter_by_company: list[int] | None = None,
        filter_by_status: list[str] | None = None,
        filter_by_name_like: str | None = None,
        filter_by_description_like: str | None = None,
        filter_by_description_equals: str | None = None,
        filter_by_id_like: str | None = None,
        filter_by_project_type: list[int] | None = None,
        filter_by_sync_to_crm: list[bool] | None = None,
        filter_by_earliest_modified_date: str | None = None,
        filter_by_latest_modified_date: str | None = None,
    ) -> list[Project]:
        """
        List projects

        ListProjects is identical across API versions; this uses v2.

        Supported API Versions: 1, 2

        Returns:
            list[Project]: The list of projects.
        """
        request = ListProjects()
        request.method_arguments = ListProjectsArguments(
            filter_by_company=filter_by_company,
            filter_by_status=filter_by_status,
            filter_by_name_like=filter_by_name_like,
            filter_by_description_like=filter_by_description_like,
            filter_by_description_equals=filter_by_description_equals,
            filter_by_id_like=filter_by_id_like,
            filter_by_project_type=filter_by_project_type,
            filter_by_sync_to_crm=filter_by_sync_to_crm,
            filter_by_earliest_modified_date=filter_by_earliest_modified_date,
            filter_by_latest_modified_date=filter_by_latest_modified_date,
        )

        request.session_token = self.get_session_token(api_version=2)
        data = self._post(request)

        # Simplify the response structure for easier consumption
        data["Content"] = cast(dict, data["Content"]).pop("Projects", [])

        return ListProjectsResponse.model_validate(data).content

    # -------------------------------------------------------------------------
    # METHOD: get_projects
    # -------------------------------------------------------------------------

    def get_projects(self, project_ids: list[int]) -> ProjectBundle:
        """
        Get project(s) by ID, with phases, invoice groups, and resources

        Uses v2, which returns a flat bundle of parallel arrays (projects,
        invoice groups, phases, resources) linked by foreign keys. Resources
        are included inline, so there is no separate "with resources" call.

        Supported API Versions: 2

        Returns:
            ProjectBundle: The projects and their related records.
        """
        request = GetProjectsV2()
        request.session_token = self.get_session_token(api_version=2)
        request.method_arguments = GetProjectsArgumentsV2(
            requested_projects=project_ids
        )
        data = self._post(request)

        return GetProjectsResponseV2.model_validate(data).content

    # -------------------------------------------------------------------------
    # METHOD: get_project_totals
    # -------------------------------------------------------------------------

    def get_project_totals(self, project_id: int) -> ProjectTotalsDetails:
        """
        Get a single project's details enriched with financial totals

        Unlike the other Get* methods, GetProjectTotals accepts a single
        project key, not a list.

        Supported API Versions: 1

        Returns:
            ProjectTotalsDetails: The project with project-level totals.
        """
        request = GetProjectTotals()
        request.session_token = self.get_session_token(api_version=1)
        request.method_arguments = GetProjectTotalsArguments(
            requested_project_totals=project_id
        )
        data = self._post(request)

        # Content wraps a single project object under "ProjectTotals".
        content: dict[str, Any] = cast(dict, data["Content"]).pop("ProjectTotals", {})

        return ProjectTotalsDetails.model_validate(content)

    # -------------------------------------------------------------------------
    # METHOD: list_project_types
    # -------------------------------------------------------------------------

    def list_project_types(
        self,
        *,
        filter_by_status: list[str] | None = ["Active"],
    ) -> list[ProjectType]:
        """
        List project types

        Supported API Versions: 1

        Returns:
            list[ProjectType]: The list of project types.
        """
        request = ListProjectTypes()
        request.method_arguments = ListProjectTypesArguments(
            filter_by_status=filter_by_status,
        )

        request.session_token = self.get_session_token(api_version=1)
        data = self._post(request)

        # Simplify the response structure for easier consumption
        data["Content"] = cast(dict, data["Content"]).pop("ProjectTypes", [])

        return ListProjectTypesResponse.model_validate(data).content

    # -------------------------------------------------------------------------
    # METHOD: list_project_templates
    # -------------------------------------------------------------------------

    def list_project_templates(
        self,
        *,
        filter_by_company: list[int] | None = None,
        filter_by_status: list[str] | None = None,
        filter_by_name_like: str | None = None,
        filter_by_description_like: str | None = None,
        filter_by_description_equals: str | None = None,
        filter_by_id_like: str | None = None,
        filter_by_project_type: list[int] | None = None,
        filter_by_sync_to_crm: list[bool] | None = None,
        filter_by_earliest_modified_date: str | None = None,
        filter_by_latest_modified_date: str | None = None,
    ) -> list[ProjectTemplate]:
        """
        List project templates

        Supported API Versions: 1

        Returns:
            list[ProjectTemplate]: The list of project templates.
        """
        request = ListProjectTemplates()
        request.method_arguments = ListProjectTemplatesArguments(
            filter_by_company=filter_by_company,
            filter_by_status=filter_by_status,
            filter_by_name_like=filter_by_name_like,
            filter_by_description_like=filter_by_description_like,
            filter_by_description_equals=filter_by_description_equals,
            filter_by_id_like=filter_by_id_like,
            filter_by_project_type=filter_by_project_type,
            filter_by_sync_to_crm=filter_by_sync_to_crm,
            filter_by_earliest_modified_date=filter_by_earliest_modified_date,
            filter_by_latest_modified_date=filter_by_latest_modified_date,
        )

        request.session_token = self.get_session_token(api_version=1)
        data = self._post(request)

        # Simplify the response structure for easier consumption
        data["Content"] = cast(dict, data["Content"]).pop("ProjectTemplates", [])

        return ListProjectTemplatesResponse.model_validate(data).content

    # -------------------------------------------------------------------------
    # METHOD: get_project_templates
    # -------------------------------------------------------------------------

    def get_project_templates(
        self, template_ids: list[int]
    ) -> list[ProjectTemplateDetails]:
        """
        Get project template(s) details by ID

        Supported API Versions: 1

        Returns:
            list[ProjectTemplateDetails]: A list of templates with the given IDs.
        """
        request = GetProjectTemplates()
        request.session_token = self.get_session_token(api_version=1)
        request.method_arguments = GetProjectTemplatesArguments(
            requested_projects=template_ids
        )
        data = self._post(request)

        # Simplify the response structure for easier consumption
        content: list[Any] = cast(dict, data["Content"]).pop("ProjectTemplates", [])

        return [ProjectTemplateDetails.model_validate(t) for t in content]

    # -------------------------------------------------------------------------
    # METHOD: update_project
    # -------------------------------------------------------------------------

    def update_project(
        self,
        project_key: int,
        *,
        description: str | None = None,
        project_id: str | None = None,
        location: str | None = None,
        billing_description: str | None = None,
        notes: str | None = None,
    ) -> ProjectBundle:
        """
        Update simple, single-line fields on one project.

        This is a convenience facade over the v2 UpdateProjects API. It fetches
        the current project bundle via GetProjects to send back as the
        unchanged baseline, and submits only the provided (non-None) fields as
        the changed delta. A field left as None is unchanged.

        Structural data (phases, invoice groups, resources, contract amounts)
        is intentionally not editable here; manage those in Ajera directly.

        If no fields are provided, the current bundle is returned without
        calling the update API.

        Supported API Versions: 2

        Returns:
            ProjectBundle: The updated project bundle.
        """
        # Fetch the current bundle to send back verbatim as the baseline.
        get_request = GetProjectsV2()
        get_request.session_token = self.get_session_token(api_version=2)
        get_request.method_arguments = GetProjectsArgumentsV2(
            requested_projects=[project_key]
        )
        baseline = self._post(get_request)
        bundle: dict[str, Any] = cast(dict, baseline["Content"])
        if not bundle.get("Projects"):
            raise ValueError(f"No project found with key {project_key}")

        # Nothing to change: return the current bundle without calling update.
        if all(
            v is None
            for v in (
                description,
                project_id,
                location,
                billing_description,
                notes,
            )
        ):
            return GetProjectsResponseV2.model_validate(baseline).content

        change = ProjectChange(
            project_key=project_key,
            description=description,
            id=project_id,
            location=location,
            billing_description=billing_description,
            notes=notes,
        )

        request = UpdateProjectsV2(
            method_arguments=UpdateProjectsArgumentsV2(
                updated_projects=[change],
                unchanged_projects=bundle,
            )
        )
        request.session_token = self.get_session_token(api_version=2)
        data = self._post(request)

        return UpdateProjectsResponseV2.model_validate(data).content

    # -------------------------------------------------------------------------
    # METHOD: create_project
    # -------------------------------------------------------------------------

    def create_project(
        self,
        description: str,
        *,
        billing_type: str,
        rate_table_key: int,
        client_key: int,
        invoice_format_key: int,
        company_key: int | None = 1,
        invoice_group_description: str | None = None,
        phase_description: str | None = None,
    ) -> ProjectBundle:
        """
        Create a new project (with one invoice group and one phase).

        Uses the v2 CreateProjects API with CreateType "Project". A project
        cannot be created on its own, so a single invoice group (billed to
        `client_key` with `invoice_format_key`) and a single phase are created
        alongside it. The invoice group and phase descriptions default to the
        project description (both are required and cannot be empty).

        Supported API Versions: 2

        Returns:
            ProjectBundle: The created project bundle.
        """
        request = CreateProjects(
            method_arguments=CreateProjectsArguments(
                project=ProjectCreate(
                    description=description,
                    billing_type=billing_type,
                    rate_table_key=rate_table_key,
                    company_key=company_key,
                ),
                invoice_groups=[
                    InvoiceGroupCreate(
                        description=invoice_group_description or description,
                        client_key=client_key,
                        invoice_format_key=invoice_format_key,
                    )
                ],
                phases=[PhaseCreate(description=phase_description or description)],
            )
        )
        request.session_token = self.get_session_token(api_version=2)
        data = self._post(request)

        return CreateProjectsResponse.model_validate(data).content

    # -------------------------------------------------------------------------
    # METHOD: list_ledger_accounts
    # -------------------------------------------------------------------------

    def list_ledger_accounts(
        self,
        *,
        filter_by_account_group: list[int] | None = None,
        filter_by_status: list[str] | None = ["Active"],
        filter_by_type: list[str] | None = None,
    ) -> list[LedgerAccount]:
        """
        List general ledger accounts

        Supported API Versions: 1, 2

        Returns:
            list[LedgerAccount]: The list of ledger accounts.
        """
        request = ListLedgerAccounts()
        request.method_arguments = ListLedgerAccountsArguments(
            filter_by_account_group=filter_by_account_group,
            filter_by_status=filter_by_status,
            filter_by_type=filter_by_type,
        )

        request.session_token = self.get_session_token(api_version=1)
        data = self._post(request)

        # Simplify the response structure for easier consumption
        data["Content"] = cast(dict, data["Content"]).pop("GLAccounts", [])

        return ListLedgerAccountsResponse.model_validate(data).content

    # -------------------------------------------------------------------------
    # METHOD: get_ledger_accounts
    # -------------------------------------------------------------------------

    def get_ledger_accounts(
        self,
        account_ids: list[int] | None = None,
        *,
        exclude_close_year_entries: bool | None = None,
        as_of_date: str | None = None,
        filter_by_account_group: list[int] | None = None,
        filter_by_status: list[str] | None = None,
        filter_by_type: list[str] | None = None,
    ) -> list[LedgerAccountDetails]:
        """
        Get general ledger account details, with calculated amounts

        Returns each account enriched with calculated balances and budgets.
        Pass `account_ids` to select specific accounts, or omit to return all.
        `as_of_date` calculates balances as of that date, and
        `exclude_close_year_entries` omits close-year entries from the amounts.

        Supported API Versions: 1

        Returns:
            list[LedgerAccountDetails]: The requested accounts with amounts.
        """
        request = GetLedgerAccounts()
        request.session_token = self.get_session_token(api_version=1)
        request.method_arguments = GetLedgerAccountsArguments(
            requested_accounts=account_ids,
            exclude_close_year_entries=exclude_close_year_entries,
            as_of_date=as_of_date,
            filter_by_account_group=filter_by_account_group,
            filter_by_status=filter_by_status,
            filter_by_type=filter_by_type,
        )
        data = self._post(request)

        # Simplify the response structure for easier consumption
        content: list[Any] = cast(dict, data["Content"]).pop("GLAccounts", [])

        return [LedgerAccountDetails.model_validate(a) for a in content]

    # -------------------------------------------------------------------------
    # METHOD: list_account_groups
    # -------------------------------------------------------------------------

    def list_account_groups(
        self,
        *,
        filter_by_status: list[str] | None = ["Active"],
    ) -> list[AccountGroup]:
        """
        List general ledger account groups

        Supported API Versions: 1

        Returns:
            list[AccountGroup]: The list of account groups.
        """
        request = ListAccountGroups()
        request.method_arguments = StatusFilterArguments(
            filter_by_status=filter_by_status
        )
        request.session_token = self.get_session_token(api_version=1)
        data = self._post(request)

        data["Content"] = cast(dict, data["Content"]).pop("AccountGroups", [])
        return ListAccountGroupsResponse.model_validate(data).content

    # -------------------------------------------------------------------------
    # METHOD: list_activities
    # -------------------------------------------------------------------------

    def list_activities(
        self,
        *,
        filter_by_status: list[str] | None = ["Active"],
        filter_by_description_like: str | None = None,
    ) -> list[Activity]:
        """
        List activities

        Supported API Versions: 1

        Returns:
            list[Activity]: The list of activities.
        """
        request = ListActivities()
        request.method_arguments = ListActivitiesArguments(
            filter_by_status=filter_by_status,
            filter_by_description_like=filter_by_description_like,
        )
        request.session_token = self.get_session_token(api_version=1)
        data = self._post(request)

        data["Content"] = cast(dict, data["Content"]).pop("Activities", [])
        return ListActivitiesResponse.model_validate(data).content

    # -------------------------------------------------------------------------
    # METHOD: list_bank_accounts
    # -------------------------------------------------------------------------

    def list_bank_accounts(
        self,
        *,
        filter_by_status: list[str] | None = ["Active"],
    ) -> list[BankAccount]:
        """
        List bank accounts

        Supported API Versions: 1

        Returns:
            list[BankAccount]: The list of bank accounts.
        """
        request = ListBankAccounts()
        request.method_arguments = StatusFilterArguments(
            filter_by_status=filter_by_status
        )
        request.session_token = self.get_session_token(api_version=1)
        data = self._post(request)

        data["Content"] = cast(dict, data["Content"]).pop("BankAccounts", [])
        return ListBankAccountsResponse.model_validate(data).content

    # -------------------------------------------------------------------------
    # METHOD: list_companies
    # -------------------------------------------------------------------------

    def list_companies(
        self,
        *,
        filter_by_status: list[str] | None = ["Active"],
    ) -> list[Company]:
        """
        List companies

        Supported API Versions: 1

        Returns:
            list[Company]: The list of companies.
        """
        request = ListCompanies()
        request.method_arguments = StatusFilterArguments(
            filter_by_status=filter_by_status
        )
        request.session_token = self.get_session_token(api_version=1)
        data = self._post(request)

        data["Content"] = cast(dict, data["Content"]).pop("Companies", [])
        return ListCompaniesResponse.model_validate(data).content

    # -------------------------------------------------------------------------
    # METHOD: list_departments
    # -------------------------------------------------------------------------

    def list_departments(
        self,
        *,
        filter_by_status: list[str] | None = ["Active"],
    ) -> list[Department]:
        """
        List departments

        Supported API Versions: 1

        Returns:
            list[Department]: The list of departments.
        """
        request = ListDepartments()
        request.method_arguments = StatusFilterArguments(
            filter_by_status=filter_by_status
        )
        request.session_token = self.get_session_token(api_version=1)
        data = self._post(request)

        data["Content"] = cast(dict, data["Content"]).pop("Departments", [])
        return ListDepartmentsResponse.model_validate(data).content

    # -------------------------------------------------------------------------
    # METHOD: list_invoice_formats
    # -------------------------------------------------------------------------

    def list_invoice_formats(
        self,
        *,
        filter_by_status: list[str] | None = ["Active"],
    ) -> list[InvoiceFormat]:
        """
        List invoice formats

        Supported API Versions: 1

        Returns:
            list[InvoiceFormat]: The list of invoice formats.
        """
        request = ListInvoiceFormats()
        request.method_arguments = StatusFilterArguments(
            filter_by_status=filter_by_status
        )
        request.session_token = self.get_session_token(api_version=1)
        data = self._post(request)

        data["Content"] = cast(dict, data["Content"]).pop("InvoiceFormats", [])
        return ListInvoiceFormatsResponse.model_validate(data).content

    # -------------------------------------------------------------------------
    # METHOD: list_payroll_taxes
    # -------------------------------------------------------------------------

    def list_payroll_taxes(
        self,
        *,
        filter_by_status: list[str] | None = ["Active"],
    ) -> list[PayrollTax]:
        """
        List payroll taxes

        Supported API Versions: 1

        Returns:
            list[PayrollTax]: The list of payroll taxes.
        """
        request = ListPayrollTaxes()
        request.method_arguments = StatusFilterArguments(
            filter_by_status=filter_by_status
        )
        request.session_token = self.get_session_token(api_version=1)
        data = self._post(request)

        data["Content"] = cast(dict, data["Content"]).pop("PayrollTaxes", [])
        return ListPayrollTaxesResponse.model_validate(data).content

    # -------------------------------------------------------------------------
    # METHOD: list_pays
    # -------------------------------------------------------------------------

    def list_pays(
        self,
        *,
        filter_by_status: list[str] | None = ["Active"],
    ) -> list[Pay]:
        """
        List pay types

        Supported API Versions: 1

        Returns:
            list[Pay]: The list of pay types.
        """
        request = ListPays()
        request.method_arguments = StatusFilterArguments(
            filter_by_status=filter_by_status
        )
        request.session_token = self.get_session_token(api_version=1)
        data = self._post(request)

        data["Content"] = cast(dict, data["Content"]).pop("Pays", [])
        return ListPaysResponse.model_validate(data).content

    # -------------------------------------------------------------------------
    # METHOD: list_rate_tables
    # -------------------------------------------------------------------------

    def list_rate_tables(
        self,
        *,
        filter_by_status: list[str] | None = ["Active"],
    ) -> list[RateTable]:
        """
        List rate tables

        Supported API Versions: 1

        Returns:
            list[RateTable]: The list of rate tables.
        """
        request = ListRateTables()
        request.method_arguments = StatusFilterArguments(
            filter_by_status=filter_by_status
        )
        request.session_token = self.get_session_token(api_version=1)
        data = self._post(request)

        data["Content"] = cast(dict, data["Content"]).pop("RateTables", [])
        return ListRateTablesResponse.model_validate(data).content

    # -------------------------------------------------------------------------
    # METHOD: list_wage_tables
    # -------------------------------------------------------------------------

    def list_wage_tables(
        self,
        *,
        filter_by_status: list[str] | None = ["Active"],
    ) -> list[WageTable]:
        """
        List wage tables

        Supported API Versions: 1

        Returns:
            list[WageTable]: The list of wage tables.
        """
        request = ListWageTables()
        request.method_arguments = StatusFilterArguments(
            filter_by_status=filter_by_status
        )
        request.session_token = self.get_session_token(api_version=1)
        data = self._post(request)

        data["Content"] = cast(dict, data["Content"]).pop("WageTables", [])
        return ListWageTablesResponse.model_validate(data).content

    # -------------------------------------------------------------------------
    # METHOD: list_chargeable_phases
    # -------------------------------------------------------------------------

    def list_chargeable_phases(self, project_key: int) -> list[ChargeablePhase]:
        """
        List the chargeable phases of a single project

        Supported API Versions: 2

        Returns:
            list[ChargeablePhase]: The project's chargeable phases.
        """
        request = ListChargeablePhases()
        request.method_arguments = ListChargeablePhasesArguments(
            project_key=project_key
        )
        request.session_token = self.get_session_token(api_version=2)
        data = self._post(request)

        data["Content"] = cast(dict, data["Content"]).pop("ChargeablePhases", [])
        return ListChargeablePhasesResponse.model_validate(data).content
