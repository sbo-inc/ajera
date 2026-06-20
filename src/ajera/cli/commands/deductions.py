import click

from ajera.cli.context import ClientContext
from ajera.cli.group import CommonClickGroup
from ajera.cli.output import render


@click.group(name="deductions", cls=CommonClickGroup)
def group() -> None:
    """
    List deductions.
    """


@group.command(name="list")
@click.option(
    "--status",
    "filter_by_status",
    type=str,
    multiple=True,
    help="Filter by status value, e.g. Active or Inactive (repeatable).",
)
@click.pass_obj
def list_(ctx: ClientContext, filter_by_status: tuple[str, ...]) -> None:
    """
    List deductions, optionally filtered by status.
    """
    render(ctx.client.list_deductions(filter_by_status=list(filter_by_status) or None))
