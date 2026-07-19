import click

from ajera.cli.context import ClientContext
from ajera.cli.group import CommonClickGroup
from ajera.cli.options import status_option
from ajera.cli.output import render


@click.group(name="ledger", cls=CommonClickGroup)
def group() -> None:
    """
    List and inspect general ledger accounts.
    """


@group.command(name="list")
@click.option(
    "--account-group",
    "filter_by_account_group",
    type=int,
    multiple=True,
    help="Filter by account group key (repeatable).",
)
@status_option
@click.option(
    "--type",
    "filter_by_type",
    type=str,
    multiple=True,
    help=(
        'Filter by account type name without spaces (e.g. "CurrentAsset", '
        '"Income") or numeric value as a string (repeatable).'
    ),
)
@click.pass_obj
def list_(
    ctx: ClientContext,
    filter_by_account_group: tuple[int, ...],
    filter_by_status: tuple[str, ...],
    filter_by_type: tuple[str, ...],
) -> None:
    """
    List general ledger accounts (active only by default).
    """
    render(
        ctx.client.list_ledger_accounts(
            filter_by_account_group=list(filter_by_account_group) or None,
            filter_by_status=list(filter_by_status),
            filter_by_type=list(filter_by_type) or None,
        )
    )


@group.command(name="get")
@click.argument("account_keys", nargs=-1, type=int)
@click.option(
    "--as-of-date",
    "as_of_date",
    type=str,
    default=None,
    help="Calculate balances as of this date (YYYY-MM-DD or ISO 8601).",
)
@click.option(
    "--exclude-close-year-entries",
    "exclude_close_year_entries",
    is_flag=True,
    default=False,
    help="Exclude close-year entries from calculated amounts.",
)
@click.pass_obj
def get(
    ctx: ClientContext,
    account_keys: tuple[int, ...],
    as_of_date: str | None,
    exclude_close_year_entries: bool,
) -> None:
    """
    Get general ledger account details, with calculated amounts.

    Pass one or more account keys, or none to return all accounts.
    """
    render(
        ctx.client.get_ledger_accounts(
            list(account_keys) or None,
            as_of_date=as_of_date,
            exclude_close_year_entries=exclude_close_year_entries or None,
        )
    )


@group.command(name="account-groups")
@status_option
@click.pass_obj
def account_groups(
    ctx: ClientContext,
    filter_by_status: tuple[str, ...],
) -> None:
    """
    List general ledger account groups (active only by default).
    """
    render(ctx.client.list_account_groups(filter_by_status=list(filter_by_status)))
