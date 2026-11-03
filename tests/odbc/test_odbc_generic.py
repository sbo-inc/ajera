"""
Offline coverage of the generic database reads and the generated models.

A small hand-written model stands in for the generated ones so the SQL each
read produces can be asserted exactly; a fake DB-API connection answers the
live-column lookup and then a scripted sequence of results.
"""

import ast
import importlib.util
import inspect
import json
import keyword
import re
import threading
import typing
from collections.abc import Callable, Sequence
from datetime import date, datetime
from decimal import Decimal
from enum import IntEnum
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest
from click.testing import CliRunner
from pydantic import Field

from ajera.cli import cli
from ajera.cli.commands import odbc as odbc_cli
from ajera.client import AjeraClient
from ajera.odbc import (
    AjeraOdbc,
    Measure,
    avg,
    count,
    count_distinct,
    filters,
    max_,
    min_,
    sum_,
)
from ajera.odbc import arguments as odbc_arguments
from ajera.odbc import connection as odbc_connection
from ajera.odbc import reader as odbc_reader
from ajera.odbc.queries import select as select_queries
from ajera.odbc.queries.mirror import MIRRORS, mirror_list
from ajera.odbc.queries.select import select
from ajera.schemas.database import (
    CODE_LABELS,
    FUNCTIONS,
    SENSITIVE_COLUMNS,
    SOURCES,
    TABLES,
    VIEWS,
    Code,
    FieldSchema,
    TransactionRecord,
    TransactionStatus,
    describe,
)
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
            # The HDP driver reads the connection's query timeout when a
            # statement executes.
            self.connection.timeouts.append(self.connection.query_timeout)
            response = self.connection.responses.pop(0)
            if isinstance(response, Exception):
                raise response
            columns, rows = response
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
    def __init__(
        self,
        *responses: tuple[list[str], list[tuple[Any, ...]]] | Exception,
        live: Sequence[tuple[str, str]] = LIVE,
    ) -> None:
        self.live = live
        self.responses = list(responses)
        self.executed: list[tuple[str, tuple[object, ...]]] = []
        self.attributes: list[tuple[int, int]] = []
        self.timeouts: list[int | None] = []
        self.query_timeout: int | None = None
        self.closed = False
        self.fail_set_attr = False

    def cursor(self) -> FakeCursor:
        return FakeCursor(self)

    def set_attr(self, attribute: int, value: int) -> None:
        if self.fail_set_attr:
            raise RuntimeError("HY000", "set_attr failed")
        self.attributes.append((attribute, value))
        self.query_timeout = value

    def close(self) -> None:
        self.closed = True

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
    assert set(source.sensitive) <= set(aliases)
    assert {source.current_column, source.deleted_column} - {None} <= set(aliases)
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


# =============================================================================
# FIXTURES: a versioned stand-in, for the #30 reads
# =============================================================================


class EntryStatus(Code):
    billable = 0
    hold = 2


class Entry(DatabaseRecord):
    __source__ = Source(
        kind="table",
        name="AxEntry",
        primary_key=("eKey",),
        foreign_keys={"eWidget": ("AxWidget", "wKey")},
        blobs=("eFile",),
        current_column="eIsCurrent",
        deleted_column="eIsDeleted",
        sensitive=("eAccountNumber",),
    )

    entry_key: int = Field(alias="eKey", json_schema_extra={"sql_type": "int"})
    widget_key: int | None = Field(
        None, alias="eWidget", json_schema_extra={"sql_type": "int"}
    )
    status: EntryStatus | int = Field(
        alias="eStatus",
        union_mode="left_to_right",
        json_schema_extra={"sql_type": "tinyint"},
    )
    posted: datetime = Field(alias="eDate", json_schema_extra={"sql_type": "datetime"})
    units: Decimal = Field(alias="eUnits", json_schema_extra={"sql_type": "decimal"})
    notes: str | None = Field(
        None, alias="eNotes", json_schema_extra={"sql_type": "varchar"}
    )
    account_number: str | None = Field(
        None,
        alias="eAccountNumber",
        repr=False,
        json_schema_extra={"sql_type": "varchar", "sensitive": True},
    )
    file: bytes | None = Field(
        None, alias="eFile", json_schema_extra={"sql_type": "image"}
    )
    is_current: bool = Field(alias="eIsCurrent", json_schema_extra={"sql_type": "bit"})
    is_deleted: bool = Field(alias="eIsDeleted", json_schema_extra={"sql_type": "bit"})


ENTRY_LIVE = [
    ("eKey", "int"),
    ("eWidget", "int"),
    ("eStatus", "tinyint"),
    ("eDate", "datetime"),
    ("eUnits", "decimal"),
    ("eNotes", "varchar"),
    ("eAccountNumber", "varchar"),
    ("eFile", "image"),
    ("eIsCurrent", "bit"),
    ("eIsDeleted", "bit"),
    ("e_Hours", "decimal"),
    ("e_Due", "date"),
    ("e_Scan", "varbinary"),
]


class Posting(DatabaseRecord):
    __source__ = Source(kind="view", name="Postings", current_column="pIsCurrent")

    is_current: bool = Field(alias="pIsCurrent")


class Pair(DatabaseRecord):
    __source__ = Source(kind="table", name="AxPair", primary_key=("aKey", "bKey"))

    a_key: int = Field(alias="aKey")
    b_key: int = Field(alias="bKey")


START, END = date(2026, 1, 1), date(2026, 3, 31)


# =============================================================================
# TEST: aggregate statements
# =============================================================================


def test_aggregate_renders_the_issue_example() -> None:
    query = select_queries.aggregate(
        Entry,
        [sum_("units", alias="hours"), count()],
        group_by=["widget_key", "posted:month"],
        where=select_queries.with_current(
            Entry,
            {"status": EntryStatus.billable, "posted": filters.between(START, END)},
        ),
    )

    month = "DATEFROMPARTS(YEAR([eDate]), MONTH([eDate]), 1)"
    assert query.statement == (
        f"SELECT [eWidget] AS [widget_key], {month} AS [posted:month], "
        "SUM([eUnits]) AS [hours], COUNT_BIG(*) AS [count] "
        "FROM [dbo].[AxEntry] "
        "WHERE [eStatus] = ? AND [eDate] BETWEEN ? AND ? "
        "AND [eIsCurrent] = ? AND [eIsDeleted] = ? "
        f"GROUP BY [eWidget], {month} "
        "ORDER BY [widget_key], [posted:month]"
    )
    assert query.parameters == (EntryStatus.billable, START, END, True, False)


