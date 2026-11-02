"""
`ajera odbc`: read any table, view, or function in the Ajera database.

Every command resolves a source by its database name (`AxTransaction`), its
model name (`TransactionRecord`), or either case-insensitively, and prints
rows as JSON. Values given on the command line are coerced to the field's
type before they are sent, always as bound parameters.
"""

import inspect
import re
import typing
from typing import Any

import click
from pydantic import TypeAdapter

from ajera.cli.output import render
from ajera.odbc import AjeraOdbc, filters
from ajera.odbc.filters import Condition
from ajera.schemas.database import SOURCES, DatabaseRecord

WHERE = re.compile(
    r"^(?P<field>[A-Za-z_][A-Za-z0-9_]*)\s*(?P<op>>=|<=|!=|=|>|<|~)\s*(?P<value>.*)$"
)
OPERATORS = {
    ">=": filters.ge,
    "<=": filters.le,
    "!=": filters.ne,
    ">": filters.gt,
    "<": filters.lt,
}


# =============================================================================
# Helpers
# =============================================================================


def _model(name: str) -> type[DatabaseRecord]:
    if name in SOURCES:
        return SOURCES[name]
    folded = name.casefold()
    for source, model in SOURCES.items():
        if folded in (source.casefold(), model.__name__.casefold()):
            return model
    raise click.BadParameter(
        f"no table, view, or function named {name!r}; see `ajera odbc sources`"
    )


def _coerce(model: type[DatabaseRecord], field: str, raw: str) -> object:
    if raw.lower() == "null":
        return None
    info = model.model_fields.get(field) or next(
        (f for f in model.model_fields.values() if f.alias == field), None
    )
    if info is None or info.annotation is None:
        return raw  # a custom column: let the server compare as text
    return TypeAdapter(info.annotation).validate_python(raw)


def _where(model: type[DatabaseRecord], clauses: tuple[str, ...]) -> dict[str, object]:
    where: dict[str, object] = {}
    for clause in clauses:
        match = WHERE.match(clause)
        if match is None:
            raise click.BadParameter(
                f"{clause!r}: expected FIELD=VALUE, or one of != > >= < <= ~ (LIKE)"
            )
        field, op, raw = match["field"], match["op"], match["value"]
        if op == "~":
            where[field] = filters.like(raw)
        elif op == "=" and "," in raw:
            where[field] = [_coerce(model, field, part) for part in raw.split(",")]
        elif op == "=":
            where[field] = _coerce(model, field, raw)
        else:
            value = _coerce(model, field, raw)
            where[field] = (
                Condition("<>", (value,)) if op == "!=" else OPERATORS[op](value)
            )
    return where


def _function_method(model: type[DatabaseRecord]) -> Any:
    for name, method in inspect.getmembers(AjeraOdbc, inspect.isfunction):
        hints = typing.get_type_hints(method)
        if hints.get("return") == list[model]:  # type: ignore[valid-type]
            return name, method
    raise click.BadParameter(f"{model.__source__.name} has no typed method")


where_option = click.option(
    "--where",
    "-w",
    "where",
    multiple=True,
    metavar="FIELD=VALUE",
    help="Filter; repeatable, all must hold. Operators: = != > >= < <= ~ (LIKE). "
    "A comma list with = matches any; 'null' matches NULL.",
)
order_option = click.option(
    "--order-by",
    "-o",
    "order_by",
    multiple=True,
    metavar="FIELD",
    help="Sort field; repeatable. Prefix with - to sort descending.",
)
limit_option = click.option("--limit", "-n", type=int, help="Most rows to return.")
offset_option = click.option(
    "--offset", type=int, help="Rows to skip (needs an order)."
)


# =============================================================================
# GROUP: odbc
# =============================================================================


@click.group(name="odbc")
@click.pass_context
def group(ctx: click.Context) -> None:
    r"""
    Read the Ajera database over ODBC (read-only).

    \b
    Needs the `ajera[odbc]` extra, the Progress HDP ODBC driver, and:
    - AJERA_ODBC_DATASOURCE, AJERA_ODBC_USERNAME, AJERA_ODBC_PASSWORD
    - optionally AJERA_ODBC_HOST and AJERA_ODBC_PORT
    """
    reader = AjeraOdbc(log=bool(getattr(ctx.obj, "_log", False)))
    ctx.obj = ctx.with_resource(reader)


@group.command(name="ping")
@click.pass_obj
def ping(db: AjeraOdbc) -> None:
    """
    Check the connection with a round trip.
    """
    render("ok" if db.ping() else "no answer")


