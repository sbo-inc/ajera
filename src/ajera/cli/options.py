from collections.abc import Callable
from typing import Any

import click

# =============================================================================
# FUNCTION: api_version_option
# =============================================================================


def api_version_option[F: Callable[..., Any]](func: F) -> F:
    """
    Add an `--api-version` option to a command.
    """
    return click.option(
        "--api-version",
        type=int,
        default=1,
        show_default=True,
        help="Ajera API version to target.",
    )(func)


# =============================================================================
# FUNCTION: status_option
# =============================================================================


def status_option[F: Callable[..., Any]](func: F) -> F:
    """
    Add a `--status` filter that defaults to active-only.

    The option is repeatable and defaults to ``Active`` so lists don't return
    inactive records unless asked. Passing any value(s) replaces the default,
    so e.g. ``--status Inactive`` returns inactive records and
    ``--status Active --status Inactive`` returns both.
    """
    return click.option(
        "--status",
        "filter_by_status",
        type=str,
        multiple=True,
        default=("Active",),
        help="Filter by status value(s). Defaults to Active only.",
    )(func)
