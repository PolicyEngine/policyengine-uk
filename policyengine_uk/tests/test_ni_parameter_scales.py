"""Public NI scale and legacy leaf contracts, specified before migration."""

import json
from pathlib import Path

import pytest
from policyengine_core.parameters import Parameter, ParameterScale

from policyengine_uk import CountryTaxBenefitSystem
from policyengine_uk.tests.fixtures.ni_metadata_api_contract import build_parameters
from types import SimpleNamespace

PREFIX = "gov.hmrc.national_insurance."
LEAVES = {
    "class_1.rates.employee.main": "class_1.employee_scale[1].rate",
    "class_1.rates.employee.additional": "class_1.employee_scale[2].rate",
    "class_1.thresholds.primary_threshold": "class_1.employee_scale[1].threshold",
    "class_1.thresholds.upper_earnings_limit": "class_1.employee_scale[2].threshold",
    "class_1.rates.employer": "class_1.employer_scale[1].rate",
    "class_1.thresholds.secondary_threshold": "class_1.employer_scale[1].threshold",
    "class_4.rates.main": "class_4.contribution_scale[1].rate",
    "class_4.rates.additional": "class_4.contribution_scale[2].rate",
    "class_4.thresholds.lower_profits_limit": "class_4.contribution_scale[1].threshold",
    "class_4.thresholds.upper_profits_limit": "class_4.contribution_scale[2].threshold",
}
# The legacy extraction ended here, with the indices of the day.
LAST_EXTRACTED_YEAR = 2039


def through_extraction(record):
    """A metadata record without the values dated after the legacy extraction."""
    values = {
        date: value
        for date, value in record["values"].items()
        if int(date[:4]) <= LAST_EXTRACTED_YEAR
    }
    return {**record, "values": values}


def test_canonical_marginal_schedules_are_discoverable():
    parameters = CountryTaxBenefitSystem().parameters
    for path in [
        "class_1.employee_scale",
        "class_1.employer_scale",
        "class_4.contribution_scale",
    ]:
        assert isinstance(parameters.get_child(PREFIX + path), ParameterScale)


@pytest.mark.parametrize("legacy,canonical", LEAVES.items())
def test_ten_legacy_scalar_paths_resolve_to_canonical_leaves(legacy, canonical):
    parameters = CountryTaxBenefitSystem().parameters
    assert parameters.get_child(PREFIX + legacy) is parameters.get_child(
        PREFIX + canonical
    )


def test_legacy_callable_attribute_updates_reach_canonical_leaves():
    system = CountryTaxBenefitSystem()
    tree = system.parameters.clone()
    tree("2026")  # Warm canonical and sibling parent reads.
    old_parent = tree.gov.hmrc.national_insurance.class_1.rates.employee
    old_parent("2026")
    old_parent.main.update(period="2026", value=0.19)
    assert tree.get_child(PREFIX + "class_1.employee_scale[1].rate")("2026") == 0.19
    assert tree("2026").gov.hmrc.national_insurance.class_1.rates.employee.main == 0.19
    assert old_parent("2026").main == 0.19
    assert (
        system.parameters.get_child(PREFIX + "class_1.rates.employee.main")("2026")
        == 0.08
    )


def test_live_parameter_metadata_preserves_legacy_scalar_records():
    expected = json.loads(
        (
            Path(__file__).parent / "fixtures/ni_legacy_parameter_metadata.json"
        ).read_text()
    )["parameters"]
    actual = build_parameters(
        SimpleNamespace(tax_benefit_system=CountryTaxBenefitSystem())
    )
    assert {name: through_extraction(actual[name]) for name in expected} == {
        name: {**record, "household": False, "economy": False}
        for name, record in expected.items()
    }
    json.dumps(actual, allow_nan=False)


def test_clone_and_baseline_views_resolve_within_their_own_tree():
    source = CountryTaxBenefitSystem().parameters
    clone = source.clone()
    source_value = source.gov.hmrc.national_insurance.class_1.rates.employee.main(
        "2026"
    )
    clone.gov.hmrc.national_insurance.class_1.rates.employee.main.update(
        period="2026", value=0.17
    )
    assert clone.get_child(PREFIX + "class_1.employee_scale[1].rate")("2026") == 0.17
    assert (
        source.gov.hmrc.national_insurance.class_1.rates.employee.main("2026")
        == source_value
    )
    assert (
        clone.baseline.gov.hmrc.national_insurance.class_1.rates.employee.main("2026")
        == source_value
    )


