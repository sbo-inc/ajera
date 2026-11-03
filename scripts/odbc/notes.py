"""
What some columns hold, where the name does not say it.

The generator writes each note into the column's field, where `describe()`
and `ajera odbc describe` show it. It appends the probe's finding on
`StartDate` (`start_date_columns` in catalog.json), unless the note already
says how `@StartDate` acts. Each note was checked live, as its comment says.
Keyed by source, then by column.
"""

# `AxFinancials` and its `_MC` variants, checked live per account against the
# sum of `AxGLDetail.gldAmount` for the same entity and account:
# - Income and expense accounts: `glaCurrentMonth` matched every ledger row
#   from StartDate through EndDate, and `glaCurrentYTDBalance` every row from
#   the first of the fiscal year that holds EndDate (January here) through
#   EndDate, for starts from 2000 to the last month. For a one-month range,
#   the first equals the difference of the second at that month's end and at
#   the month before.
# - Asset, liability, and equity accounts other than retained earnings: both
#   columns matched every ledger row through EndDate, edited versions included
#   (they net out), whatever the start: the balance, not the change since the
#   fiscal year began.
# - Retained earnings: with a StartDate after `LastDayCurrentFiscalYear`
#   (2021-01-01 against 2020-12-31 here), the column held its own ledger plus
#   the income-statement ledger before the fiscal year of EndDate, and summed
#   to zero over all accounts. With a StartDate on or before it, each
#   retained-earnings row held its own ledger alone, and the sum was not zero.
# - The prior-year columns matched the same sums a year back. The probe found
#   that StartDate moves `glaPriorYearYTDBalance` on no row.
# - Every budget column was zero, so their periods were not checked.
# - `FirstDayCurrentFiscalYear` and `LastDayCurrentFiscalYear` held one date
#   for ends in two different years, years before both.
_FINANCIALS = {
    "glaCurrentMonth": (
        "For an income or expense account, the activity from @StartDate "
        "through @EndDate: the range passed, not a calendar month. For an "
        "asset, liability, or equity account other than retained earnings, the "
        "balance at @EndDate, the same as `current_ytd_balance`. Signed as "
        "`AxGLDetail.gldAmount`."
    ),
    "glaCurrentYTDBalance": (
        "For an income or expense account, the activity from the first day of "
        "the fiscal year that holds @EndDate through @EndDate, whatever "
        "@StartDate is. For an asset, liability, or equity account, the balance "
        "at @EndDate: every ledger amount through it, not the change since the "
        "year began. Retained earnings also holds the income of the years "
        "before, so the accounts total zero, but only when @StartDate falls "
        "after `last_day_current_fiscal_year`; with an earlier @StartDate it "
        "holds its own ledger alone. Signed as `AxGLDetail.gldAmount`."
    ),
    "glaPriorYearMonth": (
        "For an income or expense account, the activity from @StartDate "
        "through @EndDate, each moved back a year. For an asset, liability, or "
        "equity account other than retained earnings, the balance at @EndDate "
        "moved back a year."
    ),
    "glaPriorYearYTDBalance": (
        "For an income or expense account, the activity of the fiscal year "
        "before, through @EndDate moved back a year. For an asset, liability, "
        "or equity account other than retained earnings, the balance at "
        "@EndDate moved back a year."
    ),
    **dict.fromkeys(
        (
            "glaBudgetCurrentMonth",
            "glaBudgetYTD",
            "glaBudgetPriorYearMonth",
            "glaBudgetPriorYTD",
        ),
        "Not checked: the database these notes were checked on holds no budgets.",
    ),
    **dict.fromkeys(
        ("FirstDayCurrentFiscalYear", "LastDayCurrentFiscalYear"),
        "Ajera's current fiscal year, which does not follow @EndDate: the "
        "year-to-date amounts start from the fiscal year that holds @EndDate.",
    ),
}

# `ProjectTotals`, checked live by the sum of each column over every project:
# - The WIP columns differed between a start in 2000 and one a month before
#   the end, and between ends in 2020 and 2026; starts in 1990 and 2000 gave
#   the same totals, and a long range took no longer than a month.
# - The receivable and payable balances were the same for ends in 2020 and
#   2026 and for starts in 2000 and the last month. The labor payable and
#   prepayment balances were zero on every project, so they were not checked.
_PROJECT_WIP = (
    "The unbilled part of the work charged from @StartDate through @EndDate, "
    "not all the WIP at @EndDate. To take in all of it, start before the "
    "oldest unbilled work: earlier starts then give the same total, and a "
    "long range is no slower."
)
_PROJECT_BALANCE = (
    "The open balance as the database holds it now: neither @StartDate nor "
    "@EndDate changes it."
)

