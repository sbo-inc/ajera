from typing import Any, Literal, override

from pydantic import Field

from ajera.schemas.generic import (
    GenericBaseModel,
    GenericRequest,
    GenericResponse,
)

# =============================================================================
# CLASS: Timesheet
# =============================================================================


class Timesheet(GenericBaseModel):
    """
    Timesheet summary, as returned by ListTimesheets.

    ListTimesheets names its properties with spaces (`"Timesheet Key"`), unlike
    the rest of the API and unlike GetTimesheets, which returns the same
    timesheet under `TimesheetKey`. The aliases below follow the wire.

    A timesheet covers a week; the per-day hours live on TimesheetDetails,
    which GetTimesheets returns for the keys listed here.
    """

    timesheet_key: int = Field(
        default=0,
        alias="Timesheet Key",
        description="Unique timesheet key.",
    )
    company_key: int = Field(
        default=0,
        alias="Company Key",
        description="Key of the company the timesheet belongs to.",
    )
    company_name: str = Field(
        default="",
        alias="Company Name",
        description="Company name.",
    )
    employee_key: int = Field(
        default=0,
        alias="Employee Key",
        description="Key of the employee the timesheet belongs to.",
    )
    employee: str = Field(
        default="",
        alias="Employee",
        description="Employee full name.",
    )
    employee_status: str = Field(
        default="",
        alias="Employee Status",
        description="Employee status, Active or Inactive.",
    )
    first_name: str = Field(
        default="",
        alias="First Name",
        description="Employee first name.",
    )
    middle_name: str = Field(
        default="",
        alias="Middle Name",
        description="Employee middle name.",
    )
    last_name: str = Field(
        default="",
        alias="Last Name",
        description="Employee last name.",
    )
    my_employee: bool = Field(
        default=False,
        alias="My Employee",
        description="Whether the employee reports to the authorizing employee.",
    )
    multilevel_employee: bool = Field(
        default=False,
        alias="Multilevel Employee",
        description="Whether the employee uses multilevel approval.",
    )
    timesheet_date: str = Field(
        default="",
        alias="Timesheet Date",
        description="Start date of the timesheet week (YYYY-MM-DD).",
    )
    timesheet_total: float = Field(
        default=0.0,
        alias="Timesheet Total",
        description="Total hours on the timesheet.",
    )
    target_billable_percent: float = Field(
        default=0.0,
        alias="Target Billable Percent",
        description="Target percentage of billable hours for the employee.",
    )
    actual_billable_percent: float = Field(
        default=0.0,
        alias="Actual Billable Percent",
        description="Actual percentage of billable hours on the timesheet.",
    )
    submitted: bool = Field(
        default=False,
        alias="Submitted",
        description="Whether the timesheet has been submitted for approval.",
    )
    submitted_date: str | None = Field(
        default=None,
        alias="Submitted Date",
        description="When the timesheet was submitted, null if it was not.",
    )
    submitted_by: str = Field(
        default="",
        alias="Submitted By",
        description="Who submitted the timesheet.",
    )
    supervisor_approved: bool = Field(
        default=False,
        alias="Supervisor Approved",
        description="Whether the supervisor has approved the timesheet.",
    )
    supervisor_approved_date: str | None = Field(
        default=None,
        alias="Supervisor Approved Date",
        description="When the supervisor approved, null if they have not.",
    )
    supervisor_approved_by: str = Field(
        default="",
        alias="Supervisor Approved By",
        description="Who approved the timesheet as supervisor.",
    )
    accounting_approved: bool = Field(
        default=False,
        alias="Accounting Approved",
        description="Whether accounting has approved the timesheet.",
    )
    accounting_approved_date: str | None = Field(
        default=None,
        alias="Accounting Approved Date",
        description="When accounting approved, null if they have not.",
    )
    accounting_approved_by: str = Field(
        default="",
        alias="Accounting Approved By",
        description="Who approved the timesheet for accounting.",
    )
    project_manager_approved: bool = Field(
        default=False,
        alias="Project Manager Approved",
        description="Whether the project manager has approved the timesheet.",
    )
    project_manager_approved_value: int = Field(
        default=0,
        alias="Project Manager Approved Value",
        description="Project-manager approval state as Ajera's numeric code.",
    )
    rejected: bool = Field(
        default=False,
        alias="Rejected",
        description="Whether the timesheet was rejected.",
    )
    rejected_value: int = Field(
        default=0,
        alias="Rejected Value",
        description="Rejection state as Ajera's numeric code.",
    )
    billed: bool = Field(
        default=False,
        alias="Billed",
        description="Whether the timesheet's hours have been billed.",
    )
    paid: bool = Field(
        default=False,
        alias="Paid",
        description="Whether the timesheet's hours have been paid.",
    )
    paid_value: int = Field(
        default=0,
        alias="Paid Value",
        description="Paid state as Ajera's numeric code.",
    )