@pytest.mark.parametrize(
    "bucket, expression",
    [
        ("day", "CAST([eDate] AS date)"),
        (
            "week",
            "DATEADD(day, -(DATEDIFF(day, 0, [eDate]) % 7), CAST([eDate] AS date))",
        ),
        ("month", "DATEFROMPARTS(YEAR([eDate]), MONTH([eDate]), 1)"),
        (
            "quarter",
            "DATEFROMPARTS(YEAR([eDate]), (DATEPART(quarter, [eDate]) - 1) * 3 + 1, 1)",
        ),
        ("year", "DATEFROMPARTS(YEAR([eDate]), 1, 1)"),
    ],
)
def test_aggregate_buckets(bucket: str, expression: str) -> None:
    query = select_queries.aggregate(Entry, [count()], group_by=[f"posted:{bucket}"])

    assert query.statement == (
        f"SELECT {expression} AS [posted:{bucket}], COUNT_BIG(*) AS [count] "
        f"FROM [dbo].[AxEntry] GROUP BY {expression} ORDER BY [posted:{bucket}]"
    )


def test_aggregate_buckets_a_custom_date_column_by_its_live_type() -> None:
    query = select_queries.aggregate(
        Entry, [count()], group_by=["e_Due:year"], live=dict(ENTRY_LIVE)
    )

    assert "DATEFROMPARTS(YEAR([e_Due]), 1, 1) AS [e_Due:year]" in query.statement


@pytest.mark.parametrize(
    "measure, expression",
    [
        (sum_("units"), "SUM([eUnits]) AS [sum_units]"),
        (avg("eUnits"), "AVG([eUnits]) AS [avg_units]"),
        (min_("posted"), "MIN([eDate]) AS [min_posted]"),
        (max_("status"), "MAX([eStatus]) AS [max_status]"),
        (
            count_distinct("widget_key"),
            "COUNT_BIG(DISTINCT [eWidget]) AS [count_distinct_widget_key]",
        ),
        (count(), "COUNT_BIG(*) AS [count]"),
        (count(alias="rows"), "COUNT_BIG(*) AS [rows]"),
        (sum_("e_Hours"), "SUM([e_Hours]) AS [sum_e_hours]"),
    ],
)
def test_aggregate_measures(measure: Measure, expression: str) -> None:
    query = select_queries.aggregate(Entry, [measure], live=dict(ENTRY_LIVE))

    # No group keys: one row, no GROUP BY, no order.
    assert query.statement == f"SELECT {expression} FROM [dbo].[AxEntry]"


def test_aggregate_over_a_function_binds_arguments_after_the_limit() -> None:
    query = select_queries.aggregate(
        WidgetTotals,
        [count()],
        group_by=["widget_key"],
        where={"widget_key": filters.gt(5)},
        order_by=["-count"],
        limit=3,
        arguments=(START, END),
    )

    assert query.statement == (
        "SELECT TOP (?) [wKey] AS [widget_key], COUNT_BIG(*) AS [count] "
        "FROM [dbo].[WidgetTotals](?, ?) WHERE [wKey] > ? "
        "GROUP BY [wKey] ORDER BY [count] DESC"
    )
    assert query.parameters == (3, START, END, 5)


