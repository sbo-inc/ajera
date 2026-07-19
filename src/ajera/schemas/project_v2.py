from typing import Any, Literal

from pydantic import Field

from ajera.schemas.generic import (
    GenericBaseModel,
    GenericRequest,
    GenericResponse,
)
from ajera.schemas.project import EmployeeReference

# =============================================================================
# CLASS: ResourceEmployee
# =============================================================================


class ResourceEmployee(GenericBaseModel):
    """
    Employee name attached to a v2 resource (no key is returned).
    """

    first_name: str = Field(
        default="",
        alias="FirstName",
        description="Employee first name.",
    )
    middle_name: str = Field(
        default="",
        alias="MiddleName",
        description="Employee middle name.",
    )
    last_name: str = Field(
        default="",
        alias="LastName",
        description="Employee last name.",
    )


# =============================================================================
# CLASS: ProjectV2
# =============================================================================


class ProjectV2(GenericBaseModel):
    """
    A project record from the v2 GetProjects bundle (flat; no nested phases).
    """

    project_key: int = Field(
        default=0,
        alias="ProjectKey",
        description="Project key.",
    )
    last_modified_date: str | None = Field(
        default=None,
        alias="LastModifiedDate",
        description="Last modified date.",
    )
    id: str = Field(
        default="",
        alias="ID",
        description="Project ID (number).",
    )
    description: str = Field(
        default="",
        alias="Description",
        description="Project description (name).",
    )
    sync_to_crm: bool = Field(
        default=False,
        alias="SyncToCRM",
        description="Sync to CRM flag.",
    )
    create_in_crm: bool = Field(
        default=False,
        alias="CreateInCRM",
        description="Create in CRM flag.",
    )
    crm_final_sync: bool = Field(
        default=False,
        alias="CRMFinalSync",
        description="CRM final sync flag.",
    )
    status: str = Field(
        default="",
        alias="Status",
        description="Status.",
    )
    summarize_billing_group: bool = Field(
        default=False,
        alias="SummarizeBillingGroup",
        description="Summarize billing group flag.",
    )
    billing_description: str = Field(
        default="",
        alias="BillingDescription",
        description="Billing description.",
    )
    company_key: int = Field(
        default=-1,
        alias="CompanyKey",
        description="Company key.",
    )
    company_description: str = Field(
        default="",
        alias="CompanyDescription",
        description="Company description.",
    )
    project_type_key: int | None = Field(
        default=None,
        alias="ProjectTypeKey",
        description="Project type key.",
    )
    project_type_description: str = Field(
        default="",
        alias="ProjectTypeDescription",
        description="Project type description.",
    )
    department_key: int | None = Field(
        default=None,
        alias="DepartmentKey",
        description="Department key.",
    )
    department_description: str = Field(
        default="",
        alias="DepartmentDescription",
        description="Department description.",
    )
    budgeted_overhead_rate: float = Field(
        default=0.0,
        alias="BudgetedOverheadRate",
        description="Budgeted overhead rate.",
    )
    project_manager: EmployeeReference | None = Field(
        default=None,
        alias="ProjectManager",
        description="Project manager.",
    )
    principal_in_charge: EmployeeReference | None = Field(
        default=None,
        alias="PrincipalInCharge",
        description="Principal in charge.",
    )
    marketing_contact: EmployeeReference | None = Field(
        default=None,
        alias="MarketingContact",
        description="Marketing contact.",
    )
    location: str = Field(
        default="",
        alias="Location",
        description="Project location.",
    )
    wage_table_key: int | None = Field(
        default=None,
        alias="WageTableKey",
        description="Wage table key.",
    )
    wage_table_description: str = Field(
        default="",
        alias="WageTableDescription",
        description="Wage table description.",
    )
    is_certified: bool = Field(
        default=False,
        alias="IsCertified",
        description="Certified payroll flag.",
    )
    restrict_time_entry_to_resources_only: bool = Field(
        default=False,
        alias="RestrictTimeEntryToResourcesOnly",
        description="Restrict time entry to resources only.",
    )
    tax_state: str = Field(
        default="",
        alias="TaxState",
        description="Tax state.",
    )
    tax_local_key: int | None = Field(
        default=None,
        alias="TaxLocalKey",
        description="Tax local key.",
    )
    tax_local_description: str = Field(
        default="",
        alias="TaxLocalDescription",
        description="Tax local description.",
    )
    estimated_start_date: str | None = Field(
        default=None,
        alias="EstimatedStartDate",
        description="Estimated start date.",
    )
    estimated_completion_date: str | None = Field(
        default=None,
        alias="EstimatedCompletionDate",
        description="Estimated completion date.",
    )
    actual_start_date: str | None = Field(
        default=None,
        alias="ActualStartDate",
        description="Actual start date.",
    )
    actual_completion_date: str | None = Field(
        default=None,
        alias="ActualCompletionDate",
        description="Actual completion date.",
    )
    apply_sales_tax: bool = Field(
        default=False,
        alias="ApplySalesTax",
        description="Apply sales tax flag.",
    )
    sales_tax_code: str = Field(
        default="",
        alias="SalesTaxCode",
        description="Sales tax code.",
    )
    sales_tax_rate: float = Field(
        default=0.0,
        alias="SalesTaxRate",
        description="Sales tax rate.",
    )
    require_timesheet_notes: bool = Field(
        default=False,
        alias="RequireTimesheetNotes",
        description="Require timesheet notes flag.",
    )
    notes: str = Field(
        default="",
        alias="Notes",
        description="Notes.",
    )
    hours_cost_budget: float = Field(
        default=0.0,
        alias="HoursCostBudget",
        description="Hours cost budget.",
    )
    labor_cost_budget: float = Field(
        default=0.0,
        alias="LaborCostBudget",
        description="Labor cost budget.",
    )
    expense_cost_budget: float = Field(
        default=0.0,
        alias="ExpenseCostBudget",
        description="Expense cost budget.",
    )
    consultant_cost_budget: float = Field(
        default=0.0,
        alias="ConsultantCostBudget",
        description="Consultant cost budget.",
    )
    percent_distribution: float = Field(
        default=0.0,
        alias="PercentDistribution",
        description="Percent distribution.",
    )
    is_final_budget: bool = Field(
        default=False,
        alias="IsFinalBudget",
        description="Is final budget flag.",
    )
    billing_type: str = Field(
        default="",
        alias="BillingType",
        description="Billing type.",
    )
    rate_table_key: int | None = Field(
        default=None,
        alias="RateTableKey",
        description="Rate table key.",
    )
    rate_table_description: str = Field(
        default="",
        alias="RateTableDescription",
        description="Rate table description.",
    )
    total_contract_amount: float = Field(
        default=0.0,
        alias="TotalContractAmount",
        description="Total contract amount.",
    )
    labor_contract_amount: float = Field(
        default=0.0,
        alias="LaborContractAmount",
        description="Labor contract amount.",
    )
    expense_contract_amount: float = Field(
        default=0.0,
        alias="ExpenseContractAmount",
        description="Expense contract amount.",
    )
    consultant_contract_amount: float = Field(
        default=0.0,
        alias="ConsultantContractAmount",
        description="Consultant contract amount.",
    )
    bill_labor_as_te: bool = Field(
        default=False,
        alias="BillLaborAsTE",
        description="Bill labor as time & expense flag.",
    )
    bill_expense_as_te: bool = Field(
        default=False,
        alias="BillExpenseAsTE",
        description="Bill expense as time & expense flag.",
    )
    bill_consultant_as_te: bool = Field(
        default=False,
        alias="BillConsultantAsTE",
        description="Bill consultant as time & expense flag.",
    )
    lock_fee: bool = Field(
        default=False,
        alias="LockFee",
        description="Lock fee flag.",
    )
    construction_cost: float = Field(
        default=0.0,
        alias="ConstructionCost",
        description="Construction cost.",
    )
    percent_of_construction_cost: float = Field(
        default=0.0,
        alias="PercentOfConstructionCost",
        description="Percent of construction cost.",
    )
    labor_entry: bool = Field(
        default=False,
        alias="LaborEntry",
        description="Labor entry allowed flag.",
    )
    expense_consultant_entry: bool = Field(
        default=False,
        alias="ExpenseConsultantEntry",
        description="Expense/consultant entry allowed flag.",
    )


