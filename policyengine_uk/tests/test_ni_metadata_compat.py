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
    assert actual[OLD] == {**expected, "household": False, "economy": False}
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


# Only these discovery flags intentionally differ from the frozen H record.
HIDDEN_DISCOVERY_PATHS = (
    "gov.hmrc.national_insurance.class_1.rates.employee.main",
    "gov.hmrc.national_insurance.class_1.rates.employee.additional",
    "gov.hmrc.national_insurance.class_1.thresholds.primary_threshold",
    "gov.hmrc.national_insurance.class_1.thresholds.upper_earnings_limit",
    "gov.hmrc.national_insurance.class_1.rates.employer",
    "gov.hmrc.national_insurance.class_1.thresholds.secondary_threshold",
    "gov.hmrc.national_insurance.class_4.rates.main",
    "gov.hmrc.national_insurance.class_4.rates.additional",
    "gov.hmrc.national_insurance.class_4.thresholds.lower_profits_limit",
    "gov.hmrc.national_insurance.class_4.thresholds.upper_profits_limit",
    "gov.hmrc.national_insurance.class_1.employee_scale[0].threshold",
    "gov.hmrc.national_insurance.class_1.employee_scale[0].rate",
    "gov.hmrc.national_insurance.class_1.employer_scale[0].threshold",
    "gov.hmrc.national_insurance.class_1.employer_scale[0].rate",
    "gov.hmrc.national_insurance.class_4.contribution_scale[0].threshold",
    "gov.hmrc.national_insurance.class_4.contribution_scale[0].rate",
)


@pytest.mark.parametrize("path", HIDDEN_DISCOVERY_PATHS)
def test_fixed_zero_and_legacy_discovery_controls_are_hidden(path):
    actual = build_parameters(
        SimpleNamespace(tax_benefit_system=CountryTaxBenefitSystem())
    )
    assert actual[path]["household"] is False
    assert actual[path]["economy"] is False


def test_discovery_views_do_not_hide_or_mutate_canonical_controls():
    from policyengine_uk.utils.ni_parameter_scales import NI_LEGACY_PATHS

    system = CountryTaxBenefitSystem()
    records = build_parameters(SimpleNamespace(tax_benefit_system=system))
    # Scope identity to the current gov tree, excluding the named baseline copy.
    discovered = {item.name: item for item in system.parameters.gov.get_descendants()}
    for old, new in NI_LEGACY_PATHS.items():
        alias = get_parameter(system.parameters, old)
        canonical = get_parameter(system.parameters, new)
        assert alias.metadata is canonical.metadata
        assert alias.values_list is canonical.values_list
        assert records[new]["household"] is True
        assert records[new]["economy"] is True
        assert records[old] == {
            **records[new],
            "parameter": old,
            "household": False,
            "economy": False,
        }
        assert discovered[old] is not alias
        assert discovered[old].metadata is not canonical.metadata
        assert discovered[new] is canonical