@pytest.mark.parametrize(
    "measures, group_by, order_by, message",
    [
        ([count()], ["nope"], None, "no field or column named 'nope'"),
        ([sum_("nope")], [], None, "no field or column named 'nope'"),
        (
            [sum_("status")],
            [],
            None,
            "SUM needs a numeric field; 'status' is a code column",
        ),
        ([avg("notes")], [], None, "AVG needs a numeric field; 'notes' is not numeric"),
        ([count()], ["units:month"], None, "a month bucket needs a date field"),
        ([count()], ["posted:decade"], None, "unknown bucket 'decade'"),
        ([count()], ["file"], None, "cannot group by binary field 'file'"),
        ([max_("file")], [], None, "cannot aggregate binary field 'file'"),
        ([min_("e_Scan")], [], None, "cannot aggregate binary field 'e_Scan'"),
        ([count(), count()], [], None, "measure alias 'count' collides"),
        ([sum_("units", alias="widget_key")], ["widget_key"], None, "collides"),
        ([count()], ["status", "status"], None, "group key 'status' collides"),
        ([count(alias="two words")], [], None, "not a Python identifier"),
        ([count()], ["status"], ["units"], "order_by 'units' names neither"),
        ([Measure("COUNT", "units")], [], None, "count\\(\\) takes no field"),
        ([Measure("SUM")], [], None, "SUM needs a field"),
        ([Measure("DROP", "units")], [], None, "unknown aggregate function 'DROP'"),  # type: ignore[arg-type]
        ([], [], None, "at least one measure"),
    ],
)
def test_aggregate_refuses(
    measures: list[Measure],
    group_by: list[str],
    order_by: list[str] | None,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        select_queries.aggregate(
            Entry, measures, group_by=group_by, order_by=order_by, live=dict(ENTRY_LIVE)
        )


def test_aggregate_decodes_group_codes_and_keeps_measures(
    connect: Callable[..., AjeraOdbc],
) -> None:
    fake = FakeConnection(
        (
            ["status", "posted:month", "sum_units", "count"],
            [
                (2, date(2026, 1, 1), Decimal("7.50"), 3),
                (9, date(2026, 2, 1), None, 1),
            ],
        ),
        live=ENTRY_LIVE,
    )

    rows = connect(fake).aggregate(
        Entry, measures=[sum_("units"), count()], group_by=["status", "posted:month"]
    )

    assert rows[0] == {
        "status": EntryStatus.hold,
        "posted:month": date(2026, 1, 1),
        "sum_units": Decimal("7.50"),
        "count": 3,
    }
    assert rows[0]["status"] is EntryStatus.hold
    # An undocumented code stays an int; a NULL total stays None.
    assert rows[1]["status"] == 9 and not isinstance(rows[1]["status"], EntryStatus)
    assert rows[1]["sum_units"] is None


# =============================================================================
# TEST: rows (projected reads)
# =============================================================================


def test_rows_select_named_fields_plus_the_key(
    connect: Callable[..., AjeraOdbc],
) -> None:
    fake = FakeConnection(
        (
            ["eKey", "eUnits", "eStatus", "e_Hours"],
            [(1, Decimal("1.25"), 2, Decimal("3")), (2, Decimal("0"), 7, None)],
        ),
        live=ENTRY_LIVE,
    )

    rows = connect(fake).rows(Entry, fields=["units", "eStatus", "e_Hours", "units"])

    assert fake.reads[0][0] == (
        "SELECT TOP (?) [eKey], [eUnits], [eStatus], [e_Hours] "
        "FROM [dbo].[AxEntry] ORDER BY [eKey]"
    )
    assert rows == [
        {
            "entry_key": 1,
            "units": Decimal("1.25"),
            "status": EntryStatus.hold,
            "e_Hours": Decimal("3"),
        },
        {"entry_key": 2, "units": Decimal("0"), "status": 7, "e_Hours": None},
    ]
    assert rows[0]["status"] is EntryStatus.hold
    assert isinstance(rows[0]["units"], Decimal)


def test_rows_fetch_a_binary_column_only_when_named(
    connect: Callable[..., AjeraOdbc],
) -> None:
    fake = FakeConnection(
        (["eKey", "eUnits"], [(1, Decimal("1"))]),
        (["eKey", "eFile"], [(1, b"\x00")]),
        live=ENTRY_LIVE,
    )
    db = connect(fake)

    db.rows(Entry, fields=["units"])
    rows = db.rows(Entry, fields=["file"])

    assert "[eFile]" not in fake.reads[0][0]
    assert "[eFile]" in fake.reads[1][0]
    assert rows == [{"entry_key": 1, "file": b"\x00"}]


def test_rows_of_a_function_take_its_arguments(
    connect: Callable[..., AjeraOdbc],
) -> None:
    fake = FakeConnection((["wKey"], [(4,)]))

    rows = connect(fake).rows(WidgetTotals, START, END, fields=["widget_key"])

    assert fake.reads[0] == (
        "SELECT [wKey] FROM [dbo].[WidgetTotals](?, ?)",
        (START, END),
    )
    assert rows == [{"widget_key": 4}]


@pytest.mark.parametrize("fields", [[], "units"])
def test_rows_need_a_list_of_fields(
    connect: Callable[..., AjeraOdbc], fields: Any
) -> None:
    with pytest.raises(ValueError, match="non-empty list"):
        connect(FakeConnection(live=ENTRY_LIVE)).rows(Entry, fields=fields)


def test_rows_refuse_unknown_fields(connect: Callable[..., AjeraOdbc]) -> None:
    with pytest.raises(ValueError, match="no field or column named 'nope'"):
        connect(FakeConnection(live=ENTRY_LIVE)).rows(Entry, fields=["nope"])


# =============================================================================
# TEST: after= (keyset cursor)
# =============================================================================


def test_after_resumes_past_a_key(
    connect: Callable[..., AjeraOdbc], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(odbc_reader, "PAGE_SIZE", 2)
    page = ["wKey", "wStatus"]
    fake = FakeConnection((page, [(41, 1), (42, 1)]), (page, [(43, 1)]))

    rows = connect(fake).read(Widget, after=40, where={"status": 1})

    assert [row.widget_key for row in rows] == [41, 42, 43]
    assert "WHERE [wStatus] = ? AND [wKey] > ? ORDER BY [wKey]" in fake.reads[0][0]
    assert [params for _, params in fake.reads] == [(2, 1, 40), (2, 1, 42)]


def test_after_works_on_rows_and_in_explicit_key_order(
    connect: Callable[..., AjeraOdbc],
) -> None:
    fake = FakeConnection((["eKey", "eUnits"], [(8, Decimal("1"))]), live=ENTRY_LIVE)

    rows = connect(fake).rows(Entry, fields=["units"], after=7, order_by=["entry_key"])

    assert "[eKey] > ?" in fake.reads[0][0]
    assert rows == [{"entry_key": 8, "units": Decimal("1")}]


@pytest.mark.parametrize(
    "model, options, message",
    [
        (Pair, {}, "AxPair does not have"),
        (WidgetView, {}, "Widgets does not have"),
        (Widget, {"offset": 10}, "cannot be combined with offset"),
        (Widget, {"order_by": ["amount"]}, "leave order_by out or order by 'wKey'"),
        (Widget, {"order_by": ["-widget_key"]}, "reads in key order"),
    ],
)
def test_after_needs_key_order_on_a_single_key(
    connect: Callable[..., AjeraOdbc],
    model: type[DatabaseRecord],
    options: dict[str, Any],
    message: str,
) -> None:
    fake = FakeConnection(live=[("wKey", "int"), ("aKey", "int"), ("bKey", "int")])

    with pytest.raises(ValueError, match=message):
        connect(fake).read(model, after=1, **options)
    assert fake.reads == []


# =============================================================================
# TEST: current=True
# =============================================================================


def test_current_adds_both_markers_as_parameters(
    connect: Callable[..., AjeraOdbc],
) -> None:
    fake = FakeConnection((["Rows"], [(5,)]), live=ENTRY_LIVE)

    total = connect(fake).count(Entry, where={"status": 0}, current=True)

    assert total == 5
    assert fake.reads[0] == (
        "SELECT COUNT_BIG(*) AS Rows FROM [dbo].[AxEntry] "
        "WHERE [eStatus] = ? AND [eIsCurrent] = ? AND [eIsDeleted] = ?",
        (0, True, False),
    )


def test_current_on_read_and_with_one_marker(connect: Callable[..., AjeraOdbc]) -> None:
    fake = FakeConnection(
        (["eKey"], []),
        (["pIsCurrent"], []),
        live=[("eKey", "int"), ("pIsCurrent", "bit")],
    )
    db = connect(fake)

    db.read(Entry, current=True)
    db.read(Posting, current=True)

    assert (
        "WHERE [eIsCurrent] = ? AND [eIsDeleted] = ? ORDER BY [eKey]"
        in fake.reads[0][0]
    )
    # A view with only a current marker gets only that predicate.
    assert fake.reads[1][0].endswith("FROM [dbo].[Postings] WHERE [pIsCurrent] = ?")
    assert fake.reads[1][1] == (True,)


def test_current_raises_on_an_unversioned_source(
    connect: Callable[..., AjeraOdbc],
) -> None:
    with pytest.raises(ValueError, match="AxWidget keeps no row versions"):
        connect(FakeConnection()).count(Widget, current=True)


@pytest.mark.parametrize("name", ["is_current", "eIsDeleted"])
def test_current_raises_on_a_conflicting_where(name: str) -> None:
    with pytest.raises(ValueError, match=f"drop '{name}' from where"):
        select_queries.with_current(Entry, {name: True})


# =============================================================================
# TEST: per-call timeout
# =============================================================================


def test_timeout_applies_to_one_call_and_is_restored(
    connect: Callable[..., AjeraOdbc],
) -> None:
    fake = FakeConnection((["Rows"], [(1,)]), (["Rows"], [(2,)]))
    db = connect(fake)

    db.count(Widget, timeout=7)
    db.count(Widget)

    # The statement ran with the call's timeout; the connection then went
    # back to the reader's own (300 s), which the next statement used.
    assert fake.timeouts == [7, 300]
    assert fake.attributes == [
        (odbc_connection.SQL_ATTR_QUERY_TIMEOUT, 7),
        (odbc_connection.SQL_ATTR_QUERY_TIMEOUT, 300),
    ]


def test_timeout_reaches_every_page_and_function_calls(
    connect: Callable[..., AjeraOdbc], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(odbc_reader, "PAGE_SIZE", 1)
    page = ["wKey", "wStatus"]
    fake = FakeConnection((page, [(1, 1)]), (page, []), (["wKey"], []))
    db = connect(fake)

    db.read(Widget, timeout=0)
    db.call(WidgetTotals, START, END, timeout=60)

    assert fake.timeouts == [0, 0, 60]


def test_a_timed_out_call_discards_the_connection(
    connect: Callable[..., AjeraOdbc], monkeypatch: pytest.MonkeyPatch
) -> None:
    first = FakeConnection(RuntimeError("HYT00", "Query timeout expired"))
    second = FakeConnection((["Rows"], [(3,)]))
    connections = iter([first, second])
    discarded: list[object] = []

    def discard(connection: object) -> threading.Thread:
        discarded.append(connection)
        thread = threading.Thread(target=lambda: None)
        thread.start()
        return thread

    monkeypatch.setattr(odbc_connection, "connect", lambda *a, **k: next(connections))
    monkeypatch.setattr(odbc_reader, "_close_in_background", discard)
    db = AjeraOdbc(datasource="ds", username="user", password="secret")

    with pytest.raises(RuntimeError, match="HYT00"):
        db.count(Widget, timeout=1)

    # Discarded in the background rather than restored, and the next read
    # opens a fresh connection.
    assert discarded == [first]
    assert first.attributes == [(odbc_connection.SQL_ATTR_QUERY_TIMEOUT, 1)]
    assert db.count(Widget) == 3
    assert second.attributes == []


def test_a_timed_out_connection_closes_off_the_calling_thread() -> None:
    fake = FakeConnection()

    thread = odbc_reader._close_in_background(fake)  # type: ignore[arg-type]
    thread.join(timeout=5)

    assert thread.daemon and fake.closed


def test_a_failed_restore_discards_the_connection(
    connect: Callable[..., AjeraOdbc],
) -> None:
    fake = FakeConnection((["Rows"], [(1,)]))
    db = connect(fake)
    original = fake.set_attr

    def set_once(attribute: int, value: int) -> None:
        original(attribute, value)
        fake.fail_set_attr = True

    fake.set_attr = set_once  # type: ignore[method-assign]

    assert db.count(Widget, timeout=5) == 1
    assert fake.closed


def test_timeout_must_not_be_negative(connect: Callable[..., AjeraOdbc]) -> None:
    with pytest.raises(ValueError, match="timeout must be 0"):
        connect(FakeConnection()).count(Widget, timeout=-1)


# =============================================================================
# TEST: describe
# =============================================================================


def test_describe_the_stand_in(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(CODE_LABELS, EntryStatus, {0: "Billable", 2: "On Hold"})

    schema = describe(Entry)

    assert (schema.name, schema.kind, schema.model) == ("AxEntry", "table", "Entry")
    assert schema.primary_key == ("eKey",)
    assert (schema.current_column, schema.deleted_column) == (
        "eIsCurrent",
        "eIsDeleted",
    )
    fields = {field.name: field for field in schema.fields}
    assert list(fields) == list(Entry.model_fields)
    assert fields["status"] == FieldSchema(
        name="status",
        column="eStatus",
        sql_type="tinyint",
        python_type="EntryStatus | int",
        nullable=False,
        enum="EntryStatus",
        codes={0: "Billable", 2: "On Hold"},
        references=None,
        sensitive=False,
        blob=False,
    )
    assert fields["widget_key"].references == ("AxWidget", "wKey")
    assert fields["widget_key"].nullable and fields["widget_key"].python_type == "int"
    assert fields["account_number"].sensitive
    assert fields["file"].blob and fields["file"].sql_type == "image"
    assert EntryStatus.hold.label == "On Hold"


def test_describe_a_generated_source() -> None:
    schema = describe(TransactionRecord)
    status = next(field for field in schema.fields if field.column == "tStatus")

    assert schema.current_column == "tIsCurrent"
    assert status.enum == "TransactionStatus"
    assert status.codes[4] == "Write Off" == TransactionStatus.write_off.label
    assert status.sql_type == "tinyint"


def test_cli_describe_needs_no_connection() -> None:
    text = CliRunner().invoke(cli, ["odbc", "describe", "axtransaction"])
    as_json = CliRunner().invoke(cli, ["odbc", "describe", "PayCheck", "--json"])

    assert text.exit_code == 0, text.output
    assert "current: tIsCurrent" in text.output
    assert "Write Off" in text.output
    assert as_json.exit_code == 0, as_json.output
    payload = json.loads(as_json.output)
    assert (payload["name"], payload["current_column"]) == ("PayCheck", "tIsCurrent")


# =============================================================================
# TEST: the generator's metadata
# =============================================================================

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts" / "odbc"


@pytest.fixture(scope="module")
def generator() -> Any:
    spec = importlib.util.spec_from_file_location(
        "odbc_generate", SCRIPTS / "generate.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def catalog() -> dict[str, Any]:
    return dict(json.loads((SCRIPTS / "catalog.json").read_text()))


def test_sensitive_columns_match_the_pattern(
    generator: Any, catalog: dict[str, Any]
) -> None:
    expected = {
        column["name"]
        for group in catalog.values()
        for source in group.values()
        for column in source["columns"]
        if generator.SENSITIVE.search(column["name"])
    }

    assert SENSITIVE_COLUMNS == expected
    for name, model in SOURCES.items():
        source = model.__source__
        flagged = {
            info.alias
            for info in model.model_fields.values()
            if isinstance(info.json_schema_extra, dict)
            and info.json_schema_extra.get("sensitive")
        }
        assert set(source.sensitive) == flagged, name
        assert flagged <= SENSITIVE_COLUMNS


def test_version_markers_match_the_catalog() -> None:
    markers = {
        name: (model.__source__.current_column, model.__source__.deleted_column)
        for name, model in SOURCES.items()
        if model.__source__.current_column or model.__source__.deleted_column
    }

    assert markers == {
        "AxTransaction": ("tIsCurrent", "tIsDeleted"),
        "CurrentTransactions": ("tIsCurrent", "tIsDeleted"),
        "Trans": ("tIsCurrent", "tIsDeleted"),
        "PayCheckPay": ("tIsCurrent", "tIsDeleted"),
        "PayCheck": ("tIsCurrent", None),
        "AxGLDetail": ("gldIsCurrent", None),
        "GLDetail": ("gldIsCurrent", None),
        "GLDetailWithOffset": ("gldIsCurrent", None),
        "AxVendorInvoiceApproval": ("viaIsCurrent", None),
    }


def test_generator_refuses_two_markers_on_one_source(generator: Any) -> None:
    columns = [
        {"name": "aIsCurrent", "type": "bit"},
        {"name": "bIsCurrent", "type": "bit"},
    ]

    with pytest.raises(SystemExit, match="AxTwice has 2 columns"):
        generator.marker("AxTwice", columns, generator.CURRENT)


def test_every_code_has_its_documented_label() -> None:
    documented = json.loads((SCRIPTS / "enums.json").read_text())
    covered: set[type[Code]] = set()

    for name, model in TABLES.items():
        for info in model.model_fields.values():
            enum = next(
                (
                    m
                    for m in typing.get_args(info.annotation)
                    if isinstance(m, type) and issubclass(m, Code)
                ),
                None,
            )
            spec = documented.get(info.alias or "")
            if enum is None or spec is None or spec["table"] != name:
                continue
            covered.add(enum)
            assert {member.value: member.label for member in enum} == {
                int(code): label for code, label in spec["codes"].items()
            }

    assert covered == set(CODE_LABELS)


# =============================================================================
# TEST: sessions still closing after a timeout
# =============================================================================


class SlowClose(FakeConnection):
    """A connection whose close waits, as the driver's does after a timeout."""

    def __init__(self, *responses: Any, release: threading.Event) -> None:
        super().__init__(*responses)
        self.release = release

    def close(self) -> None:
        self.release.wait(5)
        super().close()


def test_closing_sessions_are_counted_until_they_close(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    release = threading.Event()
    first = SlowClose(RuntimeError("HYT00", "Query timeout expired"), release=release)
    second = FakeConnection((["Rows"], [(3,)]))
    connections = iter([first, second])
    monkeypatch.setattr(odbc_connection, "connect", lambda *a, **k: next(connections))
    db = AjeraOdbc(datasource="ds", username="user", password="secret")
    assert (db.closing, db.sessions) == (0, 0)

    with pytest.raises(RuntimeError, match="HYT00"):
        db.count(Widget, timeout=1)

    # The timed-out session is still held; the reader has no open one.
    assert (db.closing, db.sessions) == (1, 1)
    assert db.count(Widget) == 3
    assert (db.closing, db.sessions) == (1, 2)
    assert db.wait_closed(timeout=0.05) is False

    release.set()

    assert db.wait_closed() is True
    assert first.closed
    assert (db.closing, db.sessions) == (0, 1)
    db.close()
    assert db.sessions == 0


# =============================================================================
# TEST: function argument checks
# =============================================================================


@pytest.mark.parametrize(
    "declaration, value, expected",
    [
        ("smalldatetime", None, None),
        ("smalldatetime", date(2026, 3, 31), date(2026, 3, 31)),
        ("smalldatetime", datetime(2026, 3, 31, 8), datetime(2026, 3, 31, 8)),
        ("smalldatetime", "2026-03-31", date(2026, 3, 31)),
        ("smalldatetime", "2026-03-31T08:00", datetime(2026, 3, 31, 8)),
        ("tinyint", 2, 2),
        ("tinyint", WidgetStatus.active, 1),
        ("int", -5, -5),
        ("bit", False, False),
        ("bit", 1, True),
        ("decimal(19,2)", Decimal("600.50"), Decimal("600.50")),
        ("decimal(19,2)", 600, 600),
        ("varchar(10)", "A", "A"),
        ("varchar(max)", "x" * 50, "x" * 50),
        ("uniqueidentifier", "anything", "anything"),
    ],
)
def test_arguments_accepted(declaration: str, value: object, expected: object) -> None:
    checked = odbc_arguments.check_argument("F", "P", declaration, value)

    assert checked == expected
    assert type(checked) is type(expected)


@pytest.mark.parametrize(
    "declaration, value, error, message",
    [
        ("smalldatetime", 2026, TypeError, "not int 2026"),
        ("smalldatetime", True, TypeError, "not bool True"),
        ("smalldatetime", "2026", ValueError, "ISO 8601"),
        ("smalldatetime", "31/03/2026", ValueError, "ISO 8601"),
        ("smalldatetime", date(1899, 12, 31), ValueError, "out of range"),
        ("smalldatetime", "2026-03-31T08:00+02:00", ValueError, "no time zone"),
        ("tinyint", Decimal("1.7"), TypeError, "takes an int, not Decimal 1.7"),
        ("tinyint", True, TypeError, "not bool True"),
        ("tinyint", "2", TypeError, "not str '2'"),
        ("tinyint", 300, ValueError, "holds 0 to 255"),
        ("bit", 5, ValueError, "True, False, 0, or 1"),
        ("bit", "A", TypeError, "takes a bool"),
        ("decimal(19,2)", Decimal("600.005"), ValueError, "would be rounded"),
        ("decimal(19,2)", 10**17, ValueError, "at most 17 digits"),
        ("decimal(19,2)", 0.5, TypeError, "a float cannot hold"),
        ("decimal(19,2)", Decimal("NaN"), ValueError, "finite"),
        ("varchar(10)", date(2026, 3, 31), TypeError, "takes a str"),
        ("varchar(10)", "x" * 11, ValueError, "cut short"),
    ],
)
def test_arguments_refused(
    declaration: str, value: object, error: type[Exception], message: str
) -> None:
    with pytest.raises(error, match=f"F @P \\({re.escape(declaration)}\\).*{message}"):
        odbc_arguments.check_argument("F", "P", declaration, value)


def test_a_bad_argument_never_reaches_the_server(
    connect: Callable[..., AjeraOdbc],
) -> None:
    fake = FakeConnection()
    db = connect(fake)

    with pytest.raises(TypeError, match=r"ProjectTotals @StartDate \(smalldatetime\)"):
        db.project_totals(2026, date(2026, 3, 31))  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="ProjectTotals @StartDate"):
        db.count(FUNCTIONS["ProjectTotals"], 2026, date(2026, 3, 31))

    assert fake.reads == []


def test_checked_arguments_are_bound_converted() -> None:
    query = select(
        FUNCTIONS["AxFinancials"],
        ["glaKey"],
        arguments=("2026-01-01", date(2026, 3, 31), 0, "Accrual"),
    )

    assert query.parameters == (date(2026, 1, 1), date(2026, 3, 31), False, "Accrual")


def test_parameter_types_match_the_catalog(
    generator: Any, catalog: dict[str, Any]
) -> None:
    for name, function in catalog["functions"].items():
        source = FUNCTIONS[name].__source__
        expected = tuple(generator.declaration(p) for p in function["parameters"])

        assert source.parameter_types == expected, name
        assert len(source.parameter_types) == len(source.parameters), name
        assert describe(FUNCTIONS[name]).parameter_types == expected

    assert FUNCTIONS["AxFinancials"].__source__.parameter_types == (
        "smalldatetime",
        "smalldatetime",
        "bit",
        "varchar(10)",
    )
    assert FUNCTIONS["Ax1099Totals"].__source__.parameter_types[0] == "decimal(19,2)"


def test_cli_reads_arguments_by_sql_type() -> None:
    model = FUNCTIONS["AxFinancials"]

    values = odbc_cli._arguments(
        model, ("2026-01-01", "2026-03-31", "false", "Accrual")
    )

    assert values == [date(2026, 1, 1), date(2026, 3, 31), False, "Accrual"]
    assert odbc_cli._arguments(
        FUNCTIONS["ReceiptTotals"], ("2026-01-01", "2026-03-31", "null", "7", "0")
    )[2:] == [None, 7, False]


@pytest.mark.parametrize(
    "arguments, message",
    [
        (["2026", "2026-03-31"], "ISO 8601"),
        (
            ["2026-01-01"],
            "takes 2 arguments: @StartDate smalldatetime, @EndDate smalldatetime",
        ),
    ],
)
def test_cli_refuses_bad_arguments(arguments: list[str], message: str) -> None:
    result = CliRunner().invoke(cli, ["odbc", "call", "ProjectTotals", *arguments])

    assert result.exit_code == 2
    assert message in " ".join(result.output.split())


def test_cli_describe_prints_parameter_types() -> None:
    result = CliRunner().invoke(cli, ["odbc", "describe", "AxFinancials"])

    assert result.exit_code == 0, result.output
    assert (
        "parameters: @StartDate smalldatetime, @EndDate smalldatetime, "
        "@CloseYear bit, @AccrualCash varchar(10)"
    ) in result.output


# =============================================================================
# TEST: parameters a function ignores
# =============================================================================

BALANCES = "Its balances stay current."


class GadgetTotals(DatabaseRecord):
    __source__ = Source(
        kind="function",
        name="GadgetTotals",
        parameters=("Kind", "StartDate", "EndDate", "Client"),
        ignored_parameters=("Kind", "StartDate", "EndDate"),
        parameter_filters={"StartDate": "gDate", "EndDate": "gDate"},
        parameter_notes={"StartDate": BALANCES, "EndDate": BALANCES},
    )

    gadget_key: int = Field(alias="gKey")
    date: datetime | None = Field(None, alias="gDate")


def ignored_warnings(caplog: pytest.LogCaptureFixture) -> list[str]:
    return [
        record.getMessage()
        for record in caplog.records
        if record.name == "ajera.odbc.arguments" and record.levelname == "WARNING"
    ]


GADGET_READS: dict[str, Callable[[AjeraOdbc, tuple[object, ...]], object]] = {
    "call": lambda db, arguments: db.call(GadgetTotals, *arguments),
    "rows": lambda db, arguments: db.rows(GadgetTotals, *arguments, fields=["date"]),
    "count": lambda db, arguments: db.count(GadgetTotals, *arguments),
    "aggregate": lambda db, arguments: db.aggregate(
        GadgetTotals, *arguments, measures=[count()]
    ),
}
GADGET_RESPONSES = {
    "call": (["gKey", "gDate"], [(1, None)]),
    "rows": (["gKey", "gDate"], [(1, None)]),
    "count": (["Rows"], [(1,)]),
    "aggregate": (["count"], [(1,)]),
}


@pytest.mark.parametrize("read", sorted(GADGET_READS))
def test_a_value_for_an_ignored_parameter_is_logged_and_the_call_runs(
    read: str,
    connect: Callable[..., AjeraOdbc],
    caplog: pytest.LogCaptureFixture,
) -> None:
    fake = FakeConnection(GADGET_RESPONSES[read])
    # The reader quiets the `ajera` logger unless asked to log statements;
    # this warning is about the rows, so it is logged regardless.
    db = connect(fake)

    result = GADGET_READS[read](db, (3, START, END, 7))

    assert result
    assert fake.reads[0][1][-4:] == (3, START, END, 7)
    assert ignored_warnings(caplog) == [
        "GadgetTotals ignores @Kind, @StartDate, and @EndDate: its rows are the "
        "same whatever they hold, so pass None. Filter on date instead. " + BALANCES
    ]


def test_none_for_an_ignored_parameter_is_not_logged(
    connect: Callable[..., AjeraOdbc], caplog: pytest.LogCaptureFixture
) -> None:
    db = connect(FakeConnection(GADGET_RESPONSES["call"]))

    db.call(GadgetTotals, None, None, None, 7)

    assert ignored_warnings(caplog) == []


def test_a_parameter_without_a_filter_is_named_alone(
    caplog: pytest.LogCaptureFixture,
) -> None:
    odbc_arguments.warn_ignored(GadgetTotals, (3, None, None, None))

    assert ignored_warnings(caplog) == [
        "GadgetTotals ignores @Kind: its rows are the same whatever they hold, "
        "so pass None."
    ]


def test_a_typed_method_logs_its_ignored_arguments(
    connect: Callable[..., AjeraOdbc], caplog: pytest.LogCaptureFixture
) -> None:
    fake = FakeConnection((["rKey"], []))

    rows = connect(fake).receipt_totals(START, END, None, None, False)

    assert rows == []
    assert fake.reads[0][1] == (START, END, False)
    assert ignored_warnings(caplog) == [
        "ReceiptTotals ignores @StartDate and @EndDate: its rows are the same "
        "whatever they hold, so pass None. Filter on r_date instead."
    ]


class WidgetPeriods(DatabaseRecord):
    __source__ = Source(
        kind="function",
        name="WidgetPeriods",
        parameters=("TotalType", "StartDate", "EndDate"),
        ignored_when={
            "StartDate": {"TotalType": (0, None)},
            "EndDate": {"TotalType": (0, None)},
        },
    )

    widget_key: int = Field(alias="wKey")


@pytest.mark.parametrize(
    "arguments, expected",
    [
        (
            (0, START, END),
            [
                "WidgetPeriods ignores @StartDate and @EndDate when @TotalType is 0: "
                "its rows are the same whatever they hold. Pass another @TotalType "
                "to apply them."
            ],
        ),
        (
            (None, START, None),
            [
                "WidgetPeriods ignores @StartDate when @TotalType is NULL: its rows "
                "are the same whatever they hold. Pass another @TotalType to apply "
                "them."
            ],
        ),
        ((2, START, END), []),
        ((0, None, None), []),
    ],
)
def test_a_parameter_ignored_under_a_code_is_logged_only_under_it(
    arguments: tuple[object, ...],
    expected: list[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    odbc_arguments.warn_ignored(WidgetPeriods, arguments)

    assert ignored_warnings(caplog) == expected


def test_describe_and_the_cli_report_conditions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(SOURCES, "WidgetPeriods", WidgetPeriods)

    schema = describe(WidgetPeriods)
    result = CliRunner().invoke(cli, ["odbc", "describe", "WidgetPeriods"])

    assert schema.ignored_parameters == ()
    assert schema.ignored_when["StartDate"] == {"TotalType": (0, None)}
    assert result.exit_code == 0, result.output
    assert "ignored: @StartDate, @EndDate when @TotalType is 0 or NULL" in result.output


def test_the_known_functions_record_their_ignored_parameters() -> None:
    receipts = describe(FUNCTIONS["ReceiptTotals"])
    invoices = describe(FUNCTIONS["ClientInvoiceTotals"])

    assert receipts.ignored_parameters == ("StartDate", "EndDate")
    assert receipts.parameter_filters == {"StartDate": "rDate", "EndDate": "rDate"}
    assert receipts.parameter_notes == {}
    # Probed live, against the issue's report: TotalType changes the invoice
    # amounts, and the dates apply under every code but 0 and NULL.
    assert invoices.ignored_parameters == ()
    for name in ("StartDate", "EndDate"):
        codes = invoices.ignored_when[name]["TotalType"]
        assert 0 in codes and None in codes and 1 not in codes


def test_ignored_parameters_match_the_catalog(
    generator: Any, catalog: dict[str, Any]
) -> None:
    for name, function in catalog["functions"].items():
        source = FUNCTIONS[name].__source__
        aliases = {info.alias for info in FUNCTIONS[name].model_fields.values()}
        listed = function.get("ignored_parameters", [])

        assert source.ignored_parameters == tuple(
            p for p in source.parameters if p in listed
        ), name
        assert set(listed) <= set(source.parameters), name
        assert dict(source.parameter_filters) == function.get("parameter_filters", {})
        assert dict(source.parameter_notes) == function.get("parameter_notes", {})
        assert {
            p: {code: tuple(values) for code, values in conditions.items()}
            for p, conditions in function.get("ignored_when", {}).items()
        } == {p: dict(c) for p, c in source.ignored_when.items()}, name
        assert not set(source.ignored_when) & set(source.ignored_parameters), name
        assert set(source.parameter_filters) <= set(source.ignored_parameters), name
        assert set(source.parameter_filters.values()) <= aliases, name
        assert not set(listed) & set(function.get("unchecked_parameters", [])), name


def test_typed_method_docs_name_their_ignored_arguments() -> None:
    doc = AjeraOdbc.receipt_totals.__doc__ or ""

    assert "ignores `start_date` and `end_date`" in " ".join(doc.split())
    assert "Filter on `r_date` instead." in " ".join(doc.split())
    assert "ignores" not in (AjeraOdbc.project_totals.__doc__ or "")


def test_cli_describe_prints_ignored_parameters() -> None:
    result = CliRunner().invoke(cli, ["odbc", "describe", "ReceiptTotals"])
    as_json = CliRunner().invoke(cli, ["odbc", "describe", "ReceiptTotals", "--json"])

    assert result.exit_code == 0, result.output
    assert "ignored: @StartDate, @EndDate (Filter on r_date instead.)" in result.output
    assert json.loads(as_json.output)["parameter_filters"] == {
        "StartDate": "rDate",
        "EndDate": "rDate",
    }


def test_harvest_keeps_probe_results_for_declared_parameters(tmp_path: Path) -> None:
    spec = importlib.util.spec_from_file_location(
        "odbc_harvest", SCRIPTS / "harvest.py"
    )
    assert spec and spec.loader
    harvest = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(harvest)
    previous = tmp_path / "catalog.json"
    previous.write_text(
        json.dumps(
            {
                "functions": {
                    "F": {
                        "ignored_parameters": ["StartDate", "Gone"],
                        "parameter_filters": {"StartDate": "fDate", "Gone": "fDate"},
                        "unchecked_parameters": ["Gone"],
                        "start_date_columns": {"fAmount": True, "fGone": False},
                    }
                }
            }
        )
    )
    fresh = {
        "functions": {
            "F": {
                "parameters": [{"name": "StartDate"}],
                "columns": [{"name": "fAmount"}],
            }
        }
    }

    harvest.carry_probed(fresh, previous)

    assert fresh["functions"]["F"] == {
        "parameters": [{"name": "StartDate"}],
        "columns": [{"name": "fAmount"}],
        "ignored_parameters": ["StartDate"],
        "parameter_filters": {"StartDate": "fDate"},
        # Keyed by column, so kept for the columns the function still returns.
        "start_date_columns": {"fAmount": True},
    }


def test_none_function_arguments_are_written_as_null() -> None:
    # The HDP driver refuses a NULL bound to a date parameter (HY104).
    query = select(
        FUNCTIONS["ReceiptTotals"],
        ["rKey"],
        where={"r_date": filters.between(START, END)},
        arguments=(None, None, None, 7, False),
    )

    assert "FROM [dbo].[ReceiptTotals](NULL, NULL, NULL, ?, ?) WHERE" in query.statement
    assert query.parameters == (7, False, START, END)


# =============================================================================
# TEST: column notes
# =============================================================================


@pytest.fixture
def probe(monkeypatch: pytest.MonkeyPatch) -> Any:
    monkeypatch.syspath_prepend(str(SCRIPTS))
    spec = importlib.util.spec_from_file_location("odbc_probe", SCRIPTS / "probe.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ScriptedFingerprints:
    """Returns each `by_column` result in turn: base, other, then both again."""

    def __init__(self, *results: tuple[int, dict[str, tuple[object, ...]]]) -> None:
        self.results = iter(results)
        self.amounts = ["month", "year", "budget", "edited"]
        self.volatile: list[str] = []

    def by_column(
        self, arguments: tuple[object, ...], fresh: bool = False
    ) -> tuple[int, dict[str, tuple[object, ...]]]:
        return next(self.results)


def test_probe_records_the_columns_start_date_changes(probe: Any) -> None:
    # Each column's aggregates: the sum of absolute values, then a checksum.
    base = {"month": (10, 1), "year": (5, 1), "budget": (0, 0), "edited": (3, 1)}
    other = {"month": (7, 2), "year": (5, 1), "budget": (0, 0), "edited": (4, 2)}
    # Between the pairs, a row of `edited` was changed, so it moved only once.
    again = {**base, "edited": (4, 2)}
    fingerprint = ScriptedFingerprints((9, base), (9, other), (9, again), (9, other))

    found = probe.start_date_columns(fingerprint, (), ())

    # `budget` is zero in every row and proves nothing.
    assert found == {"month": True, "year": False}


def test_probe_records_no_columns_when_start_date_changes_the_rows(
    probe: Any,
) -> None:
    columns = {"month": (1, 1), "year": (1, 1), "budget": (1, 1), "edited": (1, 1)}
    fingerprint = ScriptedFingerprints(
        (9, columns), (8, columns), (9, columns), (8, columns)
    )

    assert probe.start_date_columns(fingerprint, (), ()) is None


def test_fingerprint_sums_absolute_values_and_checksums_numbers(probe: Any) -> None:
    covered = probe.fingerprint_columns(FUNCTIONS["AxFinancials"])
    aggregates = [a for column, a in covered if column == "glaCurrentMonth"]

    # Debits and credits cancel in a plain sum.
    assert aggregates == [
        "SUM(ABS(CAST([glaCurrentMonth] AS decimal(38, 6))))",
        "CHECKSUM_AGG(BINARY_CHECKSUM([glaCurrentMonth]))",
    ]
    assert "glaCurrentMonth" in probe.amount_columns(FUNCTIONS["AxFinancials"])
    assert "glaKey" not in probe.amount_columns(FUNCTIONS["AxFinancials"])


def test_generated_dicts_keep_quotes_and_apostrophes(generator: Any) -> None:
    extra = {"sql_type": "decimal", "note": 'The account\'s "balance".', "x": True}

    assert ast.literal_eval(generator.python_dict(extra)) == extra


def test_generator_appends_the_probe_finding_to_each_note(
    generator: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    written = {
        "fName": "A name.",
        "fMonth": "The range.",
        "fRange": "From @StartDate through @EndDate.",
    }
    monkeypatch.setattr(generator, "NOTES", {"F": written})
    columns = ("fName", "fMonth", "fRange", "fYear", "fOther")
    source = {
        "columns": [{"name": c} for c in columns],
        "start_date_columns": {"fYear": False, "fMonth": True, "fRange": True},
    }

    notes = generator.column_notes("F", source)

    assert notes == {
        "fName": "A name.",
        "fMonth": "The range. Changes with @StartDate.",
        # A note that says how @StartDate acts is left as written.
        "fRange": "From @StartDate through @EndDate.",
        "fYear": "@StartDate does not change it.",
    }
    assert list(notes) == ["fName", "fMonth", "fRange", "fYear"]


def test_generator_refuses_a_note_on_a_missing_column(
    generator: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(generator, "NOTES", {"F": {"fGone": "Gone."}})

    with pytest.raises(SystemExit, match="F has no column fGone"):
        generator.column_notes("F", {"columns": [{"name": "fName"}]})


def test_notes_match_the_catalog(generator: Any, catalog: dict[str, Any]) -> None:
    for group in catalog.values():
        for name, source in group.items():
            model = SOURCES[name]
            expected = generator.column_notes(name, source)
            notes = {
                info.alias: info.json_schema_extra.get("note")
                for info in model.model_fields.values()
                if isinstance(info.json_schema_extra, dict)
                and info.json_schema_extra.get("note")
            }

            assert notes == expected, name
            for column, moved in source.get("start_date_columns", {}).items():
                written = generator.NOTES.get(name, {}).get(column, "")
                assert "@StartDate" in written or notes[column].endswith(
                    generator.START_DATE[moved]
                ), name


def test_describe_has_no_note_for_a_plain_column() -> None:
    fields = {f.column: f for f in describe(TransactionRecord).fields}

    assert fields["tStatus"].note is None


def test_describe_returns_the_financials_period_notes() -> None:
    fields = {f.name: f for f in describe(FUNCTIONS["AxFinancials"]).fields}
    month = " ".join((fields["current_month"].note or "").split())
    year = " ".join((fields["current_ytd_balance"].note or "").split())

    assert "the activity from @StartDate through @EndDate" in month
    assert "not a calendar month" in month
    assert "the fiscal year that holds @EndDate" in year
    assert "the balance at @EndDate" in year
    assert "`last_day_current_fiscal_year`" in year
    # The probe's sentence, on a column the hand-written note leaves to it.
    assert (fields["prior_year_ytd_balance"].note or "").endswith(
        "@StartDate does not change it."
    )
    # The `_MC` variants were checked live to behave the same.
    for name in ("AxFinancials_MC", "AxFinancials_MC_TrialBalance"):
        variant = {f.name: f.note for f in describe(FUNCTIONS[name]).fields}
        assert all(variant[f.name] == f.note for f in fields.values()), name


def test_cli_describe_prints_field_notes() -> None:
    result = CliRunner().invoke(cli, ["odbc", "describe", "ProjectTotals"])
    text = " ".join(result.output.split())

    assert result.exit_code == 0, result.output
    assert "The unbilled part of the work charged from @StartDate" in text
    assert "neither @StartDate nor @EndDate changes it" in text


def test_describe_returns_the_project_to_date_and_aging_notes() -> None:
    fields = {
        f.name: " ".join((f.note or "").split())
        for f in describe(FUNCTIONS["ProjectTotals"]).fields
    }

    for name in ("total_receipts", "total_billed_by_date", "payments"):
        assert "neither @StartDate nor @EndDate changes it" in fields[name], name
    assert "Signed the opposite way" in fields["total_billed_by_date"]
    assert fields["billed_outstanding"] == (
        "Changes with @EndDate. @StartDate does not change it."
    )
    assert "Signed" not in fields["total_billed"]
