from collections.abc import Callable
from typing import Any

from ajera.operations.generic import Operation, flatten, items
from ajera.schemas.timesheet import (
    CreateTimesheet,
    CreateTimesheetArguments,
    GetTimesheets,
    GetTimesheetsArguments,
    ListTimesheets,
    ListTimesheetsArguments,
    ListTimesheetsResponse,
    SubmitTimesheets,
    SubmitTimesheetsArguments,
    Timesheet,
    TimesheetCreate,
    TimesheetDetails,
    TimesheetOverheadEdit,
    TimesheetProjectEdit,
    TimesheetProjectRowCreate,
    TimesheetUnchangedData,
    TimesheetUpdate,
    UpdateTimesheets,
    UpdateTimesheetsArguments,
)

# Every timesheet method returns its records under the same `Content` key,
# whether it read them, created them, changed them, or submitted them.
TIMESHEETS_KEY = "Timesheets"


# -----------------------------------------------------------------------------
# FUNCTION: single_timesheet
# -----------------------------------------------------------------------------


def single_timesheet(method: str) -> Callable[[dict[str, Any]], TimesheetDetails]:
    """
    Build a parser that takes the one timesheet a single-entity call returns.

    The API answers the single-timesheet methods with the same array the batch
    methods use, so the array is unwrapped here rather than in each facade.

    Returns:
        Callable[[dict[str, Any]], TimesheetDetails]: The parser for one
            timesheet.
    """
    parse_items = items(TIMESHEETS_KEY, TimesheetDetails)

    def parse(data: dict[str, Any]) -> TimesheetDetails:
        timesheets = parse_items(data)
        if not timesheets:
            raise Exception(f"{method} returned no timesheet records")
        return timesheets[0]

    return parse


# -----------------------------------------------------------------------------
# OPERATION: list_timesheets
# -----------------------------------------------------------------------------


def list_timesheets(
    *,
    filter_by_company: list[int] | None = None,
    filter_by_employee: list[int] | None = None,
    filter_by_name_like: str | None = None,
    filter_by_paid: bool | None = None,
    filter_by_unpaid: bool | None = None,
    filter_by_submitted: bool | None = None,
    filter_by_unsubmitted: bool | None = None,
    filter_by_rejected: bool | None = None,
    filter_by_earliest_timesheet_date: str | None = None,
    filter_by_latest_timesheet_date: str | None = None,
) -> Operation[list[Timesheet]]:
    """
    Build the ListTimesheets operation.

    Returns:
        Operation[list[Timesheet]]: The list timesheets operation.
    """
    request = ListTimesheets()
    request.method_arguments = ListTimesheetsArguments(
        filter_by_company=filter_by_company,
        filter_by_employee=filter_by_employee,
        filter_by_name_like=filter_by_name_like,
        filter_by_paid=filter_by_paid,
        filter_by_unpaid=filter_by_unpaid,
        filter_by_submitted=filter_by_submitted,
        filter_by_unsubmitted=filter_by_unsubmitted,
        filter_by_rejected=filter_by_rejected,
        filter_by_earliest_timesheet_date=filter_by_earliest_timesheet_date,
        filter_by_latest_timesheet_date=filter_by_latest_timesheet_date,
    )

    return Operation(
        request=request,
        api_version=2,
        parse=flatten(TIMESHEETS_KEY, ListTimesheetsResponse),
    )


# -----------------------------------------------------------------------------
# OPERATION: get_timesheets
# -----------------------------------------------------------------------------


def get_timesheets(timesheet_keys: list[int]) -> Operation[list[TimesheetDetails]]:
    """
    Build the GetTimesheets operation.

    Returns:
        Operation[list[TimesheetDetails]]: The get timesheets operation.
    """
    request = GetTimesheets()
    request.method_arguments = GetTimesheetsArguments(
        requested_timesheets=timesheet_keys
    )

    return Operation(
        request=request,
        api_version=2,
        parse=items(TIMESHEETS_KEY, TimesheetDetails),
    )


# -----------------------------------------------------------------------------
# OPERATION: create_timesheet
# -----------------------------------------------------------------------------


def create_timesheet(
    *,
    employee_key: int,
    timesheet_date: str,
    prefill_recent: bool | None = None,
    prefill_scheduled: bool | None = None,
    copy_from_timesheet_key: int | None = None,
    activity_key: int | None = None,
    allow_past_90_days: bool | None = None,
) -> Operation[TimesheetDetails]:
    """
    Build the CreateTimesheet operation.

    Returns:
        Operation[TimesheetDetails]: The create timesheet operation.
    """
    request = CreateTimesheet(
        method_arguments=CreateTimesheetArguments(
            timesheet=TimesheetCreate(
                employee_key=employee_key,
                timesheet_date=timesheet_date,
                prefill_recent=prefill_recent,
                prefill_scheduled=prefill_scheduled,
                copy_from_timesheet_key=copy_from_timesheet_key,
                activity_key=activity_key,
                allow_past_90_days=allow_past_90_days,
            )
        )
    )

    return Operation(
        request=request,
        api_version=2,
        parse=single_timesheet("CreateTimesheet"),
    )


# -----------------------------------------------------------------------------
# OPERATION: update_timesheet
# -----------------------------------------------------------------------------


def update_timesheet(
    timesheet_key: int,
    unchanged_data: TimesheetUnchangedData,
    overheads: list[TimesheetOverheadEdit],
    projects: list[TimesheetProjectEdit | TimesheetProjectRowCreate],
) -> Operation[TimesheetDetails]:
    """
    Build the UpdateTimesheets operation for one edited timesheet.

    Returns:
        Operation[TimesheetDetails]: The update timesheet operation.
    """
    request = UpdateTimesheets(
        method_arguments=UpdateTimesheetsArguments(
            timesheets=[
                TimesheetUpdate(
                    timesheet_key=timesheet_key,
                    updated_overheads=overheads,
                    updated_projects=projects,
                    unchanged_data=unchanged_data,
                )
            ]
        )
    )

    return Operation(
        request=request,
        api_version=2,
        parse=single_timesheet("UpdateTimesheets"),
    )


# -----------------------------------------------------------------------------
# OPERATION: submit_timesheets
# -----------------------------------------------------------------------------


def submit_timesheets(
    timesheet_keys: list[int], *, unsubmit: bool = False
) -> Operation[list[TimesheetDetails]]:
    """
    Build the SubmitTimesheets operation.

    Returns:
        Operation[list[TimesheetDetails]]: The submit timesheets operation.
    """
    request = SubmitTimesheets(
        method_arguments=SubmitTimesheetsArguments(
            requested_timesheets=timesheet_keys,
            unsubmit=unsubmit or None,
        )
    )

    return Operation(
        request=request,
        api_version=2,
        parse=items(TIMESHEETS_KEY, TimesheetDetails),
    )
