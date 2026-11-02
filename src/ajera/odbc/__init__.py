"""
Read-only access to the Ajera database through Deltek's ODBC entitlement.

Requires the `odbc` extra (`pip install 'ajera[odbc]'`) and the Progress
DataDirect Hybrid Data Pipeline ODBC driver, which Deltek distributes for
x86_64 Linux and Windows only. Importing this package needs neither; the first
read does.
"""

from ajera.odbc.connection import OdbcSettings
from ajera.odbc.filters import (
    Condition,
    between,
    eq,
    ge,
    gt,
    in_,
    is_null,
    le,
    like,
    lt,
    ne,
    not_in,
    not_null,
)
from ajera.odbc.reader import PAGE_SIZE, AjeraOdbc

__all__ = [
    "PAGE_SIZE",
    "AjeraOdbc",
    "Condition",
    "OdbcSettings",
    "between",
    "eq",
    "ge",
    "gt",
    "in_",
    "is_null",
    "le",
    "like",
    "lt",
    "ne",
    "not_in",
    "not_null",
]
