from typing import Any, Literal, override

from pydantic import Field

from ajera.schemas.generic import (
    GenericBaseModel,
    GenericRequest,
    GenericResponse,
)

# =============================================================================
# CLASS: Deduction
# =============================================================================


class Deduction(GenericBaseModel):
    """
    Deduction schema for ListDeductions response
    """

    deduction_key: int = Field(
        default=0,
        alias="DeductionKey",
        description="Unique deduction key.",
    )
    description: str = Field(
        default="",
        alias="Description",
        description="Deduction description.",
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
# CLASS: ListDeductionsArguments
# =============================================================================


class ListDeductionsArguments(GenericBaseModel):
    """
    Optional filter arguments for ListDeductions
    """

    filter_by_status: list[str] | None = Field(
        default=None,
        alias="FilterByStatus",
        description="Filter deductions by status values (e.g. Active, Inactive).",
    )


# =============================================================================
# CLASS: ListDeductions
# =============================================================================


class ListDeductions(GenericRequest[ListDeductionsArguments]):
    """
    List Deductions request body
    """

    method: Literal["ListDeductions"] = Field(
        default="ListDeductions",
        alias="Method",
        description="API method name to invoke.",
        frozen=True,
    )


# =============================================================================
# CLASS: ListDeductionsResponse
# =============================================================================


class ListDeductionsResponse(GenericResponse[list[Deduction]]):
    """
    Response schema for ListDeductions
    """

    @override
    def model_post_init(self, context: Any) -> None:
        if self.content:
            # Sort the deductions by description
            self.content.sort(key=lambda deduction: deduction.description)
