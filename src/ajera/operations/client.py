from typing import Any

from ajera.operations.generic import Operation, flatten, items
from ajera.schemas.client import (
    Client,
    ClientDetails,
    ClientType,
    GetClients,
    GetClientsArguments,
    ListClients,
    ListClientsArguments,
    ListClientsResponse,
    ListClientTypes,
    ListClientTypesArguments,
    ListClientTypesResponse,
    UpdateClients,
    UpdateClientsArguments,
    UpdateClientsResponse,
    UpdatedClientResult,
)

# -----------------------------------------------------------------------------
# OPERATION: list_clients
# -----------------------------------------------------------------------------


def list_clients(
    *,
    filter_by_company: list[int] | None = None,
    filter_by_status: list[str] | None = ["Active"],
    filter_by_name_like: str | None = None,
    filter_by_name_equals: str | None = None,
    filter_by_client_type: list[int] | None = None,
    filter_by_earliest_modified_date: str | None = None,
    filter_by_latest_modified_date: str | None = None,
) -> Operation[list[Client]]:
    """
    Build the ListClients operation.

    Returns:
        Operation[list[Client]]: The list clients operation.
    """
    request = ListClients()
    request.method_arguments = ListClientsArguments(
        filter_by_company=filter_by_company,
        filter_by_status=filter_by_status,
        filter_by_name_like=filter_by_name_like,
        filter_by_name_equals=filter_by_name_equals,
        filter_by_client_type=filter_by_client_type,
        filter_by_earliest_modified_date=filter_by_earliest_modified_date,
        filter_by_latest_modified_date=filter_by_latest_modified_date,
    )

    return Operation(
        request=request,
        api_version=1,
        parse=flatten("Clients", ListClientsResponse),
    )


# -----------------------------------------------------------------------------
# OPERATION: get_clients
# -----------------------------------------------------------------------------


def get_clients(client_keys: list[int]) -> Operation[list[ClientDetails]]:
    """
    Build the GetClients operation.

    Returns:
        Operation[list[ClientDetails]]: The get clients operation.
    """
    request = GetClients()
    request.method_arguments = GetClientsArguments(requested_clients=client_keys)

    return Operation(
        request=request,
        api_version=1,
        parse=items("Clients", ClientDetails),
    )


# -----------------------------------------------------------------------------
# OPERATION: list_client_types
# -----------------------------------------------------------------------------


def list_client_types(
    *,
    filter_by_status: list[str] | None = ["Active"],
) -> Operation[list[ClientType]]:
    """
    Build the ListClientTypes operation.

    Returns:
        Operation[list[ClientType]]: The list client types operation.
    """
    request = ListClientTypes()
    request.method_arguments = ListClientTypesArguments(
        filter_by_status=filter_by_status,
    )

    return Operation(
        request=request,
        api_version=1,
        parse=flatten("ClientTypes", ListClientTypesResponse),
    )


# -----------------------------------------------------------------------------
# FUNCTION: apply_client_edits
# -----------------------------------------------------------------------------


def apply_client_edits(
    baseline: ClientDetails,
    *,
    description: str | None = None,
    account_id: str | None = None,
    email: str | None = None,
    website: str | None = None,
    primary_phone_number: str | None = None,
    secondary_phone_number: str | None = None,
    tertiary_phone_number: str | None = None,
    fax_number: str | None = None,
    notes: str | None = None,
) -> ClientDetails:
    """
    Apply the non-None edits to a deep copy of the baseline record.

    Returns:
        ClientDetails: The edited copy, which equals the baseline if nothing
            changed.
    """
    modified = baseline.model_copy(deep=True)
    if description is not None:
        modified.description = description
    if account_id is not None:
        modified.account_id = account_id
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
# FUNCTION: unchanged_client_result
# -----------------------------------------------------------------------------


def unchanged_client_result(baseline: ClientDetails) -> UpdatedClientResult:
    """
    Represent an untouched record as an update result.

    The API rejects no-op updates, so an edit that changes nothing is answered
    from the baseline instead of being sent.

    Returns:
        UpdatedClientResult: The current record, as an update result.
    """
    return UpdatedClientResult.model_validate(baseline.model_dump(by_alias=True))


# -----------------------------------------------------------------------------
# OPERATION: update_client
# -----------------------------------------------------------------------------


def update_client(
    baseline: ClientDetails, modified: ClientDetails
) -> Operation[UpdatedClientResult]:
    """
    Build the UpdateClients operation for one edited record.

    Returns:
        Operation[UpdatedClientResult]: The update client operation.
    """
    request = UpdateClients(
        method_arguments=UpdateClientsArguments(
            updated_clients=[modified],
            unchanged_clients=[baseline],
        )
    )

    def parse(data: dict[str, Any]) -> UpdatedClientResult:
        results = UpdateClientsResponse.model_validate(data).content.clients
        if not results:
            raise Exception("UpdateClients returned no client records")
        return results[0]

    return Operation(request=request, api_version=1, parse=parse)
