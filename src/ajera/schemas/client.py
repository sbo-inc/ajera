from typing import Any, Literal, override

from pydantic import Field

from ajera.schemas.generic import (
    GenericBaseModel,
    GenericRequest,
    GenericResponse,
)

# =============================================================================
# CLASS: ClientContact
# =============================================================================


class ClientContact(GenericBaseModel):
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
# CLASS: Client
# =============================================================================


class Client(GenericBaseModel):
    """
    Client schema for ListClients response
    """

    client_key: int = Field(
        default=0,
        alias="ClientKey",
        description="Unique client key.",
    )
    description: str = Field(
        default="",
        alias="Description",
        description="Client description (name).",
    )


# =============================================================================
# CLASS: ClientDetails
# =============================================================================


class ClientDetails(GenericBaseModel):
    """
    Detailed Client schema for GetClients response
    """

    client_key: int = Field(
        alias="ClientKey",
        description="Client key.",
    )
    last_modified_date: str | None = Field(
        default="",
        alias="LastModifiedDate",
        description="Last modified date.",
    )
    status: str = Field(
        default="",
        alias="Status",
        description="Status.",
    )
    description: str = Field(
        default="",
        alias="Description",
        description="Client description (name).",
    )
    date_established: str | None = Field(
        default=None,
        alias="DateEstablished",
        description="Date the client was established.",
    )
    send_statements: bool = Field(
        default=False,
        alias="SendStatements",
        description="Send statements flag.",
    )
    create_finance_charge: bool = Field(
        default=False,
        alias="CreateFinanceCharge",
        description="Create finance charge flag.",
    )
    annual_percentage_rate: float = Field(
        default=0.0,
        alias="AnnualPercentageRate",
        description="Annual percentage rate for finance charges.",
    )
    pre_payment_beginning_balance: float = Field(
        default=0.0,
        alias="PrePaymentBeginningBalance",
        description="Pre-payment beginning balance.",
    )
    account_id: str = Field(
        default="",
        alias="AccountID",
        description="Account ID.",
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
    email_statement_template_key: int | None = Field(
        default=None,
        alias="EmailStatementTemplateKey",
        description="Email statement template key.",
    )
    email_statement_template_description: str = Field(
        default="",
        alias="EmailStatementTemplateDescription",
        description="Email statement template description.",
    )
    contacts: list[ClientContact] | ClientContact | None = Field(
        default=None,
        alias="Contacts",
        description="List of contacts.",
    )
    notes: str = Field(
        default="",
        alias="Notes",
        description="Notes.",
    )
    client_type_key: int | None = Field(
        default=None,
        alias="ClientTypeKey",
        description="Client type key.",
    )
    client_type_description: str = Field(
        default="",
        alias="ClientTypeDescription",
        description="Client type description.",
    )
    client_type_notes: str = Field(
        default="",
        alias="ClientTypeNotes",
        description="Client type notes.",
    )
    invoice_delivery_preference: str = Field(
        default="",
        alias="InvoiceDeliveryPreference",
        description="Invoice delivery preference (e.g. Printed).",
    )


# =============================================================================
# CLASS: ListClientsArguments
# =============================================================================


class ListClientsArguments(GenericBaseModel):
    """
    Optional filter arguments for ListClients
    """

    filter_by_company: list[int] | None = Field(
        default=None,
        alias="FilterByCompany",
        description="Filter clients by company IDs.",
    )
    filter_by_status: list[str] | None = Field(
        default=None,
        alias="FilterByStatus",
        description="Filter clients by status values.",
    )
    filter_by_name_like: str | None = Field(
        default=None,
        alias="FilterByNameLike",
        description="Filter clients where the name contains the given substring.",
    )
    filter_by_name_equals: str | None = Field(
        default=None,
        alias="FilterByNameEquals",
        description="Filter clients where the name equals the given value.",
    )
    filter_by_client_type: list[int] | None = Field(
        default=None,
        alias="FilterByClientType",
        description="Filter clients by client type IDs.",
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
# CLASS: ListClients
# =============================================================================


class ListClients(GenericRequest[ListClientsArguments]):
    """
    List Clients request body
    """

    method: Literal["ListClients"] = Field(
        default="ListClients",
        alias="Method",
        description="API method name to invoke.",
        frozen=True,
    )


# =============================================================================
# CLASS: ListClientsResponse
# =============================================================================


class ListClientsResponse(GenericResponse[list[Client]]):
    """
    Response schema for ListClients
    """

    @override
    def model_post_init(self, context: Any) -> None:
        if self.content:
            # Sort the clients by description
            self.content.sort(key=lambda client: client.description)


# =============================================================================
# CLASS: GetClientsArguments
# =============================================================================


class GetClientsArguments(GenericBaseModel):
    """
    Optional filter arguments for GetClients
    """

    requested_clients: list[int] = Field(
        alias="RequestedClients",
        description="List of client IDs to retrieve.",
    )


# =============================================================================
# CLASS: GetClients
# =============================================================================


class GetClients(GenericRequest[GetClientsArguments]):
    """
    Get Clients request body
    """

    method: Literal["GetClients"] = Field(
        default="GetClients",
        alias="Method",
        description="API method name to invoke.",
        frozen=True,
    )


# =============================================================================
# CLASS: ClientType
# =============================================================================


class ClientType(GenericBaseModel):
    """
    Client type schema for ListClientTypes response
    """

    client_type_key: int = Field(
        default=0,
        alias="ClientTypeKey",
        description="Unique client type key.",
    )
    description: str = Field(
        default="",
        alias="Description",
        description="Client type description.",
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


# =============================================================================
# CLASS: ListClientTypesArguments
# =============================================================================


class ListClientTypesArguments(GenericBaseModel):
    """
    Optional filter arguments for ListClientTypes
    """

    filter_by_status: list[str] | None = Field(
        default=None,
        alias="FilterByStatus",
        description="Filter client types by status values (e.g. Active, Inactive).",
    )


# =============================================================================
# CLASS: ListClientTypes
# =============================================================================


class ListClientTypes(GenericRequest[ListClientTypesArguments]):
    """
    List Client Types request body
    """

    method: Literal["ListClientTypes"] = Field(
        default="ListClientTypes",
        alias="Method",
        description="API method name to invoke.",
        frozen=True,
    )


# =============================================================================
# CLASS: ListClientTypesResponse
# =============================================================================


class ListClientTypesResponse(GenericResponse[list[ClientType]]):
    """
    Response schema for ListClientTypes
    """

    @override
    def model_post_init(self, context: Any) -> None:
        if self.content:
            # Sort the client types by description
            self.content.sort(key=lambda client_type: client_type.description)


# =============================================================================
# CLASS: UpdatedClientResult
# =============================================================================


class UpdatedClientResult(ClientDetails):
    """
    Client record returned by UpdateClients.

    Extends the standard client detail with the two fields the API only
    populates on a write: `OriginalClientKey` (when a record was created)
    and `Deleted` (when a record was deleted).
    """

    original_client_key: int | None = Field(
        default=None,
        alias="OriginalClientKey",
        description="Negative key supplied on create, echoed back with the new key.",
    )
    deleted: bool | None = Field(
        default=None,
        alias="Deleted",
        description="Whether the record was deleted.",
    )


# =============================================================================
# CLASS: UpdateClientsArguments
# =============================================================================


class UpdateClientsArguments(GenericBaseModel):
    """
    Method arguments for UpdateClients.

    Both `UpdatedClients` and `UnchangedClients` are required by the API: the
    unchanged set is the baseline (e.g. from GetClients) and the updated set is
    the same baseline with the desired edits applied. (As with UpdateEmployees,
    and despite the published docs, these are NOT wrapped in a `Content`
    object.)
    """

    updated_clients: list[ClientDetails] = Field(
        default=[],
        alias="UpdatedClients",
        description="Clients with edits applied (negative key requests creation).",
    )
    unchanged_clients: list[ClientDetails] = Field(
        default=[],
        alias="UnchangedClients",
        description="Baseline client records, left untouched.",
    )
    use_single_transaction: bool = Field(
        default=False,
        alias="UseSingleTransaction",
        description="Apply all updates in one transaction; any failure rejects all.",
    )


# =============================================================================
# CLASS: UpdateClients
# =============================================================================


class UpdateClients(GenericRequest[UpdateClientsArguments]):
    """
    Update Clients request body
    """

    method: Literal["UpdateClients"] = Field(
        default="UpdateClients",
        alias="Method",
        description="API method name to invoke.",
        frozen=True,
    )


# =============================================================================
# CLASS: UpdateClientsResponseContent
# =============================================================================


class UpdateClientsResponseContent(GenericBaseModel):
    """
    Content payload returned by UpdateClients.
    """

    clients: list[UpdatedClientResult] = Field(
        default=[],
        alias="Clients",
        description="The resulting client records.",
    )
    number_of_clients_updated: int = Field(
        default=0,
        alias="NumberOfClientsUpdated",
        description="Count of clients updated.",
    )


# =============================================================================
# CLASS: UpdateClientsResponse
# =============================================================================


class UpdateClientsResponse(GenericResponse[UpdateClientsResponseContent]):
    """
    Response schema for UpdateClients
    """
