import click

from ajera.cli.context import ClientContext
from ajera.cli.group import CommonClickGroup
from ajera.cli.options import status_option
from ajera.cli.output import render
from ajera.schemas.vendor_invoice import VendorInvoiceLineItemCreate


@click.group(name="vendors", cls=CommonClickGroup)
def group() -> None:
    """
    List and inspect vendors.
    """


@group.command(name="list")
@click.option(
    "--company",
    "filter_by_company",
    type=int,
    multiple=True,
    help="Filter by company key (repeatable).",
)
@status_option
@click.option(
    "--name-like",
    "filter_by_name_like",
    type=str,
    default=None,
    help="Filter where the vendor name contains this substring.",
)
@click.option(
    "--vendor-type",
    "filter_by_vendor_type",
    type=int,
    multiple=True,
    help="Filter by vendor type key (repeatable).",
)
@click.option(
    "--modified-after",
    "filter_by_earliest_modified_date",
    type=str,
    default=None,
    help="Earliest modified date (YYYY-MM-DD or ISO 8601).",
)
@click.option(
    "--modified-before",
    "filter_by_latest_modified_date",
    type=str,
    default=None,
    help="Latest modified date (YYYY-MM-DD or ISO 8601).",
)
@click.pass_obj
def list_(
    ctx: ClientContext,
    filter_by_company: tuple[int, ...],
    filter_by_status: tuple[str, ...],
    filter_by_name_like: str | None,
    filter_by_vendor_type: tuple[int, ...],
    filter_by_earliest_modified_date: str | None,
    filter_by_latest_modified_date: str | None,
) -> None:
    """
    List vendors (active only by default).
    """
    render(
        ctx.client.list_vendors(
            filter_by_company=list(filter_by_company) or None,
            filter_by_status=list(filter_by_status),
            filter_by_name_like=filter_by_name_like,
            filter_by_vendor_type=list(filter_by_vendor_type) or None,
            filter_by_earliest_modified_date=filter_by_earliest_modified_date,
            filter_by_latest_modified_date=filter_by_latest_modified_date,
        )
    )


@group.command(name="get")
@click.argument("vendor_keys", nargs=-1, required=True, type=int)
@click.pass_obj
def get(ctx: ClientContext, vendor_keys: tuple[int, ...]) -> None:
    """
    Get one or more vendors by key.
    """
    render(ctx.client.get_vendors(list(vendor_keys)))


@group.command(name="update")
@click.argument("vendor_key", type=int)
@click.option("--name", default=None, help="New vendor name.")
@click.option("--vendor-account-id", default=None, help="New vendor account ID.")
@click.option("--email", default=None, help="New email address.")
@click.option("--website", default=None, help="New website URL.")
@click.option("--primary-phone", default=None, help="New primary phone number.")
@click.option("--secondary-phone", default=None, help="New secondary phone number.")
@click.option("--tertiary-phone", default=None, help="New tertiary phone number.")
@click.option("--fax", default=None, help="New fax number.")
@click.option("--notes", default=None, help="New notes.")
@click.pass_obj
def update(
    ctx: ClientContext,
    vendor_key: int,
    name: str | None,
    vendor_account_id: str | None,
    email: str | None,
    website: str | None,
    primary_phone: str | None,
    secondary_phone: str | None,
    tertiary_phone: str | None,
    fax: str | None,
    notes: str | None,
) -> None:
    """
    Update simple fields on one vendor.

    Only the options you pass are changed; everything else is left as-is.
    """
    render(
        ctx.client.update_vendor(
            vendor_key,
            name=name,
            vendor_account_id=vendor_account_id,
            email=email,
            website=website,
            primary_phone_number=primary_phone,
            secondary_phone_number=secondary_phone,
            tertiary_phone_number=tertiary_phone,
            fax_number=fax,
            notes=notes,
        )
    )


@group.command(name="types")
@status_option
@click.option(
    "--credit-card",
    "filter_by_is_credit_card",
    type=bool,
    multiple=True,
    help="Filter by the credit-card flag (repeatable).",
)
@click.option(
    "--consultant",
    "filter_by_is_consultant",
    type=bool,
    multiple=True,
    help="Filter by the consultant flag (repeatable).",
)
@click.pass_obj
def types(
    ctx: ClientContext,
    filter_by_status: tuple[str, ...],
    filter_by_is_credit_card: tuple[bool, ...],
    filter_by_is_consultant: tuple[bool, ...],
) -> None:
    """
    List vendor types (active only by default).
    """
    render(
        ctx.client.list_vendor_types(
            filter_by_status=list(filter_by_status),
            filter_by_is_credit_card=list(filter_by_is_credit_card) or None,
            filter_by_is_consultant=list(filter_by_is_consultant) or None,
        )
    )


@group.group(name="invoices")
def invoices() -> None:
    """
    List, inspect, and create vendor invoices.
    """


