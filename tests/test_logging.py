"""
The package's logging follows the library pattern.

Importing attaches only a NullHandler, building a client or a reader never
touches levels or handlers, and only the CLI's `--log` configures output.
"""

import logging
import subprocess
import sys
from collections.abc import Iterator

import pytest

from ajera.async_client import AsyncAjeraClient
from ajera.cli import LOG_HANDLER_NAME, enable_logging
from ajera.client import AjeraClient
from ajera.odbc import AjeraOdbc

PACKAGE = logging.getLogger("ajera")


@pytest.fixture(autouse=True)
def restore_logger() -> Iterator[None]:
    """
    Undo any handler or level a test leaves on the package logger.
    """
    handlers, level = list(PACKAGE.handlers), PACKAGE.level
    yield
    PACKAGE.handlers[:] = handlers
    PACKAGE.setLevel(level)


def test_import_attaches_only_a_null_handler() -> None:
    # A fresh interpreter, so no earlier test has touched the loggers.
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import logging, ajera, ajera.odbc;"
            "logger = logging.getLogger('ajera');"
            "arguments = logging.getLogger('ajera.odbc.arguments');"
            "print([type(h).__name__ for h in logger.handlers], logger.level, arguments.level)",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    assert result.stdout.strip() == "['NullHandler'] 0 0"


def test_building_clients_and_readers_leaves_the_logger_alone() -> None:
    PACKAGE.setLevel(logging.DEBUG)
    handlers = list(PACKAGE.handlers)

    AjeraClient(url="https://example.test/api")
    AsyncAjeraClient(url="https://example.test/api")
    AjeraOdbc(datasource="ds", username="user", password="secret")

    assert PACKAGE.level == logging.DEBUG
    assert PACKAGE.handlers == handlers


def test_cli_logging_replaces_its_own_handler() -> None:
    enable_logging()
    enable_logging()

    named = [h for h in PACKAGE.handlers if h.get_name() == LOG_HANDLER_NAME]
    assert len(named) == 1
    assert PACKAGE.level == logging.DEBUG
