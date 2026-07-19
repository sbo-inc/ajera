import click

from ajera.cli.context import ClientContext
from ajera.cli.group import CommonClickGroup
from ajera.cli.options import status_option
from ajera.cli.output import render


@click.group(name="clients", cls=CommonClickGroup)
def group() -> None:
    """
    List and inspect clients.
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
    help="Filter where the client name contains this substring.",
)
@click.option(
    "--name-equals",
    "filter_by_name_equals",
    type=str,
    default=None,
    help="Filter where the client name equals this value.",
)
@click.option(
    "--client-type",
    "filter_by_client_type",
    type=int,
    multiple=True,
    help="Filter by client type key (repeatable).",
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
    filter_by_name_equals: str | None,
    filter_by_client_type: tuple[int, ...],
    filter_by_earliest_modified_date: str | None,
    filter_by_latest_modified_date: str | None,
) -> None:
    """
    List clients (active only by default).
    """
    render(
        ctx.client.list_clients(
            filter_by_company=list(filter_by_company) or None,
            filter_by_status=list(filter_by_status),
            filter_by_name_like=filter_by_name_like,
            filter_by_name_equals=filter_by_name_equals,
            filter_by_client_type=list(filter_by_client_type) or None,
            filter_by_earliest_modified_date=filter_by_earliest_modified_date,
            filter_by_latest_modified_date=filter_by_latest_modified_date,
        )
    )


@group.command(name="get")
@click.argument("client_keys", nargs=-1, required=True, type=int)
@click.pass_obj
def get(ctx: ClientContext, client_keys: tuple[int, ...]) -> None:
    """
    Get one or more clients by key.
    """
    render(ctx.client.get_clients(list(client_keys)))


@group.command(name="update")
@click.argument("client_key", type=int)
@click.option("--description", default=None, help="New client description (name).")
@click.option("--account-id", default=None, help="New account ID.")
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
    client_key: int,
    description: str | None,
    account_id: str | None,
    email: str | None,
    website: str | None,
    primary_phone: str | None,
    secondary_phone: str | None,
    tertiary_phone: str | None,
    fax: str | None,
    notes: str | None,
) -> None:
    """
    Update simple fields on one client.

    Only the options you pass are changed; everything else is left as-is.
    """
    render(
        ctx.client.update_client(
            client_key,
            description=description,
            account_id=account_id,
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
@click.pass_obj
def types(
    ctx: ClientContext,
    filter_by_status: tuple[str, ...],
) -> None:
    """
    List client types (active only by default).
    """
    render(ctx.client.list_client_types(filter_by_status=list(filter_by_status)))