@group.command(name="sources")
@click.option(
    "--kind",
    type=click.Choice(["table", "view", "function"]),
    help="Only list one kind of source.",
)
def sources(kind: str | None) -> None:
    """
    List every table, view, and function, with its model and keys.

    Needs no connection: this is the catalog the models were generated from.
    """
    for name, model in SOURCES.items():
        source = model.__source__
        if kind and source.kind != kind:
            continue
        details = f"key={','.join(source.primary_key)}" if source.primary_key else ""
        if source.parameters:
            details = f"({', '.join('@' + p for p in source.parameters)})"
        click.echo(f"{source.kind:8} {name:42} {model.__name__:40} {details}".rstrip())


@group.command(name="columns")
@click.argument("source")
@click.pass_obj
def columns(db: AjeraOdbc, source: str) -> None:
    """
    List SOURCE's live columns, with their field names and SQL types.

    Includes the tenant's custom fields, which have no field name.
    """
    model = _model(source)
    by_alias = {info.alias: name for name, info in model.model_fields.items()}
    for column, kind in db.columns(model):
        click.echo(f"{column:40} {kind:18} {by_alias.get(column, '(custom)')}")


@group.command(name="read")
@click.argument("source")
@where_option
@order_option
@limit_option
@offset_option
@click.option("--include-blobs", is_flag=True, help="Also fetch binary columns.")
@click.pass_obj
def read(
    db: AjeraOdbc,
    source: str,
    where: tuple[str, ...],
    order_by: tuple[str, ...],
    limit: int | None,
    offset: int | None,
    include_blobs: bool,
) -> None:
    """
    Read rows of the table or view SOURCE.
    """
    model = _model(source)
    render(
        db.read(
            model,
            where=_where(model, where),
            order_by=list(order_by) or None,
            limit=limit,
            offset=offset,
            include_blobs=include_blobs,
        )
    )


@group.command(name="get")
@click.argument("table")
@click.argument("keys", nargs=-1, required=True)
@click.option("--include-blobs", is_flag=True, help="Also fetch binary columns.")
@click.pass_obj
def get(db: AjeraOdbc, table: str, keys: tuple[str, ...], include_blobs: bool) -> None:
    """
    Fetch rows of TABLE by primary key.
    """
    model = _model(table)
    key = model.__source__.primary_key
    values = [_coerce(model, key[0], k) for k in keys] if key else list(keys)
    render(db.get(model, *values, include_blobs=include_blobs))


@group.command(name="count")
@click.argument("source")
@click.argument("arguments", nargs=-1)
@where_option
@click.pass_obj
def count(
    db: AjeraOdbc, source: str, arguments: tuple[str, ...], where: tuple[str, ...]
) -> None:
    """
    Count the rows of SOURCE (a function takes its ARGUMENTS in order).
    """
    model = _model(source)
    values = _arguments(model, arguments) if model.__source__.kind == "function" else []
    render(str(db.count(model, *values, where=_where(model, where))))


def _arguments(model: type[DatabaseRecord], raw: tuple[str, ...]) -> list[object]:
    _, method = _function_method(model)
    hints = typing.get_type_hints(method)
    names = [p for p in inspect.signature(method).parameters if p != "self"]
    positional = names[: len(model.__source__.parameters)]
    if len(raw) != len(positional):
        raise click.BadParameter(
            f"{model.__source__.name} takes {len(positional)} arguments: "
            + ", ".join(positional)
        )
    return [
        None
        if value.lower() == "null"
        else TypeAdapter(hints[name]).validate_python(value)
        for name, value in zip(positional, raw)
    ]


@group.command(name="call")
@click.argument("function")
@click.argument("arguments", nargs=-1)
@where_option
@order_option
@limit_option
@offset_option
@click.pass_obj
def call(
    db: AjeraOdbc,
    function: str,
    arguments: tuple[str, ...],
    where: tuple[str, ...],
    order_by: tuple[str, ...],
    limit: int | None,
    offset: int | None,
) -> None:
    """
    Call the table-valued FUNCTION with ARGUMENTS in declaration order.

    Dates are ISO (2026-01-31); pass 'null' for an argument to leave it NULL.
    `ajera odbc sources --kind function` lists each function's parameters.
    """
    model = _model(function)
    render(
        db.call(
            model,
            *_arguments(model, arguments),
            where=_where(model, where),
            order_by=list(order_by) or None,
            limit=limit,
            offset=offset,
        )
    )