# =============================================================================
# CLASS: InvoiceGroupV2
# =============================================================================


class InvoiceGroupV2(GenericBaseModel):
    """
    An invoice group from the v2 GetProjects bundle (linked by ProjectKey).
    """

    invoice_group_key: int = Field(
        default=0,
        alias="InvoiceGroupKey",
        description="Invoice group key.",
    )
    project_key: int | None = Field(
        default=None,
        alias="ProjectKey",
        description="Owning project key.",
    )
    description: str = Field(
        default="",
        alias="Description",
        description="Invoice group description.",
    )
    client_key: int | None = Field(
        default=None,
        alias="ClientKey",
        description="Client key billed for this invoice group.",
    )
    client_description: str = Field(
        default="",
        alias="ClientDescription",
        description="Client description (name).",
    )
    invoice_format_key: int | None = Field(
        default=None,
        alias="InvoiceFormatKey",
        description="Invoice format key.",
    )
    invoice_format_description: str = Field(
        default="",
        alias="InvoiceFormatDescription",
        description="Invoice format description.",
    )
    email_invoice_template_key: int | None = Field(
        default=None,
        alias="EmailInvoiceTemplateKey",
        description="Email invoice template key.",
    )
    email_invoice_template_description: str = Field(
        default="",
        alias="EmailInvoiceTemplateDescription",
        description="Email invoice template description.",
    )
    email_client_statement_template_key: int | None = Field(
        default=None,
        alias="EmailClientStatementTemplateKey",
        description="Email client statement template key.",
    )
    email_client_statement_template_description: str = Field(
        default="",
        alias="EmailClientStatementTemplateDescription",
        description="Email client statement template description.",
    )
    print_backup: bool = Field(
        default=False,
        alias="PrintBackup",
        description="Print backup flag.",
    )
    email_include_backup: bool = Field(
        default=False,
        alias="EmailIncludeBackup",
        description="Email include backup flag.",
    )
    invoice_header_text: str = Field(
        default="",
        alias="InvoiceHeaderText",
        description="Invoice header text.",
    )
    invoice_footer_text: str = Field(
        default="",
        alias="InvoiceFooterText",
        description="Invoice footer text.",
    )
    invoice_scope: str = Field(
        default="",
        alias="InvoiceScope",
        description="Invoice scope.",
    )
    notes: str = Field(
        default="",
        alias="Notes",
        description="Notes.",
    )


