import logging
import sys

import click
import requests

from ajera.cli.commands import (
    activities,
    bank_accounts,
    clients,
    companies,
    contacts,
    departments,
    employees,
    invoice_formats,
    ledger,
    projects,
    rate_tables,
    session,
    vendors,
)
from ajera.cli.context import ClientContext
from ajera.cli.group import CommonClickGroup

CLI_DOCS = """
Deltek Ajera API command-line interface.

Connection settings are read from environment variables:

\b
- AJERA_API_URL to define the API endpoint.
- AJERA_API_USERNAME / AJERA_API_PASSWORD for authentication.
"""


@click.group(
    cls=CommonClickGroup,
    context_settings={"help_option_names": ["-h", "--help"]},
    help=CLI_DOCS,
)
@click.option(
    "--log",
    is_flag=True,
    default=False,
    help="Enable request logging at INFO level.",
)
@click.version_option(package_name="ajera", prog_name="ajera")
@click.pass_context
def cli(ctx: click.Context, log: bool) -> None:
    ctx.obj = ClientContext(log=log)


# Register all domain-specific command groups.
# Runtime gating is handled by AJERA_CLI_DISABLE.
for module in (
    session,
    employees,
    clients,
    contacts,
    vendors,
    projects,
    ledger,
    activities,
    companies,
    departments,
    rate_tables,
    bank_accounts,
    invoice_formats,
):
    cli.add_command(module.group)


def main() -> None:
    """
    Console-script entry point.

    Translates expected errors into a non-zero exit with a readable message
    instead of a traceback.
    """
    try:
        cli(standalone_mode=False)
    except click.ClickException as exc:
        exc.show()
        sys.exit(exc.exit_code)
    except click.exceptions.Abort:
        sys.exit(1)
    except requests.HTTPError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        logging.getLogger("ajera").debug("CLI error", exc_info=True)
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


__all__ = ["cli", "main"]
