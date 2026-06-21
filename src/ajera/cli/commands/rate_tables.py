import click

from ajera.cli.context import ClientContext
from ajera.cli.options import status_option
from ajera.cli.output import render


@click.command(name="rate-tables")
@status_option
@click.pass_obj
def group(
    ctx: ClientContext,
    filter_by_status: tuple[str, ...],
) -> None:
    """
    List rate tables (active only by default).
    """
    render(ctx.client.list_rate_tables(filter_by_status=list(filter_by_status)))
