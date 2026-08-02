from typing import Any

from ajera.operations.generic import Operation, flatten, items
from ajera.schemas.contact import (
    Contact,
    ContactDetails,
    ContactType,
    GetContacts,
    GetContactsArguments,
    ListContacts,
    ListContactsArguments,
    ListContactsResponse,
    ListContactTypes,
    ListContactTypesArguments,
    ListContactTypesResponse,
    UpdateContacts,
    UpdateContactsArguments,
    UpdateContactsResponse,
    UpdatedContactResult,
)

# -----------------------------------------------------------------------------
# OPERATION: list_contacts
# -----------------------------------------------------------------------------


def list_contacts(
    *,
    filter_by_company: list[int] | None = None,
    filter_by_status: list[str] | None = ["Active"],
    filter_by_text: str | None = None,
    filter_by_contact_type: list[int] | None = None,
    filter_by_earliest_modified_date: str | None = None,
    filter_by_latest_modified_date: str | None = None,
) -> Operation[list[Contact]]:
    """
    Build the ListContacts operation.

    Returns:
        Operation[list[Contact]]: The list contacts operation.
    """
    request = ListContacts()
    request.method_arguments = ListContactsArguments(
        filter_by_company=filter_by_company,
        filter_by_status=filter_by_status,
        filter_by_text=filter_by_text,
        filter_by_contact_type=filter_by_contact_type,
        filter_by_earliest_modified_date=filter_by_earliest_modified_date,
        filter_by_latest_modified_date=filter_by_latest_modified_date,
    )

    return Operation(
        request=request,
        api_version=1,
        parse=flatten("Contacts", ListContactsResponse),
    )


# -----------------------------------------------------------------------------
# OPERATION: get_contacts
# -----------------------------------------------------------------------------


def get_contacts(contact_keys: list[int]) -> Operation[list[ContactDetails]]:
    """
    Build the GetContacts operation.

    Returns:
        Operation[list[ContactDetails]]: The get contacts operation.
    """
    request = GetContacts()
    request.method_arguments = GetContactsArguments(requested_contacts=contact_keys)

    return Operation(
        request=request,
        api_version=1,
        parse=items("Contacts", ContactDetails),
    )


# -----------------------------------------------------------------------------
# OPERATION: list_contact_types
# -----------------------------------------------------------------------------


def list_contact_types(
    *,
    filter_by_status: list[str] | None = ["Active"],
) -> Operation[list[ContactType]]:
    """
    Build the ListContactTypes operation.

    Returns:
        Operation[list[ContactType]]: The list contact types operation.
    """
    request = ListContactTypes()
    request.method_arguments = ListContactTypesArguments(
        filter_by_status=filter_by_status,
    )

    return Operation(
        request=request,
        api_version=1,
        parse=flatten("ContactTypes", ListContactTypesResponse),
    )


# -----------------------------------------------------------------------------
# FUNCTION: apply_contact_edits
# -----------------------------------------------------------------------------


def apply_contact_edits(
    baseline: ContactDetails,
    *,
    first_name: str | None = None,
    middle_name: str | None = None,
    last_name: str | None = None,
    title: str | None = None,
    company: str | None = None,
    email: str | None = None,
    website: str | None = None,
    primary_phone_number: str | None = None,
    secondary_phone_number: str | None = None,
    tertiary_phone_number: str | None = None,
    fax_number: str | None = None,
    notes: str | None = None,
) -> ContactDetails:
    """
    Apply the non-None edits to a deep copy of the baseline record.

    Returns:
        ContactDetails: The edited copy, which equals the baseline if nothing
            changed.
    """
    modified = baseline.model_copy(deep=True)
    if first_name is not None:
        modified.first_name = first_name
    if middle_name is not None:
        modified.middle_name = middle_name
    if last_name is not None:
        modified.last_name = last_name
    if title is not None:
        modified.title = title
    if company is not None:
        modified.company = company
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
# FUNCTION: unchanged_contact_result
# -----------------------------------------------------------------------------


def unchanged_contact_result(baseline: ContactDetails) -> UpdatedContactResult:
    """
    Represent an untouched record as an update result.

    The API rejects no-op updates, so an edit that changes nothing is answered
    from the baseline instead of being sent.

    Returns:
        UpdatedContactResult: The current record, as an update result.
    """
    return UpdatedContactResult.model_validate(baseline.model_dump(by_alias=True))


# -----------------------------------------------------------------------------
# OPERATION: update_contact
# -----------------------------------------------------------------------------


def update_contact(
    baseline: ContactDetails, modified: ContactDetails
) -> Operation[UpdatedContactResult]:
    """
    Build the UpdateContacts operation for one edited record.

    Returns:
        Operation[UpdatedContactResult]: The update contact operation.
    """
    request = UpdateContacts(
        method_arguments=UpdateContactsArguments(
            updated_contacts=[modified],
            unchanged_contacts=[baseline],
        )
    )

    def parse(data: dict[str, Any]) -> UpdatedContactResult:
        results = UpdateContactsResponse.model_validate(data).content.contacts
        if not results:
            raise Exception("UpdateContacts returned no contact records")
        return results[0]

    return Operation(request=request, api_version=1, parse=parse)
