"""
Live read-only coverage of the ODBC reader.

Runs only where the Progress HDP driver is installed, which in practice means
the linux/amd64 image: `make test-odbc`. Production is the only database
Deltek exposes, so every check here returns metadata, counts, or the one
small reference table the reader maps; none prints row contents.
"""

import importlib
import os
import time
from collections.abc import Generator, Sequence
from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest

from ajera.client import AjeraClient
from ajera.odbc import (
    PAGE_SIZE,
    AjeraOdbc,
    between,
    count,
    count_distinct,
    filters,
    sum_,
)
from ajera.odbc.queries.generic import Query
from ajera.odbc.queries.mirror import MIRRORS
from ajera.schemas.database import (
    FUNCTIONS,
    TABLES,
    VIEWS,
    ProjectStatus,
    TransactionActivityType,
    TransactionStatus,
)

pytestmark: list[pytest.MarkDecorator] = [pytest.mark.integration, pytest.mark.odbc]

REQUIRED_ENV_VARS = (
    "AJERA_ODBC_DATASOURCE",
    "AJERA_ODBC_USERNAME",
    "AJERA_ODBC_PASSWORD",
)
REST_ENV_VARS = ("AJERA_API_URL", "AJERA_API_USERNAME", "AJERA_API_PASSWORD")

# Rows sampled per source; `make odbc-verify` covers every row.
SAMPLE = 200


@pytest.fixture(scope="module")
def db() -> Generator[AjeraOdbc]:
    """
    One connection for the module: ODBC seats are few and shared.

    Yields:
        AjeraOdbc: The connected reader.
    """
    missing = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
    if missing:
        raise RuntimeError(
            "Ajera ODBC integration test misconfigured; set environment variables: "
            + ", ".join(missing)
        )
    with AjeraOdbc() as reader:
        yield reader


@pytest.fixture(scope="module")
def rest() -> Generator[AjeraClient]:
    if not all(os.getenv(var) for var in REST_ENV_VARS):
        pytest.skip("REST credentials not set; nothing to compare against")
    with AjeraClient() as client:
        yield client


def function_arguments(db: AjeraOdbc, name: str) -> tuple[object, ...]:
    """Representative arguments for each function: this year to date."""
    start, end = date(date.today().year, 1, 1), date.today()
    receipt = db.read(TABLES["AxReceipt"], limit=1)
    arguments: dict[str, tuple[object, ...]] = {
        "Ax1099Totals": (Decimal(0), start, end),
        "AxCreditMemo": (receipt[0].receipt_key if receipt else 0,),  # type: ignore[attr-defined]
        "AxFinancials": (start, end, False, "Accrual"),
        "AxFinancials_MC": (start, end, False, "Accrual", None),
        "AxFinancials_MC_TrialBalance": (start, end, False, "Accrual", None),
        "AxGLBalanceTotals": (end,),
        "AxGLDTotals": (0, start, end),
        "AxLedger": (start, end, False, "Accrual"),
        "AxTranTotals": (0, start, end),
        "BankEntries": (end,),
        "ClientInvoiceTotals": (0, start, end),
        "ClientTotals": (0, start, end),
        "EmployeeTotals": (0, start, end),
        "GLFullAccountWithCutoff": (end,),
        "ProjectTotals": (start, end),
        "ReceiptTotals": (start, end, None, None, False),
        "RefundTotals": (start, end, None, None),
        "VendorInvoiceTotals": (0, start, end),
        "VendorTotals": (0, start, end),
    }
    return arguments[name]


def scalar(db: AjeraOdbc, statement: str) -> object:
    cursor = db.connection.cursor()
    try:
        cursor.execute(statement)
        return cursor.fetchall()[0][0]
    finally:
        cursor.close()


# =============================================================================
# TEST: connectivity
# =============================================================================


def test_driver_is_registered() -> None:
    # Imported here, not at the top: pytest collects this module everywhere,
    # and pyodbc cannot load without unixODBC.
    pyodbc = importlib.import_module("pyodbc")

    assert "DataDirect HDP 4.6" in pyodbc.drivers()