# `ProjectTotals`, checked live after #36 (#38), each column by its sum of
# absolute values and a checksum over every project, with a start in 2000 and
# ends at 2020-12-31, 2024-06-30, and 2026-09-30; two identical calls agreed:
# - The receipts, billed-by-date, payment, vendor-invoiced, and adjustment
#   columns held for every end, as for every start (`start_date_columns`).
#   The labor payments were zero on every project, so they were not checked.
# - The outstanding and aging columns moved with the end. The aging buckets
#   that were zero on every project were not checked.
# - Each billed-by-date column was negative on most projects and equal to the
#   negative of the billed column on 91% to 99% of those with an amount,
#   never to the billed column itself, but their totals differ.
_PROJECT_TO_DATE = (
    "A total to date, as the database holds it now: neither @StartDate nor "
    "@EndDate changes it."
)
_PROJECT_BILLED_BY_DATE = (
    f"{_PROJECT_TO_DATE} Signed the opposite way to the billed columns, so "
    "ordinary billing is negative; on most projects it is the negative of "
    "the matching billed amount over the whole history, but not on all."
)
_PROJECT_AS_OF_END = "Changes with @EndDate."

# `GLFullAccountWithCutoff`, checked live at cutoffs from 2012 to 2024:
# - `glfaBalance` matched the sum of `AxGLDetail.gldAmount` through the
#   cutoff, by entity and account or by account alone, and
#   `AxFinancials.glaCurrentYTDBalance` at the cutoff, only on some of the
#   accounts with a balance, so what it holds is not established.
# - One call took about a second for the end of 2020, 24 seconds for the end
#   of 2022, and timed out after 4 minutes for the end of 2024.
_CUTOFF_BALANCE = (
    "Not the ledger balance at @CutoffDate: on most accounts with a balance, "
    "it matched neither the sum of `AxGLDetail.gldAmount` through the cutoff "
    "nor `AxFinancials`' balance, so what it holds is not established. Slow "
    "for a recent cutoff, taking minutes; for a balance sheet at a date, read "
    "`current_ytd_balance` from `AxFinancials`, which takes seconds."
)

NOTES: dict[str, dict[str, str]] = {
    "AxFinancials": _FINANCIALS,
    "AxFinancials_MC": _FINANCIALS,
    "AxFinancials_MC_TrialBalance": _FINANCIALS,
    "ProjectTotals": {
        **dict.fromkeys(
            ("prjTotalWIP", "prjLaborWIP", "prjExpenseWIP", "prjConsultantWIP"),
            _PROJECT_WIP,
        ),
        **dict.fromkeys(
            (
                "prjTotalReceivableBalance",
                "prjLaborReceivableBalance",
                "prjExpenseReceivableBalance",
                "prjConsultantReceivableBalance",
                "prjPayableBalance",
                "prjExpensePayableBalance",
                "prjConsultantPayableBalance",
            ),
            _PROJECT_BALANCE,
        ),
        **dict.fromkeys(
            (
                "prjTotalReceipts",
                "prjLaborReceipts",
                "prjExpenseReceipts",
                "prjConsultantReceipts",
                "prjPayments",
                "prjExpensePayments",
                "prjConsultantPayments",
                "prjVendorInvoiced",
                "prjAdjustAmount",
            ),
            _PROJECT_TO_DATE,
        ),
        **dict.fromkeys(
            (
                "prjTotalBilledByDate",
                "prjLaborBilledByDate",
                "prjExpenseBilledByDate",
                "prjConsultantBilledByDate",
            ),
            _PROJECT_BILLED_BY_DATE,
        ),
        **dict.fromkeys(
            (
                "prjBilledOutstanding",
                "prjBilledAgingCurrent",
                "prjBilledAging30",
                "prjBilledAging60",
                "prjBilledAging90",
                "prjBilledAging120",
                "prjBilledLaborOutstanding",
                "prjBilledLaborAgingCurrent",
                "prjBilledLaborAging30",
                "prjBilledLaborAging60",
                "prjBilledLaborAging90",
                "prjBilledLaborAging120",
                "prjBilledExpenseOutstanding",
                "prjBilledExpenseAgingCurrent",
                "prjBilledExpenseAging30",
                "prjBilledExpenseAging120",
                "prjBilledConsultantOutstanding",
                "prjBilledConsultantAgingCurrent",
                "prjBilledConsultantAging120",
                "prjSpentOutstanding",
                "prjSpentAgingCurrent",
                "prjSpentAging30",
                "prjSpentAging60",
                "prjSpentAging90",
                "prjSpentAging120",
                "prjSpentLaborOutstanding",
                "prjSpentLaborAgingCurrent",
                "prjSpentLaborAging30",
                "prjSpentLaborAging60",
                "prjSpentLaborAging90",
                "prjSpentLaborAging120",
                "prjSpentExpenseOutstanding",
                "prjSpentExpenseAgingCurrent",
                "prjSpentExpenseAging30",
                "prjSpentExpenseAging120",
                "prjSpentConsultantOutstanding",
                "prjSpentConsultantAgingCurrent",
                "prjSpentConsultantAging120",
            ),
            _PROJECT_AS_OF_END,
        ),
    },
    "GLFullAccountWithCutoff": {
        "glfaBalance": _CUTOFF_BALANCE,
        "glfaCashBasisBalance": (
            "The cash-basis counterpart of `balance`, checked no further."
        ),
    },
}
