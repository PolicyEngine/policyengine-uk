"""The counted-once check, on a small fake simulation whose formulas are known.

The fake implements only the simulation API the check uses, so each case
controls exactly which component contains or reads which.
"""

from types import SimpleNamespace

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from policyengine_uk.utils.aggregate_impact.guard import (
    _slack,
    breaks_on_slope,
    counted_once,
    judge_total,
    snapshot_inputs,
    still_breaks,
)
from policyengine_uk.utils.aggregate_impact.partition import parse_partition

YEAR = 2026


class FakeHolder:
    def __init__(self, sim, variable):
        self.sim, self.variable = sim, variable

    def get_known_periods(self):
        return [p for (v, p) in self.sim.inputs if v == self.variable]

    def get_array(self, period):
        return self.sim.inputs[(self.variable, str(period))]


class FakeSim:
    """Household-level variables only; formulas read each other by name."""

    def __init__(self, formulas, inputs, weights):
        self.formulas = formulas
        self.inputs = {
            (k, str(YEAR)): np.asarray(v, dtype=float) for k, v in inputs.items()
        }
        self.inputs[("household_weight", str(YEAR))] = np.asarray(weights, dtype=float)
        self.cache = {}
        names = set(formulas) | set(inputs) | {"household_weight"}
        self.tax_benefit_system = SimpleNamespace(
            variables={
                name: SimpleNamespace(
                    entity=SimpleNamespace(key="household"),
                    definition_period="year",
                    value_type=float,
                )
                for name in names
            }
        )

    def calculate(self, variable, period, unweighted=True, map_to=None):
        key = (variable, str(period))
        if key in self.inputs:
            return self.inputs[key]
        if key not in self.cache:
            self.cache[key] = np.asarray(
                self.formulas[variable](lambda name: self.calculate(name, period)),
                dtype=float,
            )
        return self.cache[key]

    def map_result(self, values, source, target):
        assert source == target == "household"
        return values

    def set_input(self, variable, period, values):
        self.inputs[(variable, str(period))] = np.asarray(values, dtype=float)

    def delete_arrays(self, variable, period=None):
        for store in (self.inputs, self.cache):
            for key in [k for k in store if k[0] == variable]:
                del store[key]

    def get_holder(self, variable):
        return FakeHolder(self, variable)

    def _invalidate_all_caches(self):
        self.cache = {}


def partition(tax_heads, spending_heads=(), double_counts=(), reads=None):
    reads = reads or {}

    def heads(spec, total):
        return [
            {
                "id": v,
                "label": v,
                "variable": v,
                "totals": [total],
                "entity": "household",
                "reads": [{"head": r} for r in reads.get(v, [])],
            }
            for v in spec
        ]

    return parse_partition(
        {
            "schema_version": 1,
            "totals": {"gov_tax": {}, "gov_spending": {}},
            "tax_heads": heads(tax_heads, "gov_tax"),
            "spending_heads": heads(spending_heads, "gov_spending"),
            "model_double_counts": [
                {"variable": v, "contained_in": c, "totals": ["gov_tax"]}
                for v, c in double_counts
            ],
        }
    )


def model(contains=True, interaction=-0.5):
    """tax_a may contain tax_b; ben_d reads ben_c with the given slope."""
    return {
        "tax_b": lambda f: 5.0 + 0 * f("x"),
        "tax_a": lambda f: 0.1 * f("x") + (f("tax_b") if contains else 0),
        "gov_tax": lambda f: f("tax_a") + f("tax_b"),
        "ben_c": lambda f: 100 + 0 * f("x"),
        "ben_d": lambda f: np.maximum(0, 200 + interaction * f("ben_c")),
        "gov_spending": lambda f: f("ben_c") + f("ben_d"),
    }


def run(formulas, part, x=(1000, 2000, 3000), weights=(1.5, 2.0, 0.5)):
    sim = FakeSim(formulas, {"x": x}, weights)
    snapshot = snapshot_inputs(sim, part.component_variables())
    result = counted_once(sim, part, YEAR, 1e-6, snapshot)
    return sim, result


def by_variable(result):
    return {r["variable"]: r for r in result["components"]}


def kinds(row):
    """{(head, kind)} of a component's problems."""
    return {(p["head"], p["kind"]) for p in row.get("problems") or []}


