import click

from ajera.cli.context import ClientContext
from ajera.cli.group import CommonClickGroup
from ajera.cli.output import render


@click.group(name="projects", cls=CommonClickGroup)
def group() -> None:
    """
    List and inspect projects.
    """


@group.command(name="list")
@click.option(
    "--company",
    "filter_by_company",
    type=int,
    multiple=True,
    help="Filter by company ID (repeatable).",
)
@click.option(
    "--status",
    "filter_by_status",
    type=str,
    multiple=True,
    help="Filter by status value (repeatable).",
)
@click.option(
    "--name-like",
    "filter_by_name_like",
    type=str,
    default=None,
    help="Filter where the project name contains this substring.",
)
@click.option(
    "--description-like",
    "filter_by_description_like",
    type=str,
    default=None,
    help="Filter where the description contains this substring.",
)
@click.option(
    "--description-equals",
    "filter_by_description_equals",
    type=str,
    default=None,
    help="Filter where the description equals this value.",
)
@click.option(
    "--id-like",
    "filter_by_id_like",
    type=str,
    default=None,
    help="Filter where the project ID contains this substring.",
)
@click.option(
    "--project-type",
    "filter_by_project_type",
    type=int,
    multiple=True,
    help="Filter by project type ID (repeatable).",
)
@click.option(
    "--sync-to-crm/--no-sync-to-crm",
    "sync_to_crm",
    default=None,
    help="Filter by the sync-to-CRM flag.",
)
@click.option(
    "--modified-after",
    "filter_by_earliest_modified_date",
    type=str,
    default=None,
    help="Earliest modified date (YYYY-MM-DD or ISO 8601).",
)
@click.option(
    "--modified-before",
    "filter_by_latest_modified_date",
    type=str,
    default=None,
    help="Latest modified date (YYYY-MM-DD or ISO 8601).",
)
@click.pass_obj
def list_(
    ctx: ClientContext,
    filter_by_company: tuple[int, ...],
    filter_by_status: tuple[str, ...],
    filter_by_name_like: str | None,
    filter_by_description_like: str | None,
    filter_by_description_equals: str | None,
    filter_by_id_like: str | None,
    filter_by_project_type: tuple[int, ...],
    sync_to_crm: bool | None,
    filter_by_earliest_modified_date: str | None,
    filter_by_latest_modified_date: str | None,
) -> None:
    """
    List projects, optionally filtered.
    """
    render(
        ctx.client.list_projects(
            filter_by_company=list(filter_by_company) or None,
            filter_by_status=list(filter_by_status) or None,
            filter_by_name_like=filter_by_name_like,
            filter_by_description_like=filter_by_description_like,
            filter_by_description_equals=filter_by_description_equals,
            filter_by_id_like=filter_by_id_like,
            filter_by_project_type=list(filter_by_project_type) or None,
            filter_by_sync_to_crm=None if sync_to_crm is None else [sync_to_crm],
            filter_by_earliest_modified_date=filter_by_earliest_modified_date,
            filter_by_latest_modified_date=filter_by_latest_modified_date,
        )
    )


@group.command(name="get")
@click.argument("project_ids", nargs=-1, required=True, type=int)
@click.pass_obj
def get(ctx: ClientContext, project_ids: tuple[int, ...]) -> None:
    """
    Get one or more projects by ID.

    Returns the v2 flat bundle: projects, invoice groups, phases, and
    resources (resources are included inline).
    """
    render(ctx.client.get_projects(list(project_ids)))


@group.command(name="totals")
@click.argument("project_id", type=int)
@click.pass_obj
def totals(ctx: ClientContext, project_id: int) -> None:
    """
    Get a project's financial totals.

    Returns the project's details enriched with project-level financial
    totals.
    """
    render(ctx.client.get_project_totals(project_id))


@group.command(name="types")
@click.option(
    "--status",
    "filter_by_status",
    type=str,
    multiple=True,
    help="Filter by status value, e.g. Active or Inactive (repeatable).",
)
@click.pass_obj
def types(ctx: ClientContext, filter_by_status: tuple[str, ...]) -> None:
    """
    List project types, optionally filtered by status.
    """
    render(
        ctx.client.list_project_types(filter_by_status=list(filter_by_status) or None)
    )


