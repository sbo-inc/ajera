import click

from ajera.cli.context import ClientContext
from ajera.cli.group import CommonClickGroup
from ajera.cli.options import status_option
from ajera.cli.output import render


@click.group(name="contacts", cls=CommonClickGroup)
def group() -> None:
    """
    List and inspect contacts.
    """


@group.command(name="list")
@click.option(
    "--company",
    "filter_by_company",
    type=int,
    multiple=True,
    help="Filter by company ID (repeatable).",
)
@status_option
@click.option(
    "--text",
    "filter_by_text",
    type=str,
    default=None,
    help="Filter where the contact text contains this substring.",
)
@click.option(
    "--contact-type",
    "filter_by_contact_type",
    type=int,
    multiple=True,
    help="Filter by contact type ID (repeatable).",
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
    filter_by_text: str | None,
    filter_by_contact_type: tuple[int, ...],
    filter_by_earliest_modified_date: str | None,
    filter_by_latest_modified_date: str | None,
) -> None:
    """
    List contacts (active only by default).
    """
    render(
        ctx.client.list_contacts(
            filter_by_company=list(filter_by_company) or None,
            filter_by_status=list(filter_by_status),
            filter_by_text=filter_by_text,
            filter_by_contact_type=list(filter_by_contact_type) or None,
            filter_by_earliest_modified_date=filter_by_earliest_modified_date,
            filter_by_latest_modified_date=filter_by_latest_modified_date,
        )
    )


@group.command(name="get")
@click.argument("contact_ids", nargs=-1, required=True, type=int)
@click.pass_obj
def get(ctx: ClientContext, contact_ids: tuple[int, ...]) -> None:
    """
    Get one or more contacts by ID.
    """
    render(ctx.client.get_contacts(list(contact_ids)))


@group.command(name="update")
@click.argument("contact_key", type=int)
@click.option("--first-name", default=None, help="New first name.")
@click.option("--middle-name", default=None, help="New middle name.")
@click.option("--last-name", default=None, help="New last name.")
@click.option("--title", default=None, help="New title.")
@click.option("--company", default=None, help="New company.")
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
    contact_key: int,
    first_name: str | None,
    middle_name: str | None,
    last_name: str | None,
    title: str | None,
    company: str | None,
    email: str | None,
    website: str | None,
    primary_phone: str | None,
    secondary_phone: str | None,
    tertiary_phone: str | None,
    fax: str | None,
    notes: str | None,
) -> None:
    """
    Update simple fields on one contact.

    Only the options you pass are changed; everything else is left as-is.
    """
    render(
        ctx.client.update_contact(
            contact_key,
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            title=title,
            company=company,
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
    List contact types (active only by default).
    """
    render(ctx.client.list_contact_types(filter_by_status=list(filter_by_status)))
