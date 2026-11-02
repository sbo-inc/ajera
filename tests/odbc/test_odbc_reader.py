"""
Offline coverage of the ODBC reader.

`pyodbc` is never imported here: it needs unixODBC at import time, which
neither a stock Mac nor CI is guaranteed to have. The reader is driven through
a fake DB-API connection instead, substituted at `connection.connect` the way
the REST tests substitute an `httpx.MockTransport`.
"""

import subprocess
import sys
from collections.abc import Callable, Iterator, Sequence
from typing import Any

import pytest

from ajera.odbc import AjeraOdbc, OdbcSettings
from ajera.odbc import connection as odbc_connection
from ajera.odbc.connection import quote
from ajera.schemas.reference import Company

# =============================================================================
# FAKES: a DB-API connection answering from a script
# =============================================================================

Response = tuple[list[str], list[tuple[Any, ...]]] | Exception


class FakeError(Exception):
    """Shaped like `pyodbc.Error`: SQLSTATE first, then the message."""


class FakeCursor:
    def __init__(self, connection: "FakeConnection") -> None:
        self.connection = connection
        self.description: Sequence[Sequence[object]] = ()
        self.rows: list[tuple[Any, ...]] = []

    def execute(self, sql: str, *params: object) -> "FakeCursor":
        self.connection.executed.append((sql, params))
        response = self.connection.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        columns, self.rows = response
        self.description = [(column, None) for column in columns]
        return self

    def fetchall(self) -> list[tuple[Any, ...]]:
        return self.rows

    def close(self) -> None:
        pass


class FakeConnection:
    def __init__(self, *responses: Response) -> None:
        self.responses = list(responses)
        self.executed: list[tuple[str, tuple[object, ...]]] = []
        self.closed = False

    def cursor(self) -> FakeCursor:
        return FakeCursor(self)

    def close(self) -> None:
        self.closed = True


@pytest.fixture
def opened(monkeypatch: pytest.MonkeyPatch) -> Callable[..., list[dict[str, Any]]]:
    """
    Route `connection.connect` to a sequence of fake connections.

    Returns:
        Callable: Takes the fakes to hand out in order, and returns the list
        of keyword arguments each connect was called with.
    """

    def install(*connections: FakeConnection) -> list[dict[str, Any]]:
        supply: Iterator[FakeConnection] = iter(connections)
        calls: list[dict[str, Any]] = []

        def connect(settings: OdbcSettings, **kwargs: Any) -> FakeConnection:
            calls.append({"settings": settings, **kwargs})
            return next(supply)

        monkeypatch.setattr(odbc_connection, "connect", connect)
        return calls

    return install


def reader() -> AjeraOdbc:
    return AjeraOdbc(datasource="ds", username="user", password="secret")


# =============================================================================
# TEST: settings and connection string
# =============================================================================


def test_settings_fall_back_to_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AJERA_ODBC_DATASOURCE", "env-ds")
    monkeypatch.setenv("AJERA_ODBC_USERNAME", "env-user")
    monkeypatch.setenv("AJERA_ODBC_PASSWORD", "env-secret")
    monkeypatch.setenv("AJERA_ODBC_HOST", "hdp.example.test")
    monkeypatch.setenv("AJERA_ODBC_PORT", "8443")

    settings = AjeraOdbc(username="explicit").settings

    assert settings.datasource == "env-ds"
    assert settings.username == "explicit"
    assert settings.password == "env-secret"
    assert settings.host == "hdp.example.test"
    assert settings.port == 8443


def test_settings_default_to_deltek_endpoint() -> None:
    settings = reader().settings

    assert settings.host == "ajera-hdp01.prd.mydeltek.com"
    assert settings.port == 443
    assert settings.driver == "DataDirect HDP 4.6"


def test_connection_string_carries_every_attribute() -> None:
    string = reader().settings.connection_string(login_timeout=30, query_timeout=120)
    attributes = dict(part.split("=", 1) for part in string.split(";"))

    assert attributes == {
        "Driver": "DataDirect HDP 4.6",
        "Service": "ajera-hdp01.prd.mydeltek.com",
        "PortNumber": "443",
        "HybridDataPipelineDataSource": "ds",
        "LogonID": "user",
        "Password": "secret",
        "EncryptionMethod": "1",
        "ValidateServerCertificate": "1",
        "LoginTimeout": "30",
        "QueryTimeout": "120",
    }


def test_connection_string_reports_every_missing_setting() -> None:
    with pytest.raises(ValueError) as error:
        AjeraOdbc(username="user").settings.connection_string()

    assert "AJERA_ODBC_DATASOURCE" in str(error.value)
    assert "AJERA_ODBC_PASSWORD" in str(error.value)
    assert "AJERA_ODBC_USERNAME" not in str(error.value)


@pytest.mark.parametrize(
    "value, expected",
    [
        ("plain", "plain"),
        ("semi;colon", "{semi;colon}"),
        ("has=equals", "{has=equals}"),
        ("close}brace", "{close}}brace}"),
        (" padded ", "{ padded }"),
    ],
)
def test_quote_braces_values_that_would_break_the_string(
    value: str, expected: str
) -> None:
    assert quote(value) == expected