# =============================================================================
# CLASS: TimesheetOverheadTotals
# =============================================================================


class TimesheetOverheadTotals(GenericBaseModel):
    """
    Row of overhead totals for the timesheet week.

    Returned empty by CreateTimesheet, UpdateTimesheets, and SubmitTimesheets,
    which report the totals only through the detail rows they echo back.
    """

    overhead_group_detail: str = Field(
        default="",
        alias="Timesheet Overhead Group Detail",
        description="Name of the overhead group detail the totals cover.",
    )
    d1: float = Field(
        default=0.0,
        alias="D1",
        description="Total hours on day 1 of the timesheet week.",
    )
    d2: float = Field(
        default=0.0,
        alias="D2",
        description="Total hours on day 2 of the timesheet week.",
    )
    d3: float = Field(
        default=0.0,
        alias="D3",
        description="Total hours on day 3 of the timesheet week.",
    )
    d4: float = Field(
        default=0.0,
        alias="D4",
        description="Total hours on day 4 of the timesheet week.",
    )
    d5: float = Field(
        default=0.0,
        alias="D5",
        description="Total hours on day 5 of the timesheet week.",
    )
    d6: float = Field(
        default=0.0,
        alias="D6",
        description="Total hours on day 6 of the timesheet week.",
    )
    d7: float = Field(
        default=0.0,
        alias="D7",
        description="Total hours on day 7 of the timesheet week.",
    )
    d1_regular: float = Field(
        default=0.0,
        alias="D1 Regular",
        description="Regular hours on day 1 of the timesheet week.",
    )
    d2_regular: float = Field(
        default=0.0,
        alias="D2 Regular",
        description="Regular hours on day 2 of the timesheet week.",
    )
    d3_regular: float = Field(
        default=0.0,
        alias="D3 Regular",
        description="Regular hours on day 3 of the timesheet week.",
    )
    d4_regular: float = Field(
        default=0.0,
        alias="D4 Regular",
        description="Regular hours on day 4 of the timesheet week.",
    )
    d5_regular: float = Field(
        default=0.0,
        alias="D5 Regular",
        description="Regular hours on day 5 of the timesheet week.",
    )
    d6_regular: float = Field(
        default=0.0,
        alias="D6 Regular",
        description="Regular hours on day 6 of the timesheet week.",
    )
    d7_regular: float = Field(
        default=0.0,
        alias="D7 Regular",
        description="Regular hours on day 7 of the timesheet week.",
    )
    regular_hours: float = Field(
        default=0.0,
        alias="Regular Hours",
        description="Total regular hours across the week.",
    )
    ot_hours: float = Field(
        default=0.0,
        alias="OT Hours",
        description="Total overtime hours across the week.",
    )
    total_hours: float = Field(
        default=0.0,
        alias="Total Hours",
        description="Total hours across the week.",
    )


# =============================================================================
# CLASS: TimesheetOverheadEntry
# =============================================================================


