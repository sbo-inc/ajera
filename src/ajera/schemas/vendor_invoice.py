from typing import Any, Literal, override

from pydantic import Field

from ajera.schemas.generic import (
    GenericBaseModel,
    GenericRequest,
    GenericResponse,
)

# =============================================================================
# CLASS: VendorInvoice
# =============================================================================


class VendorInvoice(GenericBaseModel):
    """
    Vendor invoice header.

    Used for both ListVendorInvoices and the header records of
    GetVendorInvoices. Some fields (company, vendor type, attachments) are only
    populated by GetVendorInvoices.
    """

    vendor_invoice_key: int = Field(
        default=0,
        alias="VendorInvoiceKey",
        description="Unique vendor invoice key.",
    )
    vendor_key: int = Field(
        default=0,
        alias="VendorKey",
        description="Key of the vendor the invoice is from.",
    )
    vendor_description: str = Field(
        default="",
        alias="VendorDescription",
        description="Vendor name.",
    )
    vendor_type_key: int | None = Field(
        default=None,
        alias="VendorTypeKey",
        description="Vendor type key (populated by GetVendorInvoices).",
    )
    vendor_type_description: str = Field(
        default="",
        alias="VendorTypeDescription",
        description="Vendor type description (populated by GetVendorInvoices).",
    )
    company_key: int | None = Field(
        default=None,
        alias="CompanyKey",
        description="Company key (populated by GetVendorInvoices).",
    )
    company_description: str = Field(
        default="",
        alias="CompanyDescription",
        description="Company description (populated by GetVendorInvoices).",
    )
    description: str = Field(
        default="",
        alias="Description",
        description="Invoice description.",
    )
    status: str = Field(
        default="",
        alias="Status",
        description="Status, e.g. Normal or Voided.",
    )
    type: str = Field(
        default="",
        alias="Type",
        description="Invoice type, e.g. Normal.",
    )
    number: str = Field(
        default="",
        alias="Number",
        description="Vendor invoice number.",
    )
    date: str | None = Field(
        default=None,
        alias="Date",
        description="Invoice date.",
    )
    accounting_date: str | None = Field(
        default=None,
        alias="AccountingDate",
        description="Accounting (posting) date.",
    )
    date_to_pay: str | None = Field(
        default=None,
        alias="DateToPay",
        description="Date the invoice is scheduled to be paid.",
    )
    amount: float = Field(
        default=0.0,
        alias="Amount",
        description="Invoice amount.",
    )
    notes: str = Field(
        default="",
        alias="Notes",
        description="Notes.",
    )
    on_hold: bool = Field(
        default=False,
        alias="OnHold",
        description="Whether the whole invoice is on hold.",
    )
    partially_on_hold: bool = Field(
        default=False,
        alias="PartiallyOnHold",
        description="Whether some line items are on hold.",
    )
    attachments: list[Any] | None = Field(
        default=None,
        alias="Attachments",
        description="Attachments (populated by GetVendorInvoices when present).",
    )


# =============================================================================
# CLASS: VendorInvoiceDetail
# =============================================================================


class VendorInvoiceDetail(GenericBaseModel):
    """
    Vendor invoice line item, as returned by GetVendorInvoices
    """

    vendor_invoice_key: int = Field(
        default=0,
        alias="VendorInvoiceKey",
        description="Key of the parent vendor invoice.",
    )
    transaction_key: int | None = Field(
        default=None,
        alias="TransactionKey",
        description="Transaction key for this line item.",
    )
    project_key: int | None = Field(
        default=None,
        alias="ProjectKey",
        description="Project key the line is charged to (when project-related).",
    )
    project_description: str = Field(
        default="",
        alias="ProjectDescription",
        description="Project description.",
    )
    project_id: str = Field(
        default="",
        alias="ProjectID",
        description="Project ID/number.",
    )
    phase_key: int | None = Field(
        default=None,
        alias="PhaseKey",
        description="Phase key.",
    )
    phase_description: str = Field(
        default="",
        alias="PhaseDescription",
        description="Phase description.",
    )
    phase_id: str = Field(
        default="",
        alias="PhaseID",
        description="Phase ID/number.",
    )
    activity_key: int | None = Field(
        default=None,
        alias="ActivityKey",
        description="Activity key.",
    )
    activity_description: str = Field(
        default="",
        alias="ActivityDescription",
        description="Activity description.",
    )
    company_key: int | None = Field(
        default=None,
        alias="CompanyKey",
        description="Company key.",
    )
    company_description: str = Field(
        default="",
        alias="CompanyDescription",
        description="Company description.",
    )
    units: float = Field(
        default=0.0,
        alias="Units",
        description="Number of units.",
    )
    unit_description: str = Field(
        default="",
        alias="UnitDescription",
        description="Unit description.",
    )
    cost_rate: float = Field(
        default=0.0,
        alias="CostRate",
        description="Cost rate per unit.",
    )
    cost_amount: float = Field(
        default=0.0,
        alias="CostAmount",
        description="Line item cost amount.",
    )
    account_key: int | None = Field(
        default=None,
        alias="AccountKey",
        description="General ledger account key the line is charged to.",
    )
    account_description: str = Field(
        default="",
        alias="AccountDescription",
        description="Account description.",
    )
    department_key: int | None = Field(
        default=None,
        alias="DepartmentKey",
        description="Department key.",
    )
    department_description: str = Field(
        default="",
        alias="DepartmentDescription",
        description="Department description.",
    )
    commitment_key: int | None = Field(
        default=None,
        alias="CommitmentKey",
        description="Commitment key (when tied to a commitment).",
    )
    commitment_description: str = Field(
        default="",
        alias="CommitmentDescription",
        description="Commitment description.",
    )
    hold: bool = Field(
        default=False,
        alias="Hold",
        description="Whether this line item is on hold.",
    )
    non_1099: bool = Field(
        default=False,
        alias="Non_1099",
        description="Whether this line item is excluded from 1099 reporting.",
    )
    notes: str = Field(
        default="",
        alias="Notes",
        description="Notes.",
    )


