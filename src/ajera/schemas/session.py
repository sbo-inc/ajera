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
    session_token: str = Field(
        default="",
        alias="SessionToken",
        description="Session token to use for subsequent requests.",
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
