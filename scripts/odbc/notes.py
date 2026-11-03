"""
What some columns hold, where the name does not say it.

The generator writes each note into the column's field, where `describe()`
and `ajera odbc describe` show it. It appends the probe's finding on
`StartDate` (`start_date_columns` in catalog.json), unless the note already
says how `@StartDate` acts. Each note was checked live, as its comment says.
Keyed by source, then by column.
"""

# Every note below states how Ajera behaves, checked live against the ledger
# or another source. The checks compared counts, sums, and checksums on the
# server and reduced them to a match or a mismatch; no row, amount, count, or
# date from the database is recorded here or anywhere else in this repository.
# Where a check could not reach a column, because the database held nothing
# for it, the note follows the rest of the column's family.

# `AxFinancials` and its `_MC` variants, per account against the sum of
# `AxGLDetail.gldAmount` for the same entity and account:
# - Income and expense accounts: `glaCurrentMonth` matched the ledger from
#   StartDate through EndDate, and `glaCurrentYTDBalance` the ledger from the
#   first day of the fiscal year that holds EndDate, whatever the start. For a
#   one-month range, the first equals the difference of the second at the
#   month's end and at the month before.
# - Asset, liability, and equity accounts other than retained earnings: both
#   matched every ledger row through EndDate, edited versions included (they
#   net out), whatever the start: the balance, not the change since the
#   fiscal year began.
# - Retained earnings: with a StartDate after `LastDayCurrentFiscalYear`, it
#   held its own ledger plus the income-statement ledger before the fiscal
#   year of EndDate, and the accounts summed to zero. With a StartDate on or
#   before that day, it held its own ledger alone.
# - The prior-year columns matched the same sums a year back.
# - `FirstDayCurrentFiscalYear` and `LastDayCurrentFiscalYear` held the same
#   date for ends in different years.
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
        ("FirstDayCurrentFiscalYear", "LastDayCurrentFiscalYear"),
        "Ajera's current fiscal year, which does not follow @EndDate: the "
        "year-to-date amounts start from the fiscal year that holds @EndDate.",
    ),
}

# `ProjectTotals`, each column by its sum of absolute values and a checksum
# over every project, with two identical calls agreeing:
# - The WIP columns moved with the start and with the end. Earlier starts gave
#   the same totals, and a long range took no longer than a short one.
# - The receivable, payable, and prepayment balances, and the receipts,
#   billed-by-date, payment, vendor-invoiced, and adjustment totals, held for
#   every start and every end.
# - The outstanding and aging columns held for every start and moved with the
#   end.
# - Each billed-by-date column was negative for ordinary billing, and the
#   negative of the matching billed column on most projects but not all.
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
_PROJECT_TO_DATE = (
    "A total to date, as the database holds it now: neither @StartDate nor "
    "@EndDate changes it."
)
_PROJECT_BILLED_BY_DATE = (
    f"{_PROJECT_TO_DATE} Signed the opposite way to the billed columns, so "
    "ordinary billing is negative; on most projects it is the negative of "
    "the matching billed amount over the whole history, but not on all."
)
_PROJECT_AS_OF_END = "Changes with @EndDate; @StartDate does not change it."
_SPLITS = ("Total", "Labor", "Expense", "Consultant")


def _family(*patterns: str) -> tuple[str, ...]:
    """Each column the patterns name, once per split: `prj{}WIP` is `prjTotalWIP`, ..."""
    return tuple(p.format(split) for p in patterns for split in _SPLITS)


def _aging(kind: str) -> tuple[str, ...]:
    """`prjBilledOutstanding`, `prjBilledAgingCurrent`, ..., for every split."""
    columns = []
    for split in ("", "Labor", "Expense", "Consultant"):
        columns.append(f"prj{kind}{split}Outstanding")
        columns += [
            f"prj{kind}{split}Aging{bucket}"
            for bucket in ("Current", "30", "60", "90", "120")
        ]
    return tuple(columns)


