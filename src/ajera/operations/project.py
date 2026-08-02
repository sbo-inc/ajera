from typing import Any, cast

from ajera.operations.generic import Operation, envelope, flatten, item, items, raw
from ajera.schemas.project import (
    GetProjectTemplates,
    GetProjectTemplatesArguments,
    GetProjectTotals,
    GetProjectTotalsArguments,
    ListProjects,
    ListProjectsArguments,
    ListProjectsResponse,
    ListProjectTemplates,
    ListProjectTemplatesArguments,
    ListProjectTemplatesResponse,
    ListProjectTypes,
    ListProjectTypesArguments,
    ListProjectTypesResponse,
    Project,
    ProjectTemplate,
    ProjectTemplateDetails,
    ProjectTotalsDetails,
    ProjectType,
)
from ajera.schemas.project_summary import ProjectSummary
from ajera.schemas.project_v2 import (
    CreateProjects,
    CreateProjectsArguments,
    CreateProjectsResponse,
    GetProjectsArgumentsV2,
    GetProjectsResponseV2,
    GetProjectsV2,
    InvoiceGroupCreate,
    PhaseCreate,
    ProjectBundle,
    ProjectChange,
    ProjectCreate,
    UpdateProjectsArgumentsV2,
    UpdateProjectsResponseV2,
    UpdateProjectsV2,
)

# -----------------------------------------------------------------------------
# OPERATION: list_projects
# -----------------------------------------------------------------------------


def list_projects(
    *,
    filter_by_company: list[int] | None = None,
    filter_by_status: list[str] | None = None,
    filter_by_name_like: str | None = None,
    filter_by_description_like: str | None = None,
    filter_by_description_equals: str | None = None,
    filter_by_id_like: str | None = None,
    filter_by_project_type: list[int] | None = None,
    filter_by_sync_to_crm: list[bool] | None = None,
    filter_by_earliest_modified_date: str | None = None,
    filter_by_latest_modified_date: str | None = None,
) -> Operation[list[Project]]:
    """
    Build the ListProjects operation.

    ListProjects is identical across API versions; this uses v2.

    Returns:
        Operation[list[Project]]: The list projects operation.
    """
    request = ListProjects()
    request.method_arguments = ListProjectsArguments(
        filter_by_company=filter_by_company,
        filter_by_status=filter_by_status,
        filter_by_name_like=filter_by_name_like,
        filter_by_description_like=filter_by_description_like,
        filter_by_description_equals=filter_by_description_equals,
        filter_by_id_like=filter_by_id_like,
        filter_by_project_type=filter_by_project_type,
        filter_by_sync_to_crm=filter_by_sync_to_crm,
        filter_by_earliest_modified_date=filter_by_earliest_modified_date,
        filter_by_latest_modified_date=filter_by_latest_modified_date,
    )

    return Operation(
        request=request,
        api_version=2,
        parse=flatten("Projects", ListProjectsResponse),
    )


# -----------------------------------------------------------------------------
# OPERATION: get_projects
# -----------------------------------------------------------------------------


def get_projects(project_keys: list[int]) -> Operation[ProjectBundle]:
    """
    Build the v2 GetProjects operation.

    Returns:
        Operation[ProjectBundle]: The get projects operation.
    """
    return Operation(
        request=_get_projects_request(project_keys),
        api_version=2,
        parse=envelope(GetProjectsResponseV2),
    )


# -----------------------------------------------------------------------------
# OPERATION: get_projects_raw
# -----------------------------------------------------------------------------


def get_projects_raw(project_keys: list[int]) -> Operation[dict[str, Any]]:
    """
    Build the v2 GetProjects operation, keeping the envelope unparsed.

    `UpdateProjects` echoes the bundle back verbatim as its baseline, so the
    update path needs the wire form rather than the parsed model.

    Returns:
        Operation[dict[str, Any]]: The get projects operation, unparsed.
    """
    return Operation(
        request=_get_projects_request(project_keys),
        api_version=2,
        parse=raw,
    )


