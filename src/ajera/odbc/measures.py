"""
Measures for `AjeraOdbc.aggregate`: the totals the database computes.

    db.aggregate(
        TransactionRecord,
        measures=[sum_("units", alias="hours"), count()],
        group_by=["employee_key", "date:month"],
    )

Each helper names a field (or column) of the model and, optionally, the key
the result is returned under. The default key is `<function>_<field>`
(`sum_units`), or `count` for `count()`.
"""

from dataclasses import dataclass
from typing import Literal

type Function = Literal["SUM", "COUNT", "COUNT_DISTINCT", "MIN", "MAX", "AVG"]

# =============================================================================
# CLASS: Measure
# =============================================================================


@dataclass(frozen=True)
class Measure:
    """
    One aggregate over a column, built by the helpers below.

    Attributes:
        function: The SQL aggregate.
        field: The field or column it reads; None only for `COUNT`.
        alias: The key the value is returned under; None for the default.
    """

    function: Function
    field: str | None = None
    alias: str | None = None


def sum_(field: str, alias: str | None = None) -> Measure:
    """Add up a numeric field. A `decimal` column sums to a `Decimal`."""
    return Measure("SUM", field, alias)


def count(alias: str | None = None) -> Measure:
    """Count the rows in each group (`COUNT_BIG(*)`)."""
    return Measure("COUNT", None, alias)


def count_distinct(field: str, alias: str | None = None) -> Measure:
    """Count the distinct non-NULL values of a field in each group."""
    return Measure("COUNT_DISTINCT", field, alias)


def min_(field: str, alias: str | None = None) -> Measure:
    """The smallest value of a field in each group."""
    return Measure("MIN", field, alias)


def max_(field: str, alias: str | None = None) -> Measure:
    """The largest value of a field in each group."""
    return Measure("MAX", field, alias)


def avg(field: str, alias: str | None = None) -> Measure:
    """
    The mean of a numeric field in each group.

    SQL Server averages an integer column with integer division, so the mean
    of an `int` field is an `int`. For a fractional mean, sum and count it.
    """
    return Measure("AVG", field, alias)
