from typing import Any, Literal, override

from pydantic import Field

from ajera.schemas.generic import (
    GenericBaseModel,
    GenericRequest,
    GenericResponse,
)

# =============================================================================
# CLASS: LedgerAccount
# =============================================================================


class LedgerAccount(GenericBaseModel):
    """
    General ledger account summary, as returned by ListLedgerAccounts
    """

    account_key: int = Field(
        default=0,
        alias="GLAccountKey",
        description="Unique general ledger account key.",
    )
    id: str = Field(
        default="",
        alias="ID",
        description="General ledger account number/ID.",
    )
    description: str = Field(
        default="",
        alias="Description",
        description="General ledger account description.",
    )
    account_type: str = Field(
        default="",
        alias="AccountType",
        description="Account type, e.g. Current Asset, Income, Expense.",
    )
    account_group: str = Field(
        default="",
        alias="AccountGroup",
        description="Name of the account group this account belongs to.",
    )
    order: int = Field(
        default=0,
        alias="Order",
        description="Display order within the chart of accounts.",
    )
    status: str = Field(
        default="",
        alias="Status",
        description="Status (e.g. Active or Inactive).",
    )


# =============================================================================
# CLASS: LedgerAccountDetails
# =============================================================================


class LedgerAccountDetails(GenericBaseModel):
    """
    Detailed general ledger account, as returned by GetLedgerAccounts
    """

    account_key: int = Field(
        alias="GLAccountKey",
        description="Unique general ledger account key.",
    )
    id: str = Field(
        default="",
        alias="ID",
        description="General ledger account number/ID.",
    )
    description: str = Field(
        default="",
        alias="Description",
        description="General ledger account description.",
    )
    account_group: str = Field(
        default="",
        alias="AccountGroup",
        description="Name of the account group this account belongs to.",
    )
    account_group_order: int = Field(
        default=0,
        alias="AccountGroupOrder",
        description="Display order of the account group.",
    )
    account_group_status: str = Field(
        default="",
        alias="AccountGroupStatus",
        description="Status of the account group (e.g. Active or Inactive).",
    )
    account_type: str = Field(
        default="",
        alias="AccountType",
        description="Account type, e.g. Current Asset, Income, Expense.",
    )
    account_type_value: int = Field(
        default=0,
        alias="AccountTypeValue",
        description="Numeric value backing the account type.",
    )
    allocated: bool = Field(
        default=False,
        alias="Allocated",
        description="Whether the account is allocated.",
    )
    allow_journal_entries: bool = Field(
        default=False,
        alias="AllowJournalEntries",
        description="Whether journal entries are allowed against this account.",
    )
    intercompany_account_type: str = Field(
        default="",
        alias="IntercompanyAccountType",
        description="Intercompany account type, e.g. None.",
    )
    intercompany_account_type_value: int = Field(
        default=0,
        alias="IntercompanyAccountTypeValue",
        description="Numeric value backing the intercompany account type.",
    )
    intercompany_account: bool = Field(
        default=False,
        alias="IntercompanyAccount",
        description="Whether this is an intercompany account.",
    )
    normal_debit_balance: bool = Field(
        default=False,
        alias="NormalDebitBalance",
        description="Whether the account normally carries a debit balance.",
    )
    notes: str = Field(
        default="",
        alias="Notes",
        description="Notes.",
    )
    order: int = Field(
        default=0,
        alias="Order",
        description="Display order within the chart of accounts.",
    )
    print_net_profit_after_group: bool = Field(
        default=False,
        alias="PrintNetProfitAfterGroup",
        description="Whether to print net profit after this account's group.",
    )
    status: str = Field(
        default="",
        alias="Status",
        description="Status (e.g. Active or Inactive).",
    )
    summarize_group_on_fs: bool = Field(
        default=False,
        alias="SummarizeGroupOnFS",
        description="Whether the account group is summarized on financial statements.",
    )
    amount: float = Field(
        default=0.0,
        alias="Amount",
        description="Account amount (respects AsOfDate when supplied).",
    )
    balance: float = Field(
        default=0.0,
        alias="GLBalance",
        description="General ledger balance.",
    )
    budget: float = Field(
        default=0.0,
        alias="GLBudget",
        description="General ledger budget.",
    )
    cash_basis_balance: float = Field(
        default=0.0,
        alias="GLCashBasisBalance",
        description="General ledger cash-basis balance.",
    )
    cash_basis_budget: float = Field(
        default=0.0,
        alias="GLCashBasisBudget",
        description="General ledger cash-basis budget.",
    )