def test_ping(db: AjeraOdbc) -> None:
    assert db.ping() is True


def test_server_is_sql_server(db: AjeraOdbc) -> None:
    version = scalar(db, "SELECT @@VERSION")

    assert isinstance(version, str)
    assert version.startswith("Microsoft SQL Server")


# =============================================================================
# TEST: the login cannot write
# =============================================================================
#
# Checked through role membership rather than by attempting a write, because
# the only database behind this login is the firm's production ledger.


def test_login_reads(db: AjeraOdbc) -> None:
    assert scalar(db, "SELECT IS_MEMBER('db_datareader')") == 1


@pytest.mark.parametrize("role", ["db_datawriter", "db_ddladmin", "db_owner"])
def test_login_cannot_write(db: AjeraOdbc, role: str) -> None:
    assert scalar(db, f"SELECT IS_MEMBER('{role}')") == 0


# =============================================================================
# TEST: the schema the reader depends on
# =============================================================================


@pytest.mark.parametrize(
    "column", ["cmpKey", "cmpDescription", "cmpStatus", "cmpNotes"]
)
def test_company_columns_exist(db: AjeraOdbc, column: str) -> None:
    count = scalar(
        db,
        "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "
        f"WHERE TABLE_NAME = 'AxCompany' AND COLUMN_NAME = '{column}'",
    )
    assert count == 1


# =============================================================================
# TEST: every table, view, and function reads through its model
# =============================================================================
#
# `make odbc-verify` validates every row; these read a sample of each so the
# suite stays quick enough to run on every change.


@pytest.mark.parametrize("name", sorted(TABLES))
def test_table_reads(db: AjeraOdbc, name: str) -> None:
    rows = db.read(TABLES[name], limit=SAMPLE)

    assert all(isinstance(row, TABLES[name]) for row in rows)


@pytest.mark.parametrize("name", sorted(VIEWS))
def test_view_reads(db: AjeraOdbc, name: str) -> None:
    rows = db.read(VIEWS[name], limit=SAMPLE)

    assert all(isinstance(row, VIEWS[name]) for row in rows)


@pytest.mark.parametrize(
    "name", sorted(name for name, model in TABLES.items() if model.__source__.blobs)
)
def test_blobs_read_on_request(db: AjeraOdbc, name: str) -> None:
    db.read(TABLES[name], limit=2, include_blobs=True)


@pytest.mark.parametrize("name", sorted(FUNCTIONS))
def test_function_calls(db: AjeraOdbc, name: str) -> None:
    rows = db.call(FUNCTIONS[name], *function_arguments(db, name), limit=SAMPLE)

    assert all(isinstance(row, FUNCTIONS[name]) for row in rows)


def test_reads_page_past_one_statement(db: AjeraOdbc) -> None:
    # More than one page, so the keyset continuation is exercised for real.
    rows = db.read(TABLES["AxGLDetail"], limit=PAGE_SIZE + 5)
    keys = [row.gl_detail_key for row in rows]  # type: ignore[attr-defined]

    assert len(keys) == PAGE_SIZE + 5
    assert keys == sorted(set(keys))


def test_count_agrees_with_read(db: AjeraOdbc) -> None:
    model = TABLES["AxActivity"]

    assert db.count(model) == len(db.read(model))


# =============================================================================
# TEST: the REST-shaped reads agree with the REST API
# =============================================================================


@pytest.mark.parametrize("method", sorted(MIRRORS))
@pytest.mark.parametrize("statuses", [["Active"], ["Inactive"], ["Active", "Inactive"]])
def test_mirror_matches_rest(
    db: AjeraOdbc, rest: AjeraClient, method: str, statuses: list[str]
) -> None:
    expected = getattr(rest, method)(filter_by_status=statuses)
    actual = getattr(db, method)(filter_by_status=statuses)
    richer = MIRRORS[method].richer

    assert [row.model_dump(exclude=richer) for row in actual] == [
        row.model_dump(exclude=richer) for row in expected
    ]
    # The fields the database fills are ones REST really leaves at default.
    for row in expected:
        assert all(not getattr(row, name) for name in richer)