def _get_projects_request(project_keys: list[int]) -> GetProjectsV2:
    """
    Build the shared v2 GetProjects request body.

    Returns:
        GetProjectsV2: The request body.
    """
    request = GetProjectsV2()
    request.method_arguments = GetProjectsArgumentsV2(requested_projects=project_keys)
    return request


# -----------------------------------------------------------------------------
# OPERATION: get_project_totals
# -----------------------------------------------------------------------------


def get_project_totals(project_key: int) -> Operation[ProjectTotalsDetails]:
    """
    Build the GetProjectTotals operation.

    Unlike the other Get* methods, GetProjectTotals accepts a single project
    key, not a list.

    Returns:
        Operation[ProjectTotalsDetails]: The get project totals operation.
    """
    request = GetProjectTotals()
    request.method_arguments = GetProjectTotalsArguments(
        requested_project_totals=project_key
    )

    return Operation(
        request=request,
        api_version=1,
        parse=item("ProjectTotals", ProjectTotalsDetails),
    )


# -----------------------------------------------------------------------------
# FUNCTION: build_project_summary
# -----------------------------------------------------------------------------


def build_project_summary(
    bundle: ProjectBundle, totals: dict[str, float], *, subphases: bool
) -> ProjectSummary:
    """
    Synthesize the consolidated project overview from its two sources.

    Returns:
        ProjectSummary: The consolidated project overview.
    """
    summary = ProjectSummary.build(bundle, totals)
    if not subphases:
        for phase in summary.phases:
            phase.children = []

    return summary


# -----------------------------------------------------------------------------
# OPERATION: list_project_types
# -----------------------------------------------------------------------------


def list_project_types(
    *,
    filter_by_status: list[str] | None = ["Active"],
) -> Operation[list[ProjectType]]:
    """
    Build the ListProjectTypes operation.

    Returns:
        Operation[list[ProjectType]]: The list project types operation.
    """
    request = ListProjectTypes()
    request.method_arguments = ListProjectTypesArguments(
        filter_by_status=filter_by_status,
    )

    return Operation(
        request=request,
        api_version=1,
        parse=flatten("ProjectTypes", ListProjectTypesResponse),
    )


# -----------------------------------------------------------------------------
# OPERATION: list_project_templates
# -----------------------------------------------------------------------------


def list_project_templates(
    *,
    filter_by_company: list[int] | None = None,
    filter_by_status: list[str] | None = None,
    filter_by_name_like: str | None = None,
    filter_by_description_like: str | None = None,
    filter_by_description_equals: str | None = None,
    filter_by_id_like: str | None = None,
    filter_by_project_type: list[int] | None = None,
    filter_by_sync_to_crm: list[bool] | None = None,
    filter_by_earliest_modified_date: str | None = None,
    filter_by_latest_modified_date: str | None = None,
) -> Operation[list[ProjectTemplate]]:
    """
    Build the ListProjectTemplates operation.

    Returns:
        Operation[list[ProjectTemplate]]: The list project templates operation.
    """
    request = ListProjectTemplates()
    request.method_arguments = ListProjectTemplatesArguments(
        filter_by_company=filter_by_company,
        filter_by_status=filter_by_status,
        filter_by_name_like=filter_by_name_like,
        filter_by_description_like=filter_by_description_like,
        filter_by_description_equals=filter_by_description_equals,
        filter_by_id_like=filter_by_id_like,
        filter_by_project_type=filter_by_project_type,
        filter_by_sync_to_crm=filter_by_sync_to_crm,
        filter_by_earliest_modified_date=filter_by_earliest_modified_date,
        filter_by_latest_modified_date=filter_by_latest_modified_date,
    )

    return Operation(
        request=request,
        api_version=1,
        parse=flatten("ProjectTemplates", ListProjectTemplatesResponse),
    )


# -----------------------------------------------------------------------------
# OPERATION: get_project_templates
# -----------------------------------------------------------------------------


