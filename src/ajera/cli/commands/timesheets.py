import click

from ajera.cli.context import ClientContext
from ajera.cli.group import CommonClickGroup
from ajera.cli.output import render
from ajera.schemas.timesheet import (
    TimesheetOverheadEdit,
    TimesheetProjectEdit,
    TimesheetProjectRowCreate,
)

# A timesheet covers one week, so a day is always D1 through D7.
DAYS = range(1, 8)


@click.group(name="timesheets", cls=CommonClickGroup)
def group() -> None:
    """
    List, inspect, and edit timesheets.
    """


# =============================================================================
# FUNCTION: parse_day_values
# =============================================================================


def parse_day_values(values: tuple[str, ...], label: str) -> dict[int, str]:
    """
    Parse repeated `DAY=VALUE` options into a day-keyed mapping.

    Returns:
        dict[int, str]: The value given for each day of the timesheet week.
    """
    parsed: dict[int, str] = {}
    for value in values:
        day, separator, rest = value.partition("=")
        if not separator:
            raise click.BadParameter(f"{label} must be given as DAY=VALUE, got {value}")
        try:
            number = int(day)
        except ValueError:
            raise click.BadParameter(
                f"{label} day must be a number, got {day}"
            ) from None
        if number not in DAYS:
            raise click.BadParameter(f"{label} day must be 1-7, got {number}")
        parsed[number] = rest
    return parsed


# =============================================================================
# FUNCTION: day_payload
# =============================================================================


def day_payload(hours: tuple[str, ...], notes: tuple[str, ...]) -> dict[str, object]:
    """
    Build the aliased day fields shared by every kind of row edit.

    Returns:
        dict[str, object]: The `D<n> Regular` and `D<n> Notes` fields to set.
    """
    payload: dict[str, object] = {}
    for day, value in parse_day_values(hours, "--hours").items():
        try:
            payload[f"D{day} Regular"] = float(value)
        except ValueError:
            raise click.BadParameter(
                f"--hours value must be a number, got {value}"
            ) from None
    for day, text in parse_day_values(notes, "--note").items():
        payload[f"D{day} Notes"] = text
    return payload


@group.command(name="list")
@click.option(
    "--company",
    "filter_by_company",
    type=int,
    multiple=True,
    help="Filter by company key (repeatable).",
)
@click.option(
    "--employee",
    "filter_by_employee",
    type=int,
    multiple=True,
    help="Filter by employee key (repeatable).",
)
@click.option(
    "--name-like",
    "filter_by_name_like",
    type=str,
    default=None,
    help="Filter where the employee name contains this substring.",
)
@click.option(
    "--paid/--no-paid",
    "filter_by_paid",
    default=None,
    help="Include only paid timesheets.",
)
@click.option(
    "--unpaid/--no-unpaid",
    "filter_by_unpaid",
    default=None,
    help="Include only unpaid timesheets.",
)
@click.option(
    "--submitted/--no-submitted",
    "filter_by_submitted",
    default=None,
    help="Include only submitted timesheets.",
)
@click.option(
    "--unsubmitted/--no-unsubmitted",
    "filter_by_unsubmitted",
    default=None,
    help="Include only unsubmitted timesheets.",
)
@click.option(
    "--rejected/--no-rejected",
    "filter_by_rejected",
    default=None,
    help="Include only rejected timesheets.",
)
@click.option(
    "--after",
    "filter_by_earliest_timesheet_date",
    type=str,
    default=None,
    help="Earliest timesheet date (YYYY-MM-DD).",
)
@click.option(
    "--before",
    "filter_by_latest_timesheet_date",
    type=str,
    default=None,
    help="Latest timesheet date (YYYY-MM-DD).",
)
@click.pass_obj
def list_(
    ctx: ClientContext,
    filter_by_company: tuple[int, ...],
    filter_by_employee: tuple[int, ...],
    filter_by_name_like: str | None,
    filter_by_paid: bool | None,
    filter_by_unpaid: bool | None,
    filter_by_submitted: bool | None,
    filter_by_unsubmitted: bool | None,
    filter_by_rejected: bool | None,
    filter_by_earliest_timesheet_date: str | None,
    filter_by_latest_timesheet_date: str | None,
) -> None:
    """
    List timesheets, optionally filtered.

    Returns one summary per timesheet week, without its hours; pass the keys
    to `timesheets get` for the rows behind them.
    """
    render(
        ctx.client.list_timesheets(
            filter_by_company=list(filter_by_company) or None,
            filter_by_employee=list(filter_by_employee) or None,
            filter_by_name_like=filter_by_name_like,
            filter_by_paid=filter_by_paid,
            filter_by_unpaid=filter_by_unpaid,
            filter_by_submitted=filter_by_submitted,
            filter_by_unsubmitted=filter_by_unsubmitted,
            filter_by_rejected=filter_by_rejected,
            filter_by_earliest_timesheet_date=filter_by_earliest_timesheet_date,
            filter_by_latest_timesheet_date=filter_by_latest_timesheet_date,
        )
    )


@group.command(name="get")
@click.argument("timesheet_keys", nargs=-1, required=True, type=int)
@click.pass_obj
def get(ctx: ClientContext, timesheet_keys: tuple[int, ...]) -> None:
    """
    Get one or more timesheets by key, with their rows and daily hours.
    """
    render(ctx.client.get_timesheets(list(timesheet_keys)))


