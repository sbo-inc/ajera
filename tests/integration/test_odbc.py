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
from ajera.odbc import PAGE_SIZE, AjeraOdbc, between, count, sum_
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
