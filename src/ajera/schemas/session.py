from pydantic import Field

from ajera.schemas.generic import GenericBaseModel, GenericResponse

# =============================================================================
# CLASS: CreateAPISession
# =============================================================================


class CreateAPISession(GenericBaseModel):
    """
    Create API Session request body
    """

    method: str = Field(
        default="CreateAPISession",
        alias="Method",
        description="API method name to invoke.",
        frozen=True,
    )
    username: str = Field(
        alias="Username",
        description="Username for authentication (Environment: `AJERA_API_USERNAME`).",
    )
    password: str = Field(
        alias="Password",
        description="Password for authentication (Environment: `AJERA_API_PASSWORD`).",
    )
    api_version: int = Field(
        default=1,
        alias="APIVersion",
        description="Target API version.",
    )
    use_session_cookie: bool | None = Field(
        default=None,
        alias="UseSessionCookie",
        description="Whether to use a session cookie.",
    )


# =============================================================================
# CLASS: SessionTimesheets
# =============================================================================


class SessionTimesheets(GenericBaseModel):
    """
    Timesheet capability/settings for the authorizing employee.

    `user_has_access` reflects whether the account the API acts as has
    timesheet ("Manage Timesheets") access; timesheet methods are refused when
    it is false.
    """

    user_has_access: bool = Field(
        default=False,
        alias="UserHasAccess",
        description="Whether the authorizing employee has timesheet access.",
    )
    time_start_of_week: str = Field(
        default="",
        alias="TimeStartOfWeek",
        description="First day of the timesheet week, e.g. Monday.",
    )
    time_start_of_week_value: int | None = Field(
        default=None,
        alias="TimeStartOfWeekValue",
        description="Numeric first-day-of-week value.",
    )
    click_to_certify_enabled: bool = Field(
        default=False,
        alias="ClickToCertifyEnabled",
        description="Whether click-to-certify is enabled on timesheets.",
    )
    click_to_certify_text: str = Field(
        default="",
        alias="ClickToCertifyText",
        description="Certification text shown when submitting a timesheet.",
    )


# =============================================================================
# CLASS: APISessionContent
# =============================================================================


class APISessionContent(GenericBaseModel):
    """
    Content payload returned when creating an API session
    """

    employee_key: int | None = Field(
        default=None,
        alias="EmployeeKey",
        description="Ajera logged-in user's employee key (when available).",
    )
    employee_name: str | None = Field(
        default=None,
        alias="EmployeeName",
        description="Ajera logged-in user's name (when available).",
    )
    can_submit: bool | None = Field(
        default=None,
        alias="CanSubmit",
        description="Whether the logged-in user can submit (when available).",
    )
    company_name: str = Field(
        default="",
        alias="CompanyName",
        description="Company name.",
    )
    allow_employee_type_changes: bool | None = Field(
        default=None,
        alias="AllowEmployeeTypeChanges",
        description="Whether employee type changes are allowed.",
    )
    using_icr_mobile: bool | None = Field(
        default=None,
        alias="UsingICRMobile",
        description="Whether the ICR mobile integration is in use.",
    )
    timesheets: SessionTimesheets | None = Field(
        default=None,
        alias="Timesheets",
        description="Timesheet capability/settings for the authorizing employee.",
    )
    session_token: str = Field(
        default="",
        alias="SessionToken",
        description="Session token to use for subsequent requests.",
    )
    session_expiration: str = Field(
        default="",
        alias="SessionExpiration",
        description="Session expiration timestamp.",
    )
    api_url: str = Field(
        default="",
        alias="APIURL",
        description="Base API URL.",
    )
    ajera_version: str = Field(
        default="",
        alias="AjeraVersion",
        description="Ajera version string.",
    )


# =============================================================================
# CLASS: APISession
# =============================================================================


class APISession(GenericResponse[APISessionContent]):
    """
    Response schema for CreateAPISession
    """
