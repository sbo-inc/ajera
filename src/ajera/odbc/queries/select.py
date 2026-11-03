"""
Statements for the generic reads over any generated database model.

The model supplies everything: its `__source__` names the table, view, or
function, and its field aliases are the columns. Callers name fields; only
names that resolve against the model or the live column list reach the SQL,
and every value is a bound parameter.
"""

import types
from collections.abc import Callable, Mapping, Sequence
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from functools import cache
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import TypeAdapter
from pydantic.fields import FieldInfo

from ajera.odbc.arguments import check_arguments, warn_ignored
from ajera.odbc.filters import Condition
from ajera.odbc.measures import Measure
from ajera.odbc.queries.generic import Query, Record, placeholders
from ajera.schemas.database.base import (
    UNSORTABLE_SQL_TYPES,
    DatabaseRecord,
    annotation_members,
)

type Where = Mapping[str, object]
type ColumnKind = Literal["code", "binary", "date", "numeric", "other"]

# SQL Server accepts at most 2100 parameters per statement; key lookups are
# split well below that.
KEY_BATCH = 1000

# Each date bucket returns the first day of its period as a `date`. None
# depends on the session's @@DATEFIRST or language: day 0 (1900-01-01) is a
# Monday, so weeks start on Monday, as in ISO 8601.
BUCKETS: dict[str, Callable[[str], str]] = {
    "day": lambda column: f"CAST({column} AS date)",
    "week": lambda column: (
        f"DATEADD(day, -(DATEDIFF(day, 0, {column}) % 7), CAST({column} AS date))"
    ),
    "month": lambda column: f"DATEFROMPARTS(YEAR({column}), MONTH({column}), 1)",
    "quarter": lambda column: (
        f"DATEFROMPARTS(YEAR({column}), (DATEPART(quarter, {column}) - 1) * 3 + 1, 1)"
    ),
    "year": lambda column: f"DATEFROMPARTS(YEAR({column}), 1, 1)",
}

# The SQL for each measure. Only these reach the statement: a `Measure` built
# by hand with any other function is refused.
AGGREGATES: dict[str, Callable[[str], str]] = {
    "SUM": lambda column: f"SUM({column})",
    "AVG": lambda column: f"AVG({column})",
    "MIN": lambda column: f"MIN({column})",
    "MAX": lambda column: f"MAX({column})",
    "COUNT_DISTINCT": lambda column: f"COUNT_BIG(DISTINCT {column})",
}

# SQL types of the tenant's custom columns, which no model declares.
NUMERIC_SQL = frozenset(
    {
        "int",
        "smallint",
        "tinyint",
        "bigint",
        "decimal",
        "numeric",
        "money",
        "smallmoney",
    }
    | {"float", "real"}
)
DATE_SQL = frozenset(
    {"date", "datetime", "datetime2", "smalldatetime", "datetimeoffset"}
)
BINARY_SQL = frozenset({"image", "varbinary", "binary", "timestamp"})
# The only conditions SQL Server takes on a column it cannot compare.
MATCHING = frozenset({"LIKE", "IS NULL", "IS NOT NULL"})


# =============================================================================
# FUNCTION: quote_name
# =============================================================================


def quote_name(name: str) -> str:
    """
    Bracket an identifier for SQL Server.

    Returns:
        str: The bracketed name, with any closing bracket doubled.
    """
    return "[" + name.replace("]", "]]") + "]"


# =============================================================================
# FUNCTION: resolve
# =============================================================================


def resolve(model: type[DatabaseRecord], name: str, live: Sequence[str] = ()) -> str:
    """
    Turn a field name, alias, or live column name into the column to use.

    Live columns cover the tenant's custom fields, which no generated model
    declares.

    Returns:
        str: The database column name.
    """
    field = model.model_fields.get(name)
    if field is not None and field.alias:
        return field.alias
    if name in live or any(f.alias == name for f in model.model_fields.values()):
        return name
    raise ValueError(f"{model.__name__} has no field or column named {name!r}")


# =============================================================================
# FUNCTIONS: per-column metadata
# =============================================================================


@cache
def _fields_by_column(model: type[DatabaseRecord]) -> dict[str, tuple[str, FieldInfo]]:
    return {
        info.alias or name: (name, info) for name, info in model.model_fields.items()
    }


