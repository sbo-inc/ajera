from pydantic import Field, computed_field

from ajera.schemas.generic import GenericBaseModel
from ajera.schemas.project import EmployeeReference
from ajera.schemas.project_v2 import (
    PhaseV2,
    ProjectBundle,
    ProjectV2,
    ResourceEmployee,
    ResourceV2,
)

# =============================================================================
# HELPERS
# =============================================================================


def _join_name(first: str, middle: str, last: str) -> str | None:
    """
    Consolidate first/middle/last name parts into one display string.

    Returns:
        str | None: The joined name, or None when every part is blank.
    """
    parts = [part for part in (first, middle, last) if part]
    return " ".join(parts) or None


def _ratio(numerator: float, denominator: float) -> float | None:
    """
    Safely divide, rounding to four places.

    Returns:
        float | None: The ratio, or None when the denominator is zero.
    """
    return round(numerator / denominator, 4) if denominator else None


# =============================================================================
# CLASS: PersonRef
# =============================================================================


class PersonRef(GenericBaseModel):
    """
    A person (employee) consolidated to a single name plus their key.

    The key lets a consumer drill back into the employees API when needed.
    """

    key: int | None = Field(
        default=None,
        description="Employee key (for drill-down), if known.",
    )
    name: str | None = Field(
        default=None,
        description="Consolidated full name.",
    )


# =============================================================================
# CLASS: ClientRef
# =============================================================================


class ClientRef(GenericBaseModel):
    """
    The client (customer) billed for the project.
    """

    key: int | None = Field(
        default=None,
        description="Client key (for drill-down), if known.",
    )
    name: str | None = Field(
        default=None,
        description="Client name.",
    )


# =============================================================================
# CLASS: Team
# =============================================================================


class Team(GenericBaseModel):
    """
    The people responsible for the project.
    """

    project_manager: PersonRef | None = Field(
        default=None,
        description="Project manager.",
    )
    principal_in_charge: PersonRef | None = Field(
        default=None,
        description="Principal in charge.",
    )
    marketing_contact: PersonRef | None = Field(
        default=None,
        description="Marketing contact.",
    )


# =============================================================================
# CLASS: Schedule
# =============================================================================


class Schedule(GenericBaseModel):
    """
    Estimated and actual start/completion dates (a gantt feed).
    """

    estimated_start: str | None = Field(
        default=None,
        description="Estimated start date.",
    )
    estimated_completion: str | None = Field(
        default=None,
        description="Estimated completion date.",
    )
    actual_start: str | None = Field(
        default=None,
        description="Actual start date.",
    )
    actual_completion: str | None = Field(
        default=None,
        description="Actual completion date.",
    )


# =============================================================================
# CLASS: Contract
# =============================================================================


class Contract(GenericBaseModel):
    """
    Contract (fee) amounts the project is authorized to bill.
    """

    total: float = Field(
        default=0.0,
        description="Total contract amount.",
    )
    labor: float = Field(
        default=0.0,
        description="Labor contract amount.",
    )
    expense: float = Field(
        default=0.0,
        description="Expense contract amount.",
    )
    consultant: float = Field(
        default=0.0,
        description="Consultant contract amount.",
    )


# =============================================================================
# CLASS: Budget
# =============================================================================


class Budget(GenericBaseModel):
    """
    Budgeted hours and cost.
    """

    hours: float = Field(
        default=0.0,
        description="Budgeted hours.",
    )
    labor_cost: float = Field(
        default=0.0,
        description="Budgeted labor cost.",
    )
    expense_cost: float = Field(
        default=0.0,
        description="Budgeted expense cost.",
    )
    consultant_cost: float = Field(
        default=0.0,
        description="Budgeted consultant cost.",
    )


# =============================================================================
# CLASS: Performance
# =============================================================================