def test_declared_double_count_passes_and_the_model_total_counts_it_twice():
    _, result = run(
        model(contains=True),
        partition(["tax_a"], ["ben_c", "ben_d"], [("tax_b", "tax_a")]),
    )
    rows = by_variable(result)
    assert rows["tax_b"]["status"] == "pass"
    assert rows["tax_b"]["coefficients"]["gov_tax"] == pytest.approx(1)
    assert rows["tax_b"]["model_coefficients"]["gov_tax"] == pytest.approx(2)
    assert result["double_counts"][0]["status"] == "pass"
    assert result["reset_reproduces_baseline"]


def test_stale_double_count_declaration_fails():
    _, result = run(
        model(contains=False), partition(["tax_a"], [], [("tax_b", "tax_a")])
    )
    assert result["double_counts"][0]["status"] == "fail"
    assert result["double_counts"][0]["coefficient"] == pytest.approx(0)


def test_undeclared_containment_fails_because_another_head_moves():
    _, result = run(model(contains=True), partition(["tax_a", "tax_b"]))
    rows = by_variable(result)
    assert rows["tax_b"]["status"] == "fail"
    assert ("tax_a", "moves") in kinds(rows["tax_b"])
    assert rows["tax_b"]["responses"]["gov_tax"]["tax_a"] == pytest.approx(1)
    assert rows["tax_a"]["status"] == "pass"


@pytest.mark.parametrize("tax_level", [0, 490_000, 1e9])
def test_undeclared_tax_containment_fails_at_any_baseline(tax_level):
    formulas = model(contains=False)
    formulas["tax_a"] = lambda f: tax_level + f("tax_b")
    _, result = run(formulas, partition(["tax_a", "tax_b"]))
    row = by_variable(result)["tax_b"]
    assert row["responses"]["gov_tax"]["tax_a"] == pytest.approx(1)
    assert row["status"] == "fail" and ("tax_a", "moves") in kinds(row)
    assert row["mediated"] == []
    assert result["reset_reproduces_baseline"]


def test_means_tested_offset_passes_but_a_benefit_rising_with_income_fails():
    _, offset = run(model(interaction=-0.5), partition(["tax_a"], ["ben_c", "ben_d"]))
    row = by_variable(offset)["ben_c"]
    assert row["coefficients"]["gov_spending"] == pytest.approx(0.5)
    assert row["status"] == "pass"
    _, rising = run(model(interaction=0.2), partition(["tax_a"], ["ben_c", "ben_d"]))
    row = by_variable(rising)["ben_c"]
    assert row["status"] == "fail" and ("ben_d", "rises") in kinds(row)


def test_a_total_that_adds_a_zero_component_twice_fails():
    """Baseline identities hold while tax_b is zero; the response gives it away."""
    formulas = model(contains=False)
    formulas["tax_b"] = lambda f: 0 * f("x")
    formulas["gov_tax"] = lambda f: f("tax_a") + 2 * f("tax_b")
    _, result = run(formulas, partition(["tax_a", "tax_b"]))
    row = by_variable(result)["tax_b"]
    assert row["coefficients"]["gov_tax"] == pytest.approx(1)
    assert row["model_coefficients"]["gov_tax"] == pytest.approx(2)
    assert row["status"] == "fail" and ("gov_tax", "model_total") in kinds(row)


def test_a_means_test_fall_cannot_hide_a_benefit_that_contains_another():
    """ben_e contains ben_c while ben_d falls pound for pound: the net is 1."""
    formulas = model(interaction=-1.0)
    formulas["ben_e"] = lambda f: 50 + f("ben_c")
    formulas["gov_spending"] = lambda f: f("ben_c") + f("ben_d") + f("ben_e")
    _, result = run(formulas, partition(["tax_a"], ["ben_c", "ben_d", "ben_e"]))
    row = by_variable(result)["ben_c"]
    assert row["coefficients"]["gov_spending"] == pytest.approx(1)
    assert row["status"] == "fail" and ("ben_e", "rises") in kinds(row)


