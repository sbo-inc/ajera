from typing import Any, Literal, cast, override

from pydantic import Field, model_validator

from ajera.schemas.generic import (
    GenericBaseModel,
    GenericRequest,
    GenericResponse,
)

# =============================================================================
# CLASS: EmployeeReference
# =============================================================================


class EmployeeReference(GenericBaseModel):
    """
    Lightweight employee reference.

    Used for project manager, principal in charge, and marketing contact
    fields.
    """

    employee_key: int | None = Field(
        default=None,
        alias="EmployeeKey",
        description="Employee key.",
    )
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
# CLASS: ClientReference
# =============================================================================


class ClientReference(GenericBaseModel):
    """
    Lightweight client reference attached to an invoice group.
    """

    client_key: int | None = Field(
        default=None,
        alias="ClientKey",
        description="Client key.",
    )
    description: str = Field(
        default="",
        alias="Description",
        description="Client description (name).",
    )


# =============================================================================
# CLASS: ProjectContact
# =============================================================================


class ProjectContact(GenericBaseModel):
    contact_key: int | None = Field(
        default=None,
        alias="ContactKey",
        description="Unique contact key.",
    )
    order: int | None = Field(
        default=None,
        alias="Order",
        description="Ordering value for the contact.",
    )
    text: str | None = Field(
        default=None,
        alias="Text",
        description="Free-form text for the contact.",
    )
    first_name: str | None = Field(
        default=None,
        alias="FirstName",
        description="Contact first name.",
    )
    middle_name: str | None = Field(
        default=None,
        alias="MiddleName",
        description="Contact middle name.",
    )
    last_name: str | None = Field(
        default=None,
        alias="LastName",
        description="Contact last name.",
    )
    title: str | None = Field(
        default=None,
        alias="Title",
        description="Contact title.",
    )
    company: str | None = Field(
        default=None,
        alias="Company",
        description="Contact company.",
    )


# =============================================================================
# CLASS: ProjectResource
# =============================================================================