def test_canonical_leaves_have_one_authoritative_registered_occurrence():
    tree = CountryTaxBenefitSystem().parameters
    canonical_names = [PREFIX + name for name in LEAVES.values()]
    descendants = list(tree.gov.get_descendants())
    for name in canonical_names:
        canonical = tree.get_child(name)
        assert isinstance(canonical, Parameter)
        assert sum(item is canonical for item in descendants) == 1


def test_standalone_legacy_clone_is_independent():
    tree = CountryTaxBenefitSystem().parameters
    leaf = tree.gov.hmrc.national_insurance.class_1.rates.employee.main
    independent = leaf.clone()
    independent.update(period="2026", value=0.18)
    assert leaf("2026") == 0.08
    assert independent("2026") == 0.18


def test_processing_iteration_and_error_restoration_preserve_real_identity():
    from policyengine_core.parameters.operations.get_parameter import get_parameter
    from policyengine_uk.utils.ni_parameter_scales import (
        LegacyNIParameter,
        canonical_ni_processing,
    )

    tree = CountryTaxBenefitSystem().parameters.clone()
    legacy_parent = tree.gov.hmrc.national_insurance.class_1.rates.employee
    original_children = legacy_parent.children
    legacy = original_children["main"]
    canonical = tree.get_child(PREFIX + LEAVES["class_1.rates.employee.main"])
    canonical_parent = canonical.parent
    before = build_parameters(
        SimpleNamespace(tax_benefit_system=SimpleNamespace(parameters=tree))
    )
    with pytest.raises(RuntimeError, match="deliberate"):
        with canonical_ni_processing(tree) as same:
            assert same is tree
            assert canonical.parent is canonical_parent
            assert get_parameter(tree, PREFIX + "class_1.rates.employee.main") is legacy
            assert not any(
                isinstance(item, LegacyNIParameter) for item in tree.get_descendants()
            )
            assert sum(item is canonical for item in tree.get_descendants()) == 1
            raise RuntimeError("deliberate failure")
    assert legacy_parent.children is original_children
    assert canonical.parent is canonical_parent
    assert (
        build_parameters(
            SimpleNamespace(tax_benefit_system=SimpleNamespace(parameters=tree))
        )
        == before
    )


def test_core_uprating_orders_legacy_dependencies_without_double_processing():
    from policyengine_core.parameters.operations.uprate_parameters import (
        uprate_parameters,
    )
    from policyengine_uk.utils.ni_parameter_scales import (
        canonical_ni_processing,
        canonical_ni_uprating_references,
    )

    tree = CountryTaxBenefitSystem().parameters.clone()
    primary = tree.get_child(PREFIX + "class_1.thresholds.primary_threshold")
    secondary = tree.get_child(PREFIX + "class_1.thresholds.secondary_threshold")
    rate = tree.get_child(PREFIX + "class_1.rates.employee.main")
    primary.update(start="2041-01-01", value=100)
    primary.update(start="2042-01-01", value=200)
    secondary.update(start="2041-01-01", value=50)
    rate.update(start="2041-01-01", value=0.1)
    secondary.metadata["uprating"] = PREFIX + "class_1.thresholds.primary_threshold"
    rate.metadata["uprating"] = {
        "parameter": PREFIX + "class_1.thresholds.secondary_threshold"
    }
    old_metadata = rate.metadata["uprating"]
    with canonical_ni_processing(tree):
        with canonical_ni_uprating_references(tree):
            uprate_parameters(tree)
    assert secondary("2042") == 100
    assert rate("2042") == 0.2
    assert rate.metadata["uprating"] is old_metadata
    assert (
        tree.baseline.get_child(PREFIX + "class_1.rates.employee.main")("2042") == 0.08
    )


def test_recursive_core_metadata_propagation_visits_each_authoritative_leaf_once():
    from policyengine_core.parameters.operations.propagate_parameter_metadata import (
        propagate_parameter_metadata,
    )
    from policyengine_uk.utils.ni_parameter_scales import canonical_ni_processing

    tree = CountryTaxBenefitSystem().parameters.clone()
    ni = tree.gov.hmrc.national_insurance
    ni.metadata.update(propagate_metadata_to_children=True, scope_probe="owned-tree")
    with canonical_ni_processing(tree):
        propagate_parameter_metadata(tree)
    for canonical in LEAVES.values():
        assert (
            tree.get_child(PREFIX + canonical).metadata["scope_probe"] == "owned-tree"
        )
    assert (
        "scope_probe"
        not in CountryTaxBenefitSystem().parameters.gov.hmrc.national_insurance.metadata
    )