class TimesheetOverheadEntry(GenericBaseModel):
    """
    One overhead row on a timesheet, holding a week of daily hours.

    Overhead rows record non-project time (vacation, holiday, general
    overhead) against an overhead group detail rather than a project.
    """

    locked: bool = Field(
        default=False,
        alias="Locked",
        description="Whether the row is locked against further edits.",
    )
    timesheet_overhead_key: int = Field(
        default=0,
        alias="Timesheet Overhead Key",
        description="Unique key of this overhead row.",
    )
    employee_key: int = Field(
        default=0,
        alias="Employee Key",
        description="Key of the employee the row belongs to.",
    )
    overhead_group_detail_key: int = Field(
        default=0,
        alias="Timesheet Overhead Group Detail Key",
        description="Key of the overhead group detail the hours are charged to.",
    )
    overhead_group_detail: str = Field(
        default="",
        alias="Timesheet Overhead Group Detail",
        description="Name of the overhead group detail, e.g. Vacation.",
    )
    d1_regular: float = Field(
        default=0.0,
        alias="D1 Regular",
        description="Regular hours on day 1 of the timesheet week.",
    )
    d2_regular: float = Field(
        default=0.0,
        alias="D2 Regular",
        description="Regular hours on day 2 of the timesheet week.",
    )
    d3_regular: float = Field(
        default=0.0,
        alias="D3 Regular",
        description="Regular hours on day 3 of the timesheet week.",
    )
    d4_regular: float = Field(
        default=0.0,
        alias="D4 Regular",
        description="Regular hours on day 4 of the timesheet week.",
    )
    d5_regular: float = Field(
        default=0.0,
        alias="D5 Regular",
        description="Regular hours on day 5 of the timesheet week.",
    )
    d6_regular: float = Field(
        default=0.0,
        alias="D6 Regular",
        description="Regular hours on day 6 of the timesheet week.",
    )
    d7_regular: float = Field(
        default=0.0,
        alias="D7 Regular",
        description="Regular hours on day 7 of the timesheet week.",
    )
    d1_notes: str = Field(
        default="",
        alias="D1 Notes",
        description="Notes on the regular hours for day 1.",
    )
    d2_notes: str = Field(
        default="",
        alias="D2 Notes",
        description="Notes on the regular hours for day 2.",
    )
    d3_notes: str = Field(
        default="",
        alias="D3 Notes",
        description="Notes on the regular hours for day 3.",
    )
    d4_notes: str = Field(
        default="",
        alias="D4 Notes",
        description="Notes on the regular hours for day 4.",
    )
    d5_notes: str = Field(
        default="",
        alias="D5 Notes",
        description="Notes on the regular hours for day 5.",
    )
    d6_notes: str = Field(
        default="",
        alias="D6 Notes",
        description="Notes on the regular hours for day 6.",
    )
    d7_notes: str = Field(
        default="",
        alias="D7 Notes",
        description="Notes on the regular hours for day 7.",
    )


# =============================================================================
# CLASS: TimesheetOverhead
# =============================================================================


class TimesheetOverhead(GenericBaseModel):
    """
    Overhead section of a timesheet: its totals and its rows
    """

    totals: TimesheetOverheadTotals = Field(
        default_factory=TimesheetOverheadTotals,
        alias="Totals",
        description="Totals across the overhead rows.",
    )
    detail: list[TimesheetOverheadEntry] = Field(
        default=[],
        alias="Detail",
        description="The overhead rows.",
    )


# =============================================================================
# CLASS: TimesheetProjectTotals
# =============================================================================


class TimesheetProjectTotals(GenericBaseModel):
    """
    Row of project totals for the timesheet week.

    Returned empty by CreateTimesheet, UpdateTimesheets, and SubmitTimesheets,
    which report the totals only through the detail rows they echo back.
    """

    project_description: str = Field(
        default="",
        alias="Project Description",
        description="Project description the totals cover.",
    )
    phase_description: str = Field(
        default="",
        alias="Phase Description",
        description="Phase description the totals cover.",
    )
    activity: str = Field(
        default="",
        alias="Activity",
        description="Activity the totals cover.",
    )
    d1_regular: float = Field(
        default=0.0,
        alias="D1 Regular",
        description="Regular hours on day 1 of the timesheet week.",
    )
    d2_regular: float = Field(
        default=0.0,
        alias="D2 Regular",
        description="Regular hours on day 2 of the timesheet week.",
    )
    d3_regular: float = Field(
        default=0.0,
        alias="D3 Regular",
        description="Regular hours on day 3 of the timesheet week.",
    )
    d4_regular: float = Field(
        default=0.0,
        alias="D4 Regular",
        description="Regular hours on day 4 of the timesheet week.",
    )
    d5_regular: float = Field(
        default=0.0,
        alias="D5 Regular",
        description="Regular hours on day 5 of the timesheet week.",
    )
    d6_regular: float = Field(
        default=0.0,
        alias="D6 Regular",
        description="Regular hours on day 6 of the timesheet week.",
    )
    d7_regular: float = Field(
        default=0.0,
        alias="D7 Regular",
        description="Regular hours on day 7 of the timesheet week.",
    )
    d1_overtime: float = Field(
        default=0.0,
        alias="D1 Overtime",
        description="Overtime hours on day 1 of the timesheet week.",
    )
    d2_overtime: float = Field(
        default=0.0,
        alias="D2 Overtime",
        description="Overtime hours on day 2 of the timesheet week.",
    )
    d3_overtime: float = Field(
        default=0.0,
        alias="D3 Overtime",
        description="Overtime hours on day 3 of the timesheet week.",
    )
    d4_overtime: float = Field(
        default=0.0,
        alias="D4 Overtime",
        description="Overtime hours on day 4 of the timesheet week.",
    )
    d5_overtime: float = Field(
        default=0.0,
        alias="D5 Overtime",
        description="Overtime hours on day 5 of the timesheet week.",
    )
    d6_overtime: float = Field(
        default=0.0,
        alias="D6 Overtime",
        description="Overtime hours on day 6 of the timesheet week.",
    )
    d7_overtime: float = Field(
        default=0.0,
        alias="D7 Overtime",
        description="Overtime hours on day 7 of the timesheet week.",
    )
    d1_notes: str = Field(
        default="",
        alias="D1 Notes",
        description="Notes on the regular hours for day 1.",
    )
    d2_notes: str = Field(
        default="",
        alias="D2 Notes",
        description="Notes on the regular hours for day 2.",
    )
    d3_notes: str = Field(
        default="",
        alias="D3 Notes",
        description="Notes on the regular hours for day 3.",
    )
    d4_notes: str = Field(
        default="",
        alias="D4 Notes",
        description="Notes on the regular hours for day 4.",
    )
    d5_notes: str = Field(
        default="",
        alias="D5 Notes",
        description="Notes on the regular hours for day 5.",
    )
    d6_notes: str = Field(
        default="",
        alias="D6 Notes",
        description="Notes on the regular hours for day 6.",
    )
    d7_notes: str = Field(
        default="",
        alias="D7 Notes",
        description="Notes on the regular hours for day 7.",
    )