def test_an_eligibility_loss_in_the_same_household_cannot_hide_a_double_count():
    """One household's ben_e contains ben_c and it loses £100 of ben_f at once."""
    formulas = model(interaction=0.0)
    first = np.array([1.0, 0.0, 0.0])
    formulas["ben_e"] = lambda f: 50 + first * f("ben_c")
    formulas["ben_f"] = lambda f: np.where(
        (f("ben_c") > 100.5) & (first == 1), 0.0, 100.0
    )
    formulas["gov_spending"] = lambda f: (
        f("ben_c") + f("ben_d") + f("ben_e") + f("ben_f")
    )
    _, result = run(
        formulas, partition(["tax_a"], ["ben_c", "ben_d", "ben_e", "ben_f"])
    )
    row = by_variable(result)["ben_c"]
    assert row["status"] == "fail" and ("ben_e", "rises") in kinds(row)


def test_a_declared_read_may_respond_but_not_one_for_one():
    formulas = model(contains=False)
    formulas["tax_a"] = lambda f: 0.1 * f("x") + 0.3 * f("tax_b")
    reading = partition(["tax_a", "tax_b"], reads={"tax_a": ["tax_b"]})
    _, result = run(formulas, reading)
    assert by_variable(result)["tax_b"]["status"] == "pass"
    _, undeclared = run(formulas, partition(["tax_a", "tax_b"]))
    assert by_variable(undeclared)["tax_b"]["status"] == "fail"
    _, containing = run(model(contains=True), reading)
    row = by_variable(containing)["tax_b"]
    assert row["status"] == "fail" and ("tax_a", "contains") in kinds(row)


@pytest.mark.parametrize("tax_level", [100_000, 300_000])
@pytest.mark.parametrize("declared", [False, True])
@pytest.mark.parametrize("contains", [False, True])
def test_a_large_tax_head_is_containment_only_when_it_responds_one_for_one(
    tax_level, declared, contains
):
    """A flat £300,000 reader is unchanged at both NI-style perturbations."""
    formulas = model(contains=False)
    formulas["tax_a"] = lambda f: tax_level + contains * f("tax_b")
    reads = {"tax_a": ["tax_b"]} if declared else {}
    _, result = run(formulas, partition(["tax_a", "tax_b"], reads=reads))
    row = by_variable(result)["tax_b"]
    assert row["status"] == ("fail" if contains else "pass")
    if contains:
        assert ("tax_a", "contains" if declared else "moves") in kinds(row)
    else:
        assert "tax_a" not in row["responses"]["gov_tax"]
    assert result["reset_reproduces_baseline"]


def test_a_large_reader_with_a_mediated_slope_has_no_held_containment():
    """Both held measurements are flat after the other head stops moving."""
    formulas = model(contains=False)
    formulas["tax_c"] = lambda f: 0.5 * f("tax_b")
    formulas["tax_a"] = lambda f: 300_000 + 2 * f("tax_c")
    formulas["gov_tax"] = lambda f: f("tax_a") + f("tax_b") + f("tax_c")
    _, result = run(
        formulas,
        partition(
            ["tax_a", "tax_b", "tax_c"],
            reads={"tax_a": ["tax_b", "tax_c"], "tax_c": ["tax_b"]},
        ),
    )
    row = by_variable(result)["tax_b"]
    assert row["status"] == "pass"
    assert [(m["head"], m["kind"], m["via"]) for m in row["mediated"]] == [
        ("tax_a", "contains", ["tax_c"])
    ]
    assert result["reset_reproduces_baseline"]


def test_a_large_reader_contains_a_component_despite_an_extra_mediated_slope():
    """The unrestricted slope is 1.125; holding tax_c reveals containment."""
    formulas = model(contains=False)
    formulas["tax_c"] = lambda f: 0.25 * f("tax_b")
    formulas["tax_a"] = lambda f: 300_000 + f("tax_b") + 0.5 * f("tax_c")
    formulas["gov_tax"] = lambda f: f("tax_a") + f("tax_b") + f("tax_c")
    _, result = run(
        formulas,
        partition(
            ["tax_a", "tax_b", "tax_c"],
            reads={"tax_a": ["tax_b", "tax_c"], "tax_c": ["tax_b"]},
        ),
    )
    row = by_variable(result)["tax_b"]
    assert row["status"] == "fail"
    assert ("tax_a", "contains") in kinds(row)
    assert result["reset_reproduces_baseline"]