@pytest.mark.parametrize(
    "target",
    ["legacy_leaf", "canonical_scale", "canonical_deleted", "canonical_leaf_deleted"],
)
def test_conflicting_structural_replacement_is_rejected_without_mutating_source(target):
    from policyengine_core.parameters import ParameterNode, ParameterScale

    original = CountryTaxBenefitSystem()
    changed = original.clone()
    changed.reset_parameters()
    ni = changed.parameters.gov.hmrc.national_insurance
    if target == "legacy_leaf":
        parent = ni.class_1.rates.employee
        replacement = Parameter(parent.main.name, {"values": {"2026-01-01": 0.7}})
        parent.children["main"] = replacement
        parent.main = replacement
        replacement.parent = parent
    elif target == "canonical_scale":
        parent = ni.class_1
        replacement = ParameterScale(
            parent.employee_scale.name,
            {
                "brackets": [
                    {"threshold": {"2026-01-01": 0}, "rate": {"2026-01-01": 0.7}}
                ]
            },
            file_path=None,
        )
        parent.children["employee_scale"] = replacement
        parent.employee_scale = replacement
        replacement.parent = parent
    elif target == "canonical_deleted":
        del ni.class_1.children["employee_scale"]
        del ni.class_1.employee_scale
    else:
        bracket = ni.class_1.employee_scale.brackets[1]
        del bracket.children["rate"]
        del bracket.rate
    with pytest.raises(ValueError, match="NI.*structurally replaced"):
        changed.process_parameters()
    assert (
        original.parameters.get_child(PREFIX + "class_1.rates.employee.main")("2026")
        == 0.08
    )
    assert (
        original.parameters.get_child(PREFIX + "class_1.employee_scale[1].rate")("2026")
        == 0.08
    )


def test_supported_unrelated_structural_addition_survives_reset_and_processing():
    from policyengine_core.parameters import Parameter

    system = CountryTaxBenefitSystem()
    leaf = Parameter("gov.test_222_extra", {"values": {"2026-01-01": 7}})
    system.parameters.gov.add_child("test_222_extra", leaf)
    system.reset_parameters()
    system.process_parameters()
    assert system.parameters.gov.test_222_extra("2026") == 7
    assert (
        system.parameters.get_child(PREFIX + "class_1.rates.employee.main")("2026")
        == 0.08
    )


@pytest.mark.parametrize("reverse", [False, True])
def test_mixed_alias_and_canonical_order_keeps_one_dated_timeline(reverse):
    from policyengine_uk.utils.scenario import Scenario
    from policyengine_uk import Simulation

    old = PREFIX + "class_1.rates.employee.main"
    new = PREFIX + LEAVES["class_1.rates.employee.main"]
    entries = [
        (old, {"2026-04-06.2027-04-05": 0.11}),
        (new, {"2026-04-06.2027-04-05": 0.17}),
    ]
    if reverse:
        entries.reverse()
    sim = Simulation(
        situation={
            "people": {"p": {"age": {2026: 40}}},
            "benunits": {"b": {"members": ["p"]}},
            "households": {"h": {"members": ["p"]}},
        },
        scenario=Scenario.from_reform(dict(entries)),
    )
    params = sim.tax_benefit_system.parameters
    leaf = params.get_child(new)
    assert leaf("2026") == (0.11 if reverse else 0.17)
    assert leaf("2027") == 0.08
    assert params.get_child(old) is leaf
    assert params.baseline.get_child(old)("2026") == 0.08
    assert all(a.path == new for a in sim.tax_benefit_system.dated_assignments)


