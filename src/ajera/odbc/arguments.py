"""
Checks for the arguments of the database's table-valued functions.

SQL Server converts a mistyped argument when it can, and some of those
conversions are silent and wrong: an integer bound to a `smalldatetime`
parameter is a day count from 1900 (`2026` is 1905-07-20), and a string longer
than a `varchar` parameter is cut short. So every argument is checked against
its parameter's declared SQL type, from the catalog, before it is bound.

Pydantic's lax validation is no help here: it reads `2026` as a Unix
timestamp, the same silent error in another form.
"""

import re
from collections.abc import Sequence
from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation

from ajera.schemas.database.base import Source

# `varchar(10)`, `decimal(19,2)`, `varchar(max)`, or a bare type name.
DECLARATION = re.compile(
    r"^(?P<type>[a-z0-9]+)(?:\((?P<size>max|-1|\d+)(?:,(?P<scale>\d+))?\))?$"
)

INTEGER_RANGES = {
    "tinyint": (0, 255),
    "smallint": (-(2**15), 2**15 - 1),
    "int": (-(2**31), 2**31 - 1),
    "bigint": (-(2**63), 2**63 - 1),
}
DATE_RANGES = {
    "smalldatetime": (datetime(1900, 1, 1), datetime(2079, 6, 6, 23, 59)),
    "datetime": (datetime(1753, 1, 1), datetime(9999, 12, 31, 23, 59, 59)),
    "datetime2": (datetime.min, datetime.max),
    "date": (datetime.min, datetime.max),
}
DECIMAL_TYPES = frozenset({"decimal", "numeric"})
CHARACTER_TYPES = frozenset({"varchar", "nvarchar", "char", "nchar"})


# =============================================================================
# FUNCTION: check_arguments
# =============================================================================


def check_arguments(source: Source, arguments: Sequence[object]) -> list[object]:
    """
    Check a function's arguments against its parameters' SQL types.

    A source without recorded types (a hand-written model) is not checked.

    Returns:
        list[object]: The arguments as they will be bound; an ISO string for
        a date parameter becomes a `date` or `datetime`.
    """
    declarations = source.parameter_types or ("",) * len(source.parameters)
    return [
        check_argument(source.name, name, declaration, value)
        for name, declaration, value in zip(
            source.parameters, declarations, arguments, strict=False
        )
    ]


def check_argument(function: str, name: str, declaration: str, value: object) -> object:
    """
    Check one argument against its parameter's SQL declaration.

    None is always allowed and binds as SQL NULL. A declaration this module
    does not know passes the value through unchecked.

    Raises:
        TypeError: The value is the wrong kind for the parameter.
        ValueError: The value is the right kind, but out of the type's range,
            too long, or would be rounded.

    Returns:
        object: The value to bind.
    """
    if value is None:
        return None
    match = DECLARATION.match(declaration)
    if match is None:
        return value
    sql_type, size, scale = match["type"], match["size"], match["scale"]
    where = f"{function} @{name} ({declaration})"

    if sql_type in DATE_RANGES:
        return _date(where, sql_type, value)
    if sql_type in INTEGER_RANGES:
        return _integer(where, sql_type, value)
    if sql_type == "bit":
        return _bit(where, value)
    if sql_type in DECIMAL_TYPES:
        return _decimal(where, value, size, scale)
    if sql_type in CHARACTER_TYPES:
        return _text(where, value, size)
    return value


def _describe(value: object) -> str:
    shown = repr(value) if isinstance(value, str) else str(value)
    return f"{type(value).__name__} {shown}"


def _date(where: str, sql_type: str, value: object) -> date:
    if isinstance(value, str):
        try:
            parsed: date = (
                date.fromisoformat(value)
                if len(value) == 10
                else datetime.fromisoformat(value)
            )
        except ValueError:
            raise ValueError(
                f"{where} takes an ISO 8601 date such as 2026-03-31, not {value!r}"
            ) from None
        value = parsed
    if not isinstance(value, date):
        raise TypeError(
            f"{where} takes a date, a datetime, or an ISO 8601 string, "
            f"not {_describe(value)}"
        )
    if isinstance(value, datetime) and value.tzinfo is not None:
        raise ValueError(f"{where} has no time zone; pass a naive datetime")
    low, high = DATE_RANGES[sql_type]
    stamp = value if isinstance(value, datetime) else datetime.combine(value, time())
    if not low <= stamp <= high:
        raise ValueError(
            f"{where} holds {low.date()} to {high.date()}; {value} is out of range"
        )
    return value


def _integer(where: str, sql_type: str, value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{where} takes an int, not {_describe(value)}")
    low, high = INTEGER_RANGES[sql_type]
    if not low <= value <= high:
        raise ValueError(f"{where} holds {low} to {high}; {value} is out of range")
    return int(value)


def _bit(where: str, value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        if value not in (0, 1):
            raise ValueError(f"{where} takes True, False, 0, or 1, not {value}")
        return bool(value)
    raise TypeError(f"{where} takes a bool, not {_describe(value)}")


def _decimal(
    where: str, value: object, precision: str | None, scale: str | None
) -> Decimal | int:
    if isinstance(value, bool) or not isinstance(value, (Decimal, int)):
        hint = (
            "; a float cannot hold most decimal fractions exactly"
            if isinstance(value, float)
            else ""
        )
        raise TypeError(
            f"{where} takes a Decimal or an int, not {_describe(value)}{hint}"
        )
    number = Decimal(value)
    if not number.is_finite():
        raise ValueError(f"{where} takes a finite number, not {value}")
    if precision is None or precision in ("max", "-1") or scale is None:
        return value
    digits, places = int(precision), int(scale)
    try:
        fitted = number.quantize(Decimal(1).scaleb(-places))
    except InvalidOperation:
        fitted = None
    if fitted is None or abs(fitted) >= Decimal(10) ** (digits - places):
        raise ValueError(
            f"{where} holds at most {digits - places} digits before the point; "
            f"{value} is too large"
        )
    if fitted != number:
        raise ValueError(
            f"{where} keeps {places} decimal places; {value} would be rounded"
        )
    return value


def _text(where: str, value: object, size: str | None) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{where} takes a str, not {_describe(value)}")
    if size not in (None, "max", "-1") and len(value) > int(size):
        raise ValueError(
            f"{where} holds at most {size} characters; {len(value)} would be cut short"
        )
    return value


# =============================================================================
# FUNCTION: from_text
# =============================================================================


def from_text(declaration: str, raw: str) -> object:
    """
    Read a command-line argument by its parameter's SQL type.

    The result still goes through `check_argument`; this only turns text into
    the Python type the parameter takes. Dates stay text, for the check to
    parse as ISO 8601.

    Raises:
        ValueError: The text is not a value of that type.

    Returns:
        object: The value.
    """
    match = DECLARATION.match(declaration)
    sql_type = match["type"] if match else ""
    if sql_type in INTEGER_RANGES:
        try:
            return int(raw)
        except ValueError:
            raise ValueError(f"{raw!r} is not an integer") from None
    if sql_type == "bit":
        flags = {"true": True, "1": True, "false": False, "0": False}
        if raw.lower() not in flags:
            raise ValueError(f"{raw!r} is not one of true, false, 1, or 0")
        return flags[raw.lower()]
    if sql_type in DECIMAL_TYPES:
        try:
            return Decimal(raw)
        except InvalidOperation:
            raise ValueError(f"{raw!r} is not a number") from None
    return raw