# =============================================================================
# TEST: totals, projected reads, versions, and per-call timeouts
# =============================================================================
#
# Production data: compare values, never print them. Each comparison is
# reduced to a bool first so a failure shows no row contents.


def quiet_week() -> tuple[date, date]:
    """A Monday-to-Sunday week a month back, which nobody is still editing."""
    today = date.today()
    sunday = today - timedelta(days=today.weekday() + 1) - timedelta(weeks=4)
    return sunday - timedelta(days=6), sunday


def test_aggregate_sum_matches_read(db: AjeraOdbc) -> None:
    model = TABLES["AxTransaction"]
    where = {"date": between(*quiet_week())}

    totals = db.aggregate(model, measures=[sum_("units"), count()], where=where)
    rows = db.read(model, where=where)

    assert len(totals) == 1
    assert totals[0]["count"] == len(rows) > 0
    same = totals[0]["sum_units"] == sum(row.units for row in rows)  # type: ignore[attr-defined]
    assert same, "SUM(tUnits) differs from the sum over read"


def test_aggregate_groups_match_read(db: AjeraOdbc) -> None:
    model = TABLES["AxTransaction"]
    where = {"date": between(*quiet_week())}

    groups = db.aggregate(
        model,
        measures=[sum_("units", alias="units")],
        group_by=["employee_key", "activity_type"],
        where=where,
        current=True,
    )
    expected: dict[tuple[object, object], Decimal] = {}
    for row in db.rows(
        model,
        fields=["employee_key", "activity_type", "units"],
        where=where,
        current=True,
    ):
        key = (row["employee_key"], row["activity_type"])
        expected[key] = expected.get(key, Decimal(0)) + row["units"]  # type: ignore[operator]

    assert all(
        isinstance(group["activity_type"], TransactionActivityType) for group in groups
    )
    same = {
        (g["employee_key"], g["activity_type"]): g["units"] for g in groups
    } == expected
    assert same, "grouped SUM(tUnits) differs from the per-group sum over rows"


def test_aggregate_buckets_start_their_periods(db: AjeraOdbc) -> None:
    end = date.today()
    groups = db.aggregate(
        TABLES["AxTransaction"],
        measures=[count()],
        group_by=["date:week", "date:month", "date:quarter", "date:year"],
        where={"date": between(end - timedelta(days=120), end)},
        current=True,
    )

    assert groups
    for group in groups:
        week, month, quarter, year = (
            group[k] for k in ("date:week", "date:month", "date:quarter", "date:year")
        )
        assert isinstance(week, date) and week.weekday() == 0
        assert isinstance(month, date) and month.day == 1
        assert (
            isinstance(quarter, date)
            and quarter.day == 1
            and quarter.month in (1, 4, 7, 10)
        )
        assert isinstance(year, date) and (year.month, year.day) == (1, 1)


@pytest.mark.parametrize(
    "name, hand_written",
    [
        ("AxTransaction", {"is_current": True, "is_deleted": False}),
        ("AxGLDetail", {"is_current": True}),
    ],
)
def test_count_current_matches_hand_written_where(
    db: AjeraOdbc, name: str, hand_written: dict[str, object]
) -> None:
    model = TABLES[name]

    current = db.count(model, current=True)

    assert current == db.count(model, where=hand_written)
    assert 0 < current < db.count(model)