@pytest.mark.parametrize(
    "old, value",
    [
        ("class_1.thresholds.primary_threshold", 300),
        ("class_1.thresholds.upper_earnings_limit", 1100),
        ("class_1.thresholds.secondary_threshold", 200),
        ("class_4.thresholds.lower_profits_limit", 15000),
        ("class_4.thresholds.upper_profits_limit", 60000),
    ],
)
def test_all_five_generated_thresholds_keep_legacy_and_canonical_reform_routes(
    old, value
):
    from policyengine_uk.utils.scenario import Scenario
    from policyengine_uk import Simulation
    from policyengine_uk.parameters.gov.hmrc.create_threshold_indexation import (
        INDEXED_THRESHOLDS,
    )

    new = PREFIX + LEAVES[old]
    assert new in INDEXED_THRESHOLDS
    situations = {
        "people": {
            "p": {
                "age": {2031: 40},
                "employment_income": {2031: 60000},
                "self_employment_income": {2031: 20000},
            }
        },
        "benunits": {"b": {"members": ["p"]}},
        "households": {"h": {"members": ["p"]}},
    }
    a, b = [
        Simulation(
            situation=situations,
            scenario=Scenario.from_reform({path: {"2031-04-06.2032-04-05": value}}),
        )
        for path in (PREFIX + old, new)
    ]
    for year in (2030, 2031, 2032, 2034):
        left, right = a.tax_benefit_system.parameters, b.tax_benefit_system.parameters
        assert left.get_child(new)(str(year)) == right.get_child(new)(str(year))
        assert left.get_child(PREFIX + old) is left.get_child(new)
    assert a.tax_benefit_system.parameters.get_child(new)("2031") == value
    import numpy as np

    np.testing.assert_array_equal(
        a.calculate("national_insurance", 2031), b.calculate("national_insurance", 2031)
    )
    np.testing.assert_array_equal(
        a.calculate("household_net_income", 2031),
        b.calculate("household_net_income", 2031),
    )


def test_raw_history_and_april_sampling_remain_distinct():
    system = CountryTaxBenefitSystem()
    system.reset_parameters()
    ni = system.parameters.gov.hmrc.national_insurance
    assert ni.class_1.employee_scale.brackets[1].rate("2022-11-05") == 0.1325
    assert ni.class_1.employee_scale.brackets[1].rate("2022-11-06") == 0.12
    assert ni.class_1.rates.employee.main("2022-11-05") == 0.1325
    assert ni.class_1.rates.employee.main("2022-11-06") == 0.12
    system.process_parameters()
    assert (
        system.parameters.gov.hmrc.national_insurance.class_1.employee_scale("2022")
        .components[1]
        .rate
        == 0.1325
    )
    assert (
        system.parameters.gov.hmrc.national_insurance.class_1.rates.employee.main(
            "2022"
        )
        == 0.1325
    )


def test_public_component_inputs_retain_override_and_aggregation_contract():
    from policyengine_uk import Simulation
    from policyengine_uk.tests.test_ni_scale_equivalence import situation

    data = situation()
    data["people"]["p0"]["ni_class_1_employee_primary"] = {2026: 123}
    data["people"]["p0"]["ni_class_1_employee_additional"] = {2026: 45}
    sim = Simulation(situation=data)
    assert float(sim.calculate("ni_class_1_employee", 2026)[0]) == 168
    assert float(sim.calculate("national_insurance", 2026)[0]) == 168


def test_legacy_parent_preserves_core_tracing_and_fresh_cache_reads():
    from types import SimpleNamespace
    from policyengine_core.tracers import TracingParameterNodeAtInstant

    tree = CountryTaxBenefitSystem().parameters.clone()
    parent = tree.gov.hmrc.national_insurance.class_1.rates.employee
    reads = []
    parent.trace = True
    parent.tracer = SimpleNamespace(
        record_parameter_access=lambda *args: reads.append(args)
    )
    parent.branch_name = "test_222"
    first = parent("2026")
    assert isinstance(first, TracingParameterNodeAtInstant)
    assert first.main == 0.08
    tree.get_child(PREFIX + "class_1.employee_scale[1].rate").update(
        period="2026", value=0.21
    )
    assert parent("2026").main == 0.21
    assert [row[0] for row in reads] == [PREFIX + "class_1.rates.employee.main"] * 2
    assert [row[-1] for row in reads] == [0.08, 0.21]


_NI_ZERO_SCALES = (
    "class_1.employee_scale",
    "class_1.employer_scale",
    "class_4.contribution_scale",
)
_NI_ZERO_LEAVES = tuple(
    (scale, leaf) for scale in _NI_ZERO_SCALES for leaf in ("threshold", "rate")
)


def _ni_zero_error(scale, leaf):
    import re

    path = PREFIX + scale + "[0]." + leaf
    return r"NI.*" + re.escape(path) + r".*fixed at zero"


def _ni_zero_situation():
    return {
        "people": {
            "p": {
                "age": {2026: 40},
                "employment_income": {2026: 60_000},
                "self_employment_income": {2026: 30_000},
            }
        },
        "benunits": {"b": {"members": ["p"]}},
        "households": {
            "h": {
                "members": ["p"],
                "region": {2026: "LONDON"},
                "tenure_type": {2026: "OWNED_OUTRIGHT"},
                "council_tax": {2026: 0},
            }
        },
    }