# =============================================================================
# CLASS: TimesheetProjectEntry
# =============================================================================


class TimesheetProjectEntry(GenericBaseModel):
    """
    One project row on a timesheet, holding a week of daily hours.

    A row charges time to a project/phase/activity combination. Regular and
    overtime hours are tracked separately and carry separate notes.
    """

    timesheet_project_key: int = Field(
        default=0,
        alias="Timesheet Project Key",
        description="Unique key of this project row, used to update it.",
    )
    project_key: int = Field(
        default=0,
        alias="Project Key",
        description="Key of the project the hours are charged to.",
    )
    project_description: str = Field(
        default="",
        alias="Project Description",
        description="Project description.",
    )
    phase_key: int = Field(
        default=0,
        alias="Phase Key",
        description="Key of the phase the hours are charged to.",
    )
    phase_description: str = Field(
        default="",
        alias="Phase Description",
        description="Phase description.",
    )
    activity_key: int = Field(
        default=0,
        alias="Activity Key",
        description="Key of the activity the hours are charged to.",
    )
    activity: str = Field(
        default="",
        alias="Activity",
        description="Activity description.",
    )
    employee_type_key: int | None = Field(
        default=None,
        alias="Employee Type Key",
        description="Employee type the hours are charged at.",
    )
    d1_regular: float = Field(
        default=0.0,
        alias="D1 Regular",
        description="Regular hours on day 1 of the timesheet week.",
    )
    d2_regular: float = Field(
        default=0.0,
        alias="D2 Regular",
        description="Regular hours on day 2 of the timesheet week.",
    )
    d3_regular: float = Field(
        default=0.0,
        alias="D3 Regular",
        description="Regular hours on day 3 of the timesheet week.",
    )
    d4_regular: float = Field(
        default=0.0,
        alias="D4 Regular",
        description="Regular hours on day 4 of the timesheet week.",
    )
    d5_regular: float = Field(
        default=0.0,
        alias="D5 Regular",
        description="Regular hours on day 5 of the timesheet week.",
    )
    d6_regular: float = Field(
        default=0.0,
        alias="D6 Regular",
        description="Regular hours on day 6 of the timesheet week.",
    )
    d7_regular: float = Field(
        default=0.0,
        alias="D7 Regular",
        description="Regular hours on day 7 of the timesheet week.",
    )
    d1_overtime: float = Field(
        default=0.0,
        alias="D1 Overtime",
        description="Overtime hours on day 1 of the timesheet week.",
    )
    d2_overtime: float = Field(
        default=0.0,
        alias="D2 Overtime",
        description="Overtime hours on day 2 of the timesheet week.",
    )
    d3_overtime: float = Field(
        default=0.0,
        alias="D3 Overtime",
        description="Overtime hours on day 3 of the timesheet week.",
    )
    d4_overtime: float = Field(
        default=0.0,
        alias="D4 Overtime",
        description="Overtime hours on day 4 of the timesheet week.",
    )
    d5_overtime: float = Field(
        default=0.0,
        alias="D5 Overtime",
        description="Overtime hours on day 5 of the timesheet week.",
    )
    d6_overtime: float = Field(
        default=0.0,
        alias="D6 Overtime",
        description="Overtime hours on day 6 of the timesheet week.",
    )
    d7_overtime: float = Field(
        default=0.0,
        alias="D7 Overtime",
        description="Overtime hours on day 7 of the timesheet week.",
    )
    d1_notes: str = Field(
        default="",
        alias="D1 Notes",
        description="Notes on the regular hours for day 1.",
    )
    d2_notes: str = Field(
        default="",
        alias="D2 Notes",
        description="Notes on the regular hours for day 2.",
    )
    d3_notes: str = Field(
        default="",
        alias="D3 Notes",
        description="Notes on the regular hours for day 3.",
    )
    d4_notes: str = Field(
        default="",
        alias="D4 Notes",
        description="Notes on the regular hours for day 4.",
    )
    d5_notes: str = Field(
        default="",
        alias="D5 Notes",
        description="Notes on the regular hours for day 5.",
    )
    d6_notes: str = Field(
        default="",
        alias="D6 Notes",
        description="Notes on the regular hours for day 6.",
    )
    d7_notes: str = Field(
        default="",
        alias="D7 Notes",
        description="Notes on the regular hours for day 7.",
    )
    d1_ot_notes: str = Field(
        default="",
        alias="D1 OT Notes",
        description="Notes on the overtime hours for day 1.",
    )
    d2_ot_notes: str = Field(
        default="",
        alias="D2 OT Notes",
        description="Notes on the overtime hours for day 2.",
    )
    d3_ot_notes: str = Field(
        default="",
        alias="D3 OT Notes",
        description="Notes on the overtime hours for day 3.",
    )
    d4_ot_notes: str = Field(
        default="",
        alias="D4 OT Notes",
        description="Notes on the overtime hours for day 4.",
    )
    d5_ot_notes: str = Field(
        default="",
        alias="D5 OT Notes",
        description="Notes on the overtime hours for day 5.",
    )
    d6_ot_notes: str = Field(
        default="",
        alias="D6 OT Notes",
        description="Notes on the overtime hours for day 6.",
    )
    d7_ot_notes: str = Field(
        default="",
        alias="D7 OT Notes",
        description="Notes on the overtime hours for day 7.",
    )


