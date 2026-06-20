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
