"""
Conditions for the `where=` argument of the ODBC reads.

A `where` mapping names a field (or a raw column) and the value to match:

    db.read(TransactionRecord, where={
        "project_key": 1234,                       # =
        "status": [TransactionStatus.billable, 3], # IN (...)
        "date": between(date(2026, 1, 1), date(2026, 3, 31)),
        "notes": is_null(),
    })

Every value is sent as a bound parameter; only column names, resolved against
the model, ever reach the statement text.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal

type Operator = Literal[
    "=",
    "<>",
    "<",
    "<=",
    ">",
    ">=",
    "IN",
    "NOT IN",
    "LIKE",
    "BETWEEN",
    "IS NULL",
    "IS NOT NULL",
]

# =============================================================================
# CLASS: Condition
# =============================================================================


@dataclass(frozen=True)
class Condition:
    """
    One comparison against a column, built by the helpers below.

    Attributes:
        operator: The SQL comparison.
        values: Its operands: none for the null tests, two for `BETWEEN`,
            any number for `IN`, and one otherwise.
    """

    operator: Operator
    values: tuple[object, ...] = ()


def eq(value: object) -> Condition:
    """Match a value exactly; the same as passing the value itself."""
    return Condition("=", (value,))


def ne(value: object) -> Condition:
    """Match anything but the value (rows where the column is NULL never match)."""
    return Condition("<>", (value,))


def lt(value: object) -> Condition:
    """Match values below the bound."""
    return Condition("<", (value,))


def le(value: object) -> Condition:
    """Match values at or below the bound."""
    return Condition("<=", (value,))


def gt(value: object) -> Condition:
    """Match values above the bound."""
    return Condition(">", (value,))


def ge(value: object) -> Condition:
    """Match values at or above the bound."""
    return Condition(">=", (value,))


def between(low: object, high: object) -> Condition:
    """Match values from `low` to `high`, both inclusive."""
    return Condition("BETWEEN", (low, high))


def like(pattern: str) -> Condition:
    """Match text against a SQL `LIKE` pattern (`%` any run, `_` one character)."""
    return Condition("LIKE", (pattern,))


def in_(values: Iterable[object]) -> Condition:
    """Match any of the values; the same as passing a list."""
    return Condition("IN", tuple(values))


def not_in(values: Iterable[object]) -> Condition:
    """Match none of the values."""
    return Condition("NOT IN", tuple(values))


def is_null() -> Condition:
    """Match rows where the column is NULL; the same as passing None."""
    return Condition("IS NULL")


def not_null() -> Condition:
    """Match rows where the column has a value."""
    return Condition("IS NOT NULL")