# =============================================================================
# CLASS: PhaseV2
# =============================================================================


class PhaseV2(GenericBaseModel):
    """
    A phase from the v2 GetProjects bundle.

    Linked by `ProjectKey`, `ParentKey` (project or parent phase), and
    `InvoiceGroupKey` rather than by nesting.
    """

    project_key: int | None = Field(
        default=None,
        alias="ProjectKey",
        description="Owning project key.",
    )
    phase_key: int = Field(
        default=0,
        alias="PhaseKey",
        description="Phase key.",
    )
    parent_key: int | None = Field(
        default=None,
        alias="ParentKey",
        description="Parent key (project or parent phase).",
    )
    invoice_group_key: int | None = Field(
        default=None,
        alias="InvoiceGroupKey",
        description="Invoice group key.",
    )
    last_modified_date: str | None = Field(
        default=None,
        alias="LastModifiedDate",
        description="Last modified date.",
    )
    id: str = Field(
        default="",
        alias="ID",
        description="Phase ID.",
    )
    description: str = Field(
        default="",
        alias="Description",
        description="Phase description.",
    )
    sync_to_crm: bool = Field(
        default=False,
        alias="SyncToCRM",
        description="Sync to CRM flag.",
    )
    create_in_crm: bool = Field(
        default=False,
        alias="CreateInCRM",
        description="Create in CRM flag.",
    )
    crm_final_sync: bool = Field(
        default=False,
        alias="CRMFinalSync",
        description="CRM final sync flag.",
    )
    status: str = Field(
        default="",
        alias="Status",
        description="Status.",
    )
    is_billing_group: bool = Field(
        default=False,
        alias="IsBillingGroup",
        description="Whether the phase is a billing group.",
    )
    summarize_billing_group: bool = Field(
        default=False,
        alias="SummarizeBillingGroup",
        description="Summarize billing group flag.",
    )
    billing_description: str = Field(
        default="",
        alias="BillingDescription",
        description="Billing description.",
    )
    consultant_invoice_text: str = Field(
        default="",
        alias="ConsultantInvoiceText",
        description="Consultant invoice text.",
    )
    expense_invoice_text: str = Field(
        default="",
        alias="ExpenseInvoiceText",
        description="Expense invoice text.",
    )
    labor_invoice_text: str = Field(
        default="",
        alias="LaborInvoiceText",
        description="Labor invoice text.",
    )
    phase_invoice_text: str = Field(
        default="",
        alias="PhaseInvoiceText",
        description="Phase invoice text.",
    )
    project_type_key: int | None = Field(
        default=None,
        alias="ProjectTypeKey",
        description="Project type key.",
    )
    project_type_description: str = Field(
        default="",
        alias="ProjectTypeDescription",
        description="Project type description.",
    )
    department_key: int | None = Field(
        default=None,
        alias="DepartmentKey",
        description="Department key.",
    )
    department_description: str = Field(
        default="",
        alias="DepartmentDescription",
        description="Department description.",
    )
    budgeted_overhead_rate: float = Field(
        default=0.0,
        alias="BudgetedOverheadRate",
        description="Budgeted overhead rate.",
    )
    project_manager: EmployeeReference | None = Field(
        default=None,
        alias="ProjectManager",
        description="Project manager.",
    )
    principal_in_charge: EmployeeReference | None = Field(
        default=None,
        alias="PrincipalInCharge",
        description="Principal in charge.",
    )
    marketing_contact: EmployeeReference | None = Field(
        default=None,
        alias="MarketingContact",
        description="Marketing contact.",
    )
    wage_table_key: int | None = Field(
        default=None,
        alias="WageTableKey",
        description="Wage table key.",
    )
    wage_table_description: str = Field(
        default="",
        alias="WageTableDescription",
        description="Wage table description.",
    )
    is_certified: bool = Field(
        default=False,
        alias="IsCertified",
        description="Certified payroll flag.",
    )
    restrict_time_entry_to_resources_only: bool = Field(
        default=False,
        alias="RestrictTimeEntryToResourcesOnly",
        description="Restrict time entry to resources only.",
    )
    tax_state: str = Field(
        default="",
        alias="TaxState",
        description="Tax state.",
    )
    tax_local_key: int | None = Field(
        default=None,
        alias="TaxLocalKey",
        description="Tax local key.",
    )
    tax_local_description: str = Field(
        default="",
        alias="TaxLocalDescription",
        description="Tax local description.",
    )
    estimated_start_date: str | None = Field(
        default=None,
        alias="EstimatedStartDate",
        description="Estimated start date.",
    )
    estimated_completion_date: str | None = Field(
        default=None,
        alias="EstimatedCompletionDate",
        description="Estimated completion date.",
    )
    actual_start_date: str | None = Field(
        default=None,
        alias="ActualStartDate",
        description="Actual start date.",
    )
    actual_completion_date: str | None = Field(
        default=None,
        alias="ActualCompletionDate",
        description="Actual completion date.",
    )
    apply_sales_tax: bool = Field(
        default=False,
        alias="ApplySalesTax",
        description="Apply sales tax flag.",
    )
    sales_tax_code: str = Field(
        default="",
        alias="SalesTaxCode",
        description="Sales tax code.",
    )
    sales_tax_rate: float = Field(
        default=0.0,
        alias="SalesTaxRate",
        description="Sales tax rate.",
    )
    require_timesheet_notes: bool = Field(
        default=False,
        alias="RequireTimesheetNotes",
        description="Require timesheet notes flag.",
    )
    notes: str = Field(
        default="",
        alias="Notes",
        description="Notes.",
    )
    hours_cost_budget: float = Field(
        default=0.0,
        alias="HoursCostBudget",
        description="Hours cost budget.",
    )
    labor_cost_budget: float = Field(
        default=0.0,
        alias="LaborCostBudget",
        description="Labor cost budget.",
    )
    expense_cost_budget: float = Field(
        default=0.0,
        alias="ExpenseCostBudget",
        description="Expense cost budget.",
    )
    consultant_cost_budget: float = Field(
        default=0.0,
        alias="ConsultantCostBudget",
        description="Consultant cost budget.",
    )
    percent_distribution: float = Field(
        default=0.0,
        alias="PercentDistribution",
        description="Percent distribution.",
    )
    is_final_budget: bool = Field(
        default=False,
        alias="IsFinalBudget",
        description="Is final budget flag.",
    )
    billing_type: str = Field(
        default="",
        alias="BillingType",
        description="Billing type.",
    )
    rate_table_key: int | None = Field(
        default=None,
        alias="RateTableKey",
        description="Rate table key.",
    )
    rate_table_description: str = Field(
        default="",
        alias="RateTableDescription",
        description="Rate table description.",
    )
    total_contract_amount: float = Field(
        default=0.0,
        alias="TotalContractAmount",
        description="Total contract amount.",
    )
    labor_contract_amount: float = Field(
        default=0.0,
        alias="LaborContractAmount",
        description="Labor contract amount.",
    )
    expense_contract_amount: float = Field(
        default=0.0,
        alias="ExpenseContractAmount",
        description="Expense contract amount.",
    )
    consultant_contract_amount: float = Field(
        default=0.0,
        alias="ConsultantContractAmount",
        description="Consultant contract amount.",
    )
    bill_labor_as_te: bool = Field(
        default=False,
        alias="BillLaborAsTE",
        description="Bill labor as time & expense flag.",
    )
    bill_expense_as_te: bool = Field(
        default=False,
        alias="BillExpenseAsTE",
        description="Bill expense as time & expense flag.",
    )
    bill_consultant_as_te: bool = Field(
        default=False,
        alias="BillConsultantAsTE",
        description="Bill consultant as time & expense flag.",
    )
    lock_fee: bool = Field(
        default=False,
        alias="LockFee",
        description="Lock fee flag.",
    )
    labor_entry: bool = Field(
        default=False,
        alias="LaborEntry",
        description="Labor entry allowed flag.",
    )
    expense_consultant_entry: bool = Field(
        default=False,
        alias="ExpenseConsultantEntry",
        description="Expense/consultant entry allowed flag.",
    )