@pytest.mark.parametrize("contains", [False, True])
@settings(max_examples=60, deadline=None)
@given(
    tax_level=st.floats(0, 1e9),
    perturbation=st.floats(1e-6, 1e6),
)
def test_containment_depends_on_the_response_and_perturbation_not_the_tax_level(
    contains, tax_level, perturbation
):
    """Zero never contains; a one-for-one response always does, at any size."""
    expected = np.array([perturbation])
    first = expected if contains else np.zeros(1)
    second = 2 * first
    scales = np.array([tax_level])
    where = np.array([True])
    for second_changes in (None, {"tax_a": second}):
        verdict = judge_total(
            total="gov_tax",
            is_tax=True,
            component="tax_b",
            own_variable="tax_b",
            declared_double_count=False,
            zero_baseline=False,
            weights=np.ones(1),
            expected=expected,
            head_changes={"tax_b": expected, "tax_a": first},
            head_scales={"tax_b": scales, "tax_a": scales},
            model_change=None,
            model_scale=None,
            allowed_readers=["tax_a"],
            second_changes=second_changes,
        )
        assert bool(verdict["problems"]) == contains
        if contains:
            assert verdict["problems"][0]["head"] == "tax_a"
            assert verdict["problems"][0]["kind"] == "contains"
    slack = _slack(scales)
    for held_second in (None, second):
        direct = still_breaks("contains", where, expected, slack, first, held_second)
        assert bool(direct[0]) == contains
    at_first = breaks_on_slope("contains", where, expected, slack, second - first)
    assert bool(at_first[0]) == contains


@pytest.mark.parametrize("response_factor", [0.0, -1.0, 1.0])
@settings(max_examples=60, deadline=None)
@given(tax_level=st.floats(0, 1e9), perturbation=st.floats(1e-6, 1e6))
def test_undeclared_tax_movement_depends_on_the_response_not_the_level(
    response_factor, tax_level, perturbation
):
    """All movement paths reject an observed unit response and accept zero."""
    expected = np.array([perturbation])
    response = response_factor * expected
    scales = np.array([tax_level])
    where = np.array([True])
    verdict = judge_total(
        total="gov_tax",
        is_tax=True,
        component="tax_b",
        own_variable="tax_b",
        declared_double_count=False,
        zero_baseline=False,
        weights=np.ones(1),
        expected=expected,
        head_changes={"tax_b": expected, "tax_a": response},
        head_scales={"tax_b": scales, "tax_a": scales},
        model_change=None,
        model_scale=None,
        allowed_readers=[],
    )
    moved = response_factor != 0
    assert bool(verdict["problems"]) == moved
    if moved:
        assert verdict["problems"][0]["head"] == "tax_a"
        assert verdict["problems"][0]["kind"] == "moves"
    slack = _slack(scales)
    direct = still_breaks("moves", where, expected, slack, response)
    at_first = breaks_on_slope("moves", where, expected, slack, response)
    assert bool(direct[0]) == moved
    assert bool(at_first[0]) == moved


def test_supplied_inputs_are_restored_after_perturbation():
    formulas = model(contains=False)
    formulas.pop("tax_b")
    sim = FakeSim(formulas, {"x": (1, 2, 3), "tax_b": (7, 0, 9)}, (1, 1, 1))
    part = partition(["tax_a", "tax_b"])
    snapshot = snapshot_inputs(sim, part.component_variables())
    result = counted_once(sim, part, YEAR, 1e-6, snapshot)
    assert np.array_equal(sim.inputs[("tax_b", str(YEAR))], [7, 0, 9])
    assert result["reset_reproduces_baseline"]
    assert by_variable(result)["tax_b"]["units"] == 2


def test_zero_components_are_perturbed_everywhere():
    formulas = model(contains=False)
    formulas["tax_b"] = lambda f: 0 * f("x")
    formulas["ben_c"] = lambda f: 0 * f("x")
    _, result = run(formulas, partition(["tax_a", "tax_b"], ["ben_c", "ben_d"]))
    rows = by_variable(result)
    assert rows["tax_b"]["status"] == "pass" and rows["tax_b"]["units"] == 3
    assert rows["ben_c"]["status"] == "pass" and rows["ben_c"]["units"] == 3