@pytest.mark.parametrize(
    "name, fields, expected",
    [
        (
            "AxProject",
            ["description", "status"],
            ["project_key", "description", "status"],
        ),
        ("AxTransaction", ["units", "status"], ["transaction_key", "units", "status"]),
    ],
)
def test_rows_return_only_named_fields(
    db: AjeraOdbc, name: str, fields: list[str], expected: list[str]
) -> None:
    model = TABLES[name]

    rows = db.rows(model, fields=fields, limit=50)

    assert len(rows) == 50
    assert all(list(row) == expected for row in rows)
    assert any(
        isinstance(row["status"], (ProjectStatus, TransactionStatus)) for row in rows
    )


def test_rows_keep_field_types(db: AjeraOdbc) -> None:
    rows = db.rows(
        TABLES["AxTransaction"],
        fields=["units", "date"],
        where={"date": between(*quiet_week())},
        limit=50,
    )

    assert rows
    assert all(isinstance(row["units"], Decimal) for row in rows)
    assert all(isinstance(row["date"], datetime) for row in rows)


def test_after_resumes_where_a_read_stopped(db: AjeraOdbc) -> None:
    model = TABLES["AxActivity"]
    keys = [row.activity_key for row in db.read(model, limit=6)]  # type: ignore[attr-defined]

    resumed = db.read(model, after=keys[2], limit=3)
    projected = db.rows(model, fields=["description"], after=keys[2], limit=3)

    assert [row.activity_key for row in resumed] == keys[3:]  # type: ignore[attr-defined]
    assert [row["activity_key"] for row in projected] == keys[3:]


def waitfor(seconds: int) -> Query[int]:
    """A statement that only waits: a timeout test that reads nothing."""
    return Query(
        statement=f"WAITFOR DELAY '00:00:{seconds:02d}'; SELECT 1 AS Done",
        parse=len,
    )


def test_per_call_timeout_cuts_a_statement_short() -> None:
    with AjeraOdbc(timeout=(30, 60)) as reader:
        start = time.monotonic()
        with pytest.raises(Exception) as caught:
            reader._run(waitfor(6), timeout=1)

        # Raised at the timeout, not when the server gives up on the
        # statement: the connection closes in the background.
        assert caught.value.args[0] == "HYT00"
        assert time.monotonic() - start < 4
        # The next statement gets a fresh connection, with the reader's 60 s.
        assert reader._run(waitfor(2)) == 1


def test_per_call_timeout_extends_a_statement() -> None:
    with AjeraOdbc(timeout=(30, 2)) as reader:
        assert reader._run(waitfor(4), timeout=10) == 1
        # Restored: the reader's own 2 s applies again.
        with pytest.raises(Exception) as caught:
            reader._run(waitfor(4))
        assert caught.value.args[0] == "HYT00"


def test_per_call_timeout_through_a_public_read(db: AjeraOdbc) -> None:
    model = TABLES["AxActivity"]

    assert db.count(model, timeout=30) == db.count(model) > 0
    assert len(db.rows(model, fields=["description"], limit=5, timeout=30)) == 5


# =============================================================================
# TEST: sessions still closing, and checked function arguments
# =============================================================================


def test_closing_session_is_counted_until_the_server_finishes() -> None:
    with AjeraOdbc(timeout=(30, 60)) as reader:
        with pytest.raises(Exception) as caught:
            reader._run(waitfor(5), timeout=1)
        assert caught.value.args[0] == "HYT00"

        # Abandoned, but still held until the server finishes waiting.
        assert (reader.closing, reader.sessions) == (1, 1)
        assert reader.ping()
        assert (reader.closing, reader.sessions) == (1, 2)

        start = time.monotonic()
        assert reader.wait_closed(timeout=30)
        assert time.monotonic() - start < 10
        assert (reader.closing, reader.sessions) == (0, 1)


def test_checked_arguments_reach_the_function(db: AjeraOdbc) -> None:
    start, end = date(date.today().year, 1, 1), date.today()

    # TotalType 3 applies the dates; 0 ignores them.
    typed = db.vendor_totals(3, start, end)
    from_text = db.call(
        FUNCTIONS["VendorTotals"], 3, start.isoformat(), end.isoformat()
    )
    same = typed == from_text

    assert typed
    assert same


