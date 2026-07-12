import click

from ajera.cli.context import ClientContext
from ajera.cli.group import CommonClickGroup
from ajera.cli.output import render


@click.group(name="session", cls=CommonClickGroup)
def group() -> None:
    """
    Inspect the API session and calling user.
    """


@group.command(name="info")
@click.pass_obj
def info(ctx: ClientContext) -> None:
    """
    Show information about the calling user and API session.

    Includes company, Ajera version, and capability flags. The session token
    is omitted from the output.
    """
    render(ctx.client.get_session_info(), exclude={"session_token"})