def field_name(model: type[DatabaseRecord], column: str) -> str:
    """
    The field name a column is returned under in a projected read.

    Returns:
        str: The model's field name, or the column itself for a custom field.
    """
    declared = _fields_by_column(model).get(column)
    return declared[0] if declared else column


@cache
def field_adapter(model: type[DatabaseRecord], column: str) -> TypeAdapter[Any] | None:
    """
    A validator for one column's values, as the model validates them.

    The field's metadata comes along, so a code column validates
    left-to-right and decodes to its enum, as it does in a full read. Built
    once per column, because building one per row is slow.

    Returns:
        TypeAdapter | None: The validator, or None for a custom field.
    """
    declared = _fields_by_column(model).get(column)
    annotation = declared[1].annotation if declared else None
    if declared is None or annotation is None:
        return None
    metadata = declared[1].metadata
    form: Any = Annotated[annotation, *metadata] if metadata else annotation
    return TypeAdapter(form)


def decode(model: type[DatabaseRecord], column: str, value: object) -> object:
    """
    Validate one value of a column the way a full read would.

    Returns:
        object: The validated value; NULLs and custom fields as they came.
    """
    adapter = field_adapter(model, column)
    return value if adapter is None or value is None else adapter.validate_python(value)


def column_kind(
    model: type[DatabaseRecord], column: str, live: Mapping[str, str] | None = None
) -> ColumnKind:
    """
    Classify a column for the aggregate rules, by its field's type.

    A custom column has no field, so its live SQL type decides.

    Returns:
        ColumnKind: `code`, `binary`, `date`, `numeric`, or `other`.
    """
    declared = _fields_by_column(model).get(column)
    if declared is None:
        sql_type = (live or {}).get(column, "")
        if sql_type in BINARY_SQL:
            return "binary"
        if sql_type in DATE_SQL:
            return "date"
        return "numeric" if sql_type in NUMERIC_SQL else "other"

    members = [
        m for m in annotation_members(declared[1].annotation) if m is not types.NoneType
    ]
    if any(isinstance(m, type) and issubclass(m, Enum) for m in members):
        return "code"
    if bytes in members:
        return "binary"
    if date in members or datetime in members:
        return "date"
    if members and all(m in (int, Decimal, float) for m in members):
        return "numeric"
    return "other"


def unsortable(
    model: type[DatabaseRecord], column: str, live: Mapping[str, str] | None = None
) -> str | None:
    """
    The column's SQL type when SQL Server cannot compare it, else None.

    A `text`, `ntext`, `image`, or `xml` column cannot be sorted, grouped,
    compared with `=` or `IN`, or aggregated (error 306); `LIKE` and
    `IS NULL` work. A custom column has no field, so its live type decides.
    """
    declared = _fields_by_column(model).get(column)
    if declared is None:
        sql_type = (live or {}).get(column, "")
    else:
        extra = declared[1].json_schema_extra
        sql_type = str(extra.get("sql_type", "")) if isinstance(extra, dict) else ""
    return sql_type if sql_type in UNSORTABLE_SQL_TYPES else None


def refuse_unsortable(
    model: type[DatabaseRecord],
    column: str,
    name: str,
    use: str,
    live: Mapping[str, str] | None = None,
) -> None:
    """
    Raise before SQL Server does, naming the field and what it cannot do.

    Raises:
        ValueError: The column is `text`, `ntext`, `image`, or `xml`.
    """
    sql_type = unsortable(model, column, live)
    if sql_type:
        raise ValueError(
            f"cannot {use} {name!r}: SQL Server cannot compare a {sql_type} column"
        )


# =============================================================================
# FUNCTION: with_current
# =============================================================================


def with_current(model: type[DatabaseRecord], where: Where | None) -> dict[str, object]:
    """
    Add the current-version filter of a versioned source to a `where`.

    Ajera keeps earlier versions of an edited row with its current marker
    cleared, and keeps a deleted row with its deleted marker set. A read or a
    total that does not filter them counts the same work more than once.

    Returns:
        dict[str, object]: The `where`, plus `current_column = 1` and
        `deleted_column = 0` for whichever of the two the source has.
    """
    source = model.__source__
    markers = {
        column: value
        for column, value in (
            (source.current_column, True),
            (source.deleted_column, False),
        )
        if column
    }
    if not markers:
        raise ValueError(
            f"{source.name} keeps no row versions, so current=True does not apply"
        )
    merged = dict(where or {})
    for name in merged:
        declared = model.model_fields.get(name)
        column = declared.alias if declared and declared.alias else name
        if column in markers:
            raise ValueError(
                f"current=True already filters {column}; drop {name!r} from where"
            )
    merged.update(markers)
    return merged