def test_a_formula_result_computed_earlier_is_not_frozen_as_an_input():
    """On real policyengine-core, a holder's known periods include results."""
    from policyengine_core.country_template import CountryTaxBenefitSystem
    from policyengine_core.simulations import SimulationBuilder

    system = CountryTaxBenefitSystem()
    sim = SimulationBuilder().build_from_dict(
        system, {"persons": {"a": {"salary": {"2026-01": 3000}}}}
    )
    sim.calculate("income_tax", "2026-01")
    assert sim.get_holder("income_tax").get_known_periods()
    snapshot = snapshot_inputs(sim, ["salary", "income_tax"])
    assert set(snapshot) == {"salary"}


@settings(max_examples=40, deadline=None)
@given(
    x=st.lists(st.floats(1, 1e6), min_size=1, max_size=8),
    weight=st.floats(0.1, 1e4),
    contains=st.booleans(),
)
def test_the_model_coefficient_is_two_exactly_when_a_head_contains_another(
    x, weight, contains
):
    _, result = run(
        model(contains=contains),
        partition(["tax_a", "tax_b"]),
        x=x,
        weights=[weight] * len(x),
    )
    row = by_variable(result)["tax_b"]
    assert row["model_coefficients"]["gov_tax"] == pytest.approx(
        2 if contains else 1, rel=1e-6
    )
    assert (row["status"] == "fail") == contains
    assert result["reset_reproduces_baseline"]


def test_a_reader_that_contains_the_component_in_some_households_fails():
    """Containment in one household of three: the aggregate is far from 1."""
    formulas = model(contains=False)
    first = np.array([1.0, 0.0, 0.0])
    formulas["tax_a"] = lambda f: (
        0.1 * f("x") + first * f("tax_b") - 0.3 * (1 - first) * f("tax_b")
    )
    _, result = run(formulas, partition(["tax_a", "tax_b"], reads={"tax_a": ["tax_b"]}))
    row = by_variable(result)["tax_b"]
    assert row["status"] == "fail" and ("tax_a", "contains") in kinds(row)
    assert (
        next(p for p in row["problems"] if p["kind"] == "contains")["households"] == 1
    )


def test_a_passport_on_a_zero_benefit_passes_but_containment_with_it_fails():
    """ben_z is zero for everyone; ben_d pays £40 to anyone receiving it."""
    formulas = model(interaction=0.0)
    formulas["ben_z"] = lambda f: 0 * f("x")
    formulas["ben_d"] = lambda f: 200 + 40 * (f("ben_z") > 0)
    formulas["gov_spending"] = lambda f: f("ben_c") + f("ben_d") + f("ben_z")
    _, passport = run(formulas, partition(["tax_a"], ["ben_c", "ben_d", "ben_z"]))
    assert by_variable(passport)["ben_z"]["status"] == "pass"
    formulas["ben_d"] = lambda f: 200 + 40 * (f("ben_z") > 0) + f("ben_z")
    _, containing = run(formulas, partition(["tax_a"], ["ben_c", "ben_d", "ben_z"]))
    row = by_variable(containing)["ben_z"]
    assert row["status"] == "fail" and ("ben_d", "contains") in kinds(row)


def test_a_head_containing_the_component_for_one_small_household_fails():
    """Judged household by household, a tiny share cannot pass as noise."""
    formulas = model(contains=False)
    one = np.array([0.0, 0.0, 1.0])
    formulas["tax_a"] = lambda f: 0.1 * f("x") + one * f("tax_b")
    _, result = run(formulas, partition(["tax_a", "tax_b"]), weights=(1e6, 1e6, 1e-3))
    row = by_variable(result)["tax_b"]
    assert row["status"] == "fail" and ("tax_a", "moves") in kinds(row)


def test_a_component_only_in_zero_weight_households_is_skipped():
    formulas = model(contains=False)
    formulas["tax_b"] = lambda f: np.array([5.0, 0.0, 0.0]) + 0 * f("x")
    _, result = run(formulas, partition(["tax_a", "tax_b"]), weights=(0.0, 1.0, 1.0))
    row = by_variable(result)["tax_b"]
    assert row["status"] == "skipped" and "no weight" in row["detail"]