class Performance(GenericBaseModel):
    """
    Headline financial and effort metrics, with derived health ratios.

    Base figures come from GetProjectTotals; ratios are computed so a consumer
    can drive health charts without further arithmetic.
    """

    billed: float = Field(
        default=0.0,
        description="Amount billed to date.",
    )
    spent: float = Field(
        default=0.0,
        description="Amount spent (billable value of work performed).",
    )
    cost: float = Field(
        default=0.0,
        description="Internal cost incurred to date (labor + expense + consultant).",
    )
    billed_labor: float = Field(
        default=0.0,
        description="Amount billed for labor (excludes expense/consultant pass-through).",
    )
    spent_labor: float = Field(
        default=0.0,
        description="Billable value of labor performed.",
    )
    labor_cost: float = Field(
        default=0.0,
        description="Internal direct-labor cost incurred to date.",
    )
    write_offs: float = Field(
        default=0.0,
        description="Amounts written off to date.",
    )
    receipts: float = Field(
        default=0.0,
        description="Cash received to date.",
    )
    wip: float = Field(
        default=0.0,
        description="Work in progress (unbilled).",
    )
    receivable_balance: float = Field(
        default=0.0,
        description="Outstanding receivable balance.",
    )
    hours_worked: float = Field(
        default=0.0,
        description="Hours worked to date.",
    )
    hours_budgeted: float = Field(
        default=0.0,
        description="Budgeted resource hours.",
    )
    contract_total: float = Field(
        default=0.0,
        exclude=True,
        description="Total contract amount; basis for percent_contract_billed."
        " Excluded from output (mirrors contract.total).",
    )

    @computed_field(description="Profit to date (billed minus cost).")
    @property
    def profit(self) -> float:
        """
        Profit to date.

        Returns:
            float: Billed minus cost.
        """
        return round(self.billed - self.cost, 2)

    @computed_field(
        description="Net revenue: labor billed, net of expense/consultant pass-through."
    )
    @property
    def net_revenue(self) -> float:
        """
        Net revenue (the AEC fee base).

        Labor billed, excluding expense and consultant pass-through, which carry
        no firm margin and should not inflate cost-based ratios.

        Returns:
            float: billed labor.
        """
        return round(self.billed_labor, 2)

    @computed_field(description="Net multiplier: net_revenue / labor_cost.")
    @property
    def net_multiplier(self) -> float | None:
        """
        Net multiplier: the headline AEC profitability KPI.

        Net revenue earned per unit of direct labor cost; healthy firms run
        ~2.5-3.5. Pass-through cost is excluded from both sides, so this is
        meaningful even on consultant- or expense-heavy projects.

        Returns:
            float | None: net_revenue / labor_cost, or None when no labor cost.
        """
        return _ratio(self.net_revenue, self.labor_cost)

    @computed_field(
        description="Labor gross margin: (net_revenue - labor_cost) / net_revenue."
    )
    @property
    def gross_margin(self) -> float | None:
        """
        Gross margin on labor.

        Returns:
            float | None: (net_revenue - labor_cost) / net_revenue, or None when
            no net revenue.
        """
        return _ratio(self.net_revenue - self.labor_cost, self.net_revenue)

    @computed_field(description="Profit factor: billed / labor_cost.")
    @property
    def profit_factor(self) -> float | None:
        """
        Profit factor on work billed.

        Total billed per unit of direct labor cost (the SBO convention). Differs
        from net_multiplier by including pass-through revenue in the numerator.

        Returns:
            float | None: billed / labor_cost, or None when no labor cost.
        """
        return _ratio(self.billed, self.labor_cost)

    @computed_field(description="Billing realization: billed / spent.")
    @property
    def realization_rate(self) -> float | None:
        """
        Billing realization on work performed.

        Share of the billable value of work performed that was actually
        invoiced; below ~0.9 signals write-downs or scope creep.

        Returns:
            float | None: billed / spent, or None when nothing spent.
        """
        return _ratio(self.billed, self.spent)

    @computed_field(description="Cash collection: receipts / billed.")
    @property
    def collection_rate(self) -> float | None:
        """
        Cash collection on amounts billed.

        Returns:
            float | None: receipts / billed, or None when nothing billed.
        """
        return _ratio(self.receipts, self.billed)

    @computed_field(description="Average realized billing rate: billed / hours_worked.")
    @property
    def effective_billing_rate(self) -> float | None:
        """
        Average realized billing rate per hour worked.

        Returns:
            float | None: billed / hours_worked, or None when no hours worked.
        """
        return round(self.billed / self.hours_worked, 2) if self.hours_worked else None

    @computed_field(description="Average labor cost rate: labor_cost / hours_worked.")
    @property
    def effective_cost_rate(self) -> float | None:
        """
        Average direct-labor cost rate per hour worked.

        Uses labor cost (not blended cost) so pass-through cost does not distort
        the per-hour rate.

        Returns:
            float | None: labor_cost / hours_worked, or None when no hours worked.
        """
        return (
            round(self.labor_cost / self.hours_worked, 2) if self.hours_worked else None
        )

    @computed_field(
        description="Remaining contract fee to earn: contract_total - billed."
    )
    @property
    def backlog(self) -> float:
        """
        Remaining contract fee left to earn.

        Returns:
            float: contract_total minus billed.
        """
        return round(self.contract_total - self.billed, 2)

    @computed_field(description="Percent complete: spent / contract_total.")
    @property
    def percent_complete(self) -> float | None:
        """
        Share of the contract earned by work performed to date.

        Returns:
            float | None: spent / contract_total, or None when no contract.
        """
        return _ratio(self.spent, self.contract_total)

    @computed_field(description="Share of contract billed: billed / contract_total.")
    @property
    def percent_contract_billed(self) -> float | None:
        """
        Share of the contract billed to date.

        Returns:
            float | None: billed / contract_total, or None when no contract.
        """
        return _ratio(self.billed, self.contract_total)

    @computed_field(description="Share of budgeted hours used: worked / budgeted.")
    @property
    def percent_hours_used(self) -> float | None:
        """
        Share of budgeted hours consumed to date.

        Returns:
            float | None: hours_worked / hours_budgeted, or None when no budget.
        """
        return _ratio(self.hours_worked, self.hours_budgeted)