# =============================================================================
# FUNCTION: condition
# =============================================================================


def _bindable(value: object) -> object:
    return str(value) if isinstance(value, UUID) else value


def condition(column: str, value: object) -> tuple[str, list[object]]:
    """
    Render one `where` entry as SQL and its parameters.

    A bare value means equality, a list (or tuple or set) means `IN`, and
    None means `IS NULL`; anything else is a `Condition` from
    `ajera.odbc.filters`.

    Returns:
        tuple[str, list[object]]: The predicate and its parameters.
    """
    if not isinstance(value, Condition):
        if value is None:
            value = Condition("IS NULL")
        elif isinstance(value, (list, tuple, set, frozenset)):
            value = Condition("IN", tuple(value))
        else:
            value = Condition("=", (value,))

    target = quote_name(column)
    operator = value.operator
    operands = [_bindable(item) for item in value.values]

    if operator in ("IS NULL", "IS NOT NULL"):
        return f"{target} {operator}", []
    if operator in ("IN", "NOT IN"):
        if not operands:
            # An empty IN matches nothing; an empty NOT IN excludes nothing.
            return ("1 = 0" if operator == "IN" else "1 = 1"), []
        return f"{target} {operator} ({placeholders(len(operands))})", operands
    if operator == "BETWEEN":
        return f"{target} BETWEEN ? AND ?", operands
    return f"{target} {operator} ?", operands


# =============================================================================
# FUNCTION: source_clause
# =============================================================================


def source_clause(
    model: type[DatabaseRecord], arguments: Sequence[object] = ()
) -> tuple[str, list[object]]:
    """
    Render the `FROM` target: a table or view, or a function call.

    Returns:
        tuple[str, list[object]]: The clause and the function's arguments.
    """
    source = model.__source__
    name = f"[dbo].{quote_name(source.name)}"
    if source.kind != "function":
        if arguments:
            raise TypeError(f"{source.name} is a {source.kind}; it takes no arguments")
        return name, []
    if len(arguments) != len(source.parameters):
        raise TypeError(
            f"{source.name} takes {len(source.parameters)} arguments "
            f"({', '.join(source.parameters)}), got {len(arguments)}"
        )
    checked = check_arguments(source, arguments)
    warn_ignored(model, checked)
    # None is written into the statement as NULL rather than bound: the HDP
    # driver refuses a NULL bound to a date parameter (HY104).
    slots = ", ".join("NULL" if a is None else "?" for a in checked)
    return f"{name}({slots})", [_bindable(a) for a in checked if a is not None]


def _where(
    model: type[DatabaseRecord], where: Where | None, live: Sequence[str]
) -> tuple[str, list[object]]:
    if not where:
        return "", []
    predicates: list[str] = []
    parameters: list[object] = []
    for name, value in where.items():
        column = resolve(model, name, live)
        if value is not None and not (
            isinstance(value, Condition) and value.operator in MATCHING
        ):
            refuse_unsortable(model, column, name, "compare")
        predicate, values = condition(column, value)
        predicates.append(predicate)
        parameters.extend(values)
    return " WHERE " + " AND ".join(predicates), parameters


# =============================================================================
# QUERY: select
# =============================================================================


