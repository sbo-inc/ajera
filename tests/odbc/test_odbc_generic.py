"""
Offline coverage of the generic database reads and the generated models.

A small hand-written model stands in for the generated ones so the SQL each
read produces can be asserted exactly; a fake DB-API connection answers the
live-column lookup and then a scripted sequence of results.
"""

import inspect
import keyword
import typing
from collections.abc import Callable, Sequence
from datetime import date
from decimal import Decimal
from enum import IntEnum
from typing import Any
from uuid import UUID

import pytest
from click.testing import CliRunner
from pydantic import Field

from ajera.cli import cli
from ajera.cli.commands import odbc as odbc_cli
from ajera.client import AjeraClient
from ajera.odbc import AjeraOdbc, filters
from ajera.odbc import connection as odbc_connection
from ajera.odbc import reader as odbc_reader
from ajera.odbc.queries import select as select_queries
from ajera.odbc.queries.mirror import MIRRORS, mirror_list
from ajera.odbc.queries.select import select
from ajera.schemas.database import FUNCTIONS, SOURCES, TABLES, VIEWS
from ajera.schemas.database.base import DatabaseRecord, Source

# =============================================================================
# FIXTURES: a stand-in model and a scripted connection
# =============================================================================


class WidgetStatus(IntEnum):
    inactive = 0
    active = 1


class Widget(DatabaseRecord):
    __source__ = Source(
        kind="table", name="AxWidget", primary_key=("wKey",), blobs=("wImage",)
    )

    widget_key: int = Field(alias="wKey")
    status: WidgetStatus | int = Field(alias="wStatus", union_mode="left_to_right")
    amount: Decimal | None = Field(None, alias="wAmount")
    image: bytes | None = Field(None, alias="wImage")


class WidgetView(DatabaseRecord):
    __source__ = Source(kind="view", name="Widgets")

    widget_key: int = Field(alias="wKey")


class WidgetTotals(DatabaseRecord):
    __source__ = Source(
        kind="function", name="WidgetTotals", parameters=("StartDate", "EndDate")
    )

    widget_key: int = Field(alias="wKey")


LIVE = [
    ("wKey", "int"),
    ("wStatus", "tinyint"),
    ("wAmount", "decimal"),
    ("wImage", "image"),
    ("w_Custom", "varchar"),
]
COLUMNS = ["wKey", "wStatus", "wAmount", "w_Custom"]


class FakeCursor:
    def __init__(self, connection: "FakeConnection") -> None:
        self.connection = connection
        self.description: Sequence[Sequence[object]] = ()
        self.rows: list[tuple[Any, ...]] = []

    def execute(self, sql: str, *params: object) -> "FakeCursor":
        self.connection.executed.append((sql, params))
        if "INFORMATION_SCHEMA" in sql:
            columns, rows = ["COLUMN_NAME", "DATA_TYPE"], list(self.connection.live)
        else:
            columns, rows = self.connection.responses.pop(0)
        self.description = [(column, None) for column in columns]
        self.rows = rows
        return self

    def fetchall(self) -> list[tuple[Any, ...]]:
        rows, self.rows = self.rows, []
        return rows

    def fetchmany(self, size: int) -> list[tuple[Any, ...]]:
        rows, self.rows = self.rows[:size], self.rows[size:]
        return rows

    def close(self) -> None:
        pass


class FakeConnection:
    def __init__(self, *responses: tuple[list[str], list[tuple[Any, ...]]]) -> None:
        self.live = LIVE
        self.responses = list(responses)
        self.executed: list[tuple[str, tuple[object, ...]]] = []

    def cursor(self) -> FakeCursor:
        return FakeCursor(self)

    def close(self) -> None:
        pass

    @property
    def reads(self) -> list[tuple[str, tuple[object, ...]]]:
        return [
            entry for entry in self.executed if "INFORMATION_SCHEMA" not in entry[0]
        ]


@pytest.fixture
def connect(monkeypatch: pytest.MonkeyPatch) -> Callable[..., AjeraOdbc]:
    def install(fake: FakeConnection) -> AjeraOdbc:
        monkeypatch.setattr(odbc_connection, "connect", lambda *a, **k: fake)
        return AjeraOdbc(datasource="ds", username="user", password="secret")

    return install


