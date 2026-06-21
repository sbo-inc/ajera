from typing import Any, Literal, override

from pydantic import Field

from ajera.schemas.generic import (
    GenericBaseModel,
    GenericRequest,
    GenericResponse,
)

# =============================================================================
# CLASS: Contact
# =============================================================================


class Contact(GenericBaseModel):
    """
    Contact schema for ListContacts response
    """

    contact_key: int = Field(
        default=0,
        alias="ContactKey",
        description="Unique contact key.",
    )
    first_name: str = Field(
        default="",
        alias="FirstName",
        description="Contact first name.",
    )
    middle_name: str = Field(
        default="",
        alias="MiddleName",
        description="Contact middle name.",
    )
    last_name: str = Field(
        default="",
        alias="LastName",
        description="Contact last name.",
    )
    company: str = Field(
        default="",
        alias="Company",
        description="Contact company.",
    )


# =============================================================================
# CLASS: ContactDetails
# =============================================================================


class ContactDetails(GenericBaseModel):
    """
    Detailed Contact schema for GetContacts response
    """

    contact_key: int = Field(
        alias="ContactKey",
        description="Contact key.",
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
    company: str = Field(
        default="",
        alias="Company",
        description="Company.",
    )
    title: str = Field(
        default="",
        alias="Title",
        description="Title.",
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
    notes: str = Field(
        default="",
        alias="Notes",
        description="Notes.",
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
    contact_type_key: int | None = Field(
        default=None,
        alias="ContactTypeKey",
        description="Contact type key.",
    )
    contact_type_description: str | None = Field(
        default=None,
        alias="ContactTypeDescription",
        description="Contact type description (null when the contact has no type).",
    )
    contact_type_notes: str | None = Field(
        default=None,
        alias="ContactTypeNotes",
        description="Contact type notes (null when the contact has no type).",
    )
    contact_client_key: int | None = Field(
        default=None,
        alias="ContactClientKey",
        description="Key of the client this contact is linked to, if any.",
    )
    contact_client_description: str | None = Field(
        default=None,
        alias="ContactClientDescription",
        description="Description of the linked client, if any.",
    )
    contact_vendor_key: int | None = Field(
        default=None,
        alias="ContactVendorKey",
        description="Key of the vendor this contact is linked to, if any.",
    )
    contact_vendor_description: str | None = Field(
        default=None,
        alias="ContactVendorDescription",
        description="Description of the linked vendor, if any.",
    )


# =============================================================================
# CLASS: ListContactsArguments
# =============================================================================


class ListContactsArguments(GenericBaseModel):
    """
    Optional filter arguments for ListContacts
    """

    filter_by_company: list[int] | None = Field(
        default=None,
        alias="FilterByCompany",
        description="Filter contacts by company IDs.",
    )
    filter_by_status: list[str] | None = Field(
        default=None,
        alias="FilterByStatus",
        description="Filter contacts by status values.",
    )
    filter_by_text: str | None = Field(
        default=None,
        alias="FilterByText",
        description="Filter contacts where the text contains the given substring.",
    )
    filter_by_contact_type: list[int] | None = Field(
        default=None,
        alias="FilterByContactType",
        description="Filter contacts by contact type IDs.",
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
# CLASS: ListContacts
# =============================================================================


class ListContacts(GenericRequest[ListContactsArguments]):
    """
    List Contacts request body
    """

    method: Literal["ListContacts"] = Field(
        default="ListContacts",
        alias="Method",
        description="API method name to invoke.",
        frozen=True,
    )


# =============================================================================
# CLASS: ListContactsResponse
# =============================================================================


class ListContactsResponse(GenericResponse[list[Contact]]):
    """
    Response schema for ListContacts
    """

    @override
    def model_post_init(self, context: Any) -> None:
        if self.content:
            # Sort the contacts by last name, then first name
            self.content.sort(
                key=lambda contact: (contact.last_name, contact.first_name)
            )


# =============================================================================
# CLASS: GetContactsArguments
# =============================================================================


class GetContactsArguments(GenericBaseModel):
    """
    Optional filter arguments for GetContacts
    """

    requested_contacts: list[int] = Field(
        alias="RequestedContacts",
        description="List of contact IDs to retrieve.",
    )


# =============================================================================
# CLASS: GetContacts
# =============================================================================


class GetContacts(GenericRequest[GetContactsArguments]):
    """
    Get Contacts request body
    """

    method: Literal["GetContacts"] = Field(
        default="GetContacts",
        alias="Method",
        description="API method name to invoke.",
        frozen=True,
    )


# =============================================================================
# CLASS: ContactType
# =============================================================================


class ContactType(GenericBaseModel):
    """
    Contact type schema for ListContactTypes response
    """

    contact_type_key: int = Field(
        default=0,
        alias="ContactTypeKey",
        description="Unique contact type key.",
    )
    description: str = Field(
        default="",
        alias="Description",
        description="Contact type description.",
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
# CLASS: ListContactTypesArguments
# =============================================================================


class ListContactTypesArguments(GenericBaseModel):
    """
    Optional filter arguments for ListContactTypes
    """

    filter_by_status: list[str] | None = Field(
        default=None,
        alias="FilterByStatus",
        description="Filter contact types by status values (e.g. Active, Inactive).",
    )


# =============================================================================
# CLASS: ListContactTypes
# =============================================================================


class ListContactTypes(GenericRequest[ListContactTypesArguments]):
    """
    List Contact Types request body
    """

    method: Literal["ListContactTypes"] = Field(
        default="ListContactTypes",
        alias="Method",
        description="API method name to invoke.",
        frozen=True,
    )


# =============================================================================
# CLASS: ListContactTypesResponse
# =============================================================================


class ListContactTypesResponse(GenericResponse[list[ContactType]]):
    """
    Response schema for ListContactTypes
    """

    @override
    def model_post_init(self, context: Any) -> None:
        if self.content:
            # Sort the contact types by description
            self.content.sort(key=lambda contact_type: contact_type.description)


# =============================================================================
# CLASS: UpdatedContactResult
# =============================================================================


class UpdatedContactResult(ContactDetails):
    """
    Contact record returned by UpdateContacts.

    Extends the standard contact detail with the two fields the API only
    populates on a write: `OriginalContactKey` (when a record was created)
    and `Deleted` (when a record was deleted).
    """

    original_contact_key: int | None = Field(
        default=None,
        alias="OriginalContactKey",
        description="Negative key supplied on create, echoed back with the new key.",
    )
    deleted: bool | None = Field(
        default=None,
        alias="Deleted",
        description="Whether the record was deleted.",
    )


# =============================================================================
# CLASS: UpdateContactsArguments
# =============================================================================


class UpdateContactsArguments(GenericBaseModel):
    """
    Method arguments for UpdateContacts.

    Both `UpdatedContacts` and `UnchangedContacts` are required by the API: the
    unchanged set is the baseline (e.g. from GetContacts) and the updated set is
    the same baseline with the desired edits applied. (As with UpdateEmployees,
    and despite the published docs, these are NOT wrapped in a `Content`
    object.)
    """

    updated_contacts: list[ContactDetails] = Field(
        default=[],
        alias="UpdatedContacts",
        description="Contacts with edits applied (negative key requests creation).",
    )
    unchanged_contacts: list[ContactDetails] = Field(
        default=[],
        alias="UnchangedContacts",
        description="Baseline contact records, left untouched.",
    )
    use_single_transaction: bool = Field(
        default=False,
        alias="UseSingleTransaction",
        description="Apply all updates in one transaction; any failure rejects all.",
    )


# =============================================================================
# CLASS: UpdateContacts
# =============================================================================


class UpdateContacts(GenericRequest[UpdateContactsArguments]):
    """
    Update Contacts request body
    """

    method: Literal["UpdateContacts"] = Field(
        default="UpdateContacts",
        alias="Method",
        description="API method name to invoke.",
        frozen=True,
    )


# =============================================================================
# CLASS: UpdateContactsResponseContent
# =============================================================================


class UpdateContactsResponseContent(GenericBaseModel):
    """
    Content payload returned by UpdateContacts.
    """

    contacts: list[UpdatedContactResult] = Field(
        default=[],
        alias="Contacts",
        description="The resulting contact records.",
    )
    number_of_contacts_updated: int = Field(
        default=0,
        alias="NumberOfContactsUpdated",
        description="Count of contacts updated.",
    )


# =============================================================================
# CLASS: UpdateContactsResponse
# =============================================================================


class UpdateContactsResponse(GenericResponse[UpdateContactsResponseContent]):
    """
    Response schema for UpdateContacts
    """