def test_a_taper_that_adds_the_component_back_is_beyond_the_check():
    """Documented limit: max(0, a - c) + c does not move at the margin."""
    formulas = model(interaction=0.0)
    formulas["ben_g"] = lambda f: np.maximum(0, 300 - f("ben_c")) + f("ben_c")
    formulas["gov_spending"] = lambda f: f("ben_c") + f("ben_d") + f("ben_g")
    _, result = run(formulas, partition(["tax_a"], ["ben_c", "ben_d", "ben_g"]))
    assert by_variable(result)["ben_c"]["status"] == "pass"


def overlap_model(uc_reads_ca=1.0, uc_contains_ib=0.0, ib=10.0):
    """ca is reduced by ib (overlapping benefits); uc counts ca as income.

    The model's pattern of Incapacity Benefit, Carer's Allowance and
    Universal Credit (#2424): raising ib lowers ca, and uc rises by what ca
    lost.
    """
    formulas = model(interaction=0.0)
    formulas["ib"] = lambda f: ib + 0 * f("x")
    formulas["ca"] = lambda f: np.maximum(0, 100 - f("ib"))
    formulas["uc"] = lambda f: np.maximum(
        0, 500 - uc_reads_ca * f("ca") + uc_contains_ib * f("ib")
    )
    formulas["gov_spending"] = lambda f: f("ib") + f("ca") + f("uc")
    return formulas


OVERLAP = partition(["tax_a"], ["ib", "ca", "uc"])


def test_a_benefit_that_rises_through_another_head_is_mediated_not_contained():
    sim, result = run(overlap_model(), OVERLAP)
    row = by_variable(result)["ib"]
    assert row["status"] == "pass"
    assert row["mediated"] == [
        {
            "total": "gov_spending",
            "head": "uc",
            "kind": "rises",
            "households": 3,
            "via": ["ca"],
        }
    ]
    assert result["reset_reproduces_baseline"]
    # Holding heads leaves no input behind.
    assert {k[0] for k in sim.inputs} == {"x", "household_weight"}


def test_a_mediated_route_cannot_hide_a_direct_containment():
    _, result = run(overlap_model(uc_contains_ib=1.0), OVERLAP)
    row = by_variable(result)["ib"]
    assert row["status"] == "fail" and ("uc", "rises") in kinds(row)
    assert row["mediated"] == []


def test_a_zero_benefit_mediated_one_for_one_is_not_containment():
    """ib is zero for everyone, so uc may respond; its slope of 1 is via ca."""
    _, result = run(overlap_model(ib=0.0), OVERLAP)
    row = by_variable(result)["ib"]
    assert row["status"] == "pass"
    assert [(m["head"], m["kind"], m["via"]) for m in row["mediated"]] == [
        ("uc", "contains", ["ca"])
    ]
    _, containing = run(overlap_model(ib=0.0, uc_contains_ib=1.0), OVERLAP)
    row = by_variable(containing)["ib"]
    assert row["status"] == "fail" and ("uc", "contains") in kinds(row)


def test_a_tax_moved_by_a_declared_reader_is_mediated_and_found_directly():
    """tax_c reads tax_b (declared); tax_a reads tax_c (undeclared)."""
    formulas = model(contains=False)
    formulas["tax_c"] = lambda f: 0.2 * f("tax_b") + 0 * f("x")
    formulas["tax_a"] = lambda f: 0.1 * f("x") + 0.5 * f("tax_c")
    formulas["gov_tax"] = lambda f: f("tax_a") + f("tax_b") + f("tax_c")
    _, result = run(
        formulas, partition(["tax_a", "tax_b", "tax_c"], reads={"tax_c": ["tax_b"]})
    )
    rows = by_variable(result)
    assert rows["tax_b"]["status"] == "pass"
    assert [(m["head"], m["via"]) for m in rows["tax_b"]["mediated"]] == [
        ("tax_a", ["tax_c"])
    ]
    assert rows["tax_c"]["status"] == "fail"
    assert ("tax_a", "moves") in kinds(rows["tax_c"])