def test_a_mistyped_argument_never_reaches_the_server(db: AjeraOdbc) -> None:
    with pytest.raises(TypeError, match="VendorTotals @StartDate"):
        db.vendor_totals(0, 2026, date.today())  # type: ignore[arg-type]


# =============================================================================
# TEST: parameters a function ignores
# =============================================================================
#
# These fail if Deltek starts to apply a parameter, which means it must come
# out of `ignored_parameters`: run `make odbc-probe` and `make odbc-generate`.

# A date range that does not overlap this year's.
OTHER_DATES: dict[str, object] = {
    "StartDate": date(2023, 3, 1),
    "EndDate": date(2023, 3, 31),
}
IGNORING = sorted(
    name
    for name, model in FUNCTIONS.items()
    if model.__source__.ignored_parameters or model.__source__.ignored_when
)


def with_other_dates(
    name: str, arguments: Sequence[object], ignored: set[str]
) -> tuple[object, ...]:
    """The arguments with each ignored date moved to another year."""
    parameters = FUNCTIONS[name].__source__.parameters
    return tuple(
        OTHER_DATES[p] if p in ignored else v
        for p, v in zip(parameters, arguments, strict=True)
    )


def totals(
    db: AjeraOdbc, name: str, arguments: Sequence[object]
) -> list[dict[str, object]]:
    """The row count and the sum of every decimal column."""
    model = FUNCTIONS[name]
    decimals = [
        field
        for field, info in model.model_fields.items()
        if isinstance(info.json_schema_extra, dict)
        and info.json_schema_extra.get("sql_type") == "decimal"
    ]
    return db.aggregate(
        model, *arguments, measures=[count(), *(sum_(field) for field in decimals)]
    )


@pytest.mark.parametrize("name", IGNORING)
def test_ignored_parameters_do_not_change_the_rows(
    db: AjeraOdbc, name: str, caplog: pytest.LogCaptureFixture
) -> None:
    source = FUNCTIONS[name].__source__
    # TotalType 0, where every recorded condition holds.
    base = function_arguments(db, name)
    held = set(source.ignored_parameters) | {
        p
        for p, conditions in source.ignored_when.items()
        if all(
            base[source.parameters.index(code)] in codes
            for code, codes in conditions.items()
        )
    }

    first = totals(db, name, base)
    second = totals(db, name, with_other_dates(name, base, held))
    same = first == second

    assert held
    assert first[0]["count"]
    assert same
    assert any(
        record.name == "ajera.odbc.arguments" and record.levelname == "WARNING"
        for record in caplog.records
    )


@pytest.mark.parametrize(
    "name", sorted(n for n in IGNORING if FUNCTIONS[n].__source__.ignored_when)
)
def test_dates_apply_under_the_other_codes(db: AjeraOdbc, name: str) -> None:
    source = FUNCTIONS[name].__source__
    conditions = source.ignored_when["StartDate"]
    code = next(iter(conditions))
    applying = next(v for v in (1, 2, 3) if v not in conditions[code])
    index = source.parameters.index(code)
    base = list(function_arguments(db, name))
    base[index] = applying

    first = totals(db, name, base)
    second = totals(db, name, with_other_dates(name, base, {"StartDate", "EndDate"}))
    differ = first != second

    assert differ


def test_receipt_totals_ignores_its_dates(db: AjeraOdbc) -> None:
    this_year = (date(date.today().year, 1, 1), date.today())
    other_year = (date(2023, 3, 1), date(2023, 3, 31))

    first = totals(db, "ReceiptTotals", (*this_year, None, None, False))
    second = totals(db, "ReceiptTotals", (*other_year, None, None, False))
    undated = totals(db, "ReceiptTotals", (None, None, None, None, False))
    filtered = db.count(
        FUNCTIONS["ReceiptTotals"],
        None,
        None,
        None,
        None,
        False,
        where={"r_date": between(*this_year)},
    )
    total = first[0]["count"]
    same = first == second == undated
    narrower = isinstance(total, int) and 0 < filtered < total

    assert same
    assert narrower


