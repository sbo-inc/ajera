import click

from ajera.cli.context import ClientContext
from ajera.cli.options import status_option
from ajera.cli.output import render


@click.command(name="activities")
@status_option
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
    List activities (active only by default).
    """
    render(
        ctx.client.list_activities(
            filter_by_status=list(filter_by_status),
            filter_by_description_like=filter_by_description_like,
        )
    )
