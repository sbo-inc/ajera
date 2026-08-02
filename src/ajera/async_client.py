import asyncio
from typing import Any, Self

import httpx
from pydantic import BaseModel

from ajera.operations import client as client_ops
from ajera.operations import contact as contact_ops
from ajera.operations import employee as employee_ops
from ajera.operations import ledger as ledger_ops
from ajera.operations import project as project_ops
from ajera.operations import reference as reference_ops
from ajera.operations import vendor as vendor_ops
from ajera.operations import vendor_invoice as vendor_invoice_ops
from ajera.operations.generic import Operation
from ajera.schemas.client import Client, ClientDetails, ClientType, UpdatedClientResult
from ajera.schemas.contact import (
    Contact,
    ContactDetails,
    ContactType,
    UpdatedContactResult,
)
from ajera.schemas.deduction import Deduction
from ajera.schemas.employee import (
    Employee,
    EmployeeDetails,
    EmployeeType,
    UpdatedEmployeeResult,
)
from ajera.schemas.fringe import Fringe
from ajera.schemas.ledger import LedgerAccount, LedgerAccountDetails
from ajera.schemas.project import (
    Project,
    ProjectTemplate,
    ProjectTemplateDetails,
    ProjectTotalsDetails,
    ProjectType,
)
from ajera.schemas.project_summary import ProjectSummary
from ajera.schemas.project_v2 import ProjectBundle
from ajera.schemas.reference import (
    AccountGroup,
    Activity,
    BankAccount,
    ChargeablePhase,
    Company,
    Department,
    InvoiceFormat,
    Pay,
    PayrollTax,
    RateTable,
    WageTable,
)
from ajera.schemas.session import APISession, APISessionContent
from ajera.schemas.vendor import UpdatedVendorResult, Vendor, VendorDetails, VendorType
from ajera.schemas.vendor_invoice import (
    VendorInvoice,
    VendorInvoiceBundle,
    VendorInvoiceLineItemCreate,
)
from ajera.transport import DEFAULT_TIMEOUT, BaseAjeraClient

__all__ = ["AsyncAjeraClient"]


# =============================================================================
# CLASS: AsyncAjeraClient
# =============================================================================