# =============================================================================
# CLASS: ResourceV2
# =============================================================================


class ResourceV2(GenericBaseModel):
    """
    A budgeted resource from the v2 GetProjects bundle (linked by ParentKey).
    """

    resource_key: int = Field(
        default=0,
        alias="ResourceKey",
        description="Resource key.",
    )
    parent_key: int | None = Field(
        default=None,
        alias="ParentKey",
        description="Owning phase key.",
    )
    status: str = Field(
        default="",
        alias="Status",
        description="Resource status.",
    )
    priority: str = Field(
        default="",
        alias="Priority",
        description="Resource priority.",
    )
    description: str = Field(
        default="",
        alias="Description",
        description="Resource description.",
    )
    notes: str = Field(
        default="",
        alias="Notes",
        description="Resource notes.",
    )
    is_task: bool = Field(
        default=False,
        alias="IsTask",
        description="Whether the resource is a task.",
    )
    activity_type: str = Field(
        default="",
        alias="ActivityType",
        description="Activity type (e.g. Labor, Consultant, Expense).",
    )
    employee: ResourceEmployee | None = Field(
        default=None,
        alias="Employee",
        description="Employee assigned to the resource.",
    )
    reference: str = Field(
        default="",
        alias="Reference",
        description="Free-form reference.",
    )
    percent_distribution: float = Field(
        default=0.0,
        alias="PercentDistribution",
        description="Percent distribution.",
    )
    units: float = Field(
        default=0.0,
        alias="Units",
        description="Budgeted units (e.g. hours).",
    )
    cost_rate: float = Field(
        default=0.0,
        alias="CostRate",
        description="Cost rate.",
    )
    cost_amount: float = Field(
        default=0.0,
        alias="CostAmount",
        description="Cost amount.",
    )
    fee_rate: float = Field(
        default=0.0,
        alias="FeeRate",
        description="Fee (bill) rate.",
    )
    fee_amount: float = Field(
        default=0.0,
        alias="FeeAmount",
        description="Fee (bill) amount.",
    )
    markup_rate: float = Field(
        default=0.0,
        alias="MarkupRate",
        description="Markup rate.",
    )
    begin_balance_cost_amount: float = Field(
        default=0.0,
        alias="BeginBalanceCostAmount",
        description="Beginning balance cost amount.",
    )
    begin_balance_fee_amount: float = Field(
        default=0.0,
        alias="BeginBalanceFeeAmount",
        description="Beginning balance fee amount.",
    )


