from typing import Any, Literal, override

from pydantic import Field

from ajera.schemas.generic import (
    GenericBaseModel,
    GenericRequest,
    GenericResponse,
)

# =============================================================================
# CLASS: Fringe
# =============================================================================


class Fringe(GenericBaseModel):
    """
    Fringe schema for ListFringes response
    """

    fringe_key: int = Field(
        default=0,
        alias="FringeKey",
        description="Unique fringe key.",
    )
    description: str = Field(
        default="",
        alias="Description",
        description="Fringe description.",
    )
    status: str = Field(
        default="",
        alias="Status",
        description="Status (e.g. Active or Inactive).",
    )
    notes: str = Field(
        default="",
        alias="Notes",
        description="Notes.",
    )


# =============================================================================
# CLASS: ListFringesArguments
# =============================================================================


class ListFringesArguments(GenericBaseModel):
    """
    Optional filter arguments for ListFringes
    """

    filter_by_status: list[str] | None = Field(
        default=None,
        alias="FilterByStatus",
        description="Filter fringes by status values (e.g. Active, Inactive).",
    )


# =============================================================================
# CLASS: ListFringes
# =============================================================================


class ListFringes(GenericRequest[ListFringesArguments]):
    """
    List Fringes request body
    """

    method: Literal["ListFringes"] = Field(
        default="ListFringes",
        alias="Method",
        description="API method name to invoke.",
        frozen=True,
    )


# =============================================================================
# CLASS: ListFringesResponse
# =============================================================================


class ListFringesResponse(GenericResponse[list[Fringe]]):
    """
    Response schema for ListFringes
    """

    @override
    def model_post_init(self, context: Any) -> None:
        if self.content:
            self.content.sort(key=lambda fringe: fringe.description)
