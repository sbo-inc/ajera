import click

from ajera.cli.context import ClientContext
from ajera.cli.options import status_option
from ajera.cli.output import render


@click.command(name="invoice-formats")
@status_option
@click.pass_obj
def group(
    ctx: ClientContext,
    filter_by_status: tuple[str, ...],
) -> None:
    """
    List invoice formats (active only by default).
    """
    render(ctx.client.list_invoice_formats(filter_by_status=list(filter_by_status)))
