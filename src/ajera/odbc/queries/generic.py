from collections.abc import Callable, Mapping
from dataclasses import dataclass, field

# One row as the reader hands it to a parser: column label to value, with SQL
# NULLs left out so the model's own defaults apply, exactly as they do when
# the REST API omits a property.
type Record = dict[str, object]

# =============================================================================
# CLASS: Query
# =============================================================================


@dataclass(frozen=True)
class Query[T]:
    """
    One database read, described without performing it.

    The ODBC counterpart of `Operation`: the parameterised statement, its
    parameters, and the function that turns the fetched records into the
    result. The reader only executes it, which keeps the SQL and the row
    shaping in one place and testable without a connection.
    """

    statement: str
    parse: Callable[[list[Record]], T]
    parameters: tuple[object, ...] = field(default=())
    # Generated database models declare nullable columns as `X | None`, so
    # they take NULLs as they come. The REST-shaped models want a NULL left
    # out so their own defaults apply, as when the API omits a property.
    keep_nulls: bool = False


# =============================================================================
# CLASS: CodeMap
# =============================================================================


class CodeMap:
    """
    Two-way mapping between a `tinyint` code column and its readable value.

    The REST API reports these columns as text (`Active`) while the database
    stores the code (`1`). The codes are per column, not global: most status
    columns use `0 = Inactive; 1 = Active`, but some use the reverse, so each
    column names its own map.
    """

    def __init__(self, column: str, codes: Mapping[int, str]) -> None:
        self.column = column
        self.codes = dict(codes)
        self.values = {value: code for code, value in codes.items()}

    def decode(self, code: object) -> str:
        """
        Turn a stored code into its readable value.

        An undocumented code raises rather than passing through, because a
        status the reader cannot name is one it may be filtering wrongly.

        Returns:
            str: The readable value.
        """
        if not isinstance(code, int) or code not in self.codes:
            raise ValueError(f"Unknown {self.column} code: {code!r}")
        return self.codes[code]

    def encode(self, values: list[str]) -> list[int]:
        """
        Turn readable filter values into the codes to match on.

        Returns:
            list[int]: The codes, in the order given.
        """
        unknown = [value for value in values if value not in self.values]
        if unknown:
            raise ValueError(
                f"Unknown {self.column} value(s): {', '.join(unknown)}; "
                f"expected one of {', '.join(self.values)}"
            )
        return [self.values[value] for value in values]


# =============================================================================
# FUNCTION: placeholders
# =============================================================================


def placeholders(count: int) -> str:
    """
    Build the `?, ?, ...` list for an `IN (...)` clause.

    Returns:
        str: The comma-separated placeholders.
    """
    return ", ".join("?" * count)
