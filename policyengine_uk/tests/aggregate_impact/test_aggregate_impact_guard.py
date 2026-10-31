"""The counted-once check, on a small fake simulation whose formulas are known.

The fake implements only the simulation API the check uses, so each case
controls exactly which component contains or reads which.
"""

from types import SimpleNamespace

import numpy as np
import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st

from policyengine_uk.utils.aggregate_impact.guard import (
    _response_slack,
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
        values = np.asarray(values, dtype=float)
        # As policyengine-core's Holder does: it refuses NaN, not infinity.
        if np.isnan(values).any():
            raise ValueError(
                f'Unable to set value for variable "{variable}", as the input '
                "contains NaN values."
            )
        self.inputs[(variable, str(period))] = values

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


@pytest.mark.parametrize(
    "tax_a",
    [
        lambda f: 1 / (6 - f("tax_b")),
        lambda f: -1 / (6 - f("tax_b")),
        lambda f: np.sqrt(5 - f("tax_b")),
    ],
    ids=["infinite", "negative infinite", "not a number"],
)
def test_a_non_finite_undeclared_tax_response_fails(tax_a):
    """tax_b starts at 5, so tax_a is finite until the guard adds 1 to tax_b."""
    formulas = model(contains=False)
    formulas["tax_a"] = tax_a
    with np.errstate(divide="ignore", invalid="ignore"):
        _, result = run(formulas, partition(["tax_a", "tax_b"]), x=(1,), weights=(1,))
    row = by_variable(result)["tax_b"]
    assert row["status"] == "fail" and ("tax_a", "moves") in kinds(row)
    assert row["mediated"] == []
    assert by_variable(result)["tax_a"]["status"] == "pass"
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


def movement(expected, response, tax_level=0.0):
    """Households where each movement path finds tax_a moving with tax_b.

    Returns the masks of the initial screen, the first held check and the
    held-slope check, each given ``response`` as tax_a's observed change.
    """
    expected = np.asarray(expected, dtype=float)
    response = np.asarray(response, dtype=float)
    scales = np.full_like(expected, tax_level)
    where = np.ones_like(expected, dtype=bool)
    # Opposite infinite responses sum to a NaN coefficient for the report.
    with np.errstate(invalid="ignore"):
        verdict = judge_total(
            total="gov_tax",
            is_tax=True,
            component="tax_b",
            own_variable="tax_b",
            declared_double_count=False,
            zero_baseline=False,
            weights=np.ones_like(expected),
            expected=expected,
            head_changes={"tax_b": expected, "tax_a": response},
            head_scales={"tax_b": scales, "tax_a": scales},
            model_change=None,
            model_scale=None,
            allowed_readers=[],
        )
    initial = np.zeros_like(where)
    for found in verdict["problems"]:
        assert (found["head"], found["kind"]) == ("tax_a", "moves")
        initial = initial | found["where"]
    slack = _slack(scales)
    return (
        initial,
        still_breaks("moves", where, expected, slack, response),
        breaks_on_slope("moves", where, expected, slack, response),
    )


@pytest.mark.parametrize(
    "added, response, direct, on_slope",
    [
        (0, 0, False, False),
        (0, 1e-9, True, True),
        (1, 0, False, False),
        (1, 0.019, False, False),
        (1, 0.021, True, False),
        (1, 0.03, True, False),
        (1, 0.039, True, False),
        (1, 0.041, True, True),
        (2, 0.03, False, False),
        (2, 0.041, True, False),
        (2, 0.081, True, True),
    ],
)
def test_movement_allowances_are_2_and_4_percent_of_the_addition(
    added, response, direct, on_slope
):
    """The initial and first held checks allow 2% of what was added; the held
    slope, a two-point difference, allows 4%."""
    for tax_level in (0, 1e9):
        for sign in (-1, 1):
            found = movement([added], [sign * response], tax_level)
            assert [bool(mask[0]) for mask in found] == [direct, direct, on_slope]


@settings(max_examples=60, deadline=None)
@given(
    perturbation=st.one_of(st.just(0.0), st.floats(1e-6, 1e6)),
    tax_level=st.floats(0, 1e9),
    sign=st.sampled_from([-1.0, 1.0]),
)
@example(perturbation=0.0, tax_level=0.0, sign=1.0)
@example(perturbation=1.0, tax_level=1e9, sign=-1.0)
def test_movement_starts_exactly_beyond_the_response_allowance(
    perturbation, tax_level, sign
):
    """Issue #2606's allowance: a response r moves when |r| exceeds 0.02
    |expected| + 2e-6 |r|, or twice that for the held slope. Solving for |r|
    gives each boundary."""
    for allowances, paths in ((1, (0, 1)), (2, (2,))):
        boundary = 0.02 * allowances * perturbation / (1 - 2e-6 * allowances)
        # Where nothing was added, any movement counts.
        responses = [boundary * (1 - 1e-9), max(boundary * (1 + 1e-9), 1e-9)]
        found = movement([perturbation] * 2, np.multiply(sign, responses), tax_level)
        for path in paths:
            assert found[path].tolist() == [False, True]


@settings(max_examples=60, deadline=None)
@given(
    response=st.sampled_from([np.inf, -np.inf, np.nan]),
    perturbation=st.floats(0, 1e6),
    tax_level=st.floats(0, 1e9),
)
def test_a_non_finite_response_is_movement_on_every_path(
    response, perturbation, tax_level
):
    found = movement([perturbation], [response], tax_level)
    assert [bool(mask[0]) for mask in found] == [True, True, True]


@settings(max_examples=100, deadline=None)
@given(
    households=st.lists(
        st.tuples(
            st.floats(0, 1e6),
            st.one_of(
                st.floats(-1e12, 1e12), st.sampled_from([np.inf, -np.inf, np.nan])
            ),
        ),
        min_size=1,
        max_size=8,
    ),
    tax_level=st.floats(0, 1e9),
)
def test_the_movement_paths_agree_and_the_held_slope_is_looser(households, tax_level):
    """The initial screen and the first held check apply the same rule; the
    held slope finds a subset of their households, never sparing a non-finite
    response, and the sign of a response never matters."""
    expected, response = (np.array(column) for column in zip(*households))
    found = movement(expected, response, tax_level)
    initial, held, slope = found
    assert np.array_equal(initial, held)
    assert not (slope & ~held).any()
    assert slope[~np.isfinite(response)].all()
    for mask, mirrored in zip(found, movement(expected, -response, tax_level)):
        assert np.array_equal(mask, mirrored)


@settings(max_examples=100, deadline=None)
@given(
    households=st.lists(
        st.tuples(
            st.booleans(),
            st.floats(0, 1e6),
            st.one_of(
                st.floats(-1e12, 1e12), st.sampled_from([np.inf, -np.inf, np.nan])
            ),
        ),
        min_size=1,
        max_size=8,
    ),
)
def test_the_held_checks_stay_within_the_households_they_are_given(households):
    """A held check narrows the households it receives: it never adds one,
    however far the response moves there."""
    where, expected, response = (np.array(column) for column in zip(*households))
    slack = _slack(np.zeros_like(expected))
    everyone = np.ones_like(where)
    for check in (still_breaks, breaks_on_slope):
        assert np.array_equal(
            check("moves", where, expected, slack, response),
            where & check("moves", everyone, expected, slack, response),
        )


# Issue #2759: a response that is not finite breaks every rule, on every
# path, and a head the check cannot hold at a finite value clears nothing.

# Each is finite while ``value`` is ``at`` and not finite once the check adds
# 1 to it.
NOT_FINITE = {
    "infinite": lambda value, at: 1 / (at + 1 - value),
    "negative infinite": lambda value, at: -1 / (at + 1 - value),
    "not a number": lambda value, at: np.sqrt(at - value),
}


def run_not_finite(formulas, part, **kwargs):
    """``run``, without numpy's warnings about the values that turn."""
    with np.errstate(divide="ignore", invalid="ignore"):
        return run(formulas, part, **kwargs)


def messages(row):
    return {(p["head"], p["kind"]): p["message"] for p in row.get("problems") or []}


@pytest.mark.parametrize("response", NOT_FINITE)
def test_a_declared_reader_that_turns_not_finite_fails(response):
    """tax_a declares its read of tax_b, which starts at 5."""
    turn = NOT_FINITE[response]
    formulas = model(contains=False)
    formulas["tax_a"] = lambda f: turn(f("tax_b"), 5.0)
    part = partition(["tax_a", "tax_b"], reads={"tax_a": ["tax_b"]})
    _, result = run_not_finite(formulas, part, x=(1,), weights=(1,))
    row = by_variable(result)["tax_b"]
    assert row["status"] == "fail"
    assert messages(row)[("tax_a", "contains")] == (
        "gov_tax: tax_a rises one for one with tax_b, or is not finite, "
        "in fewer than 10 households"
    )
    assert not np.isfinite(row["responses"]["gov_tax"]["tax_a"])
    assert by_variable(result)["tax_a"]["status"] == "pass"
    assert result["reset_reproduces_baseline"]


@pytest.mark.parametrize("response", NOT_FINITE)
def test_a_benefit_that_turns_not_finite_fails(response):
    """ben_d reads ben_c, which starts at 100, without declaring it."""
    turn = NOT_FINITE[response]
    formulas = model(interaction=0.0)
    formulas["ben_d"] = lambda f: 200 + turn(f("ben_c"), 100.0)
    part = partition(["tax_a"], ["ben_c", "ben_d"])
    _, result = run_not_finite(formulas, part, x=(1,), weights=(1,))
    row = by_variable(result)["ben_c"]
    assert row["status"] == "fail"
    assert messages(row)[("ben_d", "rises")] == (
        "gov_spending: ben_d rises, or is not finite, when ben_c does "
        "in fewer than 10 households"
    )
    assert result["reset_reproduces_baseline"]


@pytest.mark.parametrize("response", NOT_FINITE)
def test_a_model_total_that_turns_not_finite_fails(response):
    """gov_tax adds a term that is zero at baseline; its heads stay finite."""
    turn = NOT_FINITE[response]
    formulas = model(contains=False)
    formulas["gov_tax"] = lambda f: (
        f("tax_a") + f("tax_b") + turn(f("tax_b"), 5.0) - turn(5.0, 5.0)
    )
    _, result = run_not_finite(
        formulas, partition(["tax_a", "tax_b"]), x=(1,), weights=(1,)
    )
    row = by_variable(result)["tax_b"]
    assert row["status"] == "fail" and kinds(row) == {("gov_tax", "model_total")}
    assert messages(row)[("gov_tax", "model_total")].startswith(
        "gov_tax: the model's gov_tax moves by other than its heads, or is not "
        "finite, when tax_b does"
    )
    assert result["reset_reproduces_baseline"]


@pytest.mark.parametrize("response", NOT_FINITE)
def test_a_double_count_whose_container_turns_not_finite_fails(response):
    """tax_a contains tax_b (declared), plus a term that turns not finite.
    The check cannot tell whether tax_a still contains tax_b, so it does not
    call the declaration stale."""
    turn = NOT_FINITE[response]
    formulas = model(contains=True)
    formulas["tax_a"] = lambda f: (
        0.1 * f("x") + f("tax_b") + turn(f("tax_b"), 5.0) - turn(5.0, 5.0)
    )
    part = partition(["tax_a"], [], [("tax_b", "tax_a")])
    _, result = run_not_finite(formulas, part, x=(1,), weights=(1,))
    (double_count,) = result["double_counts"]
    assert double_count["status"] == "fail" and double_count["not_finite"]
    assert double_count["detail"] == (
        "tax_a is not finite when tax_b rises, so the check cannot show that "
        "it still contains tax_b"
    )
    assert by_variable(result)["tax_b"]["status"] == "fail"
    assert result["reset_reproduces_baseline"]


CONTAINS_OR_NOT_FINITE = (
    "gov_tax: tax_a rises one for one with tax_b, or is not finite, "
    "in fewer than 10 households"
)


def test_a_reader_that_turns_nan_only_when_held_fails_and_says_so():
    """tax_a declares reads of tax_b and tax_c, and responds with a slope of
    0.5 while tax_c moves with tax_b. Holding tax_c at its baseline makes
    tax_a NaN, so the held measurement fails it."""
    formulas = model(contains=False)
    formulas["tax_c"] = lambda f: f("tax_b") + 0 * f("x")
    formulas["tax_a"] = lambda f: 0.5 * f("tax_b") + np.sqrt(f("tax_c") - f("tax_b"))
    formulas["gov_tax"] = lambda f: f("tax_a") + f("tax_b") + f("tax_c")
    part = partition(["tax_a", "tax_b", "tax_c"], reads={"tax_a": ["tax_b", "tax_c"]})
    _, result = run_not_finite(formulas, part, x=(1,), weights=(1,))
    row = by_variable(result)["tax_b"]
    assert messages(row)[("tax_a", "contains")] == CONTAINS_OR_NOT_FINITE
    assert result["reset_reproduces_baseline"]


@pytest.mark.parametrize("response", NOT_FINITE)
def test_a_containment_found_with_a_response_that_is_not_finite_says_so(response):
    """In the first household tax_a turns not finite. In the second it
    responds with a slope of 0.5, which holding tax_c shows is one for one.
    The one problem covering both households says the response may not be
    finite."""
    turn = NOT_FINITE[response]
    first_only = np.array([True, False])
    formulas = model(contains=False)
    formulas["tax_c"] = lambda f: f("tax_b") + 0 * f("x")
    formulas["tax_a"] = lambda f: np.where(
        first_only, turn(f("tax_b"), 5.0), f("tax_b") - 0.5 * f("tax_c")
    )
    formulas["gov_tax"] = lambda f: f("tax_a") + f("tax_b") + f("tax_c")
    part = partition(["tax_a", "tax_b", "tax_c"], reads={"tax_a": ["tax_b", "tax_c"]})
    _, result = run_not_finite(formulas, part, x=(1, 1), weights=(1, 1))
    row = by_variable(result)["tax_b"]
    assert messages(row)[("tax_a", "contains")] == CONTAINS_OR_NOT_FINITE
    (contains,) = [p for p in row["problems"] if p["kind"] == "contains"]
    assert contains["households"] == 2
    assert result["reset_reproduces_baseline"]


@pytest.mark.parametrize("route", ["direct", "mediated"])
@pytest.mark.parametrize("response", NOT_FINITE)
def test_two_heads_that_turn_not_finite_fail_by_name(response, route):
    """Issue #2759: tax_c, and tax_a directly or through tax_c, turn not
    finite when tax_b rises. The engine refuses NaN as an input, so the
    check cannot hold either head at its value after the first point. It
    names both, and goes on to check tax_c."""
    turn = NOT_FINITE[response]
    formulas = model(contains=False)
    formulas["tax_c"] = lambda f: turn(f("tax_b"), 5.0)
    if route == "direct":
        formulas["tax_a"] = lambda f: turn(f("tax_b"), 5.0)
    else:
        formulas["tax_a"] = lambda f: 2 * f("tax_c")
    formulas["gov_tax"] = lambda f: f("tax_a") + f("tax_b") + f("tax_c")
    reads = {} if route == "direct" else {"tax_a": ["tax_c"]}
    part = partition(["tax_a", "tax_b", "tax_c"], reads=reads)
    _, result = run_not_finite(formulas, part, x=(1,), weights=(1,))
    rows = by_variable(result)
    assert list(rows) == ["tax_a", "tax_b", "tax_c"]
    assert rows["tax_b"]["status"] == "fail" and rows["tax_b"]["mediated"] == []
    assert {("tax_a", "moves"), ("tax_c", "moves")} <= kinds(rows["tax_b"])
    assert rows["tax_a"]["status"] == rows["tax_c"]["status"] == "pass"
    assert result["reset_reproduces_baseline"]


@pytest.mark.parametrize("monthly", [False, True], ids=["yearly", "monthly"])
def test_two_heads_that_turn_nan_on_core_fail_by_name_and_the_check_goes_on(
    monthly,
):
    """Issue #2759, on policyengine-core: tax_a and tax_c are each
    sqrt(5 - tax_b), and tax_b starts at 5 (a year, or each month). Holding
    one at its NaN value after the first point raised the engine's
    ValueError; the check now names both heads and checks every other
    component."""
    from policyengine_core.country_template import CountryTaxBenefitSystem
    from policyengine_core.country_template.entities import Household
    from policyengine_core.periods import MONTH, YEAR as YEARLY
    from policyengine_core.simulations import Simulation
    from policyengine_core.variables import Variable

    def household_variable(name, formula=None, default=0.0, definition_period=None):
        attributes = {
            "label": name,
            "value_type": float,
            "entity": Household,
            "definition_period": definition_period or (MONTH if monthly else YEARLY),
            "default_value": default,
        }
        if formula is not None:
            attributes["formula"] = lambda household, period: formula(
                lambda other: household(other, period)
            )
        return type(name, (Variable,), attributes)

    system = CountryTaxBenefitSystem()
    for variable in (
        household_variable("tax_b", default=5.0),
        household_variable("tax_a", lambda f: np.sqrt(5 - f("tax_b"))),
        household_variable("tax_c", lambda f: np.sqrt(5 - f("tax_b"))),
        household_variable(
            "gov_tax",
            lambda f: f("tax_a") + f("tax_b") + f("tax_c"),
            definition_period=YEARLY,
        ),
        household_variable("household_weight", definition_period=YEARLY),
    ):
        system.update_variable(variable)
    sim = Simulation(
        tax_benefit_system=system,
        situation={
            "persons": {"p": {}},
            "households": {
                "h": {"parents": ["p"], "household_weight": {str(YEAR): 1.0}}
            },
        },
    )
    with np.errstate(invalid="ignore"):
        result = counted_once(sim, partition(["tax_a", "tax_b", "tax_c"]), YEAR, 1e-6)
    rows = by_variable(result)
    assert list(rows) == ["tax_a", "tax_b", "tax_c"]
    assert rows["tax_b"]["status"] == "fail"
    assert {("tax_a", "moves"), ("tax_c", "moves")} <= kinds(rows["tax_b"])
    assert "tax_a moves" in rows["tax_b"]["detail"]
    assert "tax_c moves" in rows["tax_b"]["detail"]
    assert rows["tax_a"]["status"] == rows["tax_c"]["status"] == "pass"
    assert result["reset_reproduces_baseline"]
    assert np.isfinite(sim.calculate("tax_a", YEAR)).all()


@settings(max_examples=40, deadline=None)
@given(
    turns=st.lists(st.sampled_from([None, *NOT_FINITE]), min_size=3, max_size=3),
    reads=st.lists(st.booleans(), min_size=3, max_size=3),
    chained=st.booleans(),
)
def test_the_check_names_every_head_that_turns_not_finite_and_goes_on(
    turns, reads, chained
):
    """Whichever tax heads turn not finite, directly or (tax_d through tax_c)
    by another head, the check names each and no finite head, and checks
    every component."""
    heads = ["tax_a", "tax_c", "tax_d"]
    formulas = model(contains=False)
    for head, turn in zip(heads, turns):
        formulas[head] = (
            (lambda f: 0.1 * f("x"))
            if turn is None
            else (lambda f, turn=NOT_FINITE[turn]: turn(f("tax_b"), 5.0))
        )
    declared = {head: ["tax_b"] for head, read in zip(heads, reads) if read}
    if chained:
        formulas["tax_d"] = lambda f: 2 * f("tax_c")
        declared["tax_d"] = declared.get("tax_d", []) + ["tax_c"]
    formulas["gov_tax"] = lambda f: f("tax_b") + sum(f(head) for head in heads)
    turned = {head for head, turn in zip(heads, turns) if turn is not None}
    if chained:
        turned = (turned - {"tax_d"}) | ({"tax_d"} if "tax_c" in turned else set())
    _, result = run_not_finite(
        formulas, partition(["tax_b", *heads], reads=declared), x=(1,), weights=(1,)
    )
    rows = by_variable(result)
    assert list(rows) == ["tax_b", *heads]
    named = {head for head, kind in kinds(rows["tax_b"]) if head in heads}
    assert named == turned
    for head, kind in kinds(rows["tax_b"]):
        if head in heads:
            assert kind == (
                "contains" if "tax_b" in declared.get(head, []) else "moves"
            )
    assert (rows["tax_b"]["status"] == "fail") == bool(turned)
    assert all(rows[head]["status"] == "pass" for head in heads)
    assert result["reset_reproduces_baseline"]


CHECKS = (
    "own_head",
    "contains",
    "contains, first point",
    "contains, second point",
    "rises",
    "model_total",
)


def judged(check, expected, response, tax_level=0.0):
    """Households where judge_total finds ``check`` broken, given
    ``response`` as the change of the head (or total) that check judges.

    "contains, first point" gives ``response`` as tax_a's change at the first
    point, then 2 per unit added; "contains, second point" gives no change at
    the first point and ``response`` at the second.
    """
    expected = np.asarray(expected, dtype=float)
    response = np.asarray(response, dtype=float)
    zeros = np.zeros_like(expected)
    scales = np.full_like(expected, tax_level)
    own = response if check == "own_head" else expected
    first = {
        "own_head": zeros,
        "model_total": zeros,
        "contains, second point": zeros,
    }.get(check, response)
    second_changes = {
        "contains, first point": {"tax_a": 2 * expected},
        "contains, second point": {"tax_a": response},
    }.get(check)
    with np.errstate(invalid="ignore"):
        verdict = judge_total(
            total="gov_tax",
            is_tax=check != "rises",
            component="tax_b",
            own_variable="tax_b",
            declared_double_count=False,
            zero_baseline=False,
            weights=np.ones_like(expected),
            expected=expected,
            head_changes={"tax_b": own, "tax_a": first},
            head_scales={"tax_b": scales, "tax_a": scales},
            model_change=response if check == "model_total" else None,
            model_scale=scales,
            allowed_readers=["tax_a"] if check.startswith("contains") else [],
            second_changes=second_changes,
        )
    if check == "own_head":
        found = verdict["own_problem"]
        return zeros.astype(bool) if found is None else found["where"]
    head, kind = {
        "rises": ("tax_a", "rises"),
        "model_total": ("gov_tax", "model_total"),
    }.get(check, ("tax_a", "contains"))
    found = zeros.astype(bool)
    for problem in verdict["problems"]:
        assert (problem["head"], problem["kind"]) == (head, kind)
        found = found | problem["where"]
    return found


@pytest.mark.parametrize(
    "value", [np.inf, -np.inf, np.nan], ids=["infinite", "negative", "nan"]
)
@pytest.mark.parametrize("check", CHECKS)
@settings(max_examples=30, deadline=None)
@given(
    households=st.lists(
        st.tuples(st.one_of(st.just(0.0), st.floats(1e-6, 1e6)), st.floats(-1e9, 1e9)),
        min_size=1,
        max_size=6,
    ),
    at=st.integers(0, 5),
    tax_level=st.floats(0, 1e9),
)
def test_a_non_finite_response_fails_every_check(
    check, value, households, at, tax_level
):
    """Issue #2759: in every household where the judged response is
    infinite or NaN, the check fails, whatever else the households hold."""
    expected, response = (np.array(column) for column in zip(*households))
    response[at % len(response)] = value
    found = judged(check, expected, response, tax_level)
    assert found[~np.isfinite(response)].all()


@pytest.mark.parametrize(
    "value", [np.inf, -np.inf, np.nan], ids=["infinite", "negative", "nan"]
)
@pytest.mark.parametrize("kind", ["contains", "rises", "moves"])
@settings(max_examples=30, deadline=None)
@given(
    households=st.lists(
        st.tuples(
            st.booleans(),
            st.one_of(st.just(0.0), st.floats(1e-6, 1e6)),
            st.floats(-1e9, 1e9),
        ),
        min_size=1,
        max_size=6,
    ),
    at=st.integers(0, 5),
)
def test_a_non_finite_held_measurement_breaks_every_rule(kind, value, households, at):
    """Both held measurements fail a household of those they receive where
    the head's response, or a point of its slope, is not finite, and never
    add a household they were not given."""
    where, expected, finite = (np.array(column) for column in zip(*households))
    response = finite.copy()
    response[at % len(response)] = value
    slack = _slack(np.zeros_like(expected))
    with np.errstate(invalid="ignore"):
        found = [
            still_breaks(kind, where, expected, slack, response),
            breaks_on_slope(kind, where, expected, slack, response),
        ]
        if kind == "contains":
            found += [
                still_breaks(kind, where, expected, slack, response, finite),
                still_breaks(kind, where, expected, slack, finite, response),
            ]
    for mask in found:
        assert not (mask & ~where).any()
        assert mask[where & ~np.isfinite(response)].all()


def finite_rule(kind, response, expected, slack, allowances=1):
    """Each rule as #2758 left it, which every finite response still meets."""
    allowance = allowances * _response_slack(response, expected)
    if kind == "contains":
        return np.abs(response - expected) <= allowance
    if kind == "rises":
        return response > allowances * slack
    return np.abs(response) > allowance


FINITE = st.floats(-1e9, 1e9)


def near(expected):
    """A finite response, often within a few percent of 0 or of a multiple of
    what was added, where the rules' boundaries lie."""
    return st.one_of(
        FINITE,
        st.tuples(
            st.sampled_from([0.0, 1.0, -1.0, 2.0, 0.5]), st.floats(-0.1, 0.1)
        ).map(lambda t: t[0] * expected * (1 + t[1]) + t[1]),
    )


@st.composite
def finite_households(draw):
    expected = draw(st.one_of(st.just(0.0), st.floats(1e-6, 1e6)))
    return (
        expected,
        # Household weights: none, or at least a thousandth.
        draw(st.one_of(st.just(0.0), st.floats(1e-3, 1e4))),
        draw(st.floats(0, 1e9)),
        *(draw(near(expected)) for _ in range(6)),
    )


@settings(max_examples=150, deadline=None)
@given(
    households=st.lists(finite_households(), min_size=1, max_size=6),
    is_tax=st.booleans(),
    declared=st.booleans(),
    zero_baseline=st.booleans(),
    two_points=st.booleans(),
    double_count=st.booleans(),
)
def test_finite_responses_keep_every_verdict(
    households, is_tax, declared, zero_baseline, two_points, double_count
):
    """Differential: on finite responses, judge_total and both held checks
    give exactly what #2758's rules give, household by household, with the
    same messages and coefficients."""
    columns = [np.array(column) for column in zip(*households)]
    expected, weights, scales, own, read, second, other, model_change, held = columns
    perturbed = expected > 0
    head_changes = {"tax_b": own, "tax_a": read, "tax_c": other}
    second_changes = {"tax_a": second, "tax_c": other + held} if two_points else None
    allowed = ["tax_a"] if declared else []
    verdict = judge_total(
        total="gov_tax",
        is_tax=is_tax,
        component="tax_b",
        own_variable="tax_b",
        declared_double_count=double_count,
        zero_baseline=zero_baseline,
        weights=weights,
        expected=expected,
        head_changes=head_changes,
        head_scales={v: scales for v in head_changes},
        model_change=model_change,
        model_scale=scales,
        allowed_readers=allowed,
        second_changes=second_changes,
    )
    slack = _slack(scales)
    want, screens = {}, {}
    texts = {
        "contains": "{} rises one for one with tax_b, so it contains it,",
        "moves": "{} moves when tax_b does",
        "rises": "{} rises when tax_b does",
    }
    for head, change in head_changes.items():
        if head == "tax_b":
            own_off = np.abs(change - expected) > slack
        elif head in allowed or (zero_baseline and not is_tax):
            if two_points:
                slope = second_changes[head] - change
                containing = perturbed & finite_rule(
                    "contains", slope, expected, slack, 2
                )
                screens[(head, "contains")] = (
                    perturbed
                    & (np.abs(slope) > 2 * _response_slack(slope, expected))
                    & ~containing
                )
            else:
                containing = perturbed & finite_rule(
                    "contains", change, expected, slack
                )
            want[(head, "contains")] = containing
        elif is_tax:
            want[(head, "moves")] = finite_rule("moves", change, expected, slack)
        else:
            want[(head, "rises")] = finite_rule("rises", change, expected, slack)
    heads_change = own + read + other + (expected if double_count else 0)
    want[("gov_tax", "model_total")] = np.abs(model_change - heads_change) > slack
    texts["model_total"] = (
        "the model's {} moves by other than its heads when tax_b does"
    )
    want = {key: mask for key, mask in want.items() if mask.any()}
    screens = {key: mask for key, mask in screens.items() if mask.any()}
    got = {(p["head"], p["kind"]): p for p in verdict["problems"]}
    assert set(got) == set(want)
    for (head, kind), mask in want.items():
        assert np.array_equal(got[(head, kind)]["where"], mask)
        assert got[(head, kind)]["message"].startswith(
            f"gov_tax: {texts[kind].format(head)} in "
        )
    assert {
        (s["head"], s["kind"]): s["where"].tolist() for s in verdict["screens"]
    } == {key: mask.tolist() for key, mask in screens.items()}
    if own_off.any():
        assert np.array_equal(verdict["own_problem"]["where"], own_off)
    else:
        assert verdict["own_problem"] is None
    added = float(np.sum(weights * expected))
    responses = {
        v: float(np.sum(weights * c)) / added if added else 0.0
        for v, c in head_changes.items()
    }
    assert verdict["responses"] == responses
    assert np.array_equal(
        verdict["coefficient"], float(sum(responses.values())), equal_nan=True
    )
    where = np.ones_like(perturbed)
    for kind in ("contains", "rises", "moves"):
        assert np.array_equal(
            still_breaks(kind, where, expected, slack, read),
            finite_rule(kind, read, expected, slack),
        )
        assert np.array_equal(
            breaks_on_slope(kind, where, expected, slack, read),
            finite_rule(kind, read, expected, slack, 2),
        )
    assert np.array_equal(
        still_breaks("contains", where, expected, slack, read, second),
        finite_rule("contains", second - read, expected, slack, 2),
    )


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
