"""
Connection settings and connection-string assembly for the ODBC reader.

Nothing here opens a connection or imports `pyodbc` at module load, so the
`ajera` package stays importable for callers who never install the `odbc`
extra or the Progress driver.
"""

import importlib
import os
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Protocol, cast

# Deltek's Hybrid Data Pipeline endpoint for Ajera, reached over HTTPS.
DEFAULT_HOST = "ajera-hdp01.prd.mydeltek.com"
DEFAULT_PORT = 443

# The name the Progress driver is registered under in odbcinst.ini.
DEFAULT_DRIVER = "DataDirect HDP 4.6"

# Characters that force a connection-string value into braces. A value
# containing any of them would otherwise end the attribute early or be
# misread as a new one.
_SPECIAL = frozenset(";{}=")

# ODBC's SQL_ATTR_QUERY_TIMEOUT. Set on a connection, it becomes the timeout
# of the statements the connection runs, which is how a per-call timeout
# reaches pyodbc's cursors. pyodbc's own `Connection.timeout` cannot do this:
# it sets SQL_ATTR_CONNECTION_TIMEOUT first, which the HDP driver rejects
# (HYC00, optional feature not implemented).
SQL_ATTR_QUERY_TIMEOUT = 0


# =============================================================================
# PROTOCOLS: the DB-API surface the reader uses
# =============================================================================
#
# `pyodbc` ships a stub file, but as a bare module without `py.typed` it is
# not picked up by type checkers, and it is an optional extra besides. The
# reader is typed against this slice of DB-API 2.0 instead, which `pyodbc`
# satisfies and a test double can too.


class Cursor(Protocol):
    @property
    def description(self) -> Sequence[Sequence[object]]: ...

    def execute(self, sql: str, *params: object) -> object: ...

    def fetchall(self) -> Sequence[Sequence[object]]: ...

    def fetchmany(self, size: int) -> Sequence[Sequence[object]]: ...

    def close(self) -> None: ...


class Connection(Protocol):
    def cursor(self) -> Cursor: ...

    def set_attr(self, attribute: int, value: int, /) -> None: ...

    def close(self) -> None: ...


# =============================================================================
# CLASS: OdbcSettings
# =============================================================================


@dataclass(frozen=True)
class OdbcSettings:
    """
    Everything needed to reach one Ajera database through the HDP driver.

    Deltek issues the data source, username, and password per account on the
    ODBC service request; host and port are the same for every tenant unless
    Deltek says otherwise. The password is excluded from `repr` so it never
    reaches a log line or a traceback.
    """

    datasource: str | None = None
    username: str | None = None
    password: str | None = field(default=None, repr=False)
    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    driver: str = DEFAULT_DRIVER

    # -------------------------------------------------------------------------
    # METHOD: from_environment
    # -------------------------------------------------------------------------

    @classmethod
    def from_environment(
        cls,
        datasource: str | None = None,
        username: str | None = None,
        password: str | None = None,
        host: str | None = None,
        port: int | None = None,
        driver: str | None = None,
    ) -> "OdbcSettings":
        """
        Resolve settings, falling back to the `AJERA_ODBC_*` environment.

        Explicit arguments win over the environment, matching `AjeraClient`.

        Returns:
            OdbcSettings: The resolved settings.
        """
        env = os.environ.get
        return cls(
            datasource=datasource or env("AJERA_ODBC_DATASOURCE"),
            username=username or env("AJERA_ODBC_USERNAME"),
            password=password or env("AJERA_ODBC_PASSWORD"),
            host=host or env("AJERA_ODBC_HOST") or DEFAULT_HOST,
            port=port or int(env("AJERA_ODBC_PORT") or DEFAULT_PORT),
            driver=driver or env("AJERA_ODBC_DRIVER") or DEFAULT_DRIVER,
        )

    # -------------------------------------------------------------------------
    # METHOD: connection_string
    # -------------------------------------------------------------------------

    def connection_string(
        self, *, login_timeout: int = 0, query_timeout: int = 0
    ) -> str:
        """
        Build the DSN-less connection string for the HDP driver.

        Missing credentials are reported here, at connect time, rather than at
        construction, the same point at which `AjeraClient` reports them.

        The login timeout has to be known before the connection exists, and
        the query timeout here is the default for every statement; 0 waits
        indefinitely. `set_query_timeout` changes it on an open connection.

        Returns:
            str: The connection string.
        """
        missing = [
            name
            for name, value in (
                ("AJERA_ODBC_DATASOURCE", self.datasource),
                ("AJERA_ODBC_USERNAME", self.username),
                ("AJERA_ODBC_PASSWORD", self.password),
            )
            if not value
        ]
        if missing:
            raise ValueError("No ODBC settings provided for: " + ", ".join(missing))

        attributes = {
            "Driver": self.driver,
            "Service": self.host,
            "PortNumber": str(self.port),
            "HybridDataPipelineDataSource": self.datasource,
            "LogonID": self.username,
            "Password": self.password,
            # TLS on, and the server certificate checked against the trust
            # store the installer lays down beside the driver.
            "EncryptionMethod": "1",
            "ValidateServerCertificate": "1",
            "LoginTimeout": str(login_timeout),
            "QueryTimeout": str(query_timeout),
        }
        return ";".join(
            f"{key}={quote(value or '')}" for key, value in attributes.items()
        )