# =============================================================================
# TEST: the periods the amount columns cover
# =============================================================================
#
# Each comparison runs on the server or in memory and is reduced to a bool
# before it is asserted, so a failure never shows a ledger amount.

FINANCIALS = ("AxFinancials", "AxFinancials_MC", "AxFinancials_MC_TrialBalance")
# Asset, liability, and equity accounts. Retained earnings (5) also carries the
# earlier years' income, so it is checked through the total instead.
BALANCE_SHEET = frozenset(range(5))
INCOME_STATEMENT = frozenset(range(6, 11))
LAST_YEAR = date.today().year - 1
CENT = Decimal("0.005")


def financials(
    db: AjeraOdbc, name: str, start: date, end: date
) -> dict[tuple[object, object], dict[str, object]]:
    """Each account's period columns, keyed by entity and account."""
    arguments: list[object] = [start, end, False, "Accrual"]
    if name != "AxFinancials":
        company = db.rows(TABLES["AxCompany"], fields=["cmpKey"], limit=1)
        arguments.append(company[0]["company_key"])
    rows = db.rows(
        FUNCTIONS[name],
        *arguments,
        fields=[
            "eKey",
            "glaKey",
            "glaType",
            "glaCurrentMonth",
            "glaCurrentYTDBalance",
            "LastDayCurrentFiscalYear",
        ],
    )
    return {(row["entity_key"], row["gl_account_key"]): row for row in rows}


def amount(row: dict[str, object], field: str) -> Decimal:
    value = row[field]
    return value if isinstance(value, Decimal) else Decimal(0)


@pytest.mark.parametrize("name", FINANCIALS)
def test_current_month_covers_the_range_and_ytd_does_not(
    db: AjeraOdbc, name: str
) -> None:
    end = date(LAST_YEAR, 12, 31)
    year = financials(db, name, date(LAST_YEAR, 1, 1), end)
    half = financials(db, name, date(LAST_YEAR, 7, 1), end)
    # A start in another fiscal year moves only retained earnings.
    history = financials(db, name, date(2000, 1, 1), end)
    income = [k for k, row in year.items() if row["type"] in INCOME_STATEMENT]
    sheet = [k for k, row in year.items() if row["type"] in BALANCE_SHEET]

    same_accounts = set(year) == set(half) == set(history)
    ytd_held = all(
        amount(year[k], "current_ytd_balance") == amount(half[k], "current_ytd_balance")
        for k in year
    ) and all(
        amount(year[k], "current_ytd_balance")
        == amount(history[k], "current_ytd_balance")
        for k in income + sheet
    )
    month_moved = any(
        amount(year[k], "current_month") != amount(half[k], "current_month")
        for k in income
    )
    balances_held = all(
        amount(year[k], "current_month") == amount(half[k], "current_month")
        for k in sheet
    )

    assert income and sheet
    assert same_accounts
    assert ytd_held
    assert month_moved
    assert balances_held


def test_one_month_is_the_difference_of_two_year_to_date_reads(db: AjeraOdbc) -> None:
    # June and May of one year, both inside one fiscal year.
    june = financials(db, "AxFinancials", date(LAST_YEAR, 6, 1), date(LAST_YEAR, 6, 30))
    to_june = financials(
        db, "AxFinancials", date(LAST_YEAR, 1, 1), date(LAST_YEAR, 6, 30)
    )
    to_may = financials(
        db, "AxFinancials", date(LAST_YEAR, 1, 1), date(LAST_YEAR, 5, 31)
    )
    income = [k for k, row in june.items() if row["type"] in INCOME_STATEMENT]

    equal = all(
        amount(june[k], "current_month")
        == amount(to_june[k], "current_ytd_balance")
        - amount(to_may[k], "current_ytd_balance")
        for k in income
    )

    assert income
    assert equal


