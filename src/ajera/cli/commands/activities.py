import click

from ajera.cli.context import ClientContext
from ajera.cli.output import render


@click.command(name="activities")
@click.option(
    "--status",
    "filter_by_status",
    type=str,
    multiple=True,
    help="Filter by status value, e.g. Active or Inactive (repeatable).",
)
@click.option(
    "--description-like",
    "filter_by_description_like",
    type=str,
    default=None,
    help="Filter where the description contains this substring.",
)
@click.pass_obj
def group(
    ctx: ClientContext,
    filter_by_status: tuple[str, ...],
    filter_by_description_like: str | None,
) -> None:
    """
    List activities, optionally filtered.
    """
    render(
        ctx.client.list_activities(
            filter_by_status=list(filter_by_status) or None,
            filter_by_description_like=filter_by_description_like,
        )
    )
