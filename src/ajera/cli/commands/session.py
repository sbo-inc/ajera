import click

from ajera.cli.context import ClientContext
from ajera.cli.group import CommonClickGroup
from ajera.cli.options import api_version_option
from ajera.cli.output import render


@click.group(name="session", cls=CommonClickGroup)
def group() -> None:
    """
    Authenticate and manage API sessions.
    """


@group.command(name="token")
@api_version_option
@click.pass_obj
def token(ctx: ClientContext, api_version: int) -> None:
    """
    Fetch a session token for the given API version.
    """
    render(ctx.client.get_session_token(api_version=api_version))