@group.command(name="create")
@click.option("--employee-key", required=True, type=int, help="Employee key.")
@click.option(
    "--date",
    "timesheet_date",
    required=True,
    help="Start date of the timesheet week (YYYY-MM-DD).",
)
@click.option(
    "--prefill-recent/--no-prefill-recent",
    default=None,
    help="Prefill rows from the employee's recent projects.",
)
@click.option(
    "--prefill-scheduled/--no-prefill-scheduled",
    default=None,
    help="Prefill rows from the employee's scheduled projects.",
)
@click.option(
    "--copy-from",
    "copy_from_timesheet_key",
    type=int,
    default=None,
    help="Copy the rows of this existing timesheet.",
)
@click.option(
    "--activity-key",
    type=int,
    default=None,
    help="Activity to use on the prefilled rows.",
)
@click.option(
    "--allow-past-90-days",
    is_flag=True,
    default=None,
    help="Allow a date more than 90 days in the past.",
)
@click.pass_obj
def create(
    ctx: ClientContext,
    employee_key: int,
    timesheet_date: str,
    prefill_recent: bool | None,
    prefill_scheduled: bool | None,
    copy_from_timesheet_key: int | None,
    activity_key: int | None,
    allow_past_90_days: bool | None,
) -> None:
    """
    Create a timesheet for one employee's week.

    The timesheet is empty unless a prefill option seeds it. There is no API
    method to delete a timesheet.
    """
    render(
        ctx.client.create_timesheet(
            employee_key,
            timesheet_date,
            prefill_recent=prefill_recent,
            prefill_scheduled=prefill_scheduled,
            copy_from_timesheet_key=copy_from_timesheet_key,
            activity_key=activity_key,
            allow_past_90_days=allow_past_90_days,
        )
    )


@group.command(name="update")
@click.argument("timesheet_key", type=int)
@click.option(
    "--overhead-key",
    type=int,
    default=None,
    help="Edit the overhead row charging to this overhead group detail key.",
)
@click.option(
    "--project-row-key",
    type=int,
    default=None,
    help="Edit the existing project row with this timesheet project key.",
)
@click.option(
    "--project-key",
    type=int,
    default=None,
    help="Add a project row charging to this project (needs phase and activity).",
)
@click.option("--phase-key", type=int, default=None, help="Phase key for a new row.")
@click.option(
    "--activity-key", type=int, default=None, help="Activity key for a new row."
)
@click.option(
    "--employee-type-key",
    type=int,
    default=None,
    help="Employee type to charge the hours at.",
)
@click.option(
    "--hours",
    multiple=True,
    metavar="DAY=HOURS",
    help="Regular hours for a day of the week, 1-7 (repeatable).",
)
@click.option(
    "--note",
    "notes",
    multiple=True,
    metavar="DAY=TEXT",
    help="Notes for a day of the week, 1-7 (repeatable).",
)
@click.pass_obj
def update(
    ctx: ClientContext,
    timesheet_key: int,
    overhead_key: int | None,
    project_row_key: int | None,
    project_key: int | None,
    phase_key: int | None,
    activity_key: int | None,
    employee_type_key: int | None,
    hours: tuple[str, ...],
    notes: tuple[str, ...],
) -> None:
    """
    Set daily hours and notes on one row of a timesheet.

    Name the row with exactly one of --overhead-key, --project-row-key, or
    --project-key (with --phase-key and --activity-key, to add a row), then
    give its days as `--hours 1=8 --hours 2=4` and `--note 2="Client meeting"`.
    Days you leave out keep their hours. Editing several rows in one request
    is available through the Python client.
    """
    targets = [
        overhead_key is not None,
        project_row_key is not None,
        project_key is not None,
    ]
    if sum(targets) != 1:
        raise click.UsageError(
            "Name exactly one row with --overhead-key, --project-row-key, or "
            "--project-key."
        )

    payload = day_payload(hours, notes)
    overheads: list[TimesheetOverheadEdit] = []
    projects: list[TimesheetProjectEdit | TimesheetProjectRowCreate] = []

    if overhead_key is not None:
        payload["Timesheet Overhead Group Detail Key"] = overhead_key
        overheads.append(TimesheetOverheadEdit.model_validate(payload))
    elif project_row_key is not None:
        payload["Timesheet Project Key"] = project_row_key
        payload["Employee Type Key"] = employee_type_key
        projects.append(TimesheetProjectEdit.model_validate(payload))
    else:
        if phase_key is None or activity_key is None:
            raise click.UsageError(
                "--project-key needs --phase-key and --activity-key to add a row."
            )
        payload["Project Key"] = project_key
        payload["Phase Key"] = phase_key
        payload["Activity Key"] = activity_key
        payload["Employee Type Key"] = employee_type_key
        projects.append(TimesheetProjectRowCreate.model_validate(payload))

    render(
        ctx.client.update_timesheet(
            timesheet_key,
            overheads=overheads,
            projects=projects,
        )
    )


@group.command(name="submit")
@click.argument("timesheet_keys", nargs=-1, required=True, type=int)
@click.option(
    "--unsubmit",
    is_flag=True,
    default=False,
    help="Withdraw the timesheets from approval instead of submitting them.",
)
@click.pass_obj
def submit(ctx: ClientContext, timesheet_keys: tuple[int, ...], unsubmit: bool) -> None:
    """
    Submit one or more timesheets for approval, or withdraw them.
    """
    render(ctx.client.submit_timesheets(list(timesheet_keys), unsubmit=unsubmit))