# =============================================================================
# CLASS: ProjectBundle
# =============================================================================


class ProjectBundle(GenericBaseModel):
    """
    The flat v2 project payload.

    Returned by GetProjects / UpdateProjects / CreateProjects as four parallel
    arrays linked by foreign keys.
    """

    projects: list[ProjectV2] = Field(
        default=[],
        alias="Projects",
        description="Project records.",
    )
    invoice_groups: list[InvoiceGroupV2] = Field(
        default=[],
        alias="InvoiceGroups",
        description="Invoice group records.",
    )
    phases: list[PhaseV2] = Field(
        default=[],
        alias="Phases",
        description="Phase records.",
    )
    resources: list[ResourceV2] = Field(
        default=[],
        alias="Resources",
        description="Resource records.",
    )


# =============================================================================
# CLASS: GetProjectsArgumentsV2
# =============================================================================


class GetProjectsArgumentsV2(GenericBaseModel):
    """
    Arguments for v2 GetProjects
    """

    requested_projects: list[int] = Field(
        alias="RequestedProjects",
        description="List of project keys to retrieve.",
    )


# =============================================================================
# CLASS: GetProjectsV2
# =============================================================================


class GetProjectsV2(GenericRequest[GetProjectsArgumentsV2]):
    """
    v2 Get Projects request body
    """

    method: Literal["GetProjects"] = Field(
        default="GetProjects",
        alias="Method",
        description="API method name to invoke.",
        frozen=True,
    )


