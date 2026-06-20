import os
from typing import override

import click

DISABLE_ENV_VAR = "AJERA_CLI_DISABLE"

# =============================================================================
# FUNCTION: _disabled_paths
# =============================================================================


def _disabled_paths() -> frozenset[str]:
    """
    Read the set of disabled command paths from the environment.
    """
    raw = os.environ.get(DISABLE_ENV_VAR, "")
    return frozenset(part.strip() for part in raw.split(",") if part.strip())


# =============================================================================
# FUNCTION: _command_path
# =============================================================================


def _command_path(ctx: click.Context, name: str) -> str:
    """
    Build the dotted path (e.g. `employees.list`) for a command under `ctx`.
    """
    parts: list[str] = []
    cur: click.Context | None = ctx
    while cur is not None and cur.parent is not None:
        if cur.info_name:
            parts.append(cur.info_name)
        cur = cur.parent
    parts.reverse()
    parts.append(name)
    return ".".join(parts)


# =============================================================================
# CLASS: CommonClickGroup
# =============================================================================


class CommonClickGroup(click.Group):
    """
    Click group that lists subcommands in the order they were registered.

    Commands listed in the `AJERA_CLI_DISABLE` env var (comma-separated dotted
    paths) are hidden from `--help` and rejected at dispatch, so embedded
    runtimes can suppress sensitive commands without changing the CLI.
    """

    @override
    def list_commands(self, ctx: click.Context) -> list[str]:
        disabled = _disabled_paths()
        names = list(self.commands)
        if not disabled:
            return names
        return [name for name in names if _command_path(ctx, name) not in disabled]

    @override
    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        if _command_path(ctx, cmd_name) in _disabled_paths():
            return None
        return super().get_command(ctx, cmd_name)


# Ensure nested subgroups also preserve insertion order without each having
# to pass `cls=CommonClickGroup` explicitly.
CommonClickGroup.group_class = CommonClickGroup