# =============================================================================
# TEST: statement building
# =============================================================================


def test_select_reads_in_key_order_with_brackets() -> None:
    query = select(Widget, COLUMNS, limit=10)

    assert query.statement == (
        "SELECT TOP (?) [wKey], [wStatus], [wAmount], [w_Custom] "
        "FROM [dbo].[AxWidget] ORDER BY [wKey]"
    )
    assert query.parameters == (10,)


@pytest.mark.parametrize(
    "value, predicate, parameters",
    [
        (5, "[wAmount] = ?", (5,)),
        (None, "[wAmount] IS NULL", ()),
        ([1, 2], "[wAmount] IN (?, ?)", (1, 2)),
        ([], "1 = 0", ()),
        (filters.not_in([]), "1 = 1", ()),
        (filters.not_in([3]), "[wAmount] NOT IN (?)", (3,)),
        (filters.ne(1), "[wAmount] <> ?", (1,)),
        (filters.gt(1), "[wAmount] > ?", (1,)),
        (filters.ge(1), "[wAmount] >= ?", (1,)),
        (filters.lt(1), "[wAmount] < ?", (1,)),
        (filters.le(1), "[wAmount] <= ?", (1,)),
        (filters.between(1, 9), "[wAmount] BETWEEN ? AND ?", (1, 9)),
        (filters.like("A%"), "[wAmount] LIKE ?", ("A%",)),
        (filters.not_null(), "[wAmount] IS NOT NULL", ()),
        (
            UUID(int=1),
            "[wAmount] = ?",
            ("00000000-0000-0000-0000-000000000001",),
        ),
    ],
)
def test_where_renders_every_operator(
    value: object, predicate: str, parameters: tuple[object, ...]
) -> None:
    query = select(Widget, COLUMNS, where={"amount": value})

    assert f" WHERE {predicate} ORDER BY" in query.statement
    assert query.parameters == parameters


def test_where_accepts_field_alias_and_custom_column() -> None:
    query = select(Widget, COLUMNS, where={"wStatus": 1, "w_Custom": "x"})

    assert "WHERE [wStatus] = ? AND [w_Custom] = ?" in query.statement


def test_where_rejects_unknown_names() -> None:
    with pytest.raises(ValueError, match="no field or column named 'nope'"):
        select(Widget, COLUMNS, where={"nope": 1})


def test_order_by_descending_and_offset_paging() -> None:
    query = select(Widget, COLUMNS, order_by=["-amount"], offset=20, limit=10)

    assert query.statement.endswith(
        "ORDER BY [wAmount] DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
    )
    assert query.parameters == (20, 10)


def test_offset_needs_an_order_on_an_unkeyed_view() -> None:
    with pytest.raises(ValueError, match="offset needs order_by"):
        select(WidgetView, ["wKey"], offset=5)


def test_after_bounds_the_key() -> None:
    query = select(Widget, COLUMNS, where={"status": 1}, after=40)

    assert "WHERE [wStatus] = ? AND [wKey] > ? ORDER BY [wKey]" in query.statement
    assert query.parameters == (1, 40)


def test_function_arguments_are_bound_in_order() -> None:
    query = select(
        WidgetTotals, ["wKey"], arguments=(date(2026, 1, 1), date(2026, 3, 31))
    )

    assert query.statement == "SELECT [wKey] FROM [dbo].[WidgetTotals](?, ?)"
    assert query.parameters == (date(2026, 1, 1), date(2026, 3, 31))


def test_function_argument_count_is_checked() -> None:
    with pytest.raises(TypeError, match=r"takes 2 arguments \(StartDate, EndDate\)"):
        select(WidgetTotals, ["wKey"], arguments=(date(2026, 1, 1),))


def test_tables_take_no_arguments() -> None:
    with pytest.raises(TypeError, match="takes no arguments"):
        select(Widget, COLUMNS, arguments=(1,))


def test_count_statement() -> None:
    query = select_queries.count(Widget, where={"status": [0, 1]})

    assert query.statement == (
        "SELECT COUNT_BIG(*) AS Rows FROM [dbo].[AxWidget] WHERE [wStatus] IN (?, ?)"
    )
    assert query.parse([{"Rows": 7}]) == 7