# =============================================================================
# CLASS: TimesheetProject
# =============================================================================


class TimesheetProject(GenericBaseModel):
    """
    Project section of a timesheet: its totals and its rows
    """

    totals: TimesheetProjectTotals = Field(
        default_factory=TimesheetProjectTotals,
        alias="Totals",
        description="Totals across the project rows.",
    )
    detail: list[TimesheetProjectEntry] = Field(
        default=[],
        alias="Detail",
        description="The project rows.",
    )


# =============================================================================
# CLASS: TimesheetUnchangedData
# =============================================================================


class TimesheetUnchangedData(GenericBaseModel):
    """
    Opaque baseline of a timesheet, as two base64 strings.

    UpdateTimesheets requires the pair exactly as GetTimesheets returned it:
    it is the optimistic-concurrency token for the timesheet, playing the same
    role `LastModifiedDate` plays elsewhere in the API. The contents are not
    documented and are never decoded here; they are echoed back verbatim.
    """

    overhead: str = Field(
        default="",
        alias="Overhead",
        description="Base64 baseline of the overhead section.",
    )
    project: str = Field(
        default="",
        alias="Project",
        description="Base64 baseline of the project section.",
    )


# =============================================================================
# CLASS: TimesheetDetails
# =============================================================================


class TimesheetDetails(GenericBaseModel):
    """
    A timesheet with its overhead and project rows.

    Returned by GetTimesheets, CreateTimesheet, UpdateTimesheets, and
    SubmitTimesheets. The three submission fields are populated only by
    SubmitTimesheets; the other methods leave them at their defaults.
    """

    timesheet_key: int = Field(
        default=0,
        alias="TimesheetKey",
        description="Unique timesheet key.",
    )
    timesheet_date: str = Field(
        default="",
        alias="TimesheetDate",
        description="Start date of the timesheet week.",
    )
    employee_key: int = Field(
        default=0,
        alias="EmployeeKey",
        description="Key of the employee the timesheet belongs to.",
    )
    status: str = Field(
        default="",
        alias="Status",
        description="Timesheet status (populated by SubmitTimesheets).",
    )
    submitted_date_time: str | None = Field(
        default=None,
        alias="SubmittedDateTime",
        description="When the timesheet was submitted (populated by SubmitTimesheets).",
    )
    submitted_by: int | None = Field(
        default=None,
        alias="SubmittedBy",
        description="Employee key of the submitter (populated by SubmitTimesheets).",
    )
    overhead: TimesheetOverhead = Field(
        default_factory=TimesheetOverhead,
        alias="Overhead",
        description="Overhead rows and their totals.",
    )
    project: TimesheetProject = Field(
        default_factory=TimesheetProject,
        alias="Project",
        description="Project rows and their totals.",
    )
    unchanged_data: TimesheetUnchangedData = Field(
        default_factory=TimesheetUnchangedData,
        alias="UnchangedData",
        description="Opaque baseline that UpdateTimesheets requires back.",
    )