# =============================================================================
# CLASS: GetProjectsResponseV2
# =============================================================================


class GetProjectsResponseV2(GenericResponse[ProjectBundle]):
    """
    Response schema for v2 GetProjects
    """


# =============================================================================
# CLASS: ProjectChange
# =============================================================================


class ProjectChange(GenericBaseModel):
    """
    A project-level delta for v2 UpdateProjects.

    Carries the project key plus only the simple scalar fields being changed;
    unset (None) fields are excluded from the request.
    """

    project_key: int = Field(
        alias="ProjectKey",
        description="Key of the project being updated.",
    )
    description: str | None = Field(
        default=None,
        alias="Description",
        description="New project description (name).",
    )
    id: str | None = Field(
        default=None,
        alias="ID",
        description="New project ID (number).",
    )
    location: str | None = Field(
        default=None,
        alias="Location",
        description="New project location.",
    )
    billing_description: str | None = Field(
        default=None,
        alias="BillingDescription",
        description="New billing description.",
    )
    notes: str | None = Field(
        default=None,
        alias="Notes",
        description="New notes.",
    )


# =============================================================================
# CLASS: UpdateProjectsArgumentsV2
# =============================================================================


class UpdateProjectsArgumentsV2(GenericBaseModel):
    """
    Arguments for v2 UpdateProjects.
    """

    updated_projects: list[ProjectChange] = Field(
        default=[],
        alias="UpdatedProjects",
        description="Array of changed objects (key plus changed fields).",
    )
    unchanged_projects: dict[str, Any] = Field(
        default={},
        alias="UnchangedProjects",
        description="The complete GetProjects bundle, unchanged.",
    )


