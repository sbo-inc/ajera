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
