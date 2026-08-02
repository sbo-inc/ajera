from typing import Any

from ajera.operations.generic import Operation, flatten, items
from ajera.schemas.vendor import (
    GetVendors,
    GetVendorsArguments,
    ListVendors,
    ListVendorsArguments,
    ListVendorsResponse,
    ListVendorTypes,
    ListVendorTypesArguments,
    ListVendorTypesResponse,
    UpdatedVendorResult,
    UpdateVendors,
    UpdateVendorsArguments,
    UpdateVendorsResponse,
    Vendor,
    VendorDetails,
    VendorType,
)

# -----------------------------------------------------------------------------
# OPERATION: list_vendors
# -----------------------------------------------------------------------------


def list_vendors(
    *,
    filter_by_company: list[int] | None = None,
    filter_by_status: list[str] | None = ["Active"],
    filter_by_name_like: str | None = None,
    filter_by_vendor_type: list[int] | None = None,
    filter_by_earliest_modified_date: str | None = None,
    filter_by_latest_modified_date: str | None = None,
) -> Operation[list[Vendor]]:
    """
    Build the ListVendors operation.

    Returns:
        Operation[list[Vendor]]: The list vendors operation.
    """
    request = ListVendors()
    request.method_arguments = ListVendorsArguments(
        filter_by_company=filter_by_company,
        filter_by_status=filter_by_status,
        filter_by_name_like=filter_by_name_like,
        filter_by_vendor_type=filter_by_vendor_type,
        filter_by_earliest_modified_date=filter_by_earliest_modified_date,
        filter_by_latest_modified_date=filter_by_latest_modified_date,
    )

    return Operation(
        request=request,
        api_version=1,
        parse=flatten("Vendors", ListVendorsResponse),
    )


# -----------------------------------------------------------------------------
# OPERATION: get_vendors
# -----------------------------------------------------------------------------


def get_vendors(vendor_keys: list[int]) -> Operation[list[VendorDetails]]:
    """
    Build the GetVendors operation.

    Returns:
        Operation[list[VendorDetails]]: The get vendors operation.
    """
    request = GetVendors()
    request.method_arguments = GetVendorsArguments(requested_vendors=vendor_keys)

    return Operation(
        request=request,
        api_version=1,
        parse=items("Vendors", VendorDetails),
    )


# -----------------------------------------------------------------------------
# OPERATION: list_vendor_types
# -----------------------------------------------------------------------------


def list_vendor_types(
    *,
    filter_by_status: list[str] | None = ["Active"],
    filter_by_is_credit_card: list[bool] | None = None,
    filter_by_is_consultant: list[bool] | None = None,
) -> Operation[list[VendorType]]:
    """
    Build the ListVendorTypes operation.

    Returns:
        Operation[list[VendorType]]: The list vendor types operation.
    """
    request = ListVendorTypes()
    request.method_arguments = ListVendorTypesArguments(
        filter_by_status=filter_by_status,
        filter_by_is_credit_card=filter_by_is_credit_card,
        filter_by_is_consultant=filter_by_is_consultant,
    )

    return Operation(
        request=request,
        api_version=1,
        parse=flatten("VendorTypes", ListVendorTypesResponse),
    )


# -----------------------------------------------------------------------------
# FUNCTION: apply_vendor_edits
# -----------------------------------------------------------------------------


def apply_vendor_edits(
    baseline: VendorDetails,
    *,
    name: str | None = None,
    vendor_account_id: str | None = None,
    email: str | None = None,
    website: str | None = None,
    primary_phone_number: str | None = None,
    secondary_phone_number: str | None = None,
    tertiary_phone_number: str | None = None,
    fax_number: str | None = None,
    notes: str | None = None,
) -> VendorDetails:
    """
    Apply the non-None edits to a deep copy of the baseline record.

    Returns:
        VendorDetails: The edited copy, which equals the baseline if nothing
            changed.
    """
    modified = baseline.model_copy(deep=True)
    if name is not None:
        modified.name = name
    if vendor_account_id is not None:
        modified.vendor_account_id = vendor_account_id
    if email is not None:
        modified.email = email
    if website is not None:
        modified.website = website
    if primary_phone_number is not None:
        modified.primary_phone_number = primary_phone_number
    if secondary_phone_number is not None:
        modified.secondary_phone_number = secondary_phone_number
    if tertiary_phone_number is not None:
        modified.tertiary_phone_number = tertiary_phone_number
    if fax_number is not None:
        modified.fax_number = fax_number
    if notes is not None:
        modified.notes = notes

    return modified


# -----------------------------------------------------------------------------
# FUNCTION: unchanged_vendor_result
# -----------------------------------------------------------------------------


def unchanged_vendor_result(baseline: VendorDetails) -> UpdatedVendorResult:
    """
    Represent an untouched record as an update result.

    The API rejects no-op updates, so an edit that changes nothing is answered
    from the baseline instead of being sent.

    Returns:
        UpdatedVendorResult: The current record, as an update result.
    """
    return UpdatedVendorResult.model_validate(baseline.model_dump(by_alias=True))


# -----------------------------------------------------------------------------
# OPERATION: update_vendor
# -----------------------------------------------------------------------------


def update_vendor(
    baseline: VendorDetails, modified: VendorDetails
) -> Operation[UpdatedVendorResult]:
    """
    Build the UpdateVendors operation for one edited record.

    Returns:
        Operation[UpdatedVendorResult]: The update vendor operation.
    """
    request = UpdateVendors(
        method_arguments=UpdateVendorsArguments(
            updated_vendors=[modified],
            unchanged_vendors=[baseline],
        )
    )

    def parse(data: dict[str, Any]) -> UpdatedVendorResult:
        results = UpdateVendorsResponse.model_validate(data).content.vendors
        if not results:
            raise Exception("UpdateVendors returned no vendor records")
        return results[0]

    return Operation(request=request, api_version=1, parse=parse)