# `GLFullAccountWithCutoff`, at several cutoffs:
# - `glfaBalance` matched neither the sum of `AxGLDetail.gldAmount` through the
#   cutoff, by entity and account or by account alone, nor
#   `AxFinancials.glaCurrentYTDBalance` at the cutoff, on most accounts with a
#   balance, so what it holds is not established.
# - A call slowed steeply as the cutoff moved forward.
_CUTOFF_BALANCE = (
    "Not the ledger balance at @CutoffDate: on most accounts with a balance, "
    "it matched neither the sum of `AxGLDetail.gldAmount` through the cutoff "
    "nor `AxFinancials`' balance, so what it holds is not established. Slow "
    "for a recent cutoff, taking minutes; for a balance sheet at a date, read "
    "`current_ytd_balance` from `AxFinancials`, which takes seconds."
)

# `ClientInvoiceTotals` and the `ClientInvoice` view, with every `TotalType`:
# an invoice without adjustments has one row, and one with adjustments a row
# per adjustment. Within an invoice, only `ciInvoiceAdjustment` (one
# adjustment's amount) and its notes differ, and two adjustments can match in
# both, so their rows are identical and no column tells them apart.
_ONE_ROW_PER_ADJUSTMENT = (
    "One row per adjustment of an invoice, or one for an invoice without any. "
    "The invoice's own columns repeat on each of its rows, and two adjustments "
    "of the same amount and notes give identical rows."
)
_ADJUSTMENT = (
    "One adjustment's amount, or NULL for an invoice without any. Sum it over "
    "the invoice's rows for the invoice's adjustments."
)
# The other functions whose leading key repeats: `AxFinancials` returns one
# row per account and entity, and `AxCreditMemo` one per invoice the credit
# memo applies to, with no invoice repeated.
SOURCE_NOTES: dict[str, str] = {
    "ClientInvoiceTotals": _ONE_ROW_PER_ADJUSTMENT,
    "ClientInvoice": _ONE_ROW_PER_ADJUSTMENT,
    "AxFinancials": (
        "One row per account and entity: `gl_account_key` repeats once for each entity."
    ),
    "AxCreditMemo": (
        "One row per client invoice the credit memo applies to (`client_invoice_key`)."
    ),
}
# The columns that differ between rows sharing a repeated key. Every other
# amount repeats on each of those rows, and its note says so.
VARYING: dict[str, tuple[str, ...]] = {
    "ClientInvoiceTotals": ("ciInvoiceAdjustment", "ciInvoiceAdjustmentNotes"),
    "ClientInvoice": ("ciInvoiceAdjustment", "ciInvoiceAdjustmentNotes"),
}

NOTES: dict[str, dict[str, str]] = {
    "AxFinancials": _FINANCIALS,
    "AxFinancials_MC": _FINANCIALS,
    "AxFinancials_MC_TrialBalance": _FINANCIALS,
    "ProjectTotals": {
        **dict.fromkeys(_family("prj{}WIP"), _PROJECT_WIP),
        **dict.fromkeys(
            (
                *_family("prj{}ReceivableBalance"),
                "prjPayableBalance",
                "prjLaborPayableBalance",
                "prjExpensePayableBalance",
                "prjConsultantPayableBalance",
                "prjPrepaymentBalance",
            ),
            _PROJECT_BALANCE,
        ),
        **dict.fromkeys(
            (
                *_family("prj{}Receipts"),
                "prjPayments",
                "prjLaborPayments",
                "prjExpensePayments",
                "prjConsultantPayments",
                "prjVendorInvoiced",
                "prjAdjustAmount",
            ),
            _PROJECT_TO_DATE,
        ),
        **dict.fromkeys(_family("prj{}BilledByDate"), _PROJECT_BILLED_BY_DATE),
        **dict.fromkeys((*_aging("Billed"), *_aging("Spent")), _PROJECT_AS_OF_END),
    },
    "ClientInvoiceTotals": {"ciInvoiceAdjustment": _ADJUSTMENT},
    "ClientInvoice": {"ciInvoiceAdjustment": _ADJUSTMENT},
    "GLFullAccountWithCutoff": {
        "glfaBalance": _CUTOFF_BALANCE,
        "glfaCashBasisBalance": (
            "The cash-basis counterpart of `balance`, checked no further."
        ),
    },
}