# =============================================================================
# CLASS: ListTimesheetsArguments
# =============================================================================


class ListTimesheetsArguments(GenericBaseModel):
    """
    Optional filter arguments for ListTimesheets
    """

    filter_by_company: list[int] | None = Field(
        default=None,
        alias="FilterByCompany",
        description="Filter by company keys.",
    )
    filter_by_employee: list[int] | None = Field(
        default=None,
        alias="FilterByEmployee",
        description="Filter by employee keys.",
    )
    filter_by_name_like: str | None = Field(
        default=None,
        alias="FilterByNameLike",
        description="Filter where the employee name contains this substring.",
    )
    filter_by_paid: bool | None = Field(
        default=None,
        alias="FilterByPaid",
        description="Include only paid timesheets.",
    )
    filter_by_unpaid: bool | None = Field(
        default=None,
        alias="FilterByUnpaid",
        description="Include only unpaid timesheets.",
    )
    filter_by_submitted: bool | None = Field(
        default=None,
        alias="FilterBySubmitted",
        description="Include only submitted timesheets.",
    )
    filter_by_unsubmitted: bool | None = Field(
        default=None,
        alias="FilterByUnsubmitted",
        description="Include only unsubmitted timesheets.",
    )
    filter_by_rejected: bool | None = Field(
        default=None,
        alias="FilterByRejected",
        description="Include only rejected timesheets.",
    )
    filter_by_earliest_timesheet_date: str | None = Field(
        default=None,
        alias="FilterByEarliestTimesheetDate",
        description="Earliest timesheet date (YYYY-MM-DD).",
    )
    filter_by_latest_timesheet_date: str | None = Field(
        default=None,
        alias="FilterByLatestTimesheetDate",
        description="Latest timesheet date (YYYY-MM-DD).",
    )


# =============================================================================
# CLASS: ListTimesheets
# =============================================================================


class ListTimesheets(GenericRequest[ListTimesheetsArguments]):
    """
    List Timesheets request body
    """

    method: Literal["ListTimesheets"] = Field(
        default="ListTimesheets",
        alias="Method",
        description="API method name to invoke.",
        frozen=True,
    )


# =============================================================================
# CLASS: ListTimesheetsResponse
# =============================================================================


class ListTimesheetsResponse(GenericResponse[list[Timesheet]]):
    """
    Response schema for ListTimesheets
    """

    @override
    def model_post_init(self, context: Any) -> None:
        if self.content:
            # Sort by week (most recent last), then employee, then key.
            self.content.sort(
                key=lambda sheet: (
                    sheet.timesheet_date,
                    sheet.employee_key,
                    sheet.timesheet_key,
                )
            )


# =============================================================================
# CLASS: GetTimesheetsArguments
# =============================================================================


class GetTimesheetsArguments(GenericBaseModel):
    """
    Arguments for GetTimesheets
    """

    requested_timesheets: list[int] = Field(
        alias="RequestedTimesheets",
        description="Timesheet keys to retrieve (at least one required).",
    )


# =============================================================================
# CLASS: GetTimesheets
# =============================================================================


class GetTimesheets(GenericRequest[GetTimesheetsArguments]):
    """
    Get Timesheets request body
    """

    method: Literal["GetTimesheets"] = Field(
        default="GetTimesheets",
        alias="Method",
        description="API method name to invoke.",
        frozen=True,
    )


# =============================================================================
# CLASS: TimesheetCreate
# =============================================================================