class ProjectResource(GenericBaseModel):
    """
    A budgeted resource on a phase, returned by GetProjectsWithResources.
    """

    resource_key: int | None = Field(
        default=None,
        alias="ResourceKey",
        description="Unique resource key.",
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
    employee_key: int | None = Field(
        default=None,
        alias="EmployeeKey",
        description="Employee key for the resource.",
    )
    employee_type_key: int | None = Field(
        default=None,
        alias="EmployeeTypeKey",
        description="Employee type key for the resource.",
    )
    activity_key: int | None = Field(
        default=None,
        alias="ActivityKey",
        description="Activity key for the resource.",
    )
    vendor_key: int | None = Field(
        default=None,
        alias="VendorKey",
        description="Vendor key for the resource.",
    )
    vendor_type_key: int | None = Field(
        default=None,
        alias="VendorTypeKey",
        description="Vendor type key for the resource.",
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


# =============================================================================
# CLASS: ProjectPhase
# =============================================================================


class ProjectPhase(GenericBaseModel):
    """
    A phase within a project.

    Phases may nest (a phase can contain sub-phases) and, for
    GetProjectsWithResources, carry a list of budgeted resources.
    """

    phase_key: int | None = Field(
        default=None,
        alias="PhaseKey",
        description="Unique phase key.",
    )
    last_modified_date: str | None = Field(
        default="",
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
    billing_description: str = Field(
        default="",
        alias="BillingDescription",
        description="Billing description.",
    )
    phase_invoice_text: str = Field(
        default="",
        alias="PhaseInvoiceText",
        description="Phase invoice text.",
    )
    labor_invoice_text: str = Field(
        default="",
        alias="LaborInvoiceText",
        description="Labor invoice text.",
    )
    expense_invoice_text: str = Field(
        default="",
        alias="ExpenseInvoiceText",
        description="Expense invoice text.",
    )
    consultant_invoice_text: str = Field(
        default="",
        alias="ConsultantInvoiceText",
        description="Consultant invoice text.",
    )
    contacts: list[ProjectContact] = Field(
        default=[],
        alias="Contacts",
        description="List of contacts.",
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
    resources: list[ProjectResource] | None = Field(
        default=None,
        alias="Resources",
        description="Budgeted resources (populated by GetProjectsWithResources).",
    )
    phases: list["ProjectPhase"] = Field(
        default=[],
        alias="Phases",
        description="Nested sub-phases.",
    )


# =============================================================================
# CLASS: InvoiceGroup
# =============================================================================


class InvoiceGroup(GenericBaseModel):
    """
    An invoice group within a project, wrapping a set of phases.
    """

    invoice_group_key: int | None = Field(
        default=None,
        alias="InvoiceGroupKey",
        description="Unique invoice group key.",
    )
    description: str = Field(
        default="",
        alias="Description",
        description="Invoice group description.",
    )
    client: ClientReference | None = Field(
        default=None,
        alias="Client",
        description="Client billed for this invoice group.",
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
    phases: list[ProjectPhase] = Field(
        default=[],
        alias="Phases",
        description="Phases in the invoice group.",
    )


# =============================================================================
# CLASS: Project
# =============================================================================


class Project(GenericBaseModel):
    """
    Project schema for ListProjects response
    """

    project_key: int = Field(
        default=0,
        alias="ProjectKey",
        description="Unique project key.",
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


# =============================================================================
# CLASS: ProjectDetails
# =============================================================================


class ProjectDetails(GenericBaseModel):
    """
    Detailed Project schema.

    Used for GetProjects and GetProjectsWithResources responses.
    """

    project_key: int = Field(
        alias="ProjectKey",
        description="Project key.",
    )
    last_modified_date: str | None = Field(
        default="",
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
    contacts: list[ProjectContact] = Field(
        default=[],
        alias="Contacts",
        description="List of contacts.",
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
    resources: list[ProjectResource] | None = Field(
        default=None,
        alias="Resources",
        description="Project-level resources (typically empty).",
    )
    invoice_groups: list[InvoiceGroup] = Field(
        default=[],
        alias="InvoiceGroups",
        description="Invoice groups (each wrapping phases).",
    )


# =============================================================================
# CLASS: ProjectTemplateDetails
# =============================================================================


class ProjectTemplateDetails(ProjectDetails):
    """
    Detailed project template schema for GetProjectTemplates response.

    Templates mirror projects but are keyed by `ProjectTemplateKey` and carry
    no `ProjectKey`.
    """

    project_key: int | None = Field(
        default=None,
        alias="ProjectKey",
        description="Project key (absent for templates).",
    )
    project_template_key: int = Field(
        alias="ProjectTemplateKey",
        description="Project template key.",
    )


# =============================================================================
# CLASS: ProjectTotalsDetails
# =============================================================================


class ProjectTotalsDetails(ProjectDetails):
    """
    Detailed project schema for GetProjectTotals response.

    Identical to ProjectDetails plus the financial totals the method adds at
    the project level. Ajera returns each total as an extra top-level property
    using a human-readable label (e.g. "Billed", "Cost Labor", "Receivable
    Balance"); these are collected into the `totals` map. Per-phase totals are
    not surfaced.
    """

    totals: dict[str, float] = Field(
        default={},
        alias="Totals",
        description="Project-level financial totals keyed by Ajera's labels.",
    )

    @model_validator(mode="before")
    @classmethod
    def _collect_totals(cls, data: object) -> object:
        """
        Collect extra numeric totals into `Totals`.

        Every numeric top-level property that is not a standard project field
        (nor a CF_ custom field) is moved into the `Totals` map.
        """
        if not isinstance(data, dict):
            return data
        source = cast("dict[str, object]", data)
        standard = {
            info.alias or name for name, info in ProjectDetails.model_fields.items()
        }
        totals: dict[str, float] = {}
        rest: dict[str, object] = {}
        for key, value in source.items():
            if (
                key not in standard
                and not key.startswith("CF_")
                and isinstance(value, (int, float))
                and not isinstance(value, bool)
            ):
                totals[key] = float(value)
            else:
                rest[key] = value
        rest["Totals"] = totals
        return rest


# =============================================================================
# CLASS: ListProjectsArguments
# =============================================================================


class ListProjectsArguments(GenericBaseModel):
    """
    Optional filter arguments for ListProjects
    """

    filter_by_company: list[int] | None = Field(
        default=None,
        alias="FilterByCompany",
        description="Filter projects by company IDs.",
    )
    filter_by_status: list[str] | None = Field(
        default=None,
        alias="FilterByStatus",
        description="Filter projects by status values.",
    )
    filter_by_name_like: str | None = Field(
        default=None,
        alias="FilterByNameLike",
        description="Filter projects where the name contains the given substring.",
    )
    filter_by_description_like: str | None = Field(
        default=None,
        alias="FilterByDescriptionLike",
        description="Filter projects where the description contains the substring.",
    )
    filter_by_description_equals: str | None = Field(
        default=None,
        alias="FilterByDescriptionEquals",
        description="Filter projects where the description equals the given value.",
    )
    filter_by_id_like: str | None = Field(
        default=None,
        alias="FilterByIDLike",
        description="Filter projects where the ID contains the given substring.",
    )
    filter_by_project_type: list[int] | None = Field(
        default=None,
        alias="FilterByProjectType",
        description="Filter projects by project type IDs.",
    )
    filter_by_sync_to_crm: list[bool] | None = Field(
        default=None,
        alias="FilterBySyncToCRM",
        description="Filter projects by sync-to-CRM flag.",
    )
    filter_by_earliest_modified_date: str | None = Field(
        default=None,
        alias="FilterByEarliestModifiedDate",
        description="Earliest modified date filter (e.g., YYYY-MM-DD or ISO 8601).",
    )
    filter_by_latest_modified_date: str | None = Field(
        default=None,
        alias="FilterByLatestModifiedDate",
        description="Latest modified date filter (e.g., YYYY-MM-DD or ISO 8601).",
    )


# =============================================================================
# CLASS: ListProjects
# =============================================================================


class ListProjects(GenericRequest[ListProjectsArguments]):
    """
    List Projects request body
    """

    method: Literal["ListProjects"] = Field(
        default="ListProjects",
        alias="Method",
        description="API method name to invoke.",
        frozen=True,
    )


# =============================================================================
# CLASS: ListProjectsResponse
# =============================================================================


class ListProjectsResponse(GenericResponse[list[Project]]):
    """
    Response schema for ListProjects
    """

    @override
    def model_post_init(self, context: Any) -> None:
        if self.content:
            # Sort the projects by description
            self.content.sort(key=lambda project: project.description)


# =============================================================================
# CLASS: GetProjectsArguments
# =============================================================================


class GetProjectsArguments(GenericBaseModel):
    """
    Arguments for GetProjects / GetProjectsWithResources
    """

    requested_projects: list[int] = Field(
        alias="RequestedProjects",
        description="List of project IDs to retrieve.",
    )


# =============================================================================
# CLASS: GetProjects
# =============================================================================


class GetProjects(GenericRequest[GetProjectsArguments]):
    """
    Get Projects request body
    """

    method: Literal["GetProjects"] = Field(
        default="GetProjects",
        alias="Method",
        description="API method name to invoke.",
        frozen=True,
    )


# =============================================================================
# CLASS: GetProjectsResponse
# =============================================================================


class GetProjectsResponse(GenericResponse[list[ProjectDetails]]):
    """
    Response schema for GetProjects
    """


# =============================================================================
# CLASS: GetProjectsWithResources
# =============================================================================


class GetProjectsWithResources(GenericRequest[GetProjectsArguments]):
    """
    Get Projects With Resources request body
    """

    method: Literal["GetProjectsWithResources"] = Field(
        default="GetProjectsWithResources",
        alias="Method",
        description="API method name to invoke.",
        frozen=True,
    )


# =============================================================================
# CLASS: GetProjectsWithResourcesResponse
# =============================================================================


class GetProjectsWithResourcesResponse(GenericResponse[list[ProjectDetails]]):
    """
    Response schema for GetProjectsWithResources
    """


# =============================================================================
# CLASS: GetProjectTemplatesArguments
# =============================================================================


class GetProjectTemplatesArguments(GenericBaseModel):
    """
    Arguments for GetProjectTemplates
    """

    requested_projects: list[int] = Field(
        alias="RequestedProjects",
        description="List of project template IDs to retrieve.",
    )


# =============================================================================
# CLASS: GetProjectTemplates
# =============================================================================


class GetProjectTemplates(GenericRequest[GetProjectTemplatesArguments]):
    """
    Get Project Templates request body
    """

    method: Literal["GetProjectTemplates"] = Field(
        default="GetProjectTemplates",
        alias="Method",
        description="API method name to invoke.",
        frozen=True,
    )


# =============================================================================
# CLASS: GetProjectTemplatesResponse
# =============================================================================


class GetProjectTemplatesResponse(GenericResponse[list[ProjectTemplateDetails]]):
    """
    Response schema for GetProjectTemplates
    """


# =============================================================================
# CLASS: GetProjectTotalsArguments
# =============================================================================


class GetProjectTotalsArguments(GenericBaseModel):
    """
    Arguments for GetProjectTotals.

    Unlike the other Get* methods, this takes a single project key (a scalar
    integer), not an array.
    """

    requested_project_totals: int = Field(
        alias="RequestedProjectTotals",
        description="The single project key to retrieve totals for.",
    )


# =============================================================================
# CLASS: GetProjectTotals
# =============================================================================


class GetProjectTotals(GenericRequest[GetProjectTotalsArguments]):
    """
    Get Project Totals request body
    """

    method: Literal["GetProjectTotals"] = Field(
        default="GetProjectTotals",
        alias="Method",
        description="API method name to invoke.",
        frozen=True,
    )


# =============================================================================
# CLASS: ProjectType
# =============================================================================


class ProjectType(GenericBaseModel):
    """
    Project type schema for ListProjectTypes response
    """

    project_type_key: int = Field(
        default=0,
        alias="ProjectTypeKey",
        description="Unique project type key.",
    )
    description: str = Field(
        default="",
        alias="Description",
        description="Project type description.",
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
# CLASS: ListProjectTypesArguments
# =============================================================================


class ListProjectTypesArguments(GenericBaseModel):
    """
    Optional filter arguments for ListProjectTypes
    """

    filter_by_status: list[str] | None = Field(
        default=None,
        alias="FilterByStatus",
        description="Filter project types by status values (e.g. Active, Inactive).",
    )


# =============================================================================
# CLASS: ListProjectTypes
# =============================================================================


class ListProjectTypes(GenericRequest[ListProjectTypesArguments]):
    """
    List Project Types request body
    """

    method: Literal["ListProjectTypes"] = Field(
        default="ListProjectTypes",
        alias="Method",
        description="API method name to invoke.",
        frozen=True,
    )


# =============================================================================
# CLASS: ListProjectTypesResponse
# =============================================================================


class ListProjectTypesResponse(GenericResponse[list[ProjectType]]):
    """
    Response schema for ListProjectTypes
    """

    @override
    def model_post_init(self, context: Any) -> None:
        if self.content:
            # Sort the project types by description
            self.content.sort(key=lambda project_type: project_type.description)


# =============================================================================
# CLASS: ProjectTemplate
# =============================================================================


class ProjectTemplate(GenericBaseModel):
    """
    Project template schema for ListProjectTemplates response
    """

    project_template_key: int = Field(
        default=0,
        alias="ProjectTemplateKey",
        description="Unique project template key.",
    )
    id: str = Field(
        default="",
        alias="ID",
        description="Template ID.",
    )
    description: str = Field(
        default="",
        alias="Description",
        description="Template description (name).",
    )


# =============================================================================
# CLASS: ListProjectTemplatesArguments
# =============================================================================


class ListProjectTemplatesArguments(ListProjectsArguments):
    """
    Optional filter arguments for ListProjectTemplates.

    Accepts the same filters as ListProjects.
    """


# =============================================================================
# CLASS: ListProjectTemplates
# =============================================================================


class ListProjectTemplates(GenericRequest[ListProjectTemplatesArguments]):
    """
    List Project Templates request body
    """

    method: Literal["ListProjectTemplates"] = Field(
        default="ListProjectTemplates",
        alias="Method",
        description="API method name to invoke.",
        frozen=True,
    )


# =============================================================================
# CLASS: ListProjectTemplatesResponse
# =============================================================================


class ListProjectTemplatesResponse(GenericResponse[list[ProjectTemplate]]):
    """
    Response schema for ListProjectTemplates
    """

    @override
    def model_post_init(self, context: Any) -> None:
        if self.content:
            # Sort the project templates by description
            self.content.sort(key=lambda template: template.description)


# =============================================================================
# CLASS: UpdatedProjectResult
# =============================================================================


class UpdatedProjectResult(ProjectDetails):
    """
    Project record returned by UpdateProjects.

    Extends the standard project detail with the two fields the API only
    populates on a write: `OriginalProjectKey` (when a record was created)
    and `Deleted` (when a record was deleted).
    """

    original_project_key: int | None = Field(
        default=None,
        alias="OriginalProjectKey",
        description="Negative key supplied on create, echoed back with the new key.",
    )
    deleted: bool | None = Field(
        default=None,
        alias="Deleted",
        description="Whether the record was deleted.",
    )


# =============================================================================
# CLASS: UpdateProjectsArguments
# =============================================================================


class UpdateProjectsArguments(GenericBaseModel):
    """
    Method arguments for UpdateProjects.

    Both `UpdatedProjects` and `UnchangedProjects` are required by the API: the
    unchanged set is the baseline (e.g. from GetProjects) and the updated set
    is the same baseline with the desired edits applied. (As with the other
    Update* methods, and despite the published docs, these are NOT wrapped in a
    `Content` object.)
    """

    updated_projects: list[ProjectDetails] = Field(
        default=[],
        alias="UpdatedProjects",
        description="Projects with edits applied (negative key requests creation).",
    )
    unchanged_projects: list[ProjectDetails] = Field(
        default=[],
        alias="UnchangedProjects",
        description="Baseline project records, left untouched.",
    )
    use_single_transaction: bool = Field(
        default=False,
        alias="UseSingleTransaction",
        description="Apply all updates in one transaction; any failure rejects all.",
    )


# =============================================================================
# CLASS: UpdateProjects
# =============================================================================


class UpdateProjects(GenericRequest[UpdateProjectsArguments]):
    """
    Update Projects request body
    """

    method: Literal["UpdateProjects"] = Field(
        default="UpdateProjects",
        alias="Method",
        description="API method name to invoke.",
        frozen=True,
    )


# =============================================================================
# CLASS: UpdateProjectsResponseContent
# =============================================================================


class UpdateProjectsResponseContent(GenericBaseModel):
    """
    Content payload returned by UpdateProjects.
    """

    projects: list[UpdatedProjectResult] = Field(
        default=[],
        alias="Projects",
        description="The resulting project records.",
    )
    number_of_projects_updated: int = Field(
        default=0,
        alias="NumberOfProjectsUpdated",
        description="Count of projects updated.",
    )


# =============================================================================
# CLASS: UpdateProjectsResponse
# =============================================================================


class UpdateProjectsResponse(GenericResponse[UpdateProjectsResponseContent]):
    """
    Response schema for UpdateProjects
    """
