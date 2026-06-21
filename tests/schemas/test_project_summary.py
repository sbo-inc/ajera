import pytest

from ajera.schemas.project import EmployeeReference
from ajera.schemas.project_summary import ProjectSummary
from ajera.schemas.project_v2 import (
    InvoiceGroupV2,
    PhaseV2,
    ProjectBundle,
    ProjectV2,
    ResourceEmployee,
    ResourceV2,
)

# =============================================================================
# TEST: Fixtures
# =============================================================================
#
# All fixtures use synthetic, non-identifying data. Two archetypes are modeled:
#   - "Alpha": consultant-heavy, where labor cost is barely booked relative to
#     billings, so labor-based metrics look anomalous (a data-quality signal).
#   - "Beta":  labor-driven, the "healthy normal" control, where labor-based
#     metrics land right next to the blended figures.


def _bundle() -> ProjectBundle:
    return ProjectBundle(
        Projects=[
            ProjectV2(
                ProjectKey=1001,
                ID="1001",
                Description="Project Alpha",
                Status="Active",
                BillingType="TimeAndExpense",
                CompanyDescription="Example Company",
                DepartmentDescription="Engineering Services",
                ProjectTypeDescription="Consulting Services",
                RateTableDescription="Standard 2025",
                ProjectManager=EmployeeReference(
                    EmployeeKey=501, FirstName="Alex", LastName="Rivera"
                ),
                MarketingContact=EmployeeReference(
                    EmployeeKey=502, FirstName="Jordan", LastName="Lee"
                ),
                EstimatedStartDate="2025-11-06",
                TotalContractAmount=400000.0,
                LaborContractAmount=400000.0,
                HoursCostBudget=2000.0,
                LaborCostBudget=1500.0,
            )
        ],
        InvoiceGroups=[
            InvoiceGroupV2(
                InvoiceGroupKey=701,
                Description="Invoice Group",
                ClientKey=301,
                ClientDescription="Globex Corporation",
            )
        ],
        Phases=[
            PhaseV2(
                ProjectKey=1001,
                PhaseKey=1101,
                ParentKey=1001,
                InvoiceGroupKey=701,
                ID="1001.00",
                Description="Phase One",
                Status="Active",
                EstimatedStartDate="2025-11-06",
                TotalContractAmount=400000.0,
                HoursCostBudget=2000.0,
            )
        ],
        Resources=[
            ResourceV2(
                ResourceKey=1,
                ParentKey=1101,
                ActivityType="Labor",
                Employee=ResourceEmployee(FirstName="Alex", LastName="Rivera"),
                Units=1500.0,
                CostAmount=1500.0,
                FeeAmount=300000.0,
                Notes="WOC",
            ),
            ResourceV2(
                ResourceKey=2,
                ParentKey=1101,
                ActivityType="Labor",
                Employee=ResourceEmployee(),
                Units=350.0,
                FeeAmount=100000.0,
            ),
        ],
    )


def _totals() -> dict[str, float]:
    # Alpha: consultant-heavy. Cost is almost all consultant pass-through
    # (Cost Labor is only 600), which is why its labor-based metrics look
    # anomalous and flag poor cost-rate data.
    return {
        "Billed": 200000.0,
        "Billed Labor": 200000.0,
        "Spent": 200000.0,
        "Spent Labor": 200000.0,
        "Cost": 60000.0,
        "Cost Labor": 600.0,
        "Written off": 0.0,
        "Receipts": 150000.0,
        "WIP": 0.0,
        "Receivable Balance": 50000.0,
        "Hours Worked": 800.0,
        "Resource Hours": 2000.0,
    }


def _beta_bundle() -> ProjectBundle:
    # Minimal bundle: the Performance metrics only need the contract total.
    return ProjectBundle(
        Projects=[
            ProjectV2(
                ProjectKey=1002,
                ID="1002",
                Description="Project Beta",
                TotalContractAmount=3000000.0,
            )
        ],
    )


def _beta_totals() -> dict[str, float]:
    # Beta: labor-driven (negligible pass-through), so labor-based metrics
    # land right next to the blended figures -- the "healthy normal" control.
    return {
        "Billed": 900000.0,
        "Billed Labor": 890000.0,
        "Spent": 1000000.0,
        "Spent Labor": 990000.0,
        "Cost": 300000.0,
        "Cost Labor": 297000.0,
        "Written off": 0.0,
        "Receipts": 810000.0,
        "WIP": 100000.0,
        "Receivable Balance": 90000.0,
        "Hours Worked": 5000.0,
        "Resource Hours": 20000.0,
    }


# =============================================================================
# TEST: ProjectSummary.build
# =============================================================================


def test_build_consolidates_identity_and_people() -> None:
    summary = ProjectSummary.build(_bundle(), _totals())

    assert summary.project_key == 1001
    assert summary.name == "Project Alpha"
    # Name parts are consolidated into one string, with the key retained.
    assert summary.team.project_manager is not None
    assert summary.team.project_manager.name == "Alex Rivera"
    assert summary.team.project_manager.key == 501
    # No principal in charge was supplied -> consolidated to None.
    assert summary.team.principal_in_charge is None
    # Client is pulled from the invoice group.
    assert summary.client is not None
    assert summary.client.key == 301
    assert summary.client.name == "Globex Corporation"