class TimesheetCreate(GenericBaseModel):
    """
    The timesheet to create.

    The new timesheet starts empty unless one of the prefill options is set.
    `prefill_recent` and `prefill_scheduled` seed it from the employee's recent
    or scheduled work, and `copy_from_timesheet_key` copies the rows of an
    existing timesheet.
    """

    employee_key: int = Field(
        alias="EmployeeKey",
        description="Key of the employee to create the timesheet for.",
    )
    timesheet_date: str = Field(
        alias="TimesheetDate",
        description="Start date of the timesheet week (YYYY-MM-DD).",
    )
    prefill_recent: bool | None = Field(
        default=None,
        alias="PrefillRecent",
        description="Prefill rows from the employee's recent projects.",
    )
    prefill_scheduled: bool | None = Field(
        default=None,
        alias="PrefillScheduled",
        description="Prefill rows from the employee's scheduled projects.",
    )
    copy_from_timesheet_key: int | None = Field(
        default=None,
        alias="CopyFromTimesheetKey",
        description="Copy the rows of this existing timesheet.",
    )
    activity_key: int | None = Field(
        default=None,
        alias="ActivityKey",
        description="Activity to use on the prefilled rows.",
    )
    allow_past_90_days: bool | None = Field(
        default=None,
        alias="AllowPast90Days",
        description="Allow a timesheet date more than 90 days in the past.",
    )


# =============================================================================
# CLASS: CreateTimesheetArguments
# =============================================================================


class CreateTimesheetArguments(GenericBaseModel):
    """
    Arguments for CreateTimesheet
    """

    timesheet: TimesheetCreate = Field(
        alias="Timesheet",
        description="The timesheet to create.",
    )


# =============================================================================
# CLASS: CreateTimesheet
# =============================================================================


class CreateTimesheet(GenericRequest[CreateTimesheetArguments]):
    """
    Create Timesheet request body
    """

    method: Literal["CreateTimesheet"] = Field(
        default="CreateTimesheet",
        alias="Method",
        description="API method name to invoke.",
        frozen=True,
    )


# =============================================================================
# CLASS: TimesheetRowEdit
# =============================================================================


class TimesheetRowEdit(GenericBaseModel):
    """
    The daily hours and notes shared by every kind of timesheet row edit.

    Only the days you set are sent, and the API leaves the rest of the row as
    it was, so a single-day correction need name only that day. Overtime is
    not editable through UpdateTimesheets; enter it in Ajera directly.
    """

    d1_regular: float | None = Field(
        default=None,
        alias="D1 Regular",
        description="Regular hours to set on day 1 of the timesheet week.",
    )
    d2_regular: float | None = Field(
        default=None,
        alias="D2 Regular",
        description="Regular hours to set on day 2 of the timesheet week.",
    )
    d3_regular: float | None = Field(
        default=None,
        alias="D3 Regular",
        description="Regular hours to set on day 3 of the timesheet week.",
    )
    d4_regular: float | None = Field(
        default=None,
        alias="D4 Regular",
        description="Regular hours to set on day 4 of the timesheet week.",
    )
    d5_regular: float | None = Field(
        default=None,
        alias="D5 Regular",
        description="Regular hours to set on day 5 of the timesheet week.",
    )
    d6_regular: float | None = Field(
        default=None,
        alias="D6 Regular",
        description="Regular hours to set on day 6 of the timesheet week.",
    )
    d7_regular: float | None = Field(
        default=None,
        alias="D7 Regular",
        description="Regular hours to set on day 7 of the timesheet week.",
    )
    d1_notes: str | None = Field(
        default=None,
        alias="D1 Notes",
        description="Notes to set on day 1 of the timesheet week.",
    )
    d2_notes: str | None = Field(
        default=None,
        alias="D2 Notes",
        description="Notes to set on day 2 of the timesheet week.",
    )
    d3_notes: str | None = Field(
        default=None,
        alias="D3 Notes",
        description="Notes to set on day 3 of the timesheet week.",
    )
    d4_notes: str | None = Field(
        default=None,
        alias="D4 Notes",
        description="Notes to set on day 4 of the timesheet week.",
    )
    d5_notes: str | None = Field(
        default=None,
        alias="D5 Notes",
        description="Notes to set on day 5 of the timesheet week.",
    )
    d6_notes: str | None = Field(
        default=None,
        alias="D6 Notes",
        description="Notes to set on day 6 of the timesheet week.",
    )
    d7_notes: str | None = Field(
        default=None,
        alias="D7 Notes",
        description="Notes to set on day 7 of the timesheet week.",
    )


# =============================================================================
# CLASS: TimesheetOverheadEdit
# =============================================================================


