"""
Live read-only coverage of the ODBC reader.

Runs only where the Progress HDP driver is installed, which in practice means
the linux/amd64 image: `make test-odbc`. Production is the only database
Deltek exposes, so every check here returns metadata, counts, or the one
small reference table the reader maps; none prints row contents.
"""

import importlib
import os
from collections.abc import Generator
from datetime import date
from decimal import Decimal

import pytest

from ajera.client import AjeraClient
from ajera.odbc import PAGE_SIZE, AjeraOdbc
from ajera.odbc.queries.mirror import MIRRORS
from ajera.schemas.database import FUNCTIONS, TABLES, VIEWS

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
        "AxFinancials": (start, end, False, "A"),
        "AxFinancials_MC": (start, end, False, "A", None),
        "AxFinancials_MC_TrialBalance": (start, end, False, "A", None),
        "AxGLBalanceTotals": (end,),
        "AxGLDTotals": (0, start, end),
        "AxLedger": (start, end, False, "A"),
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
