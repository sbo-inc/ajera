"""
Unit coverage of the timesheet surface, on both clients.

The fixtures are the payloads from the Ajera timesheet documentation, kept
verbatim so the models are asserted against the shape the API actually
describes - including the spaced property names ListTimesheets and the detail
rows use, which the rest of the API does not.
"""

from collections.abc import Callable
from typing import Any

import httpx
import pytest
from conftest import Handler, body, envelope, session_envelope

from ajera.async_client import AsyncAjeraClient
from ajera.client import AjeraClient
from ajera.schemas.timesheet import (
    TimesheetOverheadEdit,
    TimesheetProjectEdit,
    TimesheetProjectRowCreate,
)

# =============================================================================
# TEST: Fixtures
# =============================================================================

LIST_RECORD: dict[str, Any] = {
    "Timesheet Key": 147,
    "Company Key": 1,
    "Employee Key": 30,
    "Employee Status": "Active",
    "Employee": "Christopher Meehan",
    "First Name": "Christopher",
    "Middle Name": "E.",
    "Last Name": "Meehan",
    "My Employee": False,
    "Timesheet Date": "2012-09-09",
    "Timesheet Total": 25,
    "Submitted": False,
    "Supervisor Approved": False,
    "Accounting Approved": False,
    "Project Manager Approved": False,
    "Rejected": False,
    "Billed": True,
    "Paid": False,
    "Project Manager Approved Value": 0,
    "Paid Value": 0,
    "Rejected Value": 0,
    "Target Billable Percent": 50,
    "Actual Billable Percent": 72,
    "Company Name": "Accutera Architects",
    "Multilevel Employee": False,
    "Submitted Date": None,
    "Submitted By": "",
    "Accounting Approved Date": None,
    "Accounting Approved By": "",
    "Supervisor Approved Date": None,
    "Supervisor Approved By": "",
}

UNCHANGED_DATA: dict[str, str] = {
    "Overhead": "b3ZlcmhlYWQ=",
    "Project": "cHJvamVjdA==",
}

DETAIL_RECORD: dict[str, Any] = {
    "TimesheetKey": 147,
    "TimesheetDate": "2012-09-09T00:00:00",
    "EmployeeKey": 30,
    "Overhead": {
        "Totals": {
            "Timesheet Overhead Group Detail": "Vacation",
            "D1": 0,
            "D2": 4,
            "D3": 3,
            "D1 Regular": 0,
            "D2 Regular": 4,
            "D3 Regular": 3,
            "Regular Hours": 7,
            "OT Hours": 0,
            "Total Hours": 7,
        },
        "Detail": [
            {
                "Locked": False,
                "Timesheet Overhead Key": 147,
                "Employee Key": 30,
                "Timesheet Overhead Group Detail Key": 30,
                "Timesheet Overhead Group Detail": "General",
                "D1 Regular": 0,
                "D2 Regular": 4,
                "D3 Regular": 3,
                "D3 Notes": "",
            }
        ],
    },
    "Project": {
        "Totals": {},
        "Detail": [
            {
                "Timesheet Project Key": 2,
                "Project Key": 32,
                "Phase Key": 33,
                "Activity Key": 5,
                "Employee Type Key": 3,
                "Project Description": "04-110 Milwaukie Hospital Landscape",
                "Phase Description": "Foyer Remodel",
                "Activity": "Project Management",
                "D1 Regular": 8,
                "D2 Regular": 4,
                "D3 Regular": 5,
                "D3 Overtime": 1,
                "D3 Notes": "Meeting with client about submitted floor plans.",
                "D3 OT Notes": "",
            }
        ],
    },
    "UnchangedData": UNCHANGED_DATA,
}


def _recording_api(sent: list[dict[str, Any]], content: Any) -> Handler:
    """
    Stand in for the API, recording each request body and returning `content`.

    Returns:
        Handler: The mock transport handler.
    """

    def handler(request: httpx.Request) -> httpx.Response:
        payload = body(request)
        if payload["Method"] == "CreateAPISession":
            return session_envelope()
        sent.append(payload)
        return envelope(content)

    return handler


async def _call_on_both(
    make_client: Callable[..., AjeraClient],
    make_async_client: Callable[..., AsyncAjeraClient],
    method: str,
    content: Any,
    *args: Any,
    **kwargs: Any,
) -> tuple[Any, list[dict[str, Any]]]:
    """
    Run one client method on both surfaces, asserting they agree.

    Returns:
        tuple[Any, list[dict[str, Any]]]: The sync result and the bodies sent.
    """
    sync_sent: list[dict[str, Any]] = []
    async_sent: list[dict[str, Any]] = []

    client = make_client(_recording_api(sync_sent, content))
    async_client = make_async_client(_recording_api(async_sent, content))

    synchronous = getattr(client, method)(*args, **kwargs)
    asynchronous = await getattr(async_client, method)(*args, **kwargs)

    assert synchronous == asynchronous
    assert sync_sent == async_sent

    client.close()
    await async_client.aclose()

    return synchronous, sync_sent


