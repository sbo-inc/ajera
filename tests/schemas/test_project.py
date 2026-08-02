from ajera.schemas.project import ProjectTotalsDetails

# =============================================================================
# TEST: ProjectTotalsDetails._collect_totals
# =============================================================================
#
# Ajera returns each project total as an extra top-level property using a
# human-readable label, so the model's "before" validator sweeps unrecognized
# numeric properties into `totals`. The sweep must not swallow python field
# names, nor discard a `Totals` map the caller supplied directly.


def test_accepts_python_field_names() -> None:
    details = ProjectTotalsDetails(project_key=1, totals={"Billed": 100.0})

    assert details.project_key == 1
    assert details.totals == {"Billed": 100.0}


def test_accepts_explicit_totals_map() -> None:
    details = ProjectTotalsDetails.model_validate(
        {"ProjectKey": 1, "Totals": {"Billed": 100.0}}
    )

    assert details.project_key == 1
    assert details.totals == {"Billed": 100.0}


def test_collects_totals_from_wire_shape() -> None:
    details = ProjectTotalsDetails.model_validate(
        {"ProjectKey": 1, "Billed": 100.0, "Cost": 40.0}
    )

    assert details.project_key == 1
    assert details.totals == {"Billed": 100.0, "Cost": 40.0}


def test_merges_collected_totals_into_explicit_map() -> None:
    details = ProjectTotalsDetails.model_validate(
        {"ProjectKey": 1, "Totals": {"Billed": 100.0}, "Cost": 40.0}
    )

    assert details.totals == {"Billed": 100.0, "Cost": 40.0}


def test_standard_and_custom_fields_are_not_totals() -> None:
    details = ProjectTotalsDetails.model_validate(
        {
            "ProjectKey": 1,
            "ID": "1001",
            "Description": "Project Alpha",
            "CompanyKey": 7,
            "CF_Score": 5.0,
            "Billed": 100.0,
        }
    )

    # Numeric standard fields (ProjectKey, CompanyKey) and CF_ custom fields
    # stay out of the totals map; only the unrecognized label is collected.
    assert details.id == "1001"
    assert details.description == "Project Alpha"
    assert details.totals == {"Billed": 100.0}


def test_booleans_are_not_totals() -> None:
    details = ProjectTotalsDetails.model_validate(
        {"ProjectKey": 1, "SomeFlag": True, "Billed": 100.0}
    )

    assert details.totals == {"Billed": 100.0}


def test_non_dict_input_passes_through() -> None:
    details = ProjectTotalsDetails.model_validate(
        ProjectTotalsDetails(project_key=1, totals={"Billed": 100.0})
    )

    assert details.totals == {"Billed": 100.0}
