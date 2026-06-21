import click

from ajera.cli.context import ClientContext
from ajera.cli.options import status_option
from ajera.cli.output import render


@click.command(name="bank-accounts")
@status_option
@click.pass_obj
def group(
    ctx: ClientContext,
    filter_by_status: tuple[str, ...],
) -> None:
    """
    List bank accounts (active only by default).
    """
    render(ctx.client.list_bank_accounts(filter_by_status=list(filter_by_status)))