@settings(max_examples=40, deadline=None)
@given(
    reads_ca=st.floats(0, 1),
    contains_ib=st.sampled_from([0.0, 0.25, 1.0]),
    ib=st.sampled_from([0.0, 10.0]),
)
def test_the_guard_fails_exactly_when_a_head_responds_directly(
    reads_ca, contains_ib, ib
):
    """Whatever the mediated route carries, only the direct response fails."""
    _, result = run(overlap_model(reads_ca, contains_ib, ib), OVERLAP)
    row = by_variable(result)["ib"]
    # With ib zero for everyone uc may respond, except one for one.
    direct = contains_ib == 1.0 if ib == 0.0 else contains_ib > 0
    assert (row["status"] == "fail") == direct
    assert result["reset_reproduces_baseline"]


def test_a_rise_cancelled_everywhere_by_a_mediated_fall_is_beyond_the_check():
    """Documented limit: uc contains ib but falls with ca, which ib lowers."""
    _, hidden = run(overlap_model(uc_reads_ca=-1.0, uc_contains_ib=1.0), OVERLAP)
    assert by_variable(hidden)["ib"]["status"] == "pass"
    # In a household that has no Carer's Allowance the rise shows.
    formulas = overlap_model(uc_reads_ca=-1.0, uc_contains_ib=1.0)
    carer = np.array([1.0, 1.0, 0.0])
    formulas["ca"] = lambda f: carer * np.maximum(0, 100 - f("ib"))
    _, shown = run(formulas, OVERLAP)
    row = by_variable(shown)["ib"]
    assert row["status"] == "fail" and ("uc", "rises") in kinds(row)
    assert next(p for p in row["problems"] if p["head"] == "uc")["households"] == 1


def test_a_containment_gated_by_a_passport_on_another_head_fails():
    """Sol re-review 2, finding 2: c is zero for everyone, b passports on c,
    and h contains c only where b is paid. Holding b at its baseline (zero)
    switches h off; holding it at its perturbed value keeps h's slope of 1."""
    formulas = model(interaction=0.0)
    formulas["c"] = lambda f: 0 * f("x")
    formulas["b"] = lambda f: 40.0 * (f("c") > 0)
    formulas["h"] = lambda f: f("c") * (f("b") > 0)
    formulas["gov_spending"] = lambda f: (
        f("c") + f("b") + f("h") + f("ben_c") + f("ben_d")
    )
    _, result = run(formulas, partition(["tax_a"], ["ben_c", "ben_d", "c", "b", "h"]))
    row = by_variable(result)["c"]
    assert row["status"] == "fail" and ("h", "contains") in kinds(row)
    assert result["reset_reproduces_baseline"]


def test_a_mediated_fall_that_outweighs_a_containment_is_beyond_the_check():
    """Documented limit: uc contains ib but falls by twice what ca lost."""
    _, result = run(overlap_model(uc_reads_ca=-2.0, uc_contains_ib=1.0), OVERLAP)
    assert by_variable(result)["ib"]["status"] == "pass"


def test_mediated_records_name_the_heads_that_moved_not_a_proven_route():
    """Sol re-review 2, finding 4: an unrelated head that moved is listed too."""
    formulas = overlap_model()
    formulas["unrelated"] = lambda f: 200 - 0.5 * f("ib")
    formulas["gov_spending"] = lambda f: f("ib") + f("ca") + f("uc") + f("unrelated")
    _, result = run(formulas, partition(["tax_a"], ["ib", "ca", "uc", "unrelated"]))
    row = by_variable(result)["ib"]
    assert row["status"] == "pass"
    assert row["mediated"][0]["via"] == ["ca", "unrelated"]


def test_units_and_households_count_only_records_with_weight():
    """Sol re-review 3 of #2335, finding 4: a zero-weight record adds nothing."""
    formulas = model(contains=False)
    one = np.array([1.0, 1.0, 0.0])
    formulas["tax_a"] = lambda f: 0.1 * f("x") + one * f("tax_b")
    _, result = run(formulas, partition(["tax_a", "tax_b"]), weights=(1.5, 0.0, 0.5))
    row = by_variable(result)["tax_b"]
    # tax_b is non-zero in all three households, one of which has no weight.
    assert row["units"] == 2
    # tax_a contains tax_b in households 1 and 2; only household 1 has weight.
    moves = [p for p in row["problems"] if p["head"] == "tax_a"]
    assert moves and all(p["households"] == 1 for p in moves)