# =============================================================================
# TEST: reading through the reader
# =============================================================================


def test_read_leaves_blobs_out_and_keeps_custom_fields(
    connect: Callable[..., AjeraOdbc],
) -> None:
    fake = FakeConnection(
        (COLUMNS, [(1, 1, Decimal("1.10"), "custom"), (2, 7, None, None)])
    )

    rows = connect(fake).read(Widget)

    statement = fake.reads[0][0]
    assert "[wImage]" not in statement
    assert rows[0].status is WidgetStatus.active
    assert rows[0].amount == Decimal("1.10")
    assert rows[0].custom_fields == {"w_Custom": "custom"}
    # An undocumented code stays a plain int rather than failing the read.
    assert rows[1].status == 7 and not isinstance(rows[1].status, WidgetStatus)
    assert rows[1].amount is None


def test_read_includes_blobs_on_request(connect: Callable[..., AjeraOdbc]) -> None:
    fake = FakeConnection(
        (["wKey", "wStatus", "wImage"], [(1, 1, b"\x00\x01")]),
    )

    rows = connect(fake).read(Widget, include_blobs=True)

    assert "[wImage]" in fake.reads[0][0]
    assert rows[0].image == b"\x00\x01"


def test_large_reads_page_by_key(
    connect: Callable[..., AjeraOdbc], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(odbc_reader, "PAGE_SIZE", 2)
    page = ["wKey", "wStatus"]
    fake = FakeConnection(
        (page, [(1, 1), (2, 1)]), (page, [(3, 1), (4, 1)]), (page, [(5, 1)])
    )

    rows = connect(fake).read(Widget)

    assert [row.widget_key for row in rows] == [1, 2, 3, 4, 5]
    assert [params for _, params in fake.reads] == [(2,), (2, 2), (2, 4)]
    assert "[wKey] > ?" in fake.reads[1][0]


def test_paging_honours_the_limit(
    connect: Callable[..., AjeraOdbc], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(odbc_reader, "PAGE_SIZE", 2)
    page = ["wKey", "wStatus"]
    fake = FakeConnection((page, [(1, 1), (2, 1)]), (page, [(3, 1)]))

    rows = connect(fake).read(Widget, limit=3)

    assert len(rows) == 3
    assert [params for _, params in fake.reads] == [(2,), (1, 2)]


def test_reads_in_another_order_are_one_statement(
    connect: Callable[..., AjeraOdbc],
) -> None:
    fake = FakeConnection((["wKey", "wStatus"], [(2, 1), (1, 1)]))

    connect(fake).read(Widget, order_by=["-widget_key"])

    assert len(fake.reads) == 1
    assert fake.reads[0][0].endswith("ORDER BY [wKey] DESC")


def test_get_batches_keys(
    connect: Callable[..., AjeraOdbc], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(select_queries, "KEY_BATCH", 2)
    monkeypatch.setattr(odbc_reader, "KEY_BATCH", 2)
    page = ["wKey", "wStatus"]
    fake = FakeConnection((page, [(1, 1), (2, 1)]), (page, [(3, 1)]))

    rows = connect(fake).get(Widget, 1, 2, 3)

    assert [row.widget_key for row in rows] == [1, 2, 3]
    # Each batch is one IN lookup, after the page size.
    assert [params[1:] for _, params in fake.reads] == [(1, 2), (3,)]


def test_kinds_are_enforced(connect: Callable[..., AjeraOdbc]) -> None:
    db = connect(FakeConnection())

    with pytest.raises(TypeError, match="use call"):
        db.read(WidgetTotals)
    with pytest.raises(TypeError, match="not a function"):
        db.call(Widget)


# =============================================================================
# TEST: the generated catalog
# =============================================================================


def test_registries_cover_every_source() -> None:
    assert len(TABLES) == 165
    assert len(VIEWS) == 60
    assert len(FUNCTIONS) == 19
    assert SOURCES == {**TABLES, **VIEWS, **FUNCTIONS}


@pytest.mark.parametrize("name", sorted(SOURCES))
def test_generated_model_is_consistent(name: str) -> None:
    model = SOURCES[name]
    source = model.__source__
    aliases = [field.alias for field in model.model_fields.values()]

    assert source.name == name
    assert len(aliases) == len(set(aliases))
    assert all(
        f.isidentifier() and not keyword.iskeyword(f) for f in model.model_fields
    )
    assert set(source.primary_key) <= set(aliases)
    assert set(source.foreign_keys) <= set(aliases)
    assert set(source.blobs) <= set(aliases)
    assert (source.kind == "function") == bool(
        source.parameters
    ) or not source.parameters
    model.model_rebuild(force=True)


# =============================================================================
# TEST: the CLI
# =============================================================================


def test_cli_where_parsing() -> None:
    model = SOURCES["AxTransaction"]

    where = odbc_cli._where(
        model,
        ("project_key=12", "date>=2026-01-01", "status=0,3", "notes~%fee%", "hours!=0"),
    )

    assert where["project_key"] == 12
    assert where["date"] == filters.ge(where["date"].values[0])  # type: ignore[attr-defined]
    assert [int(code) for code in where["status"]] == [0, 3]  # type: ignore[attr-defined]
    assert where["notes"] == filters.like("%fee%")
    assert where["hours"].operator == "<>"  # type: ignore[attr-defined]


def test_cli_sources_needs_no_connection() -> None:
    result = CliRunner().invoke(cli, ["odbc", "sources", "--kind", "function"])

    assert result.exit_code == 0
    assert "ProjectTotals" in result.output
    assert "(@StartDate, @EndDate)" in result.output


def test_cli_read_renders_json(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, Any]] = []

    def read(self: AjeraOdbc, model: type[DatabaseRecord], **kwargs: Any) -> list[Any]:
        calls.append({"model": model, **kwargs})
        return [model.model_construct(company_key=1)]

    monkeypatch.setattr(AjeraOdbc, "read", read)
    result = CliRunner().invoke(
        cli, ["odbc", "read", "axcompany", "-w", "status=1", "-n", "5"]
    )

    assert result.exit_code == 0, result.output
    assert calls[0]["model"] is TABLES["AxCompany"]
    assert calls[0]["where"] == {"status": 1}
    assert calls[0]["limit"] == 5
    assert '"company_key": 1' in result.output


# =============================================================================
# TEST: REST-shaped mirrors
# =============================================================================


def test_mirror_selects_rest_aliases_and_filters_status() -> None:
    query = mirror_list(MIRRORS["list_activities"], filter_by_status=["Active"])

    assert query.statement.startswith(
        "SELECT [actKey] AS [ActivityKey], [actDescription] AS [Description]"
    )
    assert query.statement.endswith(
        "FROM [dbo].[AxActivity] WHERE ([actStatus] IN (?))"
    )
    assert query.parameters == (1,)


def test_mirror_like_filter_uses_contains() -> None:
    query = mirror_list(
        MIRRORS["list_activities"],
        filter_by_status=None,
        filter_by_description_like="Travel",
    )

    assert query.statement.endswith("WHERE ([actDescription] LIKE ?)")
    assert query.parameters == ("%Travel%",)


def test_mirror_rejects_unknown_filters() -> None:
    with pytest.raises(TypeError, match="no REST filter 'filter_by_nope'"):
        mirror_list(MIRRORS["list_pays"], filter_by_status=None, filter_by_nope=1)


def test_mirror_decodes_status_and_sorts_like_rest() -> None:
    query = mirror_list(MIRRORS["list_pays"], filter_by_status=None)

    pays = query.parse(
        [
            {"PayKey": 2, "Description": "Salary", "Status": 1},
            {"PayKey": 1, "Description": "Hourly", "Status": 0},
        ]
    )

    assert [(pay.description, pay.status) for pay in pays] == [
        ("Hourly", "Inactive"),
        ("Salary", "Active"),
    ]


@pytest.mark.parametrize("method", sorted(MIRRORS))
def test_every_mirror_has_a_reader_method_matching_rest(method: str) -> None:
    rest = inspect.signature(getattr(AjeraClient, method))
    odbc = inspect.signature(getattr(AjeraOdbc, method))

    assert list(odbc.parameters) == list(rest.parameters)
    assert (
        typing.get_type_hints(getattr(AjeraOdbc, method))["return"]
        == (typing.get_type_hints(getattr(AjeraClient, method))["return"])
    )
