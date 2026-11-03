"""
Offline descriptions of the database sources, from the generated metadata.

`describe` needs no connection: everything comes from a model's fields and
its `__source__`, which the generator took from the live catalog and Deltek's
schema documentation. `AjeraOdbc.columns` is the live view, which also lists
a tenant's custom fields.
"""

import types
from collections.abc import Mapping
from dataclasses import dataclass
from enum import IntEnum

from ajera.schemas.database.base import (
    UNSORTABLE_SQL_TYPES,
    DatabaseRecord,
    SourceKind,
    annotation_members,
)
from ajera.schemas.database.enums import Code

# =============================================================================
# CLASS: FieldSchema
# =============================================================================


@dataclass(frozen=True)
class FieldSchema:
    """
    One column of a source, as its generated model describes it.

    Attributes:
        name: The field name (`project_key`).
        column: The database column (`tProject`).
        sql_type: The column's SQL Server type (`int`, `decimal`, ...); empty
            for a hand-written model that does not record it.
        python_type: The field's type without `None` (`TransactionStatus | int`).
        nullable: Whether the field may be None. Binary columns always may,
            because a read leaves them out unless asked.
        enum: The code enum's name, when Ajera documents the column's codes.
        codes: Each documented code and Deltek's own label for it.
        references: The (table, column) the database's foreign key points at.
        sensitive: Whether the column must never reach a log line.
        blob: Whether the column is binary, and left out of a read by default.
        note: What the column holds, where its name does not say it: the
            period an amount covers, and whether a function's `StartDate`
            changes it. None for most columns.
        binary: Whether the value is bytes: a file (`blob`) or a row version
            (`timestamp`). Encode it before writing a row as JSON.
        sortable: Whether SQL Server can compare the column. False for
            `text`, `ntext`, `image`, and `xml`, which the reader refuses in
            `order_by`, `group_by`, a `where` comparison, and a measure; `like`
            and `is_null` still work.
    """

    name: str
    column: str
    sql_type: str
    python_type: str
    nullable: bool
    enum: str | None
    codes: Mapping[int, str]
    references: tuple[str, str] | None
    sensitive: bool
    blob: bool
    note: str | None = None
    binary: bool = False
    sortable: bool = True


# =============================================================================
# CLASS: SourceSchema
# =============================================================================


@dataclass(frozen=True)
class SourceSchema:
    """
    A table, view, or table-valued function, as its generated model describes it.

    Attributes:
        name: The object's name in the database (`AxTransaction`).
        kind: A table, a view, or a function.
        model: The model's class name (`TransactionRecord`).
        primary_key: The key columns; empty when the source has none.
        parameters: A function's SQL parameter names, in call order.
        parameter_types: Each parameter's SQL declaration, in the same order.
        ignored_parameters: Parameters the function declares but does not
            apply, in call order, as probed live.
        parameter_filters: For an ignored parameter, the column to filter on
            instead.
        parameter_notes: For an ignored parameter, how the result differs
            from what the parameter promises.
        ignored_when: Parameters the function ignores only under some codes,
            with those codes.
        current_column: The column marking a row's current version, if any.
        deleted_column: The column marking a deleted row Ajera keeps, if any.
        row_key: For a function, the leading key when it is unique per row.
        repeated_key: The leading key when several rows share it; `note`
            says what a row is, and the field notes which amounts repeat.
        note: What a row is, where the name does not say it.
        fields: Every column the model declares, in database order.
    """

    name: str
    kind: SourceKind
    model: str
    primary_key: tuple[str, ...]
    parameters: tuple[str, ...]
    parameter_types: tuple[str, ...]
    ignored_parameters: tuple[str, ...]
    parameter_filters: Mapping[str, str]
    parameter_notes: Mapping[str, str]
    ignored_when: Mapping[str, Mapping[str, tuple[object, ...]]]
    current_column: str | None
    deleted_column: str | None
    fields: tuple[FieldSchema, ...]
    row_key: tuple[str, ...] = ()
    repeated_key: str | None = None
    note: str | None = None


# =============================================================================
# FUNCTION: describe
# =============================================================================


def describe(model: type[DatabaseRecord]) -> SourceSchema:
    """
    Describe a source from its generated model, without connecting.

    Returns:
        SourceSchema: The source, its keys, and every declared field.
    """
    source = model.__source__
    fields = []
    for name, info in model.model_fields.items():
        column = info.alias or name
        members = annotation_members(info.annotation)
        enum = next(
            (m for m in members if isinstance(m, type) and issubclass(m, IntEnum)),
            None,
        )
        extra = (
            info.json_schema_extra if isinstance(info.json_schema_extra, dict) else {}
        )
        fields.append(
            FieldSchema(
                name=name,
                column=column,
                sql_type=str(extra.get("sql_type", "")),
                python_type=" | ".join(
                    _type_name(m) for m in members if m is not types.NoneType
                ),
                nullable=types.NoneType in members,
                enum=enum.__name__ if enum else None,
                codes=(
                    {int(code): code.label for code in enum}
                    if enum and issubclass(enum, Code)
                    else {}
                ),
                references=source.foreign_keys.get(column),
                sensitive=column in source.sensitive or bool(extra.get("sensitive")),
                blob=column in source.blobs,
                note=str(extra["note"]) if extra.get("note") else None,
                binary=bytes in members,
                sortable=extra.get("sql_type") not in UNSORTABLE_SQL_TYPES,
            )
        )
    return SourceSchema(
        name=source.name,
        kind=source.kind,
        model=model.__name__,
        primary_key=source.primary_key,
        parameters=source.parameters,
        parameter_types=source.parameter_types,
        ignored_parameters=source.ignored_parameters,
        parameter_filters=dict(source.parameter_filters),
        parameter_notes=dict(source.parameter_notes),
        ignored_when={
            name: dict(conditions) for name, conditions in source.ignored_when.items()
        },
        current_column=source.current_column,
        deleted_column=source.deleted_column,
        fields=tuple(fields),
        row_key=source.row_key,
        repeated_key=source.repeated_key,
        note=source.note,
    )


def _type_name(annotation: object) -> str:
    return getattr(annotation, "__name__", str(annotation))