@invoices.command(name="list")
@click.option(
    "--vendor",
    "filter_by_vendor",
    type=int,
    multiple=True,
    help="Filter by vendor key (repeatable).",
)
@click.option(
    "--company",
    "filter_by_company",
    type=int,
    default=None,
    help="Filter by company key.",
)
@click.option(
    "--vendor-type",
    "filter_by_vendor_type",
    type=int,
    default=None,
    help="Filter by vendor type key.",
)
@click.option(
    "--paid/--no-paid",
    "filter_by_paid",
    default=None,
    help="Include only paid invoices.",
)
@click.option(
    "--unpaid/--no-unpaid",
    "filter_by_unpaid",
    default=None,
    help="Include only unpaid invoices.",
)
@click.option(
    "--voided/--no-voided",
    "filter_by_voided",
    default=None,
    help="Include only voided invoices.",
)
@click.option(
    "--invoice-after",
    "filter_by_earliest_invoice_date",
    type=str,
    default=None,
    help="Earliest invoice date (YYYY-MM-DD).",
)
@click.option(
    "--invoice-before",
    "filter_by_latest_invoice_date",
    type=str,
    default=None,
    help="Latest invoice date (YYYY-MM-DD).",
)
@click.option(
    "--accounting-after",
    "filter_by_earliest_accounting_date",
    type=str,
    default=None,
    help="Earliest accounting date (YYYY-MM-DD).",
)
@click.option(
    "--accounting-before",
    "filter_by_latest_accounting_date",
    type=str,
    default=None,
    help="Latest accounting date (YYYY-MM-DD).",
)
@click.option(
    "--pay-after",
    "filter_by_earliest_invoice_date_to_pay",
    type=str,
    default=None,
    help="Earliest date-to-pay (YYYY-MM-DD).",
)
@click.option(
    "--pay-before",
    "filter_by_latest_date_to_pay",
    type=str,
    default=None,
    help="Latest date-to-pay (YYYY-MM-DD).",
)
@click.option(
    "--amount-over",
    "filter_by_greater_than_amount",
    type=float,
    default=None,
    help="Amount greater than this value.",
)
@click.option(
    "--amount-under",
    "filter_by_less_than_amount",
    type=float,
    default=None,
    help="Amount less than this value.",
)
@click.option(
    "--amount-equals",
    "filter_by_equal_to_amount",
    type=float,
    default=None,
    help="Amount equal to this value.",
)
@click.pass_obj
def invoices_list(
    ctx: ClientContext,
    filter_by_vendor: tuple[int, ...],
    filter_by_company: int | None,
    filter_by_vendor_type: int | None,
    filter_by_paid: bool | None,
    filter_by_unpaid: bool | None,
    filter_by_voided: bool | None,
    filter_by_earliest_invoice_date: str | None,
    filter_by_latest_invoice_date: str | None,
    filter_by_earliest_accounting_date: str | None,
    filter_by_latest_accounting_date: str | None,
    filter_by_earliest_invoice_date_to_pay: str | None,
    filter_by_latest_date_to_pay: str | None,
    filter_by_greater_than_amount: float | None,
    filter_by_less_than_amount: float | None,
    filter_by_equal_to_amount: float | None,
) -> None:
    """
    List vendor invoices, optionally filtered.
    """
    render(
        ctx.client.list_vendor_invoices(
            filter_by_vendor=list(filter_by_vendor) or None,
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
    )


@invoices.command(name="get")
@click.argument("invoice_keys", nargs=-1, required=True, type=int)
@click.pass_obj
def invoices_get(ctx: ClientContext, invoice_keys: tuple[int, ...]) -> None:
    """
    Get one or more vendor invoices by key, with their line items.
    """
    render(ctx.client.get_vendor_invoices(list(invoice_keys)))


@invoices.command(name="create")
@click.option("--vendor-key", required=True, type=int, help="Vendor key.")
@click.option("--company-key", type=int, default=1, help="Company key (default 1).")
@click.option("--amount", required=True, type=float, help="Total invoice amount.")
@click.option(
    "--account-key",
    type=int,
    default=None,
    help="General ledger account key for the single line item.",
)
@click.option(
    "--project-key",
    type=int,
    default=None,
    help="Project key for the single line item (instead of an account).",
)
@click.option("--phase-key", type=int, default=None, help="Phase key for the line.")
@click.option(
    "--activity-key", type=int, default=None, help="Activity key for the line."
)
@click.option(
    "--department-key", type=int, default=None, help="Department key for the line."
)
@click.option("--number", default=None, help="Vendor invoice number.")
@click.option("--description", default=None, help="Invoice description.")
@click.option("--date", default=None, help="Invoice date (YYYY-MM-DD).")
@click.option("--accounting-date", default=None, help="Accounting date (YYYY-MM-DD).")
@click.option("--notes", default=None, help="Notes.")
@click.pass_obj
def invoices_create(
    ctx: ClientContext,
    vendor_key: int,
    company_key: int,
    amount: float,
    account_key: int | None,
    project_key: int | None,
    phase_key: int | None,
    activity_key: int | None,
    department_key: int | None,
    number: str | None,
    description: str | None,
    date: str | None,
    accounting_date: str | None,
    notes: str | None,
) -> None:
    """
    Create a vendor invoice with a single line item.

    The line is charged to either an account (--account-key) or a project
    (--project-key); its cost amount equals --amount. There is no API method to
    void or delete a vendor invoice, so a created invoice is permanent.
    """
    line = VendorInvoiceLineItemCreate(
        cost_amount=amount,
        account_key=account_key,
        project_key=project_key,
        phase_key=phase_key,
        activity_key=activity_key,
        department_key=department_key,
    )
    render(
        ctx.client.create_vendor_invoice(
            vendor_key=vendor_key,
            company_key=company_key,
            amount=amount,
            line_items=[line],
            number=number,
            description=description,
            date=date,
            accounting_date=accounting_date,
            notes=notes,
        )
    )
