"""
Coverage of the `ajera timesheets update` row targeting and day parsing.

The command is the one place in the CLI that builds a typed model out of
free-form option text, so the `DAY=VALUE` parsing and the choice between
editing an overhead row, editing a project row, and adding one are asserted
against the bodies that reach the transport.
"""

import json
from collections.abc import Callable
from typing import Any

import httpx
import pytest
from click.testing import CliRunner, Result
from conftest import URL, body, envelope, session_envelope

from ajera.cli.commands.timesheets import group
from ajera.cli.context import ClientContext
from ajera.client import AjeraClient

TIMESHEET: dict[str, Any] = {
    "TimesheetKey": 147,
    "TimesheetDate": "2012-09-09T00:00:00",
    "EmployeeKey": 30,
    "UnchangedData": {"Overhead": "b3Y=", "Project": "cHI="},
}


@pytest.fixture
def run() -> Callable[..., tuple[Result, list[dict[str, Any]]]]:
    """
    Return a runner that invokes the group against a mock-transport client.

    Returns:
        Callable[..., tuple[Result, list[dict[str, Any]]]]: The runner, giving
            back the Click result and every non-login body that was sent.
    """
    sent: list[dict[str, Any]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        payload = body(request)
        if payload["Method"] == "CreateAPISession":
            return session_envelope()
        sent.append(payload)
        return envelope({"Timesheets": [TIMESHEET]})

    def invoke(*args: str) -> tuple[Result, list[dict[str, Any]]]:
        client = AjeraClient(url=URL, username="u", password="p")
        client.close()
        client._http = httpx.Client(transport=httpx.MockTransport(handler))

        context = ClientContext()
        context._client = client

        result = CliRunner().invoke(group, list(args), obj=context)
        return result, sent

    return invoke


# =============================================================================
# TEST: row targeting
# =============================================================================


def test_update_edits_an_overhead_row(
    run: Callable[..., tuple[Result, list[dict[str, Any]]]],
) -> None:
    result, sent = run(
        "update", "147", "--overhead-key", "30", "--hours", "1=8", "--hours", "2=4.5"
    )

    assert result.exit_code == 0, result.output
    assert sent[-1]["MethodArguments"]["Timesheets"][0]["UpdatedOverheads"] == [
        {
            "Timesheet Overhead Group Detail Key": 30,
            "D1 Regular": 8.0,
            "D2 Regular": 4.5,
        }
    ]


def test_update_edits_an_existing_project_row(
    run: Callable[..., tuple[Result, list[dict[str, Any]]]],
) -> None:
    result, sent = run(
        "update", "147", "--project-row-key", "2", "--note", "3=Client meeting"
    )

    assert result.exit_code == 0, result.output
    assert sent[-1]["MethodArguments"]["Timesheets"][0]["UpdatedProjects"] == [
        {"Timesheet Project Key": 2, "D3 Notes": "Client meeting"}
    ]


def test_update_adds_a_project_row(
    run: Callable[..., tuple[Result, list[dict[str, Any]]]],
) -> None:
    result, sent = run(
        "update",
        "147",
        "--project-key",
        "32",
        "--phase-key",
        "33",
        "--activity-key",
        "2",
        "--hours",
        "3=4",
    )

    assert result.exit_code == 0, result.output
    assert sent[-1]["MethodArguments"]["Timesheets"][0]["UpdatedProjects"] == [
        {
            "IsNewRow": True,
            "Project Key": 32,
            "Phase Key": 33,
            "Activity Key": 2,
            "D3 Regular": 4.0,
        }
    ]

    # The baseline read supplies the UnchangedData the update echoes back.
    assert sent[0]["Method"] == "GetTimesheets"
    assert (
        sent[-1]["MethodArguments"]["Timesheets"][0]["UnchangedData"]
        == (TIMESHEET["UnchangedData"])
    )


def test_update_renders_the_resulting_timesheet(
    run: Callable[..., tuple[Result, list[dict[str, Any]]]],
) -> None:
    result, _ = run("update", "147", "--overhead-key", "30", "--hours", "1=8")

    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["timesheet_key"] == 147


# =============================================================================
# TEST: usage errors
# =============================================================================


@pytest.mark.parametrize(
    "args, message",
    [
        (("update", "147", "--hours", "1=8"), "Name exactly one row"),
        (
            ("update", "147", "--overhead-key", "30", "--project-row-key", "2"),
            "Name exactly one row",
        ),
        (
            ("update", "147", "--project-key", "32", "--hours", "1=8"),
            "needs --phase-key and --activity-key",
        ),
        (
            ("update", "147", "--overhead-key", "30", "--hours", "8=1"),
            "day must be 1-7",
        ),
        (
            ("update", "147", "--overhead-key", "30", "--hours", "1"),
            "must be given as DAY=VALUE",
        ),
        (
            ("update", "147", "--overhead-key", "30", "--hours", "1=lots"),
            "value must be a number",
        ),
        (
            ("update", "147", "--overhead-key", "30", "--note", "x=hi"),
            "day must be a number",
        ),
    ],
)
def test_update_rejects_bad_usage(
    run: Callable[..., tuple[Result, list[dict[str, Any]]]],
    args: tuple[str, ...],
    message: str,
) -> None:
    result, sent = run(*args)

    assert result.exit_code != 0
    assert message in result.output
    # Nothing reached the API; a rejected invocation must not write.
    assert not [call for call in sent if call["Method"] == "UpdateTimesheets"]
