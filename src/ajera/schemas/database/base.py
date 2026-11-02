import types
import typing
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import ClassVar, Literal

from pydantic import ConfigDict

from ajera.schemas.generic import GenericBaseModel

type SourceKind = Literal["table", "view", "function"]

# =============================================================================
# CLASS: Source
# =============================================================================


@dataclass(frozen=True)
class Source:
    """
    Where a database model's rows come from, and what is known about it.

    Attached to every generated model as `__source__`, so the reader can build
    a statement from the model alone and callers can follow the database's own
    keys without a separate lookup.

    Attributes:
        kind: A table, a view, or a table-valued function.
        name: The object's name in the database (`AxTransaction`).
        primary_key: The primary-key columns; empty for views, functions, and
            the few tables without one.
        foreign_keys: Column to the (table, column) it references, as declared
            by the database's own constraints.
        blobs: Binary columns, left out of a read unless asked for, because a
            handful of them hold whole files (invoice PDFs, report designs).
        parameters: A function's SQL parameter names, in call order.
        current_column: The `bit` column that marks the current version of a
            row Ajera keeps old versions of (`tIsCurrent`), if any.
        deleted_column: The `bit` column that marks a deleted row Ajera keeps
            (`tIsDeleted`), if any.
        sensitive: Columns that must never reach a log line: identity
            numbers, credentials, tokens, and banking details. Classified by
            column name alone, so this is a fact about the name rather than a
            policy about who may read it.
    """

    kind: SourceKind
    name: str
    primary_key: tuple[str, ...] = ()
    foreign_keys: Mapping[str, tuple[str, str]] = field(default_factory=dict)
    blobs: tuple[str, ...] = ()
    parameters: tuple[str, ...] = ()
    current_column: str | None = None
    deleted_column: str | None = None
    sensitive: tuple[str, ...] = ()


# =============================================================================
# CLASS: DatabaseRecord
# =============================================================================


class DatabaseRecord(GenericBaseModel):
    """
    One row of an Ajera table, view, or table-valued function.

    Fields carry the database column as their alias (`project_key` reads
    `tProject`), so rows validate straight from the cursor. Columns a tenant
    added as custom fields are not part of any generated model; they are kept
    as extra attributes and exposed through `custom_fields`.

    Schema building is deferred to first use: there are a few hundred of these
    models, and a caller who reads one table should not pay for all of them at
    import.
    """

    model_config = ConfigDict(
        validate_by_alias=True,
        validate_by_name=True,
        extra="allow",
        defer_build=True,
        # Binary columns (row versions, files) travel as base64 in JSON, the
        # only form every byte string survives.
        ser_json_bytes="base64",
        val_json_bytes="base64",
    )

    __source__: ClassVar[Source]

    @property
    def custom_fields(self) -> dict[str, object]:
        """
        The tenant's custom columns on this row, by column name.

        Returns:
            dict[str, object]: Column name to value, empty when the tenant
            defines none on this table.
        """
        return dict(self.model_extra or {})


# =============================================================================
# FUNCTION: annotation_members
# =============================================================================


def annotation_members(annotation: object) -> tuple[object, ...]:
    """
    The types a field annotation admits: each member of a union, or itself.

    Returns:
        tuple[object, ...]: The member types, `NoneType` included if present.
    """
    origin = typing.get_origin(annotation)
    if origin is typing.Union or origin is types.UnionType:
        return typing.get_args(annotation)
    return (annotation,)
