"""
Statements for the generic reads over any generated database model.

The model supplies everything: its `__source__` names the table, view, or
function, and its field aliases are the columns. Callers name fields; only
names that resolve against the model or the live column list reach the SQL,
and every value is a bound parameter.
"""

from collections.abc import Mapping, Sequence
from uuid import UUID

from ajera.odbc.filters import Condition
from ajera.odbc.queries.generic import Query, Record, placeholders
from ajera.schemas.database.base import DatabaseRecord

type Where = Mapping[str, object]

# SQL Server accepts at most 2100 parameters per statement; key lookups are
# split well below that.
KEY_BATCH = 1000


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
    return f"{name}({placeholders(len(arguments))})", [_bindable(a) for a in arguments]


def _where(
    model: type[DatabaseRecord], where: Where | None, live: Sequence[str]
) -> tuple[str, list[object]]:
    if not where:
        return "", []
    predicates: list[str] = []
    parameters: list[object] = []
    for name, value in where.items():
        predicate, values = condition(resolve(model, name, live), value)
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
    ordering = ", ".join(
        f"{quote_name(resolve(model, name.removeprefix('-'), columns))}"
        f"{' DESC' if name.startswith('-') else ''}"
        for name in order
    )

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