# =============================================================================
# FUNCTION: quote
# =============================================================================


def quote(value: str) -> str:
    """
    Quote one connection-string value if it needs it.

    ODBC wraps a value in braces when it holds a separator, and doubles any
    closing brace inside it. Leading or trailing whitespace is also braced so
    the driver does not trim it.

    Returns:
        str: The value, braced if necessary.
    """
    if value != value.strip() or any(char in _SPECIAL for char in value):
        return "{" + value.replace("}", "}}") + "}"
    return value


# =============================================================================
# FUNCTION: connect
# =============================================================================


def connect(
    settings: OdbcSettings,
    *,
    login_timeout: int = 0,
    query_timeout: int = 0,
) -> Connection:
    """
    Open a read-only, autocommit connection through the HDP driver.

    `pyodbc` is imported here, on first connect, so it stays an optional
    extra. It also needs unixODBC's `libodbc` at import time, which is why a
    failure to load that shared library is reported the same way as a missing
    package: either way the caller has not set up the extra.

    Args:
        settings: Where and as whom to connect.
        login_timeout: Seconds to wait for the login; 0 waits indefinitely.
        query_timeout: Seconds to wait for each statement; 0 waits indefinitely.

    Returns:
        Connection: The open connection.
    """
    connection_string = settings.connection_string(
        login_timeout=login_timeout, query_timeout=query_timeout
    )

    try:
        pyodbc = importlib.import_module("pyodbc")
    except ImportError as error:
        raise ImportError(
            "The Ajera ODBC reader needs pyodbc and unixODBC. Install the extra "
            "with `pip install 'ajera[odbc]'`, and the Progress DataDirect HDP "
            f"ODBC driver from Deltek. ({error})"
        ) from error

    # Autocommit because nothing here ever writes, so there is no transaction
    # to hold open; read-only so the driver refuses a write even if the
    # credential would allow one.
    open_connection = cast(Callable[..., Connection], pyodbc.connect)
    return open_connection(connection_string, autocommit=True, readonly=True)


# =============================================================================
# FUNCTION: set_query_timeout
# =============================================================================


def set_query_timeout(connection: Connection, seconds: int) -> None:
    """
    Set the query timeout of the statements a connection runs from now on.

    The HDP driver reads it when a statement executes, so a timeout meant for
    one statement must stay set until that statement's `execute` returns.

    Args:
        connection: The open connection.
        seconds: The timeout; 0 waits indefinitely.
    """
    connection.set_attr(SQL_ATTR_QUERY_TIMEOUT, seconds)
