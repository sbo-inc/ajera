import json
import logging
import os
from typing import Any, cast

import requests
from pydantic import BaseModel

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
from ajera.schemas.session import APISession, CreateAPISession

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

    url: str
    username: str
    password: str

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

        if not url:
            url = os.environ.get("AJERA_API_URL", None)
        if not url:
            raise ValueError("No URL provided")

        if not username:
            username = os.environ.get("AJERA_API_USERNAME", None)
        if not username:
            raise ValueError("No username provided")

        if not password:
            password = os.environ.get("AJERA_API_PASSWORD", None)
        if not password:
            raise ValueError("No password provided")

        # Assign to instance variables
        self.url = url
        self.username = username
        self.password = password

        # Create the client instance
        self._session = requests.Session()
        self._session.headers.update({"Content-Type": "application/json", **headers})

        # Store the session tokens for caching
        self._session_tokens: dict[int, str] = {}

    @property
    def session(self) -> requests.Session:
        return self._session

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
            url=self.url,
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

        request = CreateAPISession(
            username=self.username,
            password=self.password,
            api_version=api_version,
        )

        # Use a new client for each session request
        response = requests.post(
            url=self.url,
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
        filter_by_status: list[str] | None = None,
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
        data["Content"]: list = cast(dict, data["Content"]).pop("Employees", [])

        return [EmployeeDetails.model_validate(e) for e in data["Content"]]

    # -------------------------------------------------------------------------
    # METHOD: list_employee_types
    # -------------------------------------------------------------------------

    def list_employee_types(
        self,
        *,
        filter_by_status: list[str] | None = None,
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
        filter_by_status: list[str] | None = None,
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
        filter_by_status: list[str] | None = None,
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
