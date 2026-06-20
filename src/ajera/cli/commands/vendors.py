import click

from ajera.cli.context import ClientContext
from ajera.cli.group import CommonClickGroup
from ajera.cli.output import render


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
    help="Filter by company ID (repeatable).",
)
@click.option(
    "--status",
    "filter_by_status",
    type=str,
    multiple=True,
    help="Filter by status value (repeatable).",
)
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
    help="Filter by vendor type ID (repeatable).",
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
    List vendors, optionally filtered.
    """
    render(
        ctx.client.list_vendors(
            filter_by_company=list(filter_by_company) or None,
            filter_by_status=list(filter_by_status) or None,
            filter_by_name_like=filter_by_name_like,
            filter_by_vendor_type=list(filter_by_vendor_type) or None,
            filter_by_earliest_modified_date=filter_by_earliest_modified_date,
            filter_by_latest_modified_date=filter_by_latest_modified_date,
        )
    )


@group.command(name="get")
@click.argument("vendor_ids", nargs=-1, required=True, type=int)
@click.pass_obj
def get(ctx: ClientContext, vendor_ids: tuple[int, ...]) -> None:
    """
    Get one or more vendors by ID.
    """
    render(ctx.client.get_vendors(list(vendor_ids)))


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
@click.option(
    "--status",
    "filter_by_status",
    type=str,
    multiple=True,
    help="Filter by status value, e.g. Active or Inactive (repeatable).",
)
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
    List vendor types, optionally filtered.
    """
    render(
        ctx.client.list_vendor_types(
            filter_by_status=list(filter_by_status) or None,
            filter_by_is_credit_card=list(filter_by_is_credit_card) or None,
            filter_by_is_consultant=list(filter_by_is_consultant) or None,
        )
    )