# =============================================================================
# TEST: list_timesheets
# =============================================================================


async def test_list_timesheets_reads_the_spaced_property_names(
    make_client: Callable[..., AjeraClient],
    make_async_client: Callable[..., AsyncAjeraClient],
) -> None:
    timesheets, sent = await _call_on_both(
        make_client,
        make_async_client,
        "list_timesheets",
        {"Timesheets": [LIST_RECORD]},
        filter_by_employee=[30],
        filter_by_unsubmitted=True,
    )

    assert sent[0]["Method"] == "ListTimesheets"
    assert sent[0]["MethodArguments"] == {
        "FilterByEmployee": [30],
        "FilterByUnsubmitted": True,
    }

    sheet = timesheets[0]
    assert sheet.timesheet_key == 147
    assert sheet.employee == "Christopher Meehan"
    assert sheet.timesheet_date == "2012-09-09"
    assert sheet.timesheet_total == 25.0
    assert sheet.billed is True
    assert sheet.paid is False
    assert sheet.submitted_date is None
    assert sheet.actual_billable_percent == 72.0


async def test_list_timesheets_sorts_by_week_then_employee(
    make_client: Callable[..., AjeraClient],
    make_async_client: Callable[..., AsyncAjeraClient],
) -> None:
    records = [
        {**LIST_RECORD, "Timesheet Key": 3, "Timesheet Date": "2012-09-16"},
        {**LIST_RECORD, "Timesheet Key": 2, "Employee Key": 40},
        {**LIST_RECORD, "Timesheet Key": 1, "Employee Key": 10},
    ]
    timesheets, _ = await _call_on_both(
        make_client, make_async_client, "list_timesheets", {"Timesheets": records}
    )

    assert [sheet.timesheet_key for sheet in timesheets] == [1, 2, 3]


# =============================================================================
# TEST: get_timesheets
# =============================================================================


async def test_get_timesheets_reads_the_rows_and_the_baseline(
    make_client: Callable[..., AjeraClient],
    make_async_client: Callable[..., AsyncAjeraClient],
) -> None:
    timesheets, sent = await _call_on_both(
        make_client,
        make_async_client,
        "get_timesheets",
        {"Timesheets": [DETAIL_RECORD]},
        [147],
    )

    assert sent[0]["Method"] == "GetTimesheets"
    assert sent[0]["MethodArguments"] == {"RequestedTimesheets": [147]}

    sheet = timesheets[0]
    assert sheet.timesheet_key == 147
    assert sheet.employee_key == 30

    overhead = sheet.overhead.detail[0]
    assert overhead.overhead_group_detail_key == 30
    assert overhead.overhead_group_detail == "General"
    assert (overhead.d2_regular, overhead.d3_regular) == (4.0, 3.0)
    assert sheet.overhead.totals.total_hours == 7.0
    assert sheet.overhead.totals.d2 == 4.0

    project = sheet.project.detail[0]
    assert (project.project_key, project.phase_key, project.activity_key) == (32, 33, 5)
    assert project.timesheet_project_key == 2
    assert project.d3_overtime == 1.0
    assert project.d3_notes.startswith("Meeting with client")
    assert project.d3_ot_notes == ""

    # Absent from the payload, so the model default stands rather than an error.
    assert project.d7_regular == 0.0

    assert sheet.unchanged_data.overhead == UNCHANGED_DATA["Overhead"]
    assert sheet.unchanged_data.project == UNCHANGED_DATA["Project"]

    # SubmitTimesheets alone populates these.
    assert sheet.status == ""
    assert sheet.submitted_by is None


# =============================================================================
# TEST: create_timesheet
# =============================================================================


async def test_create_timesheet_nests_the_timesheet_argument(
    make_client: Callable[..., AjeraClient],
    make_async_client: Callable[..., AsyncAjeraClient],
) -> None:
    created, sent = await _call_on_both(
        make_client,
        make_async_client,
        "create_timesheet",
        {"Timesheets": [DETAIL_RECORD]},
        26,
        "2025-01-26",
        prefill_scheduled=True,
        copy_from_timesheet_key=39,
    )

    assert sent[0]["Method"] == "CreateTimesheet"
    assert sent[0]["MethodArguments"] == {
        "Timesheet": {
            "EmployeeKey": 26,
            "TimesheetDate": "2025-01-26",
            "PrefillScheduled": True,
            "CopyFromTimesheetKey": 39,
        }
    }
    assert created.timesheet_key == 147


