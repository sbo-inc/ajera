from ajera.operations.generic import Operation, flatten, items
from ajera.schemas.ledger import (
    GetLedgerAccounts,
    GetLedgerAccountsArguments,
    LedgerAccount,
    LedgerAccountDetails,
    ListLedgerAccounts,
    ListLedgerAccountsArguments,
    ListLedgerAccountsResponse,
)
from ajera.schemas.reference import (
    AccountGroup,
    ListAccountGroups,
    ListAccountGroupsResponse,
    StatusFilterArguments,
)

# -----------------------------------------------------------------------------
# OPERATION: list_ledger_accounts
# -----------------------------------------------------------------------------


def list_ledger_accounts(
    *,
    filter_by_account_group: list[int] | None = None,
    filter_by_status: list[str] | None = ["Active"],
    filter_by_type: list[str] | None = None,
) -> Operation[list[LedgerAccount]]:
    """
    Build the ListGLAccounts operation.

    Returns:
        Operation[list[LedgerAccount]]: The list ledger accounts operation.
    """
    request = ListLedgerAccounts()
    request.method_arguments = ListLedgerAccountsArguments(
        filter_by_account_group=filter_by_account_group,
        filter_by_status=filter_by_status,
        filter_by_type=filter_by_type,
    )

    return Operation(
        request=request,
        api_version=1,
        parse=flatten("GLAccounts", ListLedgerAccountsResponse),
    )


# -----------------------------------------------------------------------------
# OPERATION: get_ledger_accounts
# -----------------------------------------------------------------------------


def get_ledger_accounts(
    account_keys: list[int] | None = None,
    *,
    exclude_close_year_entries: bool | None = None,
    as_of_date: str | None = None,
    filter_by_account_group: list[int] | None = None,
    filter_by_status: list[str] | None = None,
    filter_by_type: list[str] | None = None,
) -> Operation[list[LedgerAccountDetails]]:
    """
    Build the GetGLAccounts operation.

    Returns:
        Operation[list[LedgerAccountDetails]]: The get ledger accounts operation.
    """
    request = GetLedgerAccounts()
    request.method_arguments = GetLedgerAccountsArguments(
        requested_accounts=account_keys,
        exclude_close_year_entries=exclude_close_year_entries,
        as_of_date=as_of_date,
        filter_by_account_group=filter_by_account_group,
        filter_by_status=filter_by_status,
        filter_by_type=filter_by_type,
    )

    return Operation(
        request=request,
        api_version=1,
        parse=items("GLAccounts", LedgerAccountDetails),
    )


# -----------------------------------------------------------------------------
# OPERATION: list_account_groups
# -----------------------------------------------------------------------------


def list_account_groups(
    *,
    filter_by_status: list[str] | None = ["Active"],
) -> Operation[list[AccountGroup]]:
    """
    Build the ListAccountGroups operation.

    Returns:
        Operation[list[AccountGroup]]: The list account groups operation.
    """
    request = ListAccountGroups()
    request.method_arguments = StatusFilterArguments(filter_by_status=filter_by_status)

    return Operation(
        request=request,
        api_version=1,
        parse=flatten("AccountGroups", ListAccountGroupsResponse),
    )