def select[T: DatabaseRecord](
    model: type[T],
    columns: Sequence[str],
    *,
    where: Where | None = None,
    order_by: Sequence[str] | None = None,
    limit: int | None = None,
    offset: int | None = None,
    arguments: Sequence[object] = (),
    after: object | None = None,
) -> Query[list[T]]:
    """
    Build a read of `columns` from the model's source.

    A keyed source reads in key order unless told otherwise, so repeated
    reads and `offset` pages are stable. `offset` needs an order, which an
    unkeyed view or function must be given explicitly. `after` restricts the
    read to keys above a value: the reader pages large sources that way,
    because Deltek's pipeline refuses any single result over 500,000 rows.

    Returns:
        Query[list[T]]: The read, parsing each row into the model.
    """
    source = model.__source__
    target, parameters = source_clause(model, arguments)
    filters, filter_parameters = _where(model, where, columns)
    if after is not None:
        if len(source.primary_key) != 1:
            raise ValueError(f"{source.name} has no single-column key to page by")
        bound = f"{quote_name(source.primary_key[0])} > ?"
        filters = f"{filters} AND {bound}" if filters else f" WHERE {bound}"
        filter_parameters.append(after)

    order = list(order_by or source.primary_key)
    sorted_by = []
    for name in order:
        column = resolve(model, name.removeprefix("-"), columns)
        refuse_unsortable(model, column, name.removeprefix("-"), "order by")
        sorted_by.append(quote_name(column) + (" DESC" if name.startswith("-") else ""))
    ordering = ", ".join(sorted_by)

    head: list[object] = []
    top = ""
    tail = ""
    tail_parameters: list[object] = []
    if offset is not None:
        if not order:
            raise ValueError(
                f"offset needs order_by on {source.name}, which has no key"
            )
        tail = " OFFSET ? ROWS"
        tail_parameters.append(offset)
        if limit is not None:
            tail += " FETCH NEXT ? ROWS ONLY"
            tail_parameters.append(limit)
    elif limit is not None:
        top = "TOP (?) "
        head.append(limit)

    statement = (
        f"SELECT {top}{', '.join(quote_name(column) for column in columns)} "
        f"FROM {target}{filters}"
        f"{' ORDER BY ' + ordering if ordering else ''}{tail}"
    )

    def parse(records: list[Record]) -> list[T]:
        return [model.model_validate(record) for record in records]

    return Query(
        statement=statement,
        parse=parse,
        parameters=(*head, *parameters, *filter_parameters, *tail_parameters),
        keep_nulls=True,
    )


# =============================================================================
# QUERY: count
# =============================================================================


def count(
    model: type[DatabaseRecord],
    *,
    where: Where | None = None,
    arguments: Sequence[object] = (),
    live: Sequence[str] = (),
) -> Query[int]:
    """
    Build a row count over the model's source.

    Returns:
        Query[int]: The count.
    """
    target, parameters = source_clause(model, arguments)
    filters, filter_parameters = _where(model, where, live)

    def parse(records: list[Record]) -> int:
        value = records[0]["Rows"] if records else 0
        return value if isinstance(value, int) else 0

    return Query(
        statement=f"SELECT COUNT_BIG(*) AS Rows FROM {target}{filters}",
        parse=parse,
        parameters=(*parameters, *filter_parameters),
    )


# =============================================================================
# QUERY: live_columns
# =============================================================================


def live_columns(model: type[DatabaseRecord]) -> Query[list[tuple[str, str]]]:
    """
    Build the lookup of a source's columns as the database has them now.

    Returns:
        Query[list[tuple[str, str]]]: Column name and SQL type, in order.
    """
    source = model.__source__
    catalog = "ROUTINE_COLUMNS" if source.kind == "function" else "COLUMNS"

    def parse(records: list[Record]) -> list[tuple[str, str]]:
        return [(str(r["COLUMN_NAME"]), str(r["DATA_TYPE"])) for r in records]

    return Query(
        statement=(
            f"SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.{catalog} "
            "WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = ? ORDER BY ORDINAL_POSITION"
        ),
        parse=parse,
        parameters=(source.name,),
    )


# =============================================================================
# QUERY: aggregate
# =============================================================================


