from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# =============================================================================
# CLASS: GenericBaseModel
# =============================================================================


class GenericBaseModel(BaseModel):
    """
    A generic base model with common Pydantic configuration
    """

    model_config = ConfigDict(
        validate_by_alias=True,
        validate_by_name=True,
        extra="ignore",
    )


# =============================================================================
# CLASS: GenericRequest
# =============================================================================


class GenericRequest[T: BaseModel](GenericBaseModel):
    """
    A generic API request schema for Ajera API requests
    """

    method: str = Field(
        alias="Method",
        description="API method name to invoke.",
    )
    session_token: str | None = Field(
        default=None,
        alias="SessionToken",
        description="Session token for authenticated requests.",
    )
    method_arguments: T = Field(
        default_factory=T.__init__,
        alias="MethodArguments",
        description="Dictionary of method-specific arguments.",
    )


# =============================================================================
# CLASS: GenericResponse
# =============================================================================


class GenericResponse[T](GenericBaseModel):
    """
    A generic API response schema for Ajera API responses
    """

    response_code: int | None = Field(
        default=None,
        alias="ResponseCode",
        description="Numeric response code.",
    )
    message: str | None = Field(
        default=None,
        alias="Message",
        description="Response message.",
    )
    errors: list[Any] | None = Field(
        default=None,
        alias="Errors",
        description="List of errors returned by the API.",
    )
    usage_key: str | None = Field(
        default=None,
        alias="UsageKey",
        description="Usage GUID for tracking.",
    )
    content: T = Field(
        default_factory=dict,
        alias="Content",
        description="Content payload returned by the API.",
    )