def _ni_zero_scenario(route, changes):
    from policyengine_core.reforms import Reform
    from policyengine_uk.utils.scenario import Scenario

    if route == "changes":
        return Scenario(parameter_changes=changes)
    if route == "core":
        return Scenario.from_reform(Reform.from_dict(changes))
    if route == "callable":

        class UpdateNILeaves(Reform):
            def apply(self):
                def update(parameters):
                    for path, values in changes.items():
                        parameters.get_child(path).update(
                            period="2026", value=values["2026"]
                        )
                    return parameters

                self.modify_parameters(update)

        return Scenario.from_reform(UpdateNILeaves)
    return Scenario.from_reform(changes)


@pytest.mark.parametrize("scale,leaf", _NI_ZERO_LEAVES)
@pytest.mark.parametrize("route", ["dict", "changes", "core", "callable"])
def test_ni_zero_band_reforms_are_rejected(scale, leaf, route):
    from policyengine_uk import Simulation

    path = PREFIX + scale + "[0]." + leaf
    changes = {path: {"2026": 0.5 if leaf == "rate" else 1}}
    with pytest.raises(ValueError, match=_ni_zero_error(scale, leaf)):
        sim = Simulation(
            situation=_ni_zero_situation(),
            scenario=_ni_zero_scenario(route, changes),
        )
        sim.calculate("national_insurance", 2026)


@pytest.mark.parametrize("scale,leaf", _NI_ZERO_LEAVES)
@pytest.mark.parametrize("baseline", [False, True])
def test_ni_zero_band_future_edits_cannot_hide_behind_a_cached_read(
    scale, leaf, baseline
):
    source = CountryTaxBenefitSystem().parameters
    tree = source.clone()
    target = tree.baseline if baseline else tree
    target("2026")
    path = PREFIX + scale + "[0]." + leaf
    target.get_child(path).update(start="2041-01-01", value=1)
    with pytest.raises(ValueError, match=_ni_zero_error(scale, leaf)):
        target("2026")
    assert source.get_child(path)("2041") == 0
    assert source.baseline.get_child(path)("2041") == 0


@pytest.mark.parametrize("scale,leaf", _NI_ZERO_LEAVES)
@pytest.mark.parametrize("operation", ["process_parameters", "reset_parameter_caches"])
def test_ni_zero_band_validation_rejects_updates_without_mutating_source(
    scale, leaf, operation
):
    source = CountryTaxBenefitSystem()
    changed = source.clone()
    if operation == "process_parameters":
        changed.reset_parameters()
    path = PREFIX + scale + "[0]." + leaf
    changed.parameters.get_child(path).update(period="2026", value=1)
    with pytest.raises(ValueError, match=_ni_zero_error(scale, leaf)):
        getattr(changed, operation)()
    assert source.parameters.get_child(path)("2026") == 0


@pytest.mark.parametrize("scale,leaf", _NI_ZERO_LEAVES)
@pytest.mark.parametrize("damage", ["missing", "null"])
def test_ni_zero_band_malformed_leaves_raise_the_targeted_error(scale, leaf, damage):
    tree = CountryTaxBenefitSystem().parameters.clone()
    raw_scale = tree.get_child(PREFIX + scale)
    bracket = raw_scale.brackets[0]
    if damage == "missing":
        del bracket.children[leaf]
        delattr(bracket, leaf)
    else:
        bracket.children[leaf].update(period="2026", value=None)
    with pytest.raises(ValueError, match=_ni_zero_error(scale, leaf)):
        raw_scale("2026")


@pytest.mark.parametrize("scale", _NI_ZERO_SCALES)
@pytest.mark.parametrize("route", ["dict", "changes", "core", "callable"])
def test_ni_zero_band_explicit_zero_updates_are_noops(scale, route):
    import numpy as np
    from policyengine_uk import Simulation

    changes = {
        PREFIX + scale + "[0]." + leaf: {"2026": 0} for leaf in ("threshold", "rate")
    }
    original = Simulation(situation=_ni_zero_situation())
    changed = Simulation(
        situation=_ni_zero_situation(),
        scenario=_ni_zero_scenario(route, changes),
    )
    for output in ("national_insurance", "ni_class_1_employer", "household_net_income"):
        np.testing.assert_array_equal(
            changed.calculate(output, 2026), original.calculate(output, 2026)
        )