def test_balance_sheet_accounts_hold_the_balance_at_the_end(db: AjeraOdbc) -> None:
    end = date(LAST_YEAR, 12, 31)
    rows = financials(db, "AxFinancials", date(LAST_YEAR, 7, 1), end)
    # Every ledger row through the end, edited versions included: they net out.
    ledger = db.aggregate(
        TABLES["AxGLDetail"],
        measures=[sum_("amount", alias="balance")],
        group_by=["entity_key", "account_key"],
        where={"accounting_date": filters.lt(end + timedelta(days=1))},
    )
    balances = {
        (g["entity_key"], g["account_key"]): amount(g, "balance") for g in ledger
    }
    sheet = [k for k, row in rows.items() if row["type"] in BALANCE_SHEET]

    balance = all(
        abs(amount(rows[k], "current_ytd_balance") - balances.get(k, Decimal(0))) < CENT
        for k in sheet
    )
    month_is_balance = all(
        amount(rows[k], "current_month") == amount(rows[k], "current_ytd_balance")
        for k in sheet
    )
    # Retained earnings holds the earlier years' income, so the accounts net out.
    balanced = (
        abs(sum((amount(r, "current_ytd_balance") for r in rows.values()), Decimal(0)))
        < CENT
    )

    assert sheet
    assert balance
    assert month_is_balance
    assert balanced


def test_project_wip_covers_the_range_and_balances_do_not(db: AjeraOdbc) -> None:
    end = date.today().replace(day=1) - timedelta(days=1)
    model = FUNCTIONS["ProjectTotals"]
    measures = [
        sum_(field, alias=field)
        for field in ("total_wip", "total_receivable_balance", "payable_balance")
    ]

    def totals_from(start: date) -> dict[str, object]:
        return db.aggregate(model, start, end, measures=measures)[0]

    history = totals_from(date(2000, 1, 1))
    month = totals_from(end.replace(day=1))
    earlier = totals_from(date(1990, 1, 1))

    wip_moved = history["total_wip"] != month["total_wip"]
    balances_held = all(
        history[f] == month[f] for f in ("total_receivable_balance", "payable_balance")
    )
    # A start before the oldest unbilled work gives the whole of it.
    wip_settled = history["total_wip"] == earlier["total_wip"]

    assert wip_moved
    assert balances_held
    assert wip_settled


def test_retained_earnings_takes_earlier_income_after_the_current_year(
    db: AjeraOdbc,
) -> None:
    end = date(LAST_YEAR, 12, 31)
    after = financials(db, "AxFinancials", date(LAST_YEAR, 7, 1), end)
    last_day = next(iter(after.values()))["last_day_current_fiscal_year"]
    assert isinstance(last_day, datetime)
    if last_day.date() >= date(LAST_YEAR, 7, 1):
        pytest.skip("every year before last is closed; no boundary to cross")
    before = financials(db, "AxFinancials", last_day.date(), end)
    ledger = db.aggregate(
        TABLES["AxGLDetail"],
        measures=[sum_("amount", alias="balance")],
        group_by=["entity_key", "account_key"],
        where={"accounting_date": filters.lt(end + timedelta(days=1))},
    )
    balances = {
        (g["entity_key"], g["account_key"]): amount(g, "balance") for g in ledger
    }
    retained = [k for k, row in before.items() if row["type"] == 5]

    def total(rows: dict[tuple[object, object], dict[str, object]]) -> Decimal:
        return sum(
            (amount(r, "current_ytd_balance") for r in rows.values()), Decimal(0)
        )

    own_ledger_before = all(
        abs(amount(before[k], "current_ytd_balance") - balances.get(k, Decimal(0)))
        < CENT
        for k in retained
    )
    balanced_after = abs(total(after)) < CENT
    balanced_before = abs(total(before)) < CENT

    assert retained
    assert own_ledger_before
    assert balanced_after
    assert not balanced_before