class AsyncAjeraClient(BaseAjeraClient):
    """
    Asynchronous Deltek Ajera Client

    Mirrors `AjeraClient` method for method, over `httpx.AsyncClient`. Both
    clients build the same operations and differ only in how they put them on
    the wire, so behaviour, arguments, and return types match exactly.

    One instance is meant to be shared across tasks: its connection pool and
    its session-token cache are both reused, and gathered calls on a cold cache
    log in once rather than once each.

    https://help.deltek.com/Product/Ajera/api/index.html
    """

    def __init__(
        self,
        url: str | None = None,
        username: str | None = None,
        password: str | None = None,
        headers: dict[str, str] = {},
        log: bool = False,
        timeout: float | tuple[float, float] | None = DEFAULT_TIMEOUT,
        retries: int | None = None,
    ) -> None:
        """
        Create a new asynchronous client for the Deltek Ajera API.

        Args:
            url: The base URL of the API (Environment: `AJERA_API_URL`)
            username: The username to authenticate with (Environment: `AJERA_API_USERNAME`)
            password: The password to authenticate with (Environment: `AJERA_API_PASSWORD`)
            headers: Additional headers to include in requests
            log: Enables request logging at INFO level
            timeout: Per-request timeout in seconds applied to every call.
                Accepts a single float, a `(connect, read)` tuple, or `None`
                to disable. Defaults to `DEFAULT_TIMEOUT`.
            retries: Number of times to retry connection-establishment
                failures, which is safe for the non-idempotent POSTs this
                client issues: a retry only ever happens before any bytes
                reach the server, so a create can never be double-submitted.
                `None` (default) disables retries.
        """
        super().__init__(
            url=url,
            username=username,
            password=password,
            log=log,
            timeout=timeout,
        )

        self._http = httpx.AsyncClient(
            headers={"Content-Type": "application/json", **headers},
            transport=httpx.AsyncHTTPTransport(retries=retries) if retries else None,
        )

        # Guards token minting so gathered callers on a cold cache log in once
        # rather than once each.
        self._token_lock = asyncio.Lock()

    @property
    def http(self) -> httpx.AsyncClient:
        """
        The underlying HTTP client.

        Returns:
            httpx.AsyncClient: The underlying HTTP client.
        """
        return self._http

    # -------------------------------------------------------------------------
    # METHOD: aclose
    # -------------------------------------------------------------------------

    async def aclose(self) -> None:
        """
        Close the underlying HTTP client and its connection pool.
        """
        await self._http.aclose()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.aclose()

    # -------------------------------------------------------------------------
    # METHOD: _post
    # -------------------------------------------------------------------------

    async def _post(
        self,
        request: BaseModel,
        exclude: set[str] | dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        POST a request and return the decoded JSON envelope.

        Raises on a non-200 ResponseCode. `exclude` omits fields from the
        serialized request body.

        Returns:
            dict[str, Any]: The decoded JSON response body.
        """
        response = await self._http.post(
            url=self._require_url(),
            content=request.model_dump_json(
                exclude_none=True, by_alias=True, exclude=exclude
            ),
            timeout=self._request_timeout(),
        )

        return self._decode(response)

    # -------------------------------------------------------------------------
    # METHOD: _run
    # -------------------------------------------------------------------------

    async def _run[T](self, operation: Operation[T]) -> T:
        """
        Authenticate, send, and parse one operation.

        Returns:
            T: Whatever the operation's parser produces.
        """
        operation.request.session_token = await self.get_session_token(
            operation.api_version
        )
        data = await self._post(operation.request, exclude=operation.exclude)

        return operation.parse(data)

    # -------------------------------------------------------------------------
    # METHOD: get_session_info
    # -------------------------------------------------------------------------

    async def get_session_info(self, api_version: int = 1) -> APISessionContent:
        """
        Get information about the calling user and the API session.

        Returns the CreateAPISession content: company, Ajera version,
        capability flags, and the calling employee's identity (empty for a
        service integration). The resulting token is cached for reuse.

        Supported API Versions: 1, 2

        Returns:
            APISessionContent: The session and calling-user information.
        """
        data = await self._post(self._login_request(api_version))
        content = APISession.model_validate(data).content

        if content.session_token:
            self._session_tokens[api_version] = content.session_token

        return content

    # -------------------------------------------------------------------------
    # METHOD: get_session_token
    # -------------------------------------------------------------------------

    async def get_session_token(self, api_version: int) -> str:
        """
        Get a session token for an API version, minting one if not cached.

        Returns:
            str: The session token.
        """
        token = self._session_tokens.get(api_version)
        if token:
            return token

        async with self._token_lock:
            token = self._session_tokens.get(api_version)
            if token:
                return token

            return (await self.get_session_info(api_version)).session_token

    # -------------------------------------------------------------------------
    # METHOD: list_employees
    # -------------------------------------------------------------------------

    async def list_employees(
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
        return await self._run(
            employee_ops.list_employees(
                filter_by_company=filter_by_company,
                filter_by_status=filter_by_status,
                filter_by_name_like=filter_by_name_like,
                filter_by_employee_type=filter_by_employee_type,
                filter_by_earliest_modified_date=filter_by_earliest_modified_date,
                filter_by_latest_modified_date=filter_by_latest_modified_date,
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: get_employees
    # -------------------------------------------------------------------------

    async def get_employees(self, employee_keys: list[int]) -> list[EmployeeDetails]:
        """
        Get employee(s) details by key

        Supported API Versions: 1

        Returns:
            list[EmployeeDetails]: A list of employees with the specified keys.
        """
        return await self._run(employee_ops.get_employees(employee_keys))

    # -------------------------------------------------------------------------
    # METHOD: list_employee_types
    # -------------------------------------------------------------------------

    async def list_employee_types(
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
        return await self._run(
            employee_ops.list_employee_types(filter_by_status=filter_by_status)
        )

    # -------------------------------------------------------------------------
    # METHOD: list_deductions
    # -------------------------------------------------------------------------

    async def list_deductions(
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
        return await self._run(
            employee_ops.list_deductions(filter_by_status=filter_by_status)
        )

    # -------------------------------------------------------------------------
    # METHOD: list_fringes
    # -------------------------------------------------------------------------

    async def list_fringes(
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
        return await self._run(
            employee_ops.list_fringes(filter_by_status=filter_by_status)
        )

    # -------------------------------------------------------------------------
    # METHOD: update_employee
    # -------------------------------------------------------------------------

    async def update_employee(
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

        Facade over the batch UpdateEmployees API: fetches the current record
        as the baseline, applies the non-None fields to a copy, and submits
        the two as the unchanged/updated pair. Edits that change nothing
        return the current record without the update call, which the API
        would reject. Structural data (pay rates, contacts, credit cards) is
        not editable here; manage it in Ajera directly.

        Supported API Versions: 1

        Returns:
            UpdatedEmployeeResult: The resulting employee record.
        """
        employees = await self.get_employees([employee_key])
        if not employees:
            raise ValueError(f"No employee found with key {employee_key}")
        baseline = employees[0]

        modified = employee_ops.apply_employee_edits(
            baseline,
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            title=title,
            email=email,
            website=website,
            primary_phone_number=primary_phone_number,
            secondary_phone_number=secondary_phone_number,
            tertiary_phone_number=tertiary_phone_number,
            fax_number=fax_number,
        )

        # The API rejects no-op updates; return the current record instead.
        if modified == baseline:
            return employee_ops.unchanged_employee_result(baseline)

        return await self._run(employee_ops.update_employee(baseline, modified))

    # -------------------------------------------------------------------------
    # METHOD: list_clients
    # -------------------------------------------------------------------------

    async def list_clients(
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
        return await self._run(
            client_ops.list_clients(
                filter_by_company=filter_by_company,
                filter_by_status=filter_by_status,
                filter_by_name_like=filter_by_name_like,
                filter_by_name_equals=filter_by_name_equals,
                filter_by_client_type=filter_by_client_type,
                filter_by_earliest_modified_date=filter_by_earliest_modified_date,
                filter_by_latest_modified_date=filter_by_latest_modified_date,
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: get_clients
    # -------------------------------------------------------------------------

    async def get_clients(self, client_keys: list[int]) -> list[ClientDetails]:
        """
        Get client(s) details by key

        Supported API Versions: 1

        Returns:
            list[ClientDetails]: A list of clients with the specified keys.
        """
        return await self._run(client_ops.get_clients(client_keys))

    # -------------------------------------------------------------------------
    # METHOD: list_client_types
    # -------------------------------------------------------------------------

    async def list_client_types(
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
        return await self._run(
            client_ops.list_client_types(filter_by_status=filter_by_status)
        )

    # -------------------------------------------------------------------------
    # METHOD: update_client
    # -------------------------------------------------------------------------

    async def update_client(
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

        Facade over the batch UpdateClients API: fetches the current record
        as the baseline, applies the non-None fields to a copy, and submits
        the two as the unchanged/updated pair. Edits that change nothing
        return the current record without the update call, which the API
        would reject. Structural data (contacts, addresses, finance-charge
        settings) is not editable here; manage it in Ajera directly.

        Supported API Versions: 1

        Returns:
            UpdatedClientResult: The resulting client record.
        """
        clients = await self.get_clients([client_key])
        if not clients:
            raise ValueError(f"No client found with key {client_key}")
        baseline = clients[0]

        modified = client_ops.apply_client_edits(
            baseline,
            description=description,
            account_id=account_id,
            email=email,
            website=website,
            primary_phone_number=primary_phone_number,
            secondary_phone_number=secondary_phone_number,
            tertiary_phone_number=tertiary_phone_number,
            fax_number=fax_number,
            notes=notes,
        )

        # The API rejects no-op updates; return the current record instead.
        if modified == baseline:
            return client_ops.unchanged_client_result(baseline)

        return await self._run(client_ops.update_client(baseline, modified))

    # -------------------------------------------------------------------------
    # METHOD: list_contacts
    # -------------------------------------------------------------------------

    async def list_contacts(
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
        return await self._run(
            contact_ops.list_contacts(
                filter_by_company=filter_by_company,
                filter_by_status=filter_by_status,
                filter_by_text=filter_by_text,
                filter_by_contact_type=filter_by_contact_type,
                filter_by_earliest_modified_date=filter_by_earliest_modified_date,
                filter_by_latest_modified_date=filter_by_latest_modified_date,
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: get_contacts
    # -------------------------------------------------------------------------

    async def get_contacts(self, contact_keys: list[int]) -> list[ContactDetails]:
        """
        Get contact(s) details by key

        Supported API Versions: 1

        Returns:
            list[ContactDetails]: A list of contacts with the specified keys.
        """
        return await self._run(contact_ops.get_contacts(contact_keys))

    # -------------------------------------------------------------------------
    # METHOD: list_contact_types
    # -------------------------------------------------------------------------

    async def list_contact_types(
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
        return await self._run(
            contact_ops.list_contact_types(filter_by_status=filter_by_status)
        )

    # -------------------------------------------------------------------------
    # METHOD: update_contact
    # -------------------------------------------------------------------------

    async def update_contact(
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

        Facade over the batch UpdateContacts API: fetches the current record
        as the baseline, applies the non-None fields to a copy, and submits
        the two as the unchanged/updated pair. Edits that change nothing
        return the current record without the update call, which the API
        would reject. Structural data (addresses, contact type) is not
        editable here; manage it in Ajera directly.

        Supported API Versions: 1

        Returns:
            UpdatedContactResult: The resulting contact record.
        """
        contacts = await self.get_contacts([contact_key])
        if not contacts:
            raise ValueError(f"No contact found with key {contact_key}")
        baseline = contacts[0]

        modified = contact_ops.apply_contact_edits(
            baseline,
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            title=title,
            company=company,
            email=email,
            website=website,
            primary_phone_number=primary_phone_number,
            secondary_phone_number=secondary_phone_number,
            tertiary_phone_number=tertiary_phone_number,
            fax_number=fax_number,
            notes=notes,
        )

        # The API rejects no-op updates; return the current record instead.
        if modified == baseline:
            return contact_ops.unchanged_contact_result(baseline)

        return await self._run(contact_ops.update_contact(baseline, modified))

    # -------------------------------------------------------------------------
    # METHOD: list_vendors
    # -------------------------------------------------------------------------

    async def list_vendors(
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
        return await self._run(
            vendor_ops.list_vendors(
                filter_by_company=filter_by_company,
                filter_by_status=filter_by_status,
                filter_by_name_like=filter_by_name_like,
                filter_by_vendor_type=filter_by_vendor_type,
                filter_by_earliest_modified_date=filter_by_earliest_modified_date,
                filter_by_latest_modified_date=filter_by_latest_modified_date,
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: get_vendors
    # -------------------------------------------------------------------------

    async def get_vendors(self, vendor_keys: list[int]) -> list[VendorDetails]:
        """
        Get vendor(s) details by key

        Supported API Versions: 1

        Returns:
            list[VendorDetails]: A list of vendors with the specified keys.
        """
        return await self._run(vendor_ops.get_vendors(vendor_keys))

    # -------------------------------------------------------------------------
    # METHOD: list_vendor_types
    # -------------------------------------------------------------------------

    async def list_vendor_types(
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
        return await self._run(
            vendor_ops.list_vendor_types(
                filter_by_status=filter_by_status,
                filter_by_is_credit_card=filter_by_is_credit_card,
                filter_by_is_consultant=filter_by_is_consultant,
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: update_vendor
    # -------------------------------------------------------------------------

    async def update_vendor(
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

        Facade over the batch UpdateVendors API: fetches the current record
        as the baseline, applies the non-None fields to a copy, and submits
        the two as the unchanged/updated pair. Edits that change nothing
        return the current record without the update call, which the API
        would reject. Structural data (contacts, addresses, 1099/W-9
        settings, payment scheduling) is not editable here; manage it in
        Ajera directly.

        Supported API Versions: 1

        Returns:
            UpdatedVendorResult: The resulting vendor record.
        """
        vendors = await self.get_vendors([vendor_key])
        if not vendors:
            raise ValueError(f"No vendor found with key {vendor_key}")
        baseline = vendors[0]

        modified = vendor_ops.apply_vendor_edits(
            baseline,
            name=name,
            vendor_account_id=vendor_account_id,
            email=email,
            website=website,
            primary_phone_number=primary_phone_number,
            secondary_phone_number=secondary_phone_number,
            tertiary_phone_number=tertiary_phone_number,
            fax_number=fax_number,
            notes=notes,
        )

        # The API rejects no-op updates; return the current record instead.
        if modified == baseline:
            return vendor_ops.unchanged_vendor_result(baseline)

        return await self._run(vendor_ops.update_vendor(baseline, modified))

    # -------------------------------------------------------------------------
    # METHOD: list_vendor_invoices
    # -------------------------------------------------------------------------

    async def list_vendor_invoices(
        self,
        *,
        with_payment_status: bool = False,
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

        Ajera reports no payment property on any vendor invoice response and
        exposes payment state only through the paid/unpaid/voided filters. Pass
        `with_payment_status=True` to have the client derive it and populate
        `VendorInvoice.payment`; it stays None otherwise, since a derived value
        should not look like a reported one. Deriving it costs one additional
        request (the API appears to cap near 9 calls per second), so leave it
        off when the payment state is not needed.

        Supported API Versions: 2

        Returns:
            list[VendorInvoice]: The matching vendor invoice headers.
        """
        arguments = vendor_invoice_ops.list_vendor_invoices_arguments(
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

        invoices = await self._run(vendor_invoice_ops.list_vendor_invoices(arguments))

        if with_payment_status:
            paid = vendor_invoice_ops.paid_keys_or_query(arguments, invoices)
            if not isinstance(paid, set):
                paid = {
                    invoice.vendor_invoice_key
                    for invoice in await self._run(
                        vendor_invoice_ops.list_vendor_invoices(paid)
                    )
                }
            vendor_invoice_ops.assign_payment_status(invoices, paid)

        return invoices

    # -------------------------------------------------------------------------
    # METHOD: get_vendor_invoices
    # -------------------------------------------------------------------------

    async def get_vendor_invoices(self, invoice_keys: list[int]) -> VendorInvoiceBundle:
        """
        Get vendor invoice(s) by key, with their line items

        Returns a bundle of invoice headers and line items; line items are
        linked to their header by VendorInvoiceKey.

        Supported API Versions: 2

        Returns:
            VendorInvoiceBundle: The invoice headers and line items.
        """
        return await self._run(vendor_invoice_ops.get_vendor_invoices(invoice_keys))

    # -------------------------------------------------------------------------
    # METHOD: create_vendor_invoice
    # -------------------------------------------------------------------------

    async def create_vendor_invoice(
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
        return await self._run(
            vendor_invoice_ops.create_vendor_invoice(
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
        )

    # -------------------------------------------------------------------------
    # METHOD: list_projects
    # -------------------------------------------------------------------------

    async def list_projects(
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
        return await self._run(
            project_ops.list_projects(
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
        )

    # -------------------------------------------------------------------------
    # METHOD: get_projects
    # -------------------------------------------------------------------------

    async def get_projects(self, project_keys: list[int]) -> ProjectBundle:
        """
        Get project(s) by key, with phases, invoice groups, and resources

        The v2 bundle is flat parallel arrays (projects, invoice groups,
        phases, resources) linked by foreign keys.

        Supported API Versions: 2

        Returns:
            ProjectBundle: The projects and their related records.
        """
        return await self._run(project_ops.get_projects(project_keys))

    # -------------------------------------------------------------------------
    # METHOD: get_project_totals
    # -------------------------------------------------------------------------

    async def get_project_totals(self, project_key: int) -> ProjectTotalsDetails:
        """
        Get a single project's details enriched with financial totals

        Unlike the other Get* methods, GetProjectTotals accepts a single
        project key, not a list.

        Supported API Versions: 1

        Returns:
            ProjectTotalsDetails: The project with project-level totals.
        """
        return await self._run(project_ops.get_project_totals(project_key))

    # -------------------------------------------------------------------------
    # METHOD: get_project_summary
    # -------------------------------------------------------------------------

    async def get_project_summary(
        self,
        project_key: int,
        *,
        subphases: bool = True,
    ) -> ProjectSummary:
        """
        Get a consolidated, chart-ready overview of a single project

        Synthesizes the v2 GetProjects bundle and GetProjectTotals into one
        derived view (identity, people, schedule, contract, budget, phases,
        resources, financials, and computed health ratios), not a 1:1 mirror
        of any single API method.

        Phases form a tree; with `subphases` False each phase's `children` is
        emptied (`subphase_count` is retained).

        Supported API Versions: 1, 2 (one call each)

        Returns:
            ProjectSummary: The consolidated project overview.
        """
        bundle = await self.get_projects([project_key])
        totals = (await self.get_project_totals(project_key)).totals

        return project_ops.build_project_summary(bundle, totals, subphases=subphases)

    # -------------------------------------------------------------------------
    # METHOD: list_project_types
    # -------------------------------------------------------------------------

    async def list_project_types(
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
        return await self._run(
            project_ops.list_project_types(filter_by_status=filter_by_status)
        )

    # -------------------------------------------------------------------------
    # METHOD: list_project_templates
    # -------------------------------------------------------------------------

    async def list_project_templates(
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
        return await self._run(
            project_ops.list_project_templates(
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
        )

    # -------------------------------------------------------------------------
    # METHOD: get_project_templates
    # -------------------------------------------------------------------------

    async def get_project_templates(
        self, template_keys: list[int]
    ) -> list[ProjectTemplateDetails]:
        """
        Get project template(s) details by key

        Supported API Versions: 1

        Returns:
            list[ProjectTemplateDetails]: A list of templates with the given keys.
        """
        return await self._run(project_ops.get_project_templates(template_keys))

    # -------------------------------------------------------------------------
    # METHOD: update_project
    # -------------------------------------------------------------------------

    async def update_project(
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

        Facade over the v2 UpdateProjects API: fetches the current bundle as
        the unchanged baseline and submits the non-None fields as the delta.
        If no fields are given, the current bundle is returned without the
        update call. Structural data (phases, invoice groups, resources,
        contract amounts) is not editable here; manage it in Ajera directly.

        Supported API Versions: 2

        Returns:
            ProjectBundle: The updated project bundle.
        """
        data = await self._run(project_ops.get_projects_raw([project_key]))
        baseline = project_ops.project_baseline(data, project_key)

        operation = project_ops.update_project(
            project_key,
            baseline,
            description=description,
            project_id=project_id,
            location=location,
            billing_description=billing_description,
            notes=notes,
        )
        if operation is None:
            return project_ops.parse_project_bundle(data)

        return await self._run(operation)

    # -------------------------------------------------------------------------
    # METHOD: create_project
    # -------------------------------------------------------------------------

    async def create_project(
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

        A project cannot be created on its own, so one invoice group (billed
        to `client_key` with `invoice_format_key`) and one phase are created
        with it; their descriptions are required and default to the project
        description.

        Supported API Versions: 2

        Returns:
            ProjectBundle: The created project bundle.
        """
        return await self._run(
            project_ops.create_project(
                description,
                billing_type=billing_type,
                rate_table_key=rate_table_key,
                client_key=client_key,
                invoice_format_key=invoice_format_key,
                company_key=company_key,
                invoice_group_description=invoice_group_description,
                phase_description=phase_description,
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: list_ledger_accounts
    # -------------------------------------------------------------------------

    async def list_ledger_accounts(
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
        return await self._run(
            ledger_ops.list_ledger_accounts(
                filter_by_account_group=filter_by_account_group,
                filter_by_status=filter_by_status,
                filter_by_type=filter_by_type,
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: get_ledger_accounts
    # -------------------------------------------------------------------------

    async def get_ledger_accounts(
        self,
        account_keys: list[int] | None = None,
        *,
        exclude_close_year_entries: bool | None = None,
        as_of_date: str | None = None,
        filter_by_account_group: list[int] | None = None,
        filter_by_status: list[str] | None = None,
        filter_by_type: list[str] | None = None,
    ) -> list[LedgerAccountDetails]:
        """
        Get general ledger account details, with calculated amounts

        Pass `account_keys` to select specific accounts, or omit to return all.
        `as_of_date` calculates balances as of that date, and
        `exclude_close_year_entries` omits close-year entries from the amounts.

        Supported API Versions: 1

        Returns:
            list[LedgerAccountDetails]: The requested accounts with amounts.
        """
        return await self._run(
            ledger_ops.get_ledger_accounts(
                account_keys,
                exclude_close_year_entries=exclude_close_year_entries,
                as_of_date=as_of_date,
                filter_by_account_group=filter_by_account_group,
                filter_by_status=filter_by_status,
                filter_by_type=filter_by_type,
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: list_account_groups
    # -------------------------------------------------------------------------

    async def list_account_groups(
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
        return await self._run(
            ledger_ops.list_account_groups(filter_by_status=filter_by_status)
        )

    # -------------------------------------------------------------------------
    # METHOD: list_activities
    # -------------------------------------------------------------------------

    async def list_activities(
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
        return await self._run(
            reference_ops.list_activities(
                filter_by_status=filter_by_status,
                filter_by_description_like=filter_by_description_like,
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: list_bank_accounts
    # -------------------------------------------------------------------------

    async def list_bank_accounts(
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
        return await self._run(
            reference_ops.list_bank_accounts(filter_by_status=filter_by_status)
        )

    # -------------------------------------------------------------------------
    # METHOD: list_companies
    # -------------------------------------------------------------------------

    async def list_companies(
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
        return await self._run(
            reference_ops.list_companies(filter_by_status=filter_by_status)
        )

    # -------------------------------------------------------------------------
    # METHOD: list_departments
    # -------------------------------------------------------------------------

    async def list_departments(
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
        return await self._run(
            reference_ops.list_departments(filter_by_status=filter_by_status)
        )

    # -------------------------------------------------------------------------
    # METHOD: list_invoice_formats
    # -------------------------------------------------------------------------

    async def list_invoice_formats(
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
        return await self._run(
            reference_ops.list_invoice_formats(filter_by_status=filter_by_status)
        )

    # -------------------------------------------------------------------------
    # METHOD: list_payroll_taxes
    # -------------------------------------------------------------------------

    async def list_payroll_taxes(
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
        return await self._run(
            reference_ops.list_payroll_taxes(filter_by_status=filter_by_status)
        )

    # -------------------------------------------------------------------------
    # METHOD: list_pays
    # -------------------------------------------------------------------------

    async def list_pays(
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
        return await self._run(
            reference_ops.list_pays(filter_by_status=filter_by_status)
        )

    # -------------------------------------------------------------------------
    # METHOD: list_rate_tables
    # -------------------------------------------------------------------------

    async def list_rate_tables(
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
        return await self._run(
            reference_ops.list_rate_tables(filter_by_status=filter_by_status)
        )

    # -------------------------------------------------------------------------
    # METHOD: list_wage_tables
    # -------------------------------------------------------------------------

    async def list_wage_tables(
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
        return await self._run(
            reference_ops.list_wage_tables(filter_by_status=filter_by_status)
        )

    # -------------------------------------------------------------------------
    # METHOD: list_chargeable_phases
    # -------------------------------------------------------------------------

    async def list_chargeable_phases(self, project_key: int) -> list[ChargeablePhase]:
        """
        List the chargeable phases of a single project

        Supported API Versions: 2

        Returns:
            list[ChargeablePhase]: The project's chargeable phases.
        """
        return await self._run(reference_ops.list_chargeable_phases(project_key))
