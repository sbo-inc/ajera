import json
import logging
import os
from typing import Any, cast

import httpx
from pydantic import BaseModel

from ajera.schemas.employee import (
    Employee,
    EmployeeDetails,
    GetEmployees,
    GetEmployeesArguments,
    ListEmployees,
    ListEmployeesArguments,
    ListEmployeesResponse,
)
from ajera.schemas.session import APISession, CreateAPISession

logger = logging.getLogger("ajera")
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("ajera: %(message)s"))
logger.addHandler(console_handler)
logging.getLogger("httpx").setLevel(logging.WARNING)


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
        self._client = httpx.Client(
            base_url=self.url,
            headers={"Content-Type": "application/json", **headers},
        )

        # Store the session tokens for caching
        self._session_tokens: dict[int, str] = {}

    @property
    def client(self) -> httpx.Client:
        return self._client

    # -------------------------------------------------------------------------
    # METHOD: _post
    # -------------------------------------------------------------------------

    def _post(self, request: BaseModel) -> dict[str, Any]:
        """
        Make a POST request to the Ajera API.

        Args:
            request: The request body to send.

        Returns:
            str: The decoded response content.
        """
        response = self.client.post(
            url="",
            content=request.model_dump_json(exclude_none=True, by_alias=True),
        )
        data: dict[str, Any] = json.loads(response.content.decode())

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
        response = httpx.Client().post(
            url=self.url,
            content=request.model_dump_json(exclude_none=True, by_alias=True),
        )
        session = APISession.model_validate_json(response.content.decode())
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
            ListEmployeesResponse: The response containing the list of employees.
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
        Get employee(s) by ID

        Supported API Versions: 1

        Returns:
            List[Employee]: A list of employees with the specified IDs.
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