# =============================================================================
# CLASS: ResourceLine
# =============================================================================


class ResourceLine(GenericBaseModel):
    """
    A budgeted resource line on a phase.

    The v2 API returns only an employee name here (no key), so this carries the
    consolidated name without a drill-down key.
    """

    employee: str | None = Field(
        default=None,
        description="Assigned employee name (no key is available from the API).",
    )
    activity_type: str = Field(
        default="",
        description="Activity type (e.g. Labor, Consultant, Expense).",
    )
    budgeted_hours: float = Field(
        default=0.0,
        description="Budgeted units (typically hours).",
    )
    cost_amount: float = Field(
        default=0.0,
        description="Budgeted cost amount.",
    )
    fee_amount: float = Field(
        default=0.0,
        description="Budgeted fee (bill) amount.",
    )
    notes: str = Field(
        default="",
        description="Resource notes.",
    )

    @classmethod
    def from_resource(cls, resource: ResourceV2) -> "ResourceLine":
        """
        Build a resource line from a v2 resource record.

        Returns:
            ResourceLine: The consolidated resource line.
        """
        employee: ResourceEmployee | None = resource.employee
        name = (
            _join_name(employee.first_name, employee.middle_name, employee.last_name)
            if employee
            else None
        )
        return cls(
            employee=name,
            activity_type=resource.activity_type,
            budgeted_hours=resource.units,
            cost_amount=resource.cost_amount,
            fee_amount=resource.fee_amount,
            notes=resource.notes,
        )


# =============================================================================
# CLASS: PhaseSummary
# =============================================================================


class PhaseSummary(GenericBaseModel):
    """
    A de-crufted phase, nested as a tree via `children`.

    Phases form a hierarchy: rollup (parent) phases organize the work and carry
    their sub-phases under `children`; leaf phases (empty `children`) are the
    actual budgeted line items. Each phase's `contract` and `budget` are its own
    values as held in Ajera -- a parent is not necessarily the sum of its
    children. To total a branch, sum its leaf phases or use the project-level
    figures; never add a parent to its descendants.
    """

    phase_key: int = Field(
        default=0,
        description="Phase key.",
    )
    id: str = Field(
        default="",
        description="Phase ID.",
    )
    name: str = Field(
        default="",
        description="Phase description (name).",
    )
    status: str = Field(
        default="",
        description="Status.",
    )
    invoice_group: str | None = Field(
        default=None,
        description="Invoice group this phase bills under.",
    )
    schedule: Schedule = Field(
        default_factory=Schedule,
        description="Phase schedule.",
    )
    contract: Contract = Field(
        default_factory=Contract,
        description="Phase contract amounts (this phase only, not rolled up).",
    )
    budget: Budget = Field(
        default_factory=Budget,
        description="Phase budget (this phase only, not rolled up).",
    )
    resources: list[ResourceLine] = Field(
        default=[],
        description="Budgeted resource lines on this phase.",
    )
    subphase_count: int = Field(
        default=0,
        description="Number of immediate sub-phases. Equals len(children) and"
        " is retained even when children are collapsed from output.",
    )
    children: list["PhaseSummary"] = Field(
        default=[],
        description="Sub-phases nested beneath this phase (empty for a leaf).",
    )


