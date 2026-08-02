from ajera.operations.generic import Operation, envelope, flatten
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
    VendorInvoicePayment,
)

# The `Status` value a voided vendor invoice carries. On the tenant this was
# measured against, `FilterByVoided` returns exactly the invoices holding this
# status, which is what lets the payment derivation read the voided state
# straight off the record instead of spending a request on it.
VOIDED_VENDOR_INVOICE_STATUS = "Voided"


# -----------------------------------------------------------------------------
# FUNCTION: list_vendor_invoices_arguments
# -----------------------------------------------------------------------------


def list_vendor_invoices_arguments(
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
) -> ListVendorInvoicesArguments:
    """
    Collect the caller's filters.

    The arguments outlive the first request: deriving payment status re-issues
    them alongside `FilterByPaid`, so they are built once and kept.

    Returns:
        ListVendorInvoicesArguments: The filter arguments.
    """
    return ListVendorInvoicesArguments(
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
        filter_by_earliest_invoice_date_to_pay=filter_by_earliest_invoice_date_to_pay,
        filter_by_latest_date_to_pay=filter_by_latest_date_to_pay,
        filter_by_greater_than_amount=filter_by_greater_than_amount,
        filter_by_less_than_amount=filter_by_less_than_amount,
        filter_by_equal_to_amount=filter_by_equal_to_amount,
    )


# -----------------------------------------------------------------------------
# OPERATION: list_vendor_invoices
# -----------------------------------------------------------------------------


def list_vendor_invoices(
    arguments: ListVendorInvoicesArguments,
) -> Operation[list[VendorInvoice]]:
    """
    Build one ListVendorInvoices operation with the given arguments.

    Returns:
        Operation[list[VendorInvoice]]: The list vendor invoices operation.
    """
    request = ListVendorInvoices(method_arguments=arguments)

    return Operation(
        request=request,
        api_version=2,
        # The list call also returns an (empty) VendorInvoicesDetails array
        parse=flatten("VendorInvoices", ListVendorInvoicesResponse),
    )


# -----------------------------------------------------------------------------
# FUNCTION: paid_keys_or_query
# -----------------------------------------------------------------------------


def paid_keys_or_query(
    arguments: ListVendorInvoicesArguments,
    invoices: list[VendorInvoice],
) -> set[int] | ListVendorInvoicesArguments:
    """
    Decide how the paid key set is obtained for a listing.

    Returns the set outright when the caller's own filters already determine
    it, and otherwise the arguments for the one extra request that does.

    Returns:
        set[int] | ListVendorInvoicesArguments: The paid keys, or the query
            that fetches them.
    """
    if arguments.filter_by_paid:
        # The caller already narrowed the result to paid invoices, and
        # re-issuing that filter alongside itself would buy nothing.
        return {invoice.vendor_invoice_key for invoice in invoices}

    if arguments.filter_by_unpaid or arguments.filter_by_voided:
        # The caller already excluded paid invoices, and asking for paid
        # ones on top of those filters would be a contradictory request.
        return set()

    # Re-issue the caller's own filters alongside FilterByPaid: the key set has
    # to be drawn from the same population as the records being labelled, or it
    # will not line up with them.
    paid_arguments = arguments.model_copy()
    paid_arguments.filter_by_paid = True
    return paid_arguments


# -----------------------------------------------------------------------------
# FUNCTION: assign_payment_status
# -----------------------------------------------------------------------------


def assign_payment_status(invoices: list[VendorInvoice], paid_keys: set[int]) -> None:
    """
    Set the derived `payment` field on each invoice, in place.

    Voided is read from the record's own `Status`, which makes the paid set the
    only thing that has to be fetched. If `FilterByVoided` ever stops agreeing
    with `Status == "Voided"`, fetch the voided key set the same way the paid
    one is fetched and test membership in it instead of reading the status.
    """
    for invoice in invoices:
        if invoice.status == VOIDED_VENDOR_INVOICE_STATUS:
            invoice.payment = VendorInvoicePayment.voided
        elif invoice.vendor_invoice_key in paid_keys:
            invoice.payment = VendorInvoicePayment.paid
        else:
            invoice.payment = VendorInvoicePayment.unpaid


# -----------------------------------------------------------------------------
# OPERATION: get_vendor_invoices
# -----------------------------------------------------------------------------


def get_vendor_invoices(invoice_keys: list[int]) -> Operation[VendorInvoiceBundle]:
    """
    Build the GetVendorInvoices operation.

    Returns:
        Operation[VendorInvoiceBundle]: The get vendor invoices operation.
    """
    request = GetVendorInvoices()
    request.method_arguments = GetVendorInvoicesArguments(
        requested_vendor_invoices=invoice_keys
    )

    return Operation(
        request=request,
        api_version=2,
        parse=envelope(GetVendorInvoicesResponse),
    )


# -----------------------------------------------------------------------------
# OPERATION: create_vendor_invoice
# -----------------------------------------------------------------------------


def create_vendor_invoice(
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
) -> Operation[VendorInvoiceBundle]:
    """
    Build the CreateVendorInvoices operation for a single invoice.

    Returns:
        Operation[VendorInvoiceBundle]: The create vendor invoice operation.
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

    return Operation(
        request=request,
        api_version=2,
        parse=envelope(CreateVendorInvoicesResponse),
    )