# =============================================================================
# CLASS: VendorInvoiceBundle
# =============================================================================


class VendorInvoiceBundle(GenericBaseModel):
    """
    GetVendorInvoices content: invoice headers and their line items.

    Line items are linked to their header by `VendorInvoiceKey`.
    """

    vendor_invoices: list[VendorInvoice] = Field(
        default=[],
        alias="VendorInvoices",
        description="Invoice header records.",
    )
    vendor_invoices_details: list[VendorInvoiceDetail] = Field(
        default=[],
        alias="VendorInvoicesDetails",
        description="Invoice line item records.",
    )


# =============================================================================
# CLASS: ListVendorInvoicesArguments
# =============================================================================


class ListVendorInvoicesArguments(GenericBaseModel):
    """
    Optional filter arguments for ListVendorInvoices
    """

    filter_by_vendor: list[int] | None = Field(
        default=None,
        alias="FilterByVendor",
        description="Filter by vendor keys.",
    )
    filter_by_company: int | None = Field(
        default=None,
        alias="FilterByCompany",
        description="Filter by company key.",
    )
    filter_by_vendor_type: int | None = Field(
        default=None,
        alias="FilterByVendorType",
        description="Filter by vendor type key.",
    )
    filter_by_paid: bool | None = Field(
        default=None,
        alias="FilterByPaid",
        description="Include only paid invoices.",
    )
    filter_by_unpaid: bool | None = Field(
        default=None,
        alias="FilterByUnpaid",
        description="Include only unpaid invoices.",
    )
    filter_by_voided: bool | None = Field(
        default=None,
        alias="FilterByVoided",
        description="Include only voided invoices.",
    )
    filter_by_earliest_invoice_date: str | None = Field(
        default=None,
        alias="FilterByEarliestInvoiceDate",
        description="Earliest invoice date (YYYY-MM-DD).",
    )
    filter_by_latest_invoice_date: str | None = Field(
        default=None,
        alias="FilterByLatestInvoiceDate",
        description="Latest invoice date (YYYY-MM-DD).",
    )
    filter_by_earliest_accounting_date: str | None = Field(
        default=None,
        alias="FilterByEarliestAccountingDate",
        description="Earliest accounting date (YYYY-MM-DD).",
    )
    filter_by_latest_accounting_date: str | None = Field(
        default=None,
        alias="FilterByLatestAccountingDate",
        description="Latest accounting date (YYYY-MM-DD).",
    )
    filter_by_earliest_invoice_date_to_pay: str | None = Field(
        default=None,
        alias="FilterByEarliestInvoiceDatetoPay",
        description="Earliest date-to-pay (YYYY-MM-DD).",
    )
    filter_by_latest_date_to_pay: str | None = Field(
        default=None,
        alias="FilterByLatestDatetoPay",
        description="Latest date-to-pay (YYYY-MM-DD).",
    )
    filter_by_greater_than_amount: float | None = Field(
        default=None,
        alias="FilterByGreaterThanAmount",
        description="Include invoices with an amount greater than this value.",
    )
    filter_by_less_than_amount: float | None = Field(
        default=None,
        alias="FilterByLessThanAmount",
        description="Include invoices with an amount less than this value.",
    )
    filter_by_equal_to_amount: float | None = Field(
        default=None,
        alias="FilterByEqualToAmount",
        description="Include invoices with an amount equal to this value.",
    )


# =============================================================================
# CLASS: ListVendorInvoices
# =============================================================================


class ListVendorInvoices(GenericRequest[ListVendorInvoicesArguments]):
    """
    List Vendor Invoices request body
    """

    method: Literal["ListVendorInvoices"] = Field(
        default="ListVendorInvoices",
        alias="Method",
        description="API method name to invoke.",
        frozen=True,
    )


# =============================================================================
# CLASS: ListVendorInvoicesResponse
# =============================================================================


class ListVendorInvoicesResponse(GenericResponse[list[VendorInvoice]]):
    """
    Response schema for ListVendorInvoices
    """

    @override
    def model_post_init(self, context: Any) -> None:
        if self.content:
            # Sort by invoice date (most recent last), then key, for stability.
            self.content.sort(key=lambda inv: (inv.date or "", inv.vendor_invoice_key))