# =============================================================================
# CLASS: ListLedgerAccountsArguments
# =============================================================================


class ListLedgerAccountsArguments(GenericBaseModel):
    """
    Optional filter arguments for ListLedgerAccounts
    """

    filter_by_account_group: list[int] | None = Field(
        default=None,
        alias="FilterByAccountGroup",
        description="Filter ledger accounts by account group keys.",
    )
    filter_by_status: list[str] | None = Field(
        default=None,
        alias="FilterByStatus",
        description="Filter ledger accounts by status values (e.g. Active, Inactive).",
    )
    filter_by_type: list[str] | None = Field(
        default=None,
        alias="FilterByType",
        description=(
            "Filter ledger accounts by account type. Accepts the type name "
            'without spaces (e.g. "CurrentAsset", "Income") or its numeric '
            'value as a string (e.g. "5"); the spaced display name is not '
            "accepted."
        ),
    )


# =============================================================================
# CLASS: ListLedgerAccounts
# =============================================================================


class ListLedgerAccounts(GenericRequest[ListLedgerAccountsArguments]):
    """
    List ledger accounts request body
    """

    method: Literal["ListGLAccounts"] = Field(
        default="ListGLAccounts",
        alias="Method",
        description="API method name to invoke.",
        frozen=True,
    )


# =============================================================================
# CLASS: ListLedgerAccountsResponse
# =============================================================================


class ListLedgerAccountsResponse(GenericResponse[list[LedgerAccount]]):
    """
    Response schema for ListLedgerAccounts
    """

    @override
    def model_post_init(self, context: Any) -> None:
        if self.content:
            # Sort by display order, then account ID, for a stable chart order.
            self.content.sort(key=lambda account: (account.order, account.id))


# =============================================================================
# CLASS: GetLedgerAccountsArguments
# =============================================================================


class GetLedgerAccountsArguments(GenericBaseModel):
    """
    Arguments for GetLedgerAccounts.

    `RequestedGLAccounts` selects specific accounts; when omitted all accounts
    are returned. The remaining fields refine the calculated amounts and the
    accounts included.
    """

    requested_accounts: list[int] | None = Field(
        default=None,
        alias="RequestedGLAccounts",
        description="Ledger account keys to retrieve; omit for all accounts.",
    )
    exclude_close_year_entries: bool | None = Field(
        default=None,
        alias="ExcludeCloseYearEntries",
        description="Exclude close-year entries from calculated amounts.",
    )
    as_of_date: str | None = Field(
        default=None,
        alias="AsOfDate",
        description="Calculate balances as of this date (YYYY-MM-DD or ISO 8601).",
    )
    filter_by_account_group: list[int] | None = Field(
        default=None,
        alias="FilterByAccountGroup",
        description="Filter ledger accounts by account group keys.",
    )
    filter_by_status: list[str] | None = Field(
        default=None,
        alias="FilterByStatus",
        description="Filter ledger accounts by status values (e.g. Active, Inactive).",
    )
    filter_by_type: list[str] | None = Field(
        default=None,
        alias="FilterByType",
        description=(
            "Filter ledger accounts by account type. Accepts the type name "
            'without spaces (e.g. "CurrentAsset", "Income") or its numeric '
            'value as a string (e.g. "5"); the spaced display name is not '
            "accepted."
        ),
    )


# =============================================================================
# CLASS: GetLedgerAccounts
# =============================================================================


class GetLedgerAccounts(GenericRequest[GetLedgerAccountsArguments]):
    """
    Get ledger accounts request body
    """

    method: Literal["GetGLAccounts"] = Field(
        default="GetGLAccounts",
        alias="Method",
        description="API method name to invoke.",
        frozen=True,
    )


# =============================================================================
# CLASS: GetLedgerAccountsResponse
# =============================================================================


class GetLedgerAccountsResponse(GenericResponse[list[LedgerAccountDetails]]):
    """
    Response schema for GetLedgerAccounts
    """
