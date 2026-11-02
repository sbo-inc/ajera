import logging
from collections.abc import Iterator, Sequence
from types import TracebackType
from typing import Self, override

from ajera.odbc import connection as odbc_connection
from ajera.odbc.connection import Connection, Cursor, OdbcSettings
from ajera.odbc.functions import FunctionReads
from ajera.odbc.queries import reference as reference_queries
from ajera.odbc.queries import select as select_queries
from ajera.odbc.queries.generic import Query, Record
from ajera.odbc.queries.select import KEY_BATCH, Where
from ajera.odbc.rest import RestReads
from ajera.schemas.database.base import DatabaseRecord

logger = logging.getLogger("ajera")

# Default (login, query) timeout in seconds. The login crosses the internet to
# Deltek's pipeline and back to the tenant database, so it gets the driver's
# own default; a query gets long enough for a scan of the largest tables.
DEFAULT_TIMEOUT: tuple[int, int] = (30, 300)

# SQLSTATE classes that mean the connection itself is gone, after which one
# reconnect and retry is safe because every statement here is a read.
DISCONNECT_STATES = frozenset({"08S01", "08003", "08007"})

# SQLSTATE for a statement that ran past the query timeout. The pipeline keeps
# working on it, and the next statement on the same connection times out too,
# so the connection is discarded; the read is not retried, since it would only
# time out again.
TIMEOUT_STATE = "HYT00"

# Column types left out of a read unless `include_blobs=True`. A few hold
# whole files: client invoice snapshots alone run to hundreds of megabytes.
BLOB_TYPES = frozenset({"image", "varbinary", "binary"})

# Rows per statement when paging a keyed source. Deltek's pipeline refuses any
# single result over 500,000 rows ("The limit on the number of rows that can
# be returned from a query -- 500,000 -- has been exceeded").
PAGE_SIZE = 100_000


# =============================================================================
# CLASS: AjeraOdbc
# =============================================================================


