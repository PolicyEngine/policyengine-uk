"""The counted-once check, on a small fake simulation whose formulas are known.

The fake implements only the simulation API the check uses, so each case
controls exactly which component contains or reads which.
"""

from types import SimpleNamespace

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from policyengine_uk.utils.aggregate_impact.guard import counted_once, snapshot_inputs
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
    assert "tax_a moves by +1.0000" in rows["tax_b"]["detail"]
    assert rows["tax_b"]["responses"]["gov_tax"]["tax_a"] == pytest.approx(1)
    assert rows["tax_a"]["status"] == "pass"


def test_means_tested_offset_passes_but_a_benefit_rising_with_income_fails():
    _, offset = run(model(interaction=-0.5), partition(["tax_a"], ["ben_c", "ben_d"]))
    row = by_variable(offset)["ben_c"]
    assert row["coefficients"]["gov_spending"] == pytest.approx(0.5)
    assert row["status"] == "pass"
    _, rising = run(model(interaction=0.2), partition(["tax_a"], ["ben_c", "ben_d"]))
    row = by_variable(rising)["ben_c"]
    assert row["status"] == "fail" and "ben_d rises by 0.2000" in row["detail"]


def test_a_total_that_adds_a_zero_component_twice_fails():
    """Baseline identities hold while tax_b is zero; the response gives it away."""
    formulas = model(contains=False)
    formulas["tax_b"] = lambda f: 0 * f("x")
    formulas["gov_tax"] = lambda f: f("tax_a") + 2 * f("tax_b")
    _, result = run(formulas, partition(["tax_a", "tax_b"]))
    row = by_variable(result)["tax_b"]
    assert row["coefficients"]["gov_tax"] == pytest.approx(1)
    assert row["model_coefficients"]["gov_tax"] == pytest.approx(2)
    assert (
        row["status"] == "fail"
        and "the model's gov_tax moves by 2.0000" in row["detail"]
    )


def test_a_means_test_fall_cannot_hide_a_benefit_that_contains_another():
    """ben_e contains ben_c while ben_d falls pound for pound: the net is 1."""
    formulas = model(interaction=-1.0)
    formulas["ben_e"] = lambda f: 50 + f("ben_c")
    formulas["gov_spending"] = lambda f: f("ben_c") + f("ben_d") + f("ben_e")
    _, result = run(formulas, partition(["tax_a"], ["ben_c", "ben_d", "ben_e"]))
    row = by_variable(result)["ben_c"]
    assert row["coefficients"]["gov_spending"] == pytest.approx(1)
    assert row["status"] == "fail" and "ben_e rises by 1.0000" in row["detail"]


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
    assert row["status"] == "fail" and "ben_e rises" in row["detail"]


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
    assert row["status"] == "fail" and "contains it" in row["detail"]


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
