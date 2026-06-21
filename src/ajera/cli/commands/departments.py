import click

from ajera.cli.context import ClientContext
from ajera.cli.options import status_option
from ajera.cli.output import render


@click.command(name="departments")
@status_option
@click.pass_obj
def group(
    ctx: ClientContext,
    filter_by_status: tuple[str, ...],
) -> None:
    """
    List departments (active only by default).
    """
    render(ctx.client.list_departments(filter_by_status=list(filter_by_status)))