class AjeraOdbc(FunctionReads, RestReads):
    """
    Read-only access to the Ajera database over Deltek's ODBC entitlement.

    Every table, view, and table-valued function the database exposes has a
    model in `ajera.schemas.database`; pass the model to `read`, `stream`,
    `count`, or `get`, or call a function through its typed method
    (`project_totals`, `ledger`, ...). Values reach the server only as bound
    parameters, and nothing here writes. The REST client's list methods are
    here too (`list_companies`, ...), returning the REST models from the
    database. One connection is opened on first
    use, reused for every read, and reopened once if it drops.
    """

    settings: OdbcSettings
    timeout: tuple[int, int]

    def __init__(
        self,
        datasource: str | None = None,
        username: str | None = None,
        password: str | None = None,
        *,
        host: str | None = None,
        port: int | None = None,
        driver: str | None = None,
        timeout: int | tuple[int, int] | None = DEFAULT_TIMEOUT,
        log: bool = False,
    ) -> None:
        """
        Resolve configuration, falling back to the `AJERA_ODBC_*` environment.

        Nothing connects here; the first read does.

        Args:
            datasource: The HDP data source name (Environment: `AJERA_ODBC_DATASOURCE`)
            username: The ODBC logon ID (Environment: `AJERA_ODBC_USERNAME`)
            password: The ODBC password (Environment: `AJERA_ODBC_PASSWORD`)
            host: The HDP service host (Environment: `AJERA_ODBC_HOST`)
            port: The HDP service port (Environment: `AJERA_ODBC_PORT`)
            driver: The registered ODBC driver name (Environment: `AJERA_ODBC_DRIVER`)
            timeout: Seconds for the login and for each query, as one value
                or a `(login, query)` pair; None waits indefinitely.
            log: Enables statement logging at INFO level
        """
        logger.setLevel(logging.INFO if log else logging.CRITICAL)

        self.settings = OdbcSettings.from_environment(
            datasource=datasource,
            username=username,
            password=password,
            host=host,
            port=port,
            driver=driver,
        )
        if timeout is None:
            self.timeout = (0, 0)
        elif isinstance(timeout, int):
            self.timeout = (timeout, timeout)
        else:
            self.timeout = timeout

        self._connection: Connection | None = None
        self._columns: dict[str, list[tuple[str, str]]] = {}

    # -------------------------------------------------------------------------
    # Connection lifecycle
    # -------------------------------------------------------------------------

    @property
    def connection(self) -> Connection:
        """
        The open connection, opened on first access.

        Returns:
            Connection: The connection.
        """
        if self._connection is None:
            self._connection = self._open()
        return self._connection

    def _open(self) -> Connection:
        login, query = self.timeout
        return odbc_connection.connect(
            self.settings, login_timeout=login, query_timeout=query
        )

    def close(self) -> None:
        """
        Close the connection, if one is open.

        Closing a connection the server already dropped can itself raise; the
        handle is discarded either way so the next read opens a fresh one.
        """
        connection, self._connection = self._connection, None
        if connection is not None:
            try:
                connection.close()
            except Exception:
                logger.info("Ignoring error while closing a dropped connection")

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    # -------------------------------------------------------------------------
    # Execution
    # -------------------------------------------------------------------------

    def _execute[T](self, query: Query[T]) -> Cursor:
        logger.info("%s %s", query.statement, query.parameters)
        cursor = self.connection.cursor()
        try:
            cursor.execute(query.statement, *query.parameters)
        except Exception as error:
            cursor.close()
            if _sqlstate(error) == TIMEOUT_STATE:
                logger.info("Statement timed out; discarding the connection")
                self.close()
            raise
        return cursor

    @staticmethod
    def _records(
        cursor: Cursor, rows: Sequence[Sequence[object]], keep_nulls: bool
    ) -> list[Record]:
        columns = [str(column[0]) for column in cursor.description]
        return [
            {
                column: value
                for column, value in zip(columns, row)
                if keep_nulls or value is not None
            }
            for row in rows
        ]

    def _fetch[T](self, query: Query[T]) -> list[Record]:
        cursor = self._execute(query)
        try:
            return self._records(cursor, cursor.fetchall(), query.keep_nulls)
        finally:
            cursor.close()

    @override
    def _run[T](self, query: Query[T]) -> T:
        try:
            records = self._fetch(query)
        except Exception as error:
            if not _is_disconnect(error):
                raise
            logger.info("Connection dropped (%s); reconnecting once", error)
            self.close()
            records = self._fetch(query)
        return query.parse(records)

    # -------------------------------------------------------------------------
    # Live schema
    # -------------------------------------------------------------------------

    def columns(self, model: type[DatabaseRecord]) -> list[tuple[str, str]]:
        """
        The model's source columns as the database reports them now.

        Includes the tenant's custom fields, which no generated model
        declares. Looked up once per source and connection lifetime.

        Returns:
            list[tuple[str, str]]: Column name and SQL type, in order.
        """
        name = model.__source__.name
        if name not in self._columns:
            self._columns[name] = self._run(select_queries.live_columns(model))
        return self._columns[name]

    def _select_list(
        self, model: type[DatabaseRecord], include_blobs: bool
    ) -> list[str]:
        live = self.columns(model)
        if not live:
            raise LookupError(f"{model.__source__.name} is not visible to this login")
        return [name for name, kind in live if include_blobs or kind not in BLOB_TYPES]

    # -------------------------------------------------------------------------
    # Generic reads
    # -------------------------------------------------------------------------

    def read[T: DatabaseRecord](
        self,
        model: type[T],
        *,
        where: Where | None = None,
        order_by: Sequence[str] | None = None,
        limit: int | None = None,
        offset: int | None = None,
        include_blobs: bool = False,
    ) -> list[T]:
        """
        Read rows of a table or view into its model.

        Deltek's pipeline refuses any single result over 500,000 rows, so a
        keyed source read in key order is fetched in pages of `PAGE_SIZE`
        transparently. A read in any other order, or of an unkeyed view, is
        one statement and must stay under that limit; filter it, or `stream`
        it in key order.

        Args:
            model: The model of the table or view, from `ajera.schemas.database`.
            where: Field (or column) to value or `ajera.odbc.filters` condition,
                all of which must hold. A list matches any of its values.
            order_by: Fields to sort by; prefix one with `-` to sort it
                descending. Keyed sources default to key order.
            limit: The most rows to return.
            offset: Rows to skip first, for paging; needs an order.
            include_blobs: Also fetch binary columns (files, images), which
                are otherwise left as None.

        Returns:
            list[T]: The rows.
        """
        return list(
            self.stream(
                model,
                where=where,
                order_by=order_by,
                limit=limit,
                offset=offset,
                include_blobs=include_blobs,
            )
        )

    def stream[T: DatabaseRecord](
        self,
        model: type[T],
        *,
        where: Where | None = None,
        order_by: Sequence[str] | None = None,
        limit: int | None = None,
        offset: int | None = None,
        include_blobs: bool = False,
        batch_size: int = 5000,
    ) -> Iterator[T]:
        """
        Read rows of a table or view lazily, a batch at a time.

        For the large tables (`AxGLDetail` holds millions of rows) where
        holding every row at once is wasteful. Takes the same arguments as
        `read`, and pages the same way.

        Yields:
            T: Each row, in order.
        """
        self._require(model, "table", "view")
        columns = self._select_list(model, include_blobs)
        for record in self._records_paged(
            model,
            columns,
            where=where,
            order_by=order_by,
            limit=limit,
            offset=offset,
            batch_size=batch_size,
        ):
            yield model.model_validate(record)

    def _keyset(
        self,
        model: type[DatabaseRecord],
        order_by: Sequence[str] | None,
        offset: int | None,
    ) -> str | None:
        """The key column to page by, or None when the read cannot be paged."""
        key = model.__source__.primary_key
        if len(key) != 1 or offset is not None:
            return None
        if order_by:
            if len(order_by) != 1 or order_by[0].startswith("-"):
                return None
            if select_queries.resolve(model, order_by[0]) != key[0]:
                return None
        return key[0]

    def _cursor_records[T](self, query: Query[T], batch_size: int) -> Iterator[Record]:
        try:
            cursor = self._execute(query)
        except Exception as error:
            if not _is_disconnect(error):
                raise
            logger.info("Connection dropped (%s); reconnecting once", error)
            self.close()
            cursor = self._execute(query)
        try:
            while rows := cursor.fetchmany(batch_size):
                yield from self._records(cursor, rows, keep_nulls=True)
        finally:
            cursor.close()

    def _records_paged(
        self,
        model: type[DatabaseRecord],
        columns: Sequence[str],
        *,
        where: Where | None,
        order_by: Sequence[str] | None,
        limit: int | None,
        offset: int | None,
        batch_size: int,
        arguments: Sequence[object] = (),
    ) -> Iterator[Record]:
        key = self._keyset(model, order_by, offset) if not arguments else None
        if key is None:
            yield from self._cursor_records(
                select_queries.select(
                    model,
                    columns,
                    where=where,
                    order_by=order_by,
                    limit=limit,
                    offset=offset,
                    arguments=arguments,
                ),
                batch_size,
            )
            return

        remaining = limit
        after: object | None = None
        while remaining is None or remaining > 0:
            size = PAGE_SIZE if remaining is None else min(PAGE_SIZE, remaining)
            query = select_queries.select(
                model, columns, where=where, order_by=[key], limit=size, after=after
            )
            fetched = 0
            for record in self._cursor_records(query, batch_size):
                fetched += 1
                after = record[key]
                yield record
            if remaining is not None:
                remaining -= fetched
            if fetched < size:
                return

    def count(
        self,
        model: type[DatabaseRecord],
        *arguments: object,
        where: Where | None = None,
    ) -> int:
        """
        Count the rows a read would return.

        Args:
            model: The model of a table, view, or function.
            arguments: A function's arguments, in declaration order.
            where: As for `read`.

        Returns:
            int: The number of rows.
        """
        live = [name for name, _ in self.columns(model)] if where else []
        return self._run(
            select_queries.count(model, where=where, arguments=arguments, live=live)
        )

    def get[T: DatabaseRecord](
        self,
        model: type[T],
        *keys: object,
        include_blobs: bool = False,
    ) -> list[T]:
        """
        Fetch rows of a table (or keyed view) by key, in key order.

        Keys that match nothing are skipped, as the REST `Get*` methods skip
        them.

        Returns:
            list[T]: The matching rows.
        """
        self._require(model, "table", "view")
        key = model.__source__.primary_key
        if len(key) != 1:
            raise TypeError(f"{model.__source__.name} has no single-column primary key")
        rows: list[T] = []
        for start in range(0, len(keys), KEY_BATCH):
            batch = list(keys[start : start + KEY_BATCH])
            rows += self.read(model, where={key[0]: batch}, include_blobs=include_blobs)
        return rows

    @override
    def call[T: DatabaseRecord](
        self,
        model: type[T],
        *arguments: object,
        where: Where | None = None,
        order_by: Sequence[str] | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[T]:
        """
        Call a table-valued function and parse its rows.

        Prefer the typed method for each function (`project_totals`, ...),
        which names and types the arguments.

        Returns:
            list[T]: The function's rows.
        """
        self._require(model, "function")
        return self._run(
            select_queries.select(
                model,
                self._select_list(model, include_blobs=False),
                where=where,
                order_by=order_by,
                limit=limit,
                offset=offset,
                arguments=arguments,
            )
        )

    @staticmethod
    def _require(model: type[DatabaseRecord], *kinds: str) -> None:
        kind = model.__source__.kind
        if kind not in kinds:
            hint = " (use call or its typed method)" if kind == "function" else ""
            raise TypeError(
                f"{model.__name__} reads a {kind}, not a {' or '.join(kinds)}{hint}"
            )

    # -------------------------------------------------------------------------
    # Health
    # -------------------------------------------------------------------------

    def ping(self) -> bool:
        """
        Round-trip a trivial statement to prove the connection works.

        Returns:
            bool: True when the server answers.
        """
        return self._run(reference_queries.ping())


# =============================================================================
# FUNCTION: _is_disconnect
# =============================================================================


def _is_disconnect(error: Exception) -> bool:
    """
    Tell whether an error means the connection itself was lost.

    `pyodbc.Error` carries the SQLSTATE as its first argument. Matching on it
    rather than on the exception class keeps `pyodbc` out of this module's
    imports, so the reader can be exercised without the extra installed.

    Returns:
        bool: True for a lost connection.
    """
    return _sqlstate(error) in DISCONNECT_STATES


def _sqlstate(error: Exception) -> str | None:
    """The SQLSTATE a `pyodbc.Error` carries as its first argument, if any."""
    state = error.args[0] if error.args else None
    return state if isinstance(state, str) else None
