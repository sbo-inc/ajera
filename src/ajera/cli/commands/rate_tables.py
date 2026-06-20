import click

from ajera.cli.context import ClientContext
from ajera.cli.output import render


@click.command(name="rate-tables")
@click.option(
    "--status",
    "filter_by_status",
    type=str,
    multiple=True,
    help="Filter by status value, e.g. Active or Inactive (repeatable).",
)
@click.pass_obj
def group(ctx: ClientContext, filter_by_status: tuple[str, ...]) -> None:
    """
    List rate tables, optionally filtered by status.
    """
    render(ctx.client.list_rate_tables(filter_by_status=list(filter_by_status) or None))