@group.group(name="templates")
def templates() -> None:
    """
    List and inspect project templates.
    """


@templates.command(name="list")
@click.option(
    "--company",
    "filter_by_company",
    type=int,
    multiple=True,
    help="Filter by company ID (repeatable).",
)
@click.option(
    "--status",
    "filter_by_status",
    type=str,
    multiple=True,
    help="Filter by status value (repeatable).",
)
@click.option(
    "--name-like",
    "filter_by_name_like",
    type=str,
    default=None,
    help="Filter where the template name contains this substring.",
)
@click.option(
    "--project-type",
    "filter_by_project_type",
    type=int,
    multiple=True,
    help="Filter by project type ID (repeatable).",
)
@click.pass_obj
def templates_list(
    ctx: ClientContext,
    filter_by_company: tuple[int, ...],
    filter_by_status: tuple[str, ...],
    filter_by_name_like: str | None,
    filter_by_project_type: tuple[int, ...],
) -> None:
    """
    List project templates, optionally filtered.
    """
    render(
        ctx.client.list_project_templates(
            filter_by_company=list(filter_by_company) or None,
            filter_by_status=list(filter_by_status) or None,
            filter_by_name_like=filter_by_name_like,
            filter_by_project_type=list(filter_by_project_type) or None,
        )
    )


@templates.command(name="get")
@click.argument("template_ids", nargs=-1, required=True, type=int)
@click.pass_obj
def templates_get(ctx: ClientContext, template_ids: tuple[int, ...]) -> None:
    """
    Get one or more project templates by ID.
    """
    render(ctx.client.get_project_templates(list(template_ids)))


@group.command(name="update")
@click.argument("project_key", type=int)
@click.option("--description", default=None, help="New project description (name).")
@click.option("--project-id", default=None, help="New project ID (number).")
@click.option("--location", default=None, help="New project location.")
@click.option("--billing-description", default=None, help="New billing description.")
@click.option("--notes", default=None, help="New notes.")
@click.pass_obj
def update(
    ctx: ClientContext,
    project_key: int,
    description: str | None,
    project_id: str | None,
    location: str | None,
    billing_description: str | None,
    notes: str | None,
) -> None:
    """
    Update simple fields on one project.

    Only the options you pass are changed; everything else is left as-is.
    """
    render(
        ctx.client.update_project(
            project_key,
            description=description,
            project_id=project_id,
            location=location,
            billing_description=billing_description,
            notes=notes,
        )
    )


@group.command(name="chargeable-phases")
@click.argument("project_key", type=int)
@click.pass_obj
def chargeable_phases(ctx: ClientContext, project_key: int) -> None:
    """
    List the chargeable phases of a project.
    """
    render(ctx.client.list_chargeable_phases(project_key))


@group.command(name="create")
@click.argument("description", type=str)
@click.option(
    "--billing-type", required=True, help="Billing type, e.g. TimeAndExpense."
)
@click.option("--rate-table-key", required=True, type=int, help="Rate table key.")
@click.option(
    "--client-key",
    required=True,
    type=int,
    help="Client key for the project's invoice group.",
)
@click.option(
    "--invoice-format-key",
    required=True,
    type=int,
    help="Invoice format key for the project's invoice group.",
)
@click.option("--company-key", type=int, default=1, help="Company key (default 1).")
@click.option(
    "--invoice-group-description",
    default=None,
    help="Description for the created invoice group (defaults to the project name).",
)
@click.option(
    "--phase-description",
    default=None,
    help="Description for the created phase (defaults to the project description).",
)
@click.pass_obj
def create(
    ctx: ClientContext,
    description: str,
    billing_type: str,
    rate_table_key: int,
    client_key: int,
    invoice_format_key: int,
    company_key: int,
    invoice_group_description: str | None,
    phase_description: str | None,
) -> None:
    """
    Create a new project.

    A project is created together with one invoice group and one phase.
    """
    render(
        ctx.client.create_project(
            description,
            billing_type=billing_type,
            rate_table_key=rate_table_key,
            client_key=client_key,
            invoice_format_key=invoice_format_key,
            company_key=company_key,
            invoice_group_description=invoice_group_description,
            phase_description=phase_description,
        )
    )
