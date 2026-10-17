"""Pinned source-extracted API contracts; no installed API or service calls."""

from types import SimpleNamespace
from pathlib import Path
from policyengine_core.parameters.operations.get_parameter import get_parameter
import json
import pytest

from policyengine_uk import CountryTaxBenefitSystem
from policyengine_uk.tests.fixtures.ni_metadata_api_contract import (
    build_parameters,
    _normalize_reform_values,
    _apply_reform_to_system,
    create_policy_reform,
    get_safe_json,
)

OLD = "gov.hmrc.national_insurance.class_1.rates.employee.main"
NEW = "gov.hmrc.national_insurance.class_1.employee_scale[1].rate"


@pytest.mark.parametrize("path", [OLD, NEW])
def test_actual_core_get_parameter_api_normalization_and_update(path, record_property):
    original = CountryTaxBenefitSystem()
    system = original.clone()
    data = {path: {"2026-01-01.2026-12-31": "0.16"}}
    normalized = _normalize_reform_values(SimpleNamespace(), data, system)
    assert normalized[path]["2026-01-01.2026-12-31"] == 0.16
    build_parameters(SimpleNamespace(tax_benefit_system=system))
    _apply_reform_to_system(SimpleNamespace(), system, normalized)
    actual = build_parameters(SimpleNamespace(tax_benefit_system=system))
    # Exact immutable-B control reproduces baseline-name overwrite in this
    # synthetic reserialization: construction-cached Country metadata is not
    # a live changed-system export. Preserve that whole old record, rather
    # than introducing an unrelated baseline/API lifecycle change.
    # Base-control result SHA25645bc659d1915a86afb6340ef276e535588783f88a46218b993f4cb3c97a14c02.
    expected = json.loads(
        (
            Path(__file__).parent / "fixtures/ni_legacy_parameter_metadata.json"
        ).read_text()
    )["parameters"][OLD]
    assert actual[OLD] == expected
    assert actual[NEW] == {**expected, "parameter": NEW}
    alias = get_parameter(system.parameters, OLD)
    canonical = get_parameter(system.parameters, NEW)
    assert alias.metadata is canonical.metadata
    assert alias.values_list is canonical.values_list
    assert alias("2026") == canonical("2026") == 0.16
    assert any(
        entry.instant_str == "2026-01-01" and entry.value == 0.16
        for entry in alias.values_list
    )
    assert system.parameters.baseline.get_child(OLD)("2026") == 0.08
    record_property(
        "source_extracted_metadata_contract",
        json.dumps(
            {
                "update_path": path,
                "old_complete_record": actual[OLD],
                "canonical_complete_record": actual[NEW],
                "live_root_value": alias("2026"),
                "baseline_value": system.parameters.baseline.get_child(OLD)("2026"),
                "same_values_list": alias.values_list is canonical.values_list,
                "same_metadata": alias.metadata is canonical.metadata,
            },
            sort_keys=True,
        ),
    )
    assert original.parameters.get_child(OLD)("2026") == 0.08
    json.dumps(actual, allow_nan=False)


@pytest.mark.parametrize("path", [OLD, NEW])
def test_actual_legacy_api_manual_children_reform_route(path):
    original = CountryTaxBenefitSystem()
    reform = create_policy_reform({path: {"2026-01-01.2026-12-31": 0.14}})
    updated = reform(original)
    assert updated.parameters.get_child(OLD)("2026") == 0.14
    assert updated.parameters.get_child(NEW)("2026") == 0.14
    assert original.parameters.get_child(OLD)("2026") == 0.08


def test_exact_pinned_json_helper_handles_nonfinite_nested_values():
    assert get_safe_json({"value": [float("inf"), float("-inf"), None, 0.08]}) == {
        "value": ["Infinity", "-Infinity", None, 0.08]
    }
