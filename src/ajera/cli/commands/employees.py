import click

from ajera.cli.context import ClientContext
from ajera.cli.group import CommonClickGroup
from ajera.cli.output import render


@click.group(name="employees", cls=CommonClickGroup)
def group() -> None:
    """
    List and inspect employees.
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
    help="Filter where the employee name contains this substring.",
)
@click.option(
    "--employee-type",
    "filter_by_employee_type",
    type=int,
    multiple=True,
    help="Filter by employee type ID (repeatable).",
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
    filter_by_employee_type: tuple[int, ...],
    filter_by_earliest_modified_date: str | None,
    filter_by_latest_modified_date: str | None,
) -> None:
    """
    List employees, optionally filtered.
    """
    render(
        ctx.client.list_employees(
            filter_by_company=list(filter_by_company) or None,
            filter_by_status=list(filter_by_status) or None,
            filter_by_name_like=filter_by_name_like,
            filter_by_employee_type=list(filter_by_employee_type) or None,
            filter_by_earliest_modified_date=filter_by_earliest_modified_date,
            filter_by_latest_modified_date=filter_by_latest_modified_date,
        )
    )


@group.command(name="get")
@click.argument("employee_ids", nargs=-1, required=True, type=int)
@click.pass_obj
def get(ctx: ClientContext, employee_ids: tuple[int, ...]) -> None:
    """
    Get one or more employees by ID.
    """
    render(ctx.client.get_employees(list(employee_ids)))


@group.command(name="update")
@click.argument("employee_key", type=int)
@click.option("--first-name", default=None, help="New first name.")
@click.option("--middle-name", default=None, help="New middle name.")
@click.option("--last-name", default=None, help="New last name.")
@click.option("--title", default=None, help="New job title.")
@click.option("--email", default=None, help="New email address.")
@click.option("--website", default=None, help="New website URL.")
@click.option("--primary-phone", default=None, help="New primary phone number.")
@click.option("--secondary-phone", default=None, help="New secondary phone number.")
@click.option("--tertiary-phone", default=None, help="New tertiary phone number.")
@click.option("--fax", default=None, help="New fax number.")
@click.pass_obj
def update(
    ctx: ClientContext,
    employee_key: int,
    first_name: str | None,
    middle_name: str | None,
    last_name: str | None,
    title: str | None,
    email: str | None,
    website: str | None,
    primary_phone: str | None,
    secondary_phone: str | None,
    tertiary_phone: str | None,
    fax: str | None,
) -> None:
    """
    Update simple fields on one employee.

    Only the options you pass are changed; everything else is left as-is.
    """
    render(
        ctx.client.update_employee(
            employee_key,
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            title=title,
            email=email,
            website=website,
            primary_phone_number=primary_phone,
            secondary_phone_number=secondary_phone,
            tertiary_phone_number=tertiary_phone,
            fax_number=fax,
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
@click.pass_obj
def types(ctx: ClientContext, filter_by_status: tuple[str, ...]) -> None:
    """
    List employee types, optionally filtered by status.
    """
    render(
        ctx.client.list_employee_types(filter_by_status=list(filter_by_status) or None)
    )


@group.command(name="deductions")
@click.option(
    "--status",
    "filter_by_status",
    type=str,
    multiple=True,
    help="Filter by status value, e.g. Active or Inactive (repeatable).",
)
@click.pass_obj
def deductions(ctx: ClientContext, filter_by_status: tuple[str, ...]) -> None:
    """
    List deductions, optionally filtered by status.
    """
    render(ctx.client.list_deductions(filter_by_status=list(filter_by_status) or None))


@group.command(name="fringes")
@click.option(
    "--status",
    "filter_by_status",
    type=str,
    multiple=True,
    help="Filter by status value, e.g. Active or Inactive (repeatable).",
)
@click.pass_obj
def fringes(ctx: ClientContext, filter_by_status: tuple[str, ...]) -> None:
    """
    List fringes, optionally filtered by status.
    """
    render(ctx.client.list_fringes(filter_by_status=list(filter_by_status) or None))


@group.command(name="pays")
@click.option(
    "--status",
    "filter_by_status",
    type=str,
    multiple=True,
    help="Filter by status value, e.g. Active or Inactive (repeatable).",
)
@click.pass_obj
def pays(ctx: ClientContext, filter_by_status: tuple[str, ...]) -> None:
    """
    List pay types, optionally filtered by status.
    """
    render(ctx.client.list_pays(filter_by_status=list(filter_by_status) or None))


@group.command(name="payroll-taxes")
@click.option(
    "--status",
    "filter_by_status",
    type=str,
    multiple=True,
    help="Filter by status value, e.g. Active or Inactive (repeatable).",
)
@click.pass_obj
def payroll_taxes(ctx: ClientContext, filter_by_status: tuple[str, ...]) -> None:
    """
    List payroll taxes, optionally filtered by status.
    """
    render(
        ctx.client.list_payroll_taxes(filter_by_status=list(filter_by_status) or None)
    )


@group.command(name="wage-tables")
@click.option(
    "--status",
    "filter_by_status",
    type=str,
    multiple=True,
    help="Filter by status value, e.g. Active or Inactive (repeatable).",
)
@click.pass_obj
def wage_tables(ctx: ClientContext, filter_by_status: tuple[str, ...]) -> None:
    """
    List wage tables, optionally filtered by status.
    """
    render(ctx.client.list_wage_tables(filter_by_status=list(filter_by_status) or None))