def test_project_to_date_totals_ignore_the_end_and_aging_follows_it(
    db: AjeraOdbc,
) -> None:
    model = FUNCTIONS["ProjectTotals"]
    to_date = ("total_receipts", "total_billed_by_date", "payments", "vendor_invoiced")
    measures = [sum_(f, alias=f) for f in (*to_date, "billed_outstanding")]

    def totals_to(end: date) -> dict[str, object]:
        return db.aggregate(model, date(2000, 1, 1), end, measures=measures)[0]

    early, late = totals_to(date(2020, 12, 31)), totals_to(date(2026, 9, 30))

    to_date_held = all(early[f] == late[f] for f in to_date)
    aging_moved = early["billed_outstanding"] != late["billed_outstanding"]

    assert to_date_held
    assert aging_moved


def test_billed_by_date_is_signed_against_billed(db: AjeraOdbc) -> None:
    rows = db.rows(
        FUNCTIONS["ProjectTotals"],
        date(1990, 1, 1),
        date.today(),
        fields=["prjTotalBilled", "prjTotalBilledByDate"],
    )
    billed = [
        (amount(r, "total_billed"), amount(r, "total_billed_by_date"))
        for r in rows
        if amount(r, "total_billed_by_date")
    ]

    mostly_negative = sum(by_date < 0 for _, by_date in billed) > 0.9 * len(billed)
    mostly_opposite = sum(abs(b + d) < CENT for b, d in billed) > 0.9 * len(billed)
    never_equal = not any(abs(b - d) < CENT for b, d in billed)

    assert billed
    assert mostly_negative
    assert mostly_opposite
    assert never_equal


# =============================================================================
# TEST: row grain
# =============================================================================


@pytest.mark.parametrize(
    "target", ["ClientInvoiceTotals(0, NULL, NULL)", "ClientInvoice"]
)
def test_client_invoices_repeat_once_per_adjustment(db: AjeraOdbc, target: str) -> None:
    rows, invoices, invoice_level = (
        scalar(db, f"SELECT {measure} FROM {target}")
        for measure in (
            "COUNT_BIG(*)",
            "COUNT_BIG(DISTINCT ciKey)",
            # The invoice's own amounts: the same on every row of one invoice.
            "COUNT_BIG(DISTINCT CONCAT(ciKey, ':', ciInvoiceAmount, ':', "
            "ciTotalReceipts, ':', ciTotalReceivableBalance))",
        )
    )
    adjusted = scalar(
        db,
        "SELECT COUNT(*) FROM (SELECT ciKey FROM "
        f"{target} GROUP BY ciKey HAVING COUNT(*) > 1 "
        "AND COUNT(*) > SUM(CASE WHEN ciInvoiceAdjustment IS NULL THEN 0 ELSE 1 END)"
        ") g",
    )

    assert isinstance(rows, int) and isinstance(invoices, int)
    assert rows > invoices
    assert invoice_level == invoices
    # Every repeated row carries an adjustment.
    assert adjusted == 0


ROW_KEYED = sorted(n for n, m in FUNCTIONS.items() if m.__source__.row_key)


@pytest.mark.parametrize("name", ROW_KEYED)
def test_row_keyed_functions_return_one_row_per_key(db: AjeraOdbc, name: str) -> None:
    model = FUNCTIONS[name]
    (key,) = model.__source__.row_key
    totals = db.aggregate(
        model,
        *function_arguments(db, name),
        measures=[count(), count_distinct(key, alias="keys")],
    )[0]

    assert totals["count"] == totals["keys"]


def test_text_columns_still_take_like_and_null_checks(db: AjeraOdbc) -> None:
    model = TABLES["AxProject"]
    matched = db.count(model, where={"notes": filters.like("%a%")})
    empty = db.count(model, where={"notes": None})

    assert matched >= 0 and empty >= 0
    with pytest.raises(ValueError, match="cannot order by 'notes'"):
        db.rows(model, fields=["project_key"], order_by=["notes"], limit=1)