def test_password_is_not_in_repr() -> None:
    assert "secret" not in repr(reader().settings)


def test_timeout_forms_normalise_to_login_and_query() -> None:
    assert AjeraOdbc(timeout=10).timeout == (10, 10)
    assert AjeraOdbc(timeout=(5, 60)).timeout == (5, 60)
    assert AjeraOdbc(timeout=None).timeout == (0, 0)


# =============================================================================
# TEST: the optional extra
# =============================================================================


def test_importing_the_package_does_not_import_pyodbc() -> None:
    # A fresh interpreter, because this process may already hold pyodbc.
    code = "import sys, ajera, ajera.odbc; sys.exit('pyodbc' in sys.modules)"
    assert subprocess.run([sys.executable, "-c", code]).returncode == 0


def test_missing_pyodbc_names_the_extra(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "pyodbc", None)

    with pytest.raises(ImportError, match=r"ajera\[odbc\]"):
        reader().ping()


# =============================================================================
# TEST: connection lifecycle
# =============================================================================


def test_construction_does_not_connect(opened: Callable[..., Any]) -> None:
    calls = opened()

    reader()

    assert calls == []


def test_one_connection_serves_every_read(opened: Callable[..., Any]) -> None:
    fake = FakeConnection((["Ping"], [(1,)]), (["Ping"], [(1,)]))
    calls = opened(fake)
    db = reader()

    assert db.ping() and db.ping()
    assert len(calls) == 1
    assert calls[0]["login_timeout"] == 30
    assert calls[0]["query_timeout"] == 300


def test_dropped_connection_is_reopened_once(opened: Callable[..., Any]) -> None:
    dropped = FakeConnection(FakeError("08S01", "Communication link failure"))
    fresh = FakeConnection((["Ping"], [(1,)]))
    calls = opened(dropped, fresh)

    assert reader().ping() is True
    assert len(calls) == 2
    assert dropped.closed


def test_second_drop_propagates(opened: Callable[..., Any]) -> None:
    opened(
        FakeConnection(FakeError("08S01", "gone")),
        FakeConnection(FakeError("08S01", "still gone")),
    )

    with pytest.raises(FakeError, match="still gone"):
        reader().ping()


def test_other_errors_are_not_retried(opened: Callable[..., Any]) -> None:
    calls = opened(FakeConnection(FakeError("42S02", "Invalid object name")))

    with pytest.raises(FakeError, match="Invalid object name"):
        reader().ping()
    assert len(calls) == 1


def test_context_manager_closes(opened: Callable[..., Any]) -> None:
    fake = FakeConnection((["Ping"], [(1,)]))
    opened(fake)

    with reader() as db:
        db.ping()

    assert fake.closed


# =============================================================================
# TEST: list_companies
# =============================================================================

COMPANY_COLUMNS = ["CompanyKey", "Description", "Status", "Notes"]


def test_list_companies_filters_active_by_default(opened: Callable[..., Any]) -> None:
    fake = FakeConnection((COMPANY_COLUMNS, [(1, "Firm", 1, "note")]))
    opened(fake)

    companies = reader().list_companies()

    assert companies == [
        Company(company_key=1, description="Firm", status="Active", notes="note")
    ]
    statement, params = fake.executed[0]
    assert statement.endswith("WHERE ([cmpStatus] IN (?))")
    assert params == (1,)


def test_list_companies_unfiltered_has_no_where(opened: Callable[..., Any]) -> None:
    fake = FakeConnection((COMPANY_COLUMNS, []))
    opened(fake)

    reader().list_companies(filter_by_status=None)

    statement, params = fake.executed[0]
    assert "WHERE" not in statement
    assert params == ()


def test_list_companies_sorts_and_defaults_nulls(opened: Callable[..., Any]) -> None:
    rows = [(2, "Zeta", 0, None), (1, "Alpha", 1, None)]
    opened(FakeConnection((COMPANY_COLUMNS, rows)))

    companies = reader().list_companies(filter_by_status=["Active", "Inactive"])

    # Ordered by description, as the REST response model orders it, and a
    # NULL lands as the model default rather than failing validation.
    assert [company.description for company in companies] == ["Alpha", "Zeta"]
    assert [company.status for company in companies] == ["Active", "Inactive"]
    assert all(company.notes == "" for company in companies)


def test_list_companies_rejects_unknown_filter() -> None:
    with pytest.raises(ValueError, match="Unknown AxCompany status value"):
        reader().list_companies(filter_by_status=["Archived"])


def test_list_companies_rejects_undocumented_code(opened: Callable[..., Any]) -> None:
    opened(FakeConnection((COMPANY_COLUMNS, [(1, "Firm", 7, None)])))

    with pytest.raises(ValueError, match="Unknown AxCompany status code: 7"):
        reader().list_companies(filter_by_status=None)


def test_timeout_discards_the_connection(opened: Callable[..., Any]) -> None:
    timed_out = FakeConnection(FakeError("HYT00", "Timeout expired"))
    fresh = FakeConnection((["Ping"], [(1,)]))
    calls = opened(timed_out, fresh)
    db = reader()

    with pytest.raises(FakeError, match="Timeout expired"):
        db.ping()
    assert timed_out.closed
    assert db.ping() is True
    assert len(calls) == 2