async def test_create_timesheet_raises_when_nothing_comes_back(
    make_client: Callable[..., AjeraClient],
) -> None:
    client = make_client(_recording_api([], {"Timesheets": []}))

    with pytest.raises(Exception, match="CreateTimesheet returned no timesheet"):
        client.create_timesheet(26, "2025-01-26")

    client.close()


# =============================================================================
# TEST: update_timesheet
# =============================================================================


async def test_update_timesheet_sends_the_documented_edit_shape(
    make_client: Callable[..., AjeraClient],
    make_async_client: Callable[..., AsyncAjeraClient],
) -> None:
    _, sent = await _call_on_both(
        make_client,
        make_async_client,
        "update_timesheet",
        {"Timesheets": [DETAIL_RECORD]},
        147,
        overheads=[TimesheetOverheadEdit(overhead_group_detail_key=30, d1_regular=1)],
        projects=[
            TimesheetProjectEdit(
                timesheet_project_key=2, d2_regular=1, d2_notes="Client meeting"
            ),
            TimesheetProjectRowCreate(
                project_key=32,
                phase_key=33,
                activity_key=2,
                d3_regular=4,
                d3_notes="Design review",
            ),
        ],
    )

    # The baseline read comes first; its UnchangedData is what the update
    # echoes back, so the caller never handles the opaque blobs themselves.
    assert [call["Method"] for call in sent] == ["GetTimesheets", "UpdateTimesheets"]
    assert sent[1]["MethodArguments"] == {
        "Timesheets": [
            {
                "TimesheetKey": 147,
                "UpdatedOverheads": [
                    {"Timesheet Overhead Group Detail Key": 30, "D1 Regular": 1.0}
                ],
                "UpdatedProjects": [
                    {
                        "Timesheet Project Key": 2,
                        "D2 Regular": 1.0,
                        "D2 Notes": "Client meeting",
                    },
                    {
                        "IsNewRow": True,
                        "Project Key": 32,
                        "Phase Key": 33,
                        "Activity Key": 2,
                        "D3 Regular": 4.0,
                        "D3 Notes": "Design review",
                    },
                ],
                "UnchangedData": UNCHANGED_DATA,
            }
        ]
    }


async def test_update_timesheet_without_edits_skips_the_update(
    make_client: Callable[..., AjeraClient],
    make_async_client: Callable[..., AsyncAjeraClient],
) -> None:
    timesheet, sent = await _call_on_both(
        make_client,
        make_async_client,
        "update_timesheet",
        {"Timesheets": [DETAIL_RECORD]},
        147,
    )

    assert [call["Method"] for call in sent] == ["GetTimesheets"]
    assert timesheet.timesheet_key == 147


async def test_update_timesheet_raises_on_an_unknown_key(
    make_client: Callable[..., AjeraClient],
) -> None:
    client = make_client(_recording_api([], {"Timesheets": []}))

    with pytest.raises(ValueError, match="No timesheet found with key 999"):
        client.update_timesheet(999)

    client.close()


# =============================================================================
# TEST: submit_timesheets
# =============================================================================


async def test_submit_timesheets_returns_the_submission_details(
    make_client: Callable[..., AjeraClient],
    make_async_client: Callable[..., AsyncAjeraClient],
) -> None:
    submitted = {
        **DETAIL_RECORD,
        "Status": "Submitted",
        "SubmittedDateTime": "2023-05-15T12:34:56",
        "SubmittedBy": 30,
    }
    timesheets, sent = await _call_on_both(
        make_client,
        make_async_client,
        "submit_timesheets",
        {"Timesheets": [submitted]},
        [147, 148],
    )

    assert sent[0]["Method"] == "SubmitTimesheets"
    # An omitted Unsubmit submits, so the default carries no flag.
    assert sent[0]["MethodArguments"] == {"RequestedTimesheets": [147, 148]}

    assert timesheets[0].status == "Submitted"
    assert timesheets[0].submitted_by == 30
    assert timesheets[0].submitted_date_time == "2023-05-15T12:34:56"


async def test_submit_timesheets_can_unsubmit(
    make_client: Callable[..., AjeraClient],
    make_async_client: Callable[..., AsyncAjeraClient],
) -> None:
    _, sent = await _call_on_both(
        make_client,
        make_async_client,
        "submit_timesheets",
        {"Timesheets": [DETAIL_RECORD]},
        [147],
        unsubmit=True,
    )

    assert sent[0]["MethodArguments"] == {
        "RequestedTimesheets": [147],
        "Unsubmit": True,
    }
