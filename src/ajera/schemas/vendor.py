from typing import Any, Literal, override

from pydantic import Field

from ajera.schemas.generic import (
    GenericBaseModel,
    GenericRequest,
    GenericResponse,
)

# =============================================================================
# CLASS: VendorContact
# =============================================================================


class VendorContact(GenericBaseModel):
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
# CLASS: Vendor
# =============================================================================


class Vendor(GenericBaseModel):
    """
    Vendor schema for ListVendors response
    """

    vendor_key: int = Field(
        default=0,
        alias="VendorKey",
        description="Unique vendor key.",
    )
    name: str = Field(
        default="",
        alias="Name",
        description="Vendor name.",
    )


# =============================================================================
# CLASS: VendorDetails
# =============================================================================


class VendorDetails(GenericBaseModel):
    """
    Detailed Vendor schema for GetVendors response
    """

    vendor_key: int = Field(
        alias="VendorKey",
        description="Vendor key.",
    )
    last_modified_date: str | None = Field(
        default="",
        alias="LastModifiedDate",
        description="Last modified date.",
    )
    name: str = Field(
        default="",
        alias="Name",
        description="Vendor name.",
    )
    status: str = Field(
        default="",
        alias="Status",
        description="Status.",
    )
    date_established: str | None = Field(
        default=None,
        alias="DateEstablished",
        description="Date the vendor was established.",
    )
    receives_1099_form: bool = Field(
        default=False,
        alias="Receives1099Form",
        description="Whether the vendor receives a 1099 form.",
    )
    form_type_1099: str = Field(
        default="",
        alias="FormType1099",
        description="1099 form type (e.g. Rents).",
    )
    recipient_id_1099: str = Field(
        default="",
        alias="RecipientID1099",
        description="1099 recipient ID.",
    )
    recipient_name_1099: str = Field(
        default="",
        alias="RecipientName1099",
        description="1099 recipient name.",
    )
    reported_amount_1099: float = Field(
        default=0.0,
        alias="ReportedAmount1099",
        description="1099 reported amount.",
    )
    # Field name preserves the API's spelling ("Witheld").
    federal_tax_witheld: float = Field(
        default=0.0,
        alias="FederalTaxWitheld",
        description="Federal tax withheld.",
    )
    receives_w9_form: bool = Field(
        default=False,
        alias="ReceivesW9Form",
        description="Whether the vendor receives a W-9 form.",
    )
    # Field name preserves the API's spelling ("Buisness").
    buisness_type_w9: str = Field(
        default="",
        alias="BuisnessTypeW9",
        description="W-9 business type (e.g. Individual/Sole Proprietor).",
    )
    other_description_w9: str = Field(
        default="",
        alias="OtherDescriptionW9",
        description="W-9 other description.",
    )
    department_key: int | None = Field(
        default=None,
        alias="DepartmentKey",
        description="Department key.",
    )
    department_description: str | None = Field(
        default=None,
        alias="DepartmentDescription",
        description="Department description.",
    )
    account_key: int | None = Field(
        default=None,
        alias="AccountKey",
        description="Account key.",
    )
    account_description: str | None = Field(
        default=None,
        alias="AccountDescription",
        description="Account description.",
    )
    account_id: str | None = Field(
        default=None,
        alias="AccountID",
        description="Account ID.",
    )
    vendor_account_id: str = Field(
        default="",
        alias="VendorAccountID",
        description="The account number assigned to you by the vendor.",
    )
    remittance_contact: str | None = Field(
        default=None,
        alias="RemittanceContact",
        description="Remittance contact.",
    )
    remittance_contact_email: str | None = Field(
        default=None,
        alias="RemittanceContactEmail",
        description="Remittance contact email.",
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
    contacts: list[VendorContact] | VendorContact | None = Field(
        default=None,
        alias="Contacts",
        description="List of contacts.",
    )
    notes: str = Field(
        default="",
        alias="Notes",
        description="Notes.",
    )
    vendor_type_key: int | None = Field(
        default=None,
        alias="VendorTypeKey",
        description="Vendor type key.",
    )
    vendor_type_description: str = Field(
        default="",
        alias="VendorTypeDescription",
        description="Vendor type description.",
    )
    vendor_type_is_consultant: bool = Field(
        default=False,
        alias="VendorTypeIsConsultant",
        description="Whether the vendor type is a consultant.",
    )
    vendor_type_is_credit_card: bool = Field(
        default=False,
        alias="VendorTypeIsCreditCard",
        description="Whether the vendor type is a credit card.",
    )
    vendor_type_notes: str = Field(
        default="",
        alias="VendorTypeNotes",
        description="Vendor type notes.",
    )


# =============================================================================
# CLASS: ListVendorsArguments
# =============================================================================


class ListVendorsArguments(GenericBaseModel):
    """
    Optional filter arguments for ListVendors
    """

    filter_by_company: list[int] | None = Field(
        default=None,
        alias="FilterByCompany",
        description="Filter vendors by company IDs.",
    )
    filter_by_status: list[str] | None = Field(
        default=None,
        alias="FilterByStatus",
        description="Filter vendors by status values.",
    )
    filter_by_name_like: str | None = Field(
        default=None,
        alias="FilterByNameLike",
        description="Filter vendors where the name contains the given substring.",
    )
    filter_by_vendor_type: list[int] | None = Field(
        default=None,
        alias="FilterByVendorType",
        description="Filter vendors by vendor type IDs.",
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
# CLASS: ListVendors
# =============================================================================


class ListVendors(GenericRequest[ListVendorsArguments]):
    """
    List Vendors request body
    """

    method: Literal["ListVendors"] = Field(
        default="ListVendors",
        alias="Method",
        description="API method name to invoke.",
        frozen=True,
    )


# =============================================================================
# CLASS: ListVendorsResponse
# =============================================================================


class ListVendorsResponse(GenericResponse[list[Vendor]]):
    """
    Response schema for ListVendors
    """

    @override
    def model_post_init(self, context: Any) -> None:
        if self.content:
            # Sort the vendors by name
            self.content.sort(key=lambda vendor: vendor.name)


# =============================================================================
# CLASS: GetVendorsArguments
# =============================================================================


class GetVendorsArguments(GenericBaseModel):
    """
    Optional filter arguments for GetVendors
    """

    requested_vendors: list[int] = Field(
        alias="RequestedVendors",
        description="List of vendor IDs to retrieve.",
    )


# =============================================================================
# CLASS: GetVendors
# =============================================================================


class GetVendors(GenericRequest[GetVendorsArguments]):
    """
    Get Vendors request body
    """

    method: Literal["GetVendors"] = Field(
        default="GetVendors",
        alias="Method",
        description="API method name to invoke.",
        frozen=True,
    )


# =============================================================================
# CLASS: GetVendorsResponse
# =============================================================================


class GetVendorsResponse(GenericResponse[list[VendorDetails]]):
    """
    Response schema for GetVendors
    """


# =============================================================================
# CLASS: VendorType
# =============================================================================


class VendorType(GenericBaseModel):
    """
    Vendor type schema for ListVendorTypes response
    """

    vendor_type_key: int = Field(
        default=0,
        alias="VendorTypeKey",
        description="Unique vendor type key.",
    )
    description: str = Field(
        default="",
        alias="Description",
        description="Vendor type description.",
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
# CLASS: ListVendorTypesArguments
# =============================================================================


class ListVendorTypesArguments(GenericBaseModel):
    """
    Optional filter arguments for ListVendorTypes
    """

    filter_by_status: list[str] | None = Field(
        default=None,
        alias="FilterByStatus",
        description="Filter vendor types by status values (e.g. Active, Inactive).",
    )
    filter_by_is_credit_card: list[bool] | None = Field(
        default=None,
        alias="FilterByIsCreditCard",
        description="Filter vendor types by their credit-card flag.",
    )
    filter_by_is_consultant: list[bool] | None = Field(
        default=None,
        alias="FilterByIsConsultant",
        description="Filter vendor types by their consultant flag.",
    )


# =============================================================================
# CLASS: ListVendorTypes
# =============================================================================


class ListVendorTypes(GenericRequest[ListVendorTypesArguments]):
    """
    List Vendor Types request body
    """

    method: Literal["ListVendorTypes"] = Field(
        default="ListVendorTypes",
        alias="Method",
        description="API method name to invoke.",
        frozen=True,
    )


# =============================================================================
# CLASS: ListVendorTypesResponse
# =============================================================================


class ListVendorTypesResponse(GenericResponse[list[VendorType]]):
    """
    Response schema for ListVendorTypes
    """

    @override
    def model_post_init(self, context: Any) -> None:
        if self.content:
            # Sort the vendor types by description
            self.content.sort(key=lambda vendor_type: vendor_type.description)


# =============================================================================
# CLASS: UpdatedVendorResult
# =============================================================================


class UpdatedVendorResult(VendorDetails):
    """
    Vendor record returned by UpdateVendors.

    Extends the standard vendor detail with the two fields the API only
    populates on a write: `OriginalVendorKey` (when a record was created)
    and `Deleted` (when a record was deleted).
    """

    original_vendor_key: int | None = Field(
        default=None,
        alias="OriginalVendorKey",
        description="Negative key supplied on create, echoed back with the new key.",
    )
    deleted: bool | None = Field(
        default=None,
        alias="Deleted",
        description="Whether the record was deleted.",
    )


# =============================================================================
# CLASS: UpdateVendorsArguments
# =============================================================================


class UpdateVendorsArguments(GenericBaseModel):
    """
    Method arguments for UpdateVendors.

    Both `UpdatedVendors` and `UnchangedVendors` are required by the API: the
    unchanged set is the baseline (e.g. from GetVendors) and the updated set is
    the same baseline with the desired edits applied. (As with UpdateEmployees,
    and despite the published docs, these are NOT wrapped in a `Content`
    object.)
    """

    updated_vendors: list[VendorDetails] = Field(
        default=[],
        alias="UpdatedVendors",
        description="Vendors with edits applied (negative key requests creation).",
    )
    unchanged_vendors: list[VendorDetails] = Field(
        default=[],
        alias="UnchangedVendors",
        description="Baseline vendor records, left untouched.",
    )
    use_single_transaction: bool = Field(
        default=False,
        alias="UseSingleTransaction",
        description="Apply all updates in one transaction; any failure rejects all.",
    )


# =============================================================================
# CLASS: UpdateVendors
# =============================================================================


class UpdateVendors(GenericRequest[UpdateVendorsArguments]):
    """
    Update Vendors request body
    """

    method: Literal["UpdateVendors"] = Field(
        default="UpdateVendors",
        alias="Method",
        description="API method name to invoke.",
        frozen=True,
    )


# =============================================================================
# CLASS: UpdateVendorsResponseContent
# =============================================================================


class UpdateVendorsResponseContent(GenericBaseModel):
    """
    Content payload returned by UpdateVendors.
    """

    vendors: list[UpdatedVendorResult] = Field(
        default=[],
        alias="Vendors",
        description="The resulting vendor records.",
    )
    number_of_vendors_updated: int = Field(
        default=0,
        alias="NumberOfVendorsUpdated",
        description="Count of vendors updated.",
    )


# =============================================================================
# CLASS: UpdateVendorsResponse
# =============================================================================


class UpdateVendorsResponse(GenericResponse[UpdateVendorsResponseContent]):
    """
    Response schema for UpdateVendors
    """