def test_build_computes_health_ratios() -> None:
    summary = ProjectSummary.build(_bundle(), _totals())
    perf = summary.performance

    assert perf.billed == 200000.0
    assert perf.profit == 140000.0
    # Labor gross margin: (net_revenue - labor_cost) / net_revenue. Near 1.0
    # because Alpha's labor cost (600) is barely recorded -- a data-quality
    # flag, not a real 99.7% margin.
    assert perf.gross_margin == 0.997
    assert perf.percent_contract_billed == 0.5
    assert perf.percent_hours_used == 0.4

    # contract_total backs the ratio but is excluded from serialized output.
    dumped = summary.performance.model_dump()
    assert "contract_total" not in dumped


def test_build_computes_contract_health_metrics() -> None:
    summary = ProjectSummary.build(_bundle(), _totals())
    perf = summary.performance

    # Labor-based cost metrics. With labor cost barely booked (600), the
    # multiplier and cost rate are anomalous -- intentionally surfaced, not hidden.
    assert perf.net_revenue == 200000.0
    assert perf.net_multiplier == 333.3333
    assert (
        perf.profit_factor == 333.3333
    )  # equals net_multiplier: no billed pass-through
    assert perf.effective_cost_rate == 0.75
    # Revenue/hours-based metrics are unaffected by the pass-through split.
    assert perf.realization_rate == 1.0
    assert perf.collection_rate == 0.75
    assert perf.effective_billing_rate == 250.0
    assert perf.backlog == 200000.0
    assert perf.percent_complete == 0.5


def test_build_labor_metrics_on_labor_driven_project() -> None:
    # Beta is labor-driven, so labor-based metrics match the blended figures:
    # realistic multiplier (~3.0), margin (~67%), and cost rate (~$59/hr).
    summary = ProjectSummary.build(_beta_bundle(), _beta_totals())
    perf = summary.performance

    assert perf.net_revenue == 890000.0
    assert perf.net_multiplier == 2.9966
    # profit_factor sits just above net_multiplier: the gap is billed expense
    # pass-through, which net_multiplier strips out.
    assert perf.profit_factor == 3.0303
    assert perf.gross_margin == 0.6663
    assert perf.effective_cost_rate == 59.4
    assert perf.effective_billing_rate == 180.0
    assert perf.realization_rate == 0.9
    assert perf.collection_rate == 0.9
    assert perf.backlog == 2100000.0
    assert perf.percent_complete == 0.3333
    assert perf.percent_contract_billed == 0.3
    assert perf.percent_hours_used == 0.25


def test_build_ratios_guard_against_zero() -> None:
    summary = ProjectSummary.build(_bundle(), {})
    perf = summary.performance

    assert perf.profit == 0.0
    assert perf.net_revenue == 0.0
    # Nothing billed/spent and no hours or labor cost -> zero denominators.
    assert perf.gross_margin is None
    assert perf.percent_hours_used is None
    assert perf.net_multiplier is None
    assert perf.profit_factor is None
    assert perf.realization_rate is None
    assert perf.collection_rate is None
    assert perf.effective_billing_rate is None
    assert perf.effective_cost_rate is None
    # A contract still exists, so these stay meaningful (not undefined).
    assert perf.percent_contract_billed == 0.0
    assert perf.percent_complete == 0.0
    assert perf.backlog == 400000.0


def test_build_groups_resources_under_phase() -> None:
    summary = ProjectSummary.build(_bundle(), _totals())

    assert len(summary.phases) == 1
    phase = summary.phases[0]
    assert phase.invoice_group == "Invoice Group"
    assert len(phase.resources) == 2
    # Blank employee name consolidates to None; populated one joins parts.
    assert phase.resources[0].employee == "Alex Rivera"
    assert phase.resources[1].employee is None
    assert phase.resources[1].budgeted_hours == 350.0


def test_build_nests_phases_into_a_tree() -> None:
    bundle = ProjectBundle(
        Projects=[ProjectV2(ProjectKey=1, Description="P", TotalContractAmount=100.0)],
        Phases=[
            PhaseV2(PhaseKey=10, ParentKey=1, ID="10", Description="Rollup"),
            PhaseV2(
                PhaseKey=11,
                ParentKey=10,
                ID="10.1",
                Description="Leaf A",
                TotalContractAmount=60.0,
            ),
            PhaseV2(
                PhaseKey=12,
                ParentKey=10,
                ID="10.2",
                Description="Leaf B",
                TotalContractAmount=40.0,
            ),
        ],
        Resources=[
            ResourceV2(ResourceKey=1, ParentKey=11, ActivityType="Labor", Units=5.0),
        ],
    )

    summary = ProjectSummary.build(bundle, {})

    # Only the rollup phase is top-level; its parent (the project) is not a phase.
    assert len(summary.phases) == 1
    rollup = summary.phases[0]
    assert rollup.name == "Rollup"
    assert "parent_key" not in rollup.model_dump()
    # Sub-phases are nested under children, not flattened into the top level.
    assert {child.name for child in rollup.children} == {"Leaf A", "Leaf B"}
    assert rollup.subphase_count == 2  # count matches len(children)
    leaf_a = next(c for c in rollup.children if c.name == "Leaf A")
    assert leaf_a.children == []  # a leaf has no children
    assert leaf_a.subphase_count == 0  # a leaf has no sub-phases
    assert len(leaf_a.resources) == 1  # resources attach to their own phase

    # The count survives collapsing children (as the CLI does for --no-subphases).
    rollup.children = []
    assert rollup.subphase_count == 2


def test_build_raises_without_project() -> None:
    with pytest.raises(ValueError, match="No project"):
        ProjectSummary.build(ProjectBundle(), _totals())
