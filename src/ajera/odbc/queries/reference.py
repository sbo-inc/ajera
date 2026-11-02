"""
Connection health checks.

The REST-shaped reads live in `ajera.odbc.queries.mirror`.
"""

from ajera.odbc.queries.generic import Query, Record

# =============================================================================
# QUERY: ping
# =============================================================================


def ping() -> Query[bool]:
    """
    Build the round-trip check.

    Returns:
        Query[bool]: True when the server answers.
    """

    def parse(records: list[Record]) -> bool:
        return len(records) == 1 and list(records[0].values()) == [1]

    return Query(statement="SELECT 1 AS Ping", parse=parse)