# =============================================================================
# CLASS: GetVendorInvoicesArguments
# =============================================================================


class GetVendorInvoicesArguments(GenericBaseModel):
    """
    Arguments for GetVendorInvoices
    """

    requested_vendor_invoices: list[int] = Field(
        alias="RequestedVendorInvoices",
        description="Vendor invoice keys to retrieve (at least one required).",
    )


# =============================================================================
# CLASS: GetVendorInvoices
# =============================================================================


class GetVendorInvoices(GenericRequest[GetVendorInvoicesArguments]):
    """
    Get Vendor Invoices request body
    """

    method: Literal["GetVendorInvoices"] = Field(
        default="GetVendorInvoices",
        alias="Method",
        description="API method name to invoke.",
        frozen=True,
    )


# =============================================================================
# CLASS: GetVendorInvoicesResponse
# =============================================================================


class GetVendorInvoicesResponse(GenericResponse[VendorInvoiceBundle]):
    """
    Response schema for GetVendorInvoices
    """


# =============================================================================
# CLASS: VendorInvoiceLineItemCreate
# =============================================================================


class VendorInvoiceLineItemCreate(GenericBaseModel):
    """
    A line item to create on a new vendor invoice.

    A line is charged either to a general ledger account (`account_key`) or to a
    project/phase/activity. `cost_amount` is the line's amount.
    """

    cost_amount: float = Field(
        alias="CostAmount",
        description="Line item cost amount.",
    )
    account_key: int | None = Field(
        default=None,
        alias="AccountKey",
        description="General ledger account key to charge the line to.",
    )
    project_key: int | None = Field(
        default=None,
        alias="ProjectKey",
        description="Project key to charge the line to.",
    )
    phase_key: int | None = Field(
        default=None,
        alias="PhaseKey",
        description="Phase key.",
    )
    activity_key: int | None = Field(
        default=None,
        alias="ActivityKey",
        description="Activity key.",
    )
    company_key: int | None = Field(
        default=None,
        alias="CompanyKey",
        description="Company key.",
    )
    department_key: int | None = Field(
        default=None,
        alias="DepartmentKey",
        description="Department key.",
    )
    units: float | None = Field(
        default=None,
        alias="Units",
        description="Number of units.",
    )
    cost_rate: float | None = Field(
        default=None,
        alias="CostRate",
        description="Cost rate per unit.",
    )
    hold: bool | None = Field(
        default=None,
        alias="Hold",
        description="Whether this line item is on hold.",
    )
    non_1099: bool | None = Field(
        default=None,
        alias="Non_1099",
        description="Whether this line item is excluded from 1099 reporting.",
    )
    notes: str | None = Field(
        default=None,
        alias="Notes",
        description="Notes.",
    )


# =============================================================================
# CLASS: VendorInvoiceCreate
# =============================================================================


class VendorInvoiceCreate(GenericBaseModel):
    """
    A vendor invoice to create, with its line items
    """

    vendor_key: int = Field(
        alias="VendorKey",
        description="Key of the vendor the invoice is from.",
    )
    company_key: int = Field(
        alias="CompanyKey",
        description="Company key.",
    )
    amount: float = Field(
        alias="Amount",
        description="Total invoice amount (should equal the sum of line items).",
    )
    line_items: list[VendorInvoiceLineItemCreate] = Field(
        alias="LineItems",
        description="Line items that make up the invoice.",
    )
    number: str | None = Field(
        default=None,
        alias="Number",
        description="Vendor invoice number.",
    )
    description: str | None = Field(
        default=None,
        alias="Description",
        description="Invoice description.",
    )
    date: str | None = Field(
        default=None,
        alias="Date",
        description="Invoice date (YYYY-MM-DD).",
    )
    accounting_date: str | None = Field(
        default=None,
        alias="AccountingDate",
        description="Accounting (posting) date (YYYY-MM-DD).",
    )
    notes: str | None = Field(
        default=None,
        alias="Notes",
        description="Notes.",
    )


# =============================================================================
# CLASS: CreateVendorInvoicesArguments
# =============================================================================


class CreateVendorInvoicesArguments(GenericBaseModel):
    """
    Arguments for CreateVendorInvoices
    """

    vendor_invoices: list[VendorInvoiceCreate] = Field(
        alias="VendorInvoices",
        description="The vendor invoices to create.",
    )
    show_timing: bool | None = Field(
        default=None,
        alias="ShowTiming",
        description="Whether the response should include timing information.",
    )


# =============================================================================
# CLASS: CreateVendorInvoices
# =============================================================================


class CreateVendorInvoices(GenericRequest[CreateVendorInvoicesArguments]):
    """
    Create Vendor Invoices request body
    """

    method: Literal["CreateVendorInvoices"] = Field(
        default="CreateVendorInvoices",
        alias="Method",
        description="API method name to invoke.",
        frozen=True,
    )


# =============================================================================
# CLASS: CreateVendorInvoicesResponse
# =============================================================================


class CreateVendorInvoicesResponse(GenericResponse[VendorInvoiceBundle]):
    """
    Response schema for CreateVendorInvoices
    """