def aggregate(
    model: type[DatabaseRecord],
    measures: Sequence[Measure],
    *,
    group_by: Sequence[str] = (),
    where: Where | None = None,
    order_by: Sequence[str] | None = None,
    limit: int | None = None,
    arguments: Sequence[object] = (),
    live: Mapping[str, str] | None = None,
) -> Query[list[dict[str, object]]]:
    """
    Build a server-side `GROUP BY` over the model's source.

    Every column resolves against the model or the live columns, and every
    bucket and function comes from a fixed set, so nothing the caller types
    reaches the statement except a resolved name inside `quote_name`.

    Args:
        model: The model of a table, view, or function.
        measures: The totals to compute, from `ajera.odbc.measures`.
        group_by: Fields to group by; `field:day`, `field:week`,
            `field:month`, `field:quarter`, or `field:year` groups a date
            field by the first day of its period.
        where: As for `select`.
        order_by: Group keys or measure aliases, `-` for descending. Defaults
            to the group keys.
        limit: The most groups to return.
        arguments: A function's arguments, in declaration order.
        live: The source's live columns and their SQL types, for custom fields.

    Returns:
        Query[list[dict[str, object]]]: One dictionary per group, keyed by
        each `group_by` entry as spelled and each measure's alias.
    """
    if not measures:
        raise ValueError("aggregate needs at least one measure")
    live = live or {}
    target, parameters = source_clause(model, arguments)
    filters, filter_parameters = _where(model, where, list(live))

    keys: list[str] = []
    selected: list[str] = []
    grouped: list[str] = []
    decoded: dict[str, str] = {}

    def claim(key: str, what: str) -> None:
        if key in keys:
            raise ValueError(f"{what} {key!r} collides with another group key or alias")
        keys.append(key)

    for entry in group_by:
        name, _, bucket = entry.partition(":")
        column = resolve(model, name, list(live))
        kind = column_kind(model, column, live)
        expression = quote_name(column)
        if kind == "binary":
            raise ValueError(f"cannot group by binary field {name!r}")
        refuse_unsortable(model, column, name, "group by", live)
        if bucket:
            if bucket not in BUCKETS:
                raise ValueError(
                    f"{entry!r}: unknown bucket {bucket!r}; use one of "
                    + ", ".join(BUCKETS)
                )
            if kind != "date":
                raise ValueError(f"{entry!r}: a {bucket} bucket needs a date field")
            expression = BUCKETS[bucket](expression)
        else:
            decoded[entry] = column
        claim(entry, "group key")
        selected.append(f"{expression} AS {quote_name(entry)}")
        grouped.append(expression)

    for measure in measures:
        if measure.function == "COUNT":
            if measure.field is not None:
                raise ValueError("count() takes no field; use count_distinct(field)")
            expression, default = "COUNT_BIG(*)", "count"
        elif measure.function in AGGREGATES:
            if measure.field is None:
                raise ValueError(f"{measure.function} needs a field")
            column = resolve(model, measure.field, list(live))
            kind = column_kind(model, column, live)
            if kind == "binary":
                raise ValueError(f"cannot aggregate binary field {measure.field!r}")
            refuse_unsortable(model, column, measure.field, "aggregate", live)
            if measure.function in ("SUM", "AVG") and kind != "numeric":
                described = "a code column" if kind == "code" else "not numeric"
                raise ValueError(
                    f"{measure.function} needs a numeric field; "
                    f"{measure.field!r} is {described}"
                )
            expression = AGGREGATES[measure.function](quote_name(column))
            default = f"{measure.function}_{field_name(model, column)}".lower()
        else:
            raise ValueError(f"unknown aggregate function {measure.function!r}")
        alias = measure.alias or default
        if not alias.isidentifier():
            raise ValueError(
                f"measure alias {alias!r} is not a Python identifier; pass alias="
            )
        claim(alias, "measure alias")
        selected.append(f"{expression} AS {quote_name(alias)}")

    ordering: list[str] = []
    for name in order_by if order_by is not None else group_by:
        key = name.removeprefix("-")
        if key not in keys:
            raise ValueError(
                f"order_by {name!r} names neither a group key nor a measure alias"
            )
        ordering.append(quote_name(key) + (" DESC" if name.startswith("-") else ""))

    head: list[object] = []
    top = ""
    if limit is not None:
        top = "TOP (?) "
        head.append(limit)

    statement = (
        f"SELECT {top}{', '.join(selected)} FROM {target}{filters}"
        f"{' GROUP BY ' + ', '.join(grouped) if grouped else ''}"
        f"{' ORDER BY ' + ', '.join(ordering) if ordering else ''}"
    )

    def parse(records: list[Record]) -> list[dict[str, object]]:
        return [
            {
                key: decode(model, decoded[key], value) if key in decoded else value
                for key, value in record.items()
            }
            for record in records
        ]

    return Query(
        statement=statement,
        parse=parse,
        parameters=(*head, *parameters, *filter_parameters),
        keep_nulls=True,
    )