def get_project_templates(
    template_keys: list[int],
) -> Operation[list[ProjectTemplateDetails]]:
    """
    Build the GetProjectTemplates operation.

    Returns:
        Operation[list[ProjectTemplateDetails]]: The get templates operation.
    """
    request = GetProjectTemplates()
    request.method_arguments = GetProjectTemplatesArguments(
        requested_projects=template_keys
    )

    return Operation(
        request=request,
        api_version=1,
        parse=items("ProjectTemplates", ProjectTemplateDetails),
    )


# -----------------------------------------------------------------------------
# FUNCTION: project_baseline
# -----------------------------------------------------------------------------


def project_baseline(data: dict[str, Any], project_key: int) -> dict[str, Any]:
    """
    Extract the unparsed bundle that `UpdateProjects` takes as its baseline.

    Returns:
        dict[str, Any]: The `Content` bundle from a v2 GetProjects response.
    """
    bundle: dict[str, Any] = cast(dict, data["Content"])
    if not bundle.get("Projects"):
        raise ValueError(f"No project found with key {project_key}")
    return bundle


# -----------------------------------------------------------------------------
# FUNCTION: parse_project_bundle
# -----------------------------------------------------------------------------


def parse_project_bundle(data: dict[str, Any]) -> ProjectBundle:
    """
    Parse an unparsed v2 GetProjects envelope into its bundle.

    Returns:
        ProjectBundle: The projects and their related records.
    """
    return GetProjectsResponseV2.model_validate(data).content


# -----------------------------------------------------------------------------
# OPERATION: update_project
# -----------------------------------------------------------------------------


def update_project(
    project_key: int,
    baseline: dict[str, Any],
    *,
    description: str | None = None,
    project_id: str | None = None,
    location: str | None = None,
    billing_description: str | None = None,
    notes: str | None = None,
) -> Operation[ProjectBundle] | None:
    """
    Build the v2 UpdateProjects operation, or None if there is nothing to send.

    Unlike the pair updates, `UpdatedProjects` carries only the edited fields
    while `UnchangedProjects` carries the whole baseline bundle.

    Returns:
        Operation[ProjectBundle] | None: The update operation, or None when no
            fields were given.
    """
    if all(
        value is None
        for value in (
            description,
            project_id,
            location,
            billing_description,
            notes,
        )
    ):
        return None

    change = ProjectChange(
        project_key=project_key,
        description=description,
        id=project_id,
        location=location,
        billing_description=billing_description,
        notes=notes,
    )

    request = UpdateProjectsV2(
        method_arguments=UpdateProjectsArgumentsV2(
            updated_projects=[change],
            unchanged_projects=baseline,
        )
    )

    return Operation(
        request=request,
        api_version=2,
        parse=envelope(UpdateProjectsResponseV2),
    )


# -----------------------------------------------------------------------------
# OPERATION: create_project
# -----------------------------------------------------------------------------


def create_project(
    description: str,
    *,
    billing_type: str,
    rate_table_key: int,
    client_key: int,
    invoice_format_key: int,
    company_key: int | None = 1,
    invoice_group_description: str | None = None,
    phase_description: str | None = None,
) -> Operation[ProjectBundle]:
    """
    Build the CreateProjects operation for one project.

    A project cannot be created on its own, so one invoice group and one phase
    are created with it; their required descriptions default to the project's.

    Returns:
        Operation[ProjectBundle]: The create project operation.
    """
    request = CreateProjects(
        method_arguments=CreateProjectsArguments(
            project=ProjectCreate(
                description=description,
                billing_type=billing_type,
                rate_table_key=rate_table_key,
                company_key=company_key,
            ),
            invoice_groups=[
                InvoiceGroupCreate(
                    description=invoice_group_description or description,
                    client_key=client_key,
                    invoice_format_key=invoice_format_key,
                )
            ],
            phases=[PhaseCreate(description=phase_description or description)],
        )
    )

    return Operation(
        request=request,
        api_version=2,
        parse=envelope(CreateProjectsResponse),
    )