# =============================================================================
# CLASS: ProjectSummary
# =============================================================================


class ProjectSummary(GenericBaseModel):
    """
    A consolidated, chart-ready project overview.

    Synthesized from the v2 GetProjects bundle (identity, people, schedule,
    contract, budget, phases, resources) and GetProjectTotals (financials).
    Cruft fields (CRM sync, tax, certified payroll, invoice text, email
    templates, etc.) are dropped and names are consolidated. This is a derived
    view, not a 1:1 mirror of any single API method.
    """

    project_key: int = Field(
        default=0,
        description="Project key.",
    )
    id: str = Field(
        default="",
        description="Project ID (number).",
    )
    name: str = Field(
        default="",
        description="Project description (name).",
    )
    status: str = Field(
        default="",
        description="Status.",
    )
    billing_type: str = Field(
        default="",
        description="Billing type.",
    )
    company: str = Field(
        default="",
        description="Company name.",
    )
    department: str = Field(
        default="",
        description="Department name.",
    )
    project_type: str = Field(
        default="",
        description="Project type.",
    )
    rate_table: str = Field(
        default="",
        description="Rate table name.",
    )
    location: str = Field(
        default="",
        description="Project location.",
    )
    notes: str = Field(
        default="",
        description="Project notes.",
    )
    client: ClientRef | None = Field(
        default=None,
        description="Client (customer) billed for the project.",
    )
    team: Team = Field(
        default_factory=Team,
        description="People responsible for the project.",
    )
    schedule: Schedule = Field(
        default_factory=Schedule,
        description="Project schedule.",
    )
    contract: Contract = Field(
        default_factory=Contract,
        description="Contract (fee) amounts.",
    )
    budget: Budget = Field(
        default_factory=Budget,
        description="Budgeted hours and cost.",
    )
    performance: Performance = Field(
        default_factory=Performance,
        description="Financial and effort metrics with derived health ratios.",
    )
    phases: list[PhaseSummary] = Field(
        default=[],
        description="Top-level phases under the project; sub-phases nest under"
        " each phase's `children`.",
    )

    # -------------------------------------------------------------------------
    # METHOD: build
    # -------------------------------------------------------------------------

    @classmethod
    def build(
        cls,
        bundle: ProjectBundle,
        totals: dict[str, float],
    ) -> "ProjectSummary":
        """
        Merge a v2 project bundle and project totals into one summary.

        Returns:
            ProjectSummary: The consolidated overview.

        Raises:
            ValueError: If the bundle contains no project.
        """
        if not bundle.projects:
            raise ValueError("No project found in the bundle")

        project: ProjectV2 = bundle.projects[0]

        # The first invoice group's client is treated as the project's client.
        group_names = {
            group.invoice_group_key: group.description
            for group in bundle.invoice_groups
        }
        client = (
            ClientRef(
                key=bundle.invoice_groups[0].client_key,
                name=bundle.invoice_groups[0].client_description or None,
            )
            if bundle.invoice_groups
            else None
        )

        resources_by_phase: dict[int | None, list[ResourceLine]] = {}
        for resource in bundle.resources:
            resources_by_phase.setdefault(resource.parent_key, []).append(
                ResourceLine.from_resource(resource)
            )

        children_by_parent: dict[int | None, list[PhaseV2]] = {}
        for phase in bundle.phases:
            children_by_parent.setdefault(phase.parent_key, []).append(phase)

        # A phase whose parent is not itself a phase (i.e. the project) is a root.
        phase_keys = {phase.phase_key for phase in bundle.phases}
        phases = [
            cls._build_phase(phase, group_names, resources_by_phase, children_by_parent)
            for phase in bundle.phases
            if phase.parent_key not in phase_keys
        ]

        return cls(
            project_key=project.project_key,
            id=project.id,
            name=project.description,
            status=project.status,
            billing_type=project.billing_type,
            company=project.company_description,
            department=project.department_description,
            project_type=project.project_type_description,
            rate_table=project.rate_table_description,
            location=project.location,
            notes=project.notes,
            client=client,
            team=Team(
                project_manager=_person(project.project_manager),
                principal_in_charge=_person(project.principal_in_charge),
                marketing_contact=_person(project.marketing_contact),
            ),
            schedule=Schedule(
                estimated_start=project.estimated_start_date,
                estimated_completion=project.estimated_completion_date,
                actual_start=project.actual_start_date,
                actual_completion=project.actual_completion_date,
            ),
            contract=Contract(
                total=project.total_contract_amount,
                labor=project.labor_contract_amount,
                expense=project.expense_contract_amount,
                consultant=project.consultant_contract_amount,
            ),
            budget=Budget(
                hours=project.hours_cost_budget,
                labor_cost=project.labor_cost_budget,
                expense_cost=project.expense_cost_budget,
                consultant_cost=project.consultant_cost_budget,
            ),
            performance=Performance(
                billed=totals.get("Billed", 0.0),
                spent=totals.get("Spent", 0.0),
                cost=totals.get("Cost", 0.0),
                billed_labor=totals.get("Billed Labor", 0.0),
                spent_labor=totals.get("Spent Labor", 0.0),
                labor_cost=totals.get("Cost Labor", 0.0),
                write_offs=totals.get("Written off", 0.0),
                receipts=totals.get("Receipts", 0.0),
                wip=totals.get("WIP", 0.0),
                receivable_balance=totals.get("Receivable Balance", 0.0),
                hours_worked=totals.get("Hours Worked", 0.0),
                hours_budgeted=totals.get("Resource Hours", 0.0),
                contract_total=project.total_contract_amount,
            ),
            phases=phases,
        )

    # -------------------------------------------------------------------------
    # METHOD: _build_phase
    # -------------------------------------------------------------------------

    @classmethod
    def _build_phase(
        cls,
        phase: PhaseV2,
        group_names: dict[int, str],
        resources_by_phase: dict[int | None, list[ResourceLine]],
        children_by_parent: dict[int | None, list[PhaseV2]],
    ) -> PhaseSummary:
        """
        Build a single phase summary, recursing into its sub-phases.

        Returns:
            PhaseSummary: The consolidated phase with nested children.
        """
        children = [
            cls._build_phase(child, group_names, resources_by_phase, children_by_parent)
            for child in children_by_parent.get(phase.phase_key, [])
        ]
        return PhaseSummary(
            phase_key=phase.phase_key,
            id=phase.id,
            name=phase.description,
            status=phase.status,
            invoice_group=group_names.get(phase.invoice_group_key)
            if phase.invoice_group_key is not None
            else None,
            schedule=Schedule(
                estimated_start=phase.estimated_start_date,
                estimated_completion=phase.estimated_completion_date,
                actual_start=phase.actual_start_date,
                actual_completion=phase.actual_completion_date,
            ),
            contract=Contract(
                total=phase.total_contract_amount,
                labor=phase.labor_contract_amount,
                expense=phase.expense_contract_amount,
                consultant=phase.consultant_contract_amount,
            ),
            budget=Budget(
                hours=phase.hours_cost_budget,
                labor_cost=phase.labor_cost_budget,
                expense_cost=phase.expense_cost_budget,
                consultant_cost=phase.consultant_cost_budget,
            ),
            resources=resources_by_phase.get(phase.phase_key, []),
            subphase_count=len(children),
            children=children,
        )


# =============================================================================
# HELPERS (post-definition, needing model types)
# =============================================================================


def _person(ref: EmployeeReference | None) -> PersonRef | None:
    """
    Consolidate an employee reference into a PersonRef.

    Returns:
        PersonRef | None: The person, or None when there is nothing to show.
    """
    if ref is None:
        return None
    name = _join_name(ref.first_name, ref.middle_name, ref.last_name)
    if ref.employee_key is None and name is None:
        return None
    return PersonRef(key=ref.employee_key, name=name)