# =============================================================================
# CLASS: UpdateProjectsV2
# =============================================================================


class UpdateProjectsV2(GenericRequest[UpdateProjectsArgumentsV2]):
    """
    v2 Update Projects request body
    """

    method: Literal["UpdateProjects"] = Field(
        default="UpdateProjects",
        alias="Method",
        description="API method name to invoke.",
        frozen=True,
    )


# =============================================================================
# CLASS: UpdateProjectsResponseV2
# =============================================================================


class UpdateProjectsResponseV2(GenericResponse[ProjectBundle]):
    """
    Response schema for v2 UpdateProjects (returns the updated bundle).
    """


# =============================================================================
# CLASS: ProjectCreate
# =============================================================================


class ProjectCreate(GenericBaseModel):
    """
    The new project's fields for v2 CreateProjects (CreateType "Project").
    """

    description: str = Field(
        alias="Description",
        description="Project description (name); required, max 80 chars.",
    )
    billing_type: str = Field(
        alias="BillingType",
        description="Billing type (e.g. TimeAndExpense, FixedFee); required.",
    )
    rate_table_key: int = Field(
        alias="RateTableKey",
        description="Rate table key; required.",
    )
    company_key: int | None = Field(
        default=None,
        alias="CompanyKey",
        description="Company key; required when multi-company is enabled.",
    )


# =============================================================================
# CLASS: InvoiceGroupCreate
# =============================================================================


class InvoiceGroupCreate(GenericBaseModel):
    """
    A new invoice group for v2 CreateProjects.
    """

    description: str = Field(
        default="",
        alias="Description",
        description="Invoice group description.",
    )
    client_key: int = Field(
        alias="ClientKey",
        description="Client key billed for this invoice group; required.",
    )
    invoice_format_key: int = Field(
        alias="InvoiceFormatKey",
        description="Invoice format key; required.",
    )


# =============================================================================
# CLASS: PhaseCreate
# =============================================================================


class PhaseCreate(GenericBaseModel):
    """
    A new phase for v2 CreateProjects.
    """

    description: str = Field(
        alias="Description",
        description="Phase description; required, max 80 chars.",
    )


# =============================================================================
# CLASS: CreateProjectsArguments
# =============================================================================


class CreateProjectsArguments(GenericBaseModel):
    """
    Arguments for v2 CreateProjects with CreateType "Project".

    A project cannot be created alone: at least one invoice group and one
    phase must accompany it.
    """

    create_type: Literal["Project"] = Field(
        default="Project",
        alias="CreateType",
        description="The type of object being created.",
        frozen=True,
    )
    project: ProjectCreate = Field(
        alias="Project",
        description="The new project's fields.",
    )
    invoice_groups: list[InvoiceGroupCreate] = Field(
        default=[],
        alias="InvoiceGroups",
        description="Invoice groups to create with the project.",
    )
    phases: list[PhaseCreate] = Field(
        default=[],
        alias="Phases",
        description="Phases to create with the project.",
    )


# =============================================================================
# CLASS: CreateProjects
# =============================================================================


class CreateProjects(GenericRequest[CreateProjectsArguments]):
    """
    v2 Create Projects request body
    """

    method: Literal["CreateProjects"] = Field(
        default="CreateProjects",
        alias="Method",
        description="API method name to invoke.",
        frozen=True,
    )


# =============================================================================
# CLASS: CreateProjectsResponse
# =============================================================================


class CreateProjectsResponse(GenericResponse[ProjectBundle]):
    """
    Response schema for v2 CreateProjects (returns the created bundle).
    """
