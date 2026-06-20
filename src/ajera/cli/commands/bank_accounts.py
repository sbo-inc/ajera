import click

from ajera.cli.context import ClientContext
from ajera.cli.output import render


@click.command(name="bank-accounts")
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
    List bank accounts, optionally filtered by status.
    """
    render(
        ctx.client.list_bank_accounts(filter_by_status=list(filter_by_status) or None)
    )