class TimesheetOverheadEdit(TimesheetRowEdit):
    """
    An edit to one overhead row of a timesheet.

    The row is identified by the overhead group detail it charges to, which
    `TimesheetOverheadEntry.overhead_group_detail_key` carries.
    """

    overhead_group_detail_key: int = Field(
        alias="Timesheet Overhead Group Detail Key",
        description="Key of the overhead group detail the row charges to.",
    )


# =============================================================================
# CLASS: TimesheetProjectEdit
# =============================================================================


class TimesheetProjectEdit(TimesheetRowEdit):
    """
    An edit to an existing project row of a timesheet.

    The row is identified by `TimesheetProjectEntry.timesheet_project_key`. To
    add a row that is not on the timesheet yet, use TimesheetProjectRowCreate.
    """

    timesheet_project_key: int = Field(
        alias="Timesheet Project Key",
        description="Key of the project row to edit.",
    )
    employee_type_key: int | None = Field(
        default=None,
        alias="Employee Type Key",
        description="Employee type to charge the hours at.",
    )


# =============================================================================
# CLASS: TimesheetProjectRowCreate
# =============================================================================


class TimesheetProjectRowCreate(TimesheetRowEdit):
    """
    A new project row to add to a timesheet.

    Ajera creates the row from the project, phase, and activity given here, so
    all three are required; an existing row is edited with
    TimesheetProjectEdit instead.
    """

    is_new_row: Literal[True] = Field(
        default=True,
        alias="IsNewRow",
        description="Marks the row as one to create.",
        frozen=True,
    )
    project_key: int = Field(
        alias="Project Key",
        description="Key of the project to charge the hours to.",
    )
    phase_key: int = Field(
        alias="Phase Key",
        description="Key of the phase to charge the hours to.",
    )
    activity_key: int = Field(
        alias="Activity Key",
        description="Key of the activity to charge the hours to.",
    )
    employee_type_key: int | None = Field(
        default=None,
        alias="Employee Type Key",
        description="Employee type to charge the hours at.",
    )


# =============================================================================
# CLASS: TimesheetUpdate
# =============================================================================


class TimesheetUpdate(GenericBaseModel):
    """
    The edits to apply to one timesheet, with the baseline they apply to
    """

    timesheet_key: int = Field(
        alias="TimesheetKey",
        description="Key of the timesheet to update.",
    )
    updated_overheads: list[TimesheetOverheadEdit] = Field(
        default=[],
        alias="UpdatedOverheads",
        description="Edits to the overhead rows.",
    )
    updated_projects: list[TimesheetProjectEdit | TimesheetProjectRowCreate] = Field(
        default=[],
        alias="UpdatedProjects",
        description="Edits to existing project rows, and rows to create.",
    )
    unchanged_data: TimesheetUnchangedData = Field(
        alias="UnchangedData",
        description="The baseline exactly as GetTimesheets returned it.",
    )


# =============================================================================
# CLASS: UpdateTimesheetsArguments
# =============================================================================


class UpdateTimesheetsArguments(GenericBaseModel):
    """
    Arguments for UpdateTimesheets
    """

    timesheets: list[TimesheetUpdate] = Field(
        alias="Timesheets",
        description="The timesheets to update, each with its own edits.",
    )


# =============================================================================
# CLASS: UpdateTimesheets
# =============================================================================


class UpdateTimesheets(GenericRequest[UpdateTimesheetsArguments]):
    """
    Update Timesheets request body
    """

    method: Literal["UpdateTimesheets"] = Field(
        default="UpdateTimesheets",
        alias="Method",
        description="API method name to invoke.",
        frozen=True,
    )


# =============================================================================
# CLASS: SubmitTimesheetsArguments
# =============================================================================


class SubmitTimesheetsArguments(GenericBaseModel):
    """
    Arguments for SubmitTimesheets
    """

    requested_timesheets: list[int] = Field(
        alias="RequestedTimesheets",
        description="Timesheet keys to submit (at least one required).",
    )
    unsubmit: bool | None = Field(
        default=None,
        alias="Unsubmit",
        description="Withdraw the timesheets from approval instead.",
    )


# =============================================================================
# CLASS: SubmitTimesheets
# =============================================================================


class SubmitTimesheets(GenericRequest[SubmitTimesheetsArguments]):
    """
    Submit Timesheets request body
    """

    method: Literal["SubmitTimesheets"] = Field(
        default="SubmitTimesheets",
        alias="Method",
        description="API method name to invoke.",
        frozen=True,
    )
