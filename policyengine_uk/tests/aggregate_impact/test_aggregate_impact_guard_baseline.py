"""The counted-once check where a head, a model total or a component is not
finite at baseline (#2773), on the fake simulations of
``test_aggregate_impact_guard`` and on policyengine-core.

Such a value has no change to read. The check names each variable it could
not read once, as a failure of a ``finite:`` check; it fails no component for
it, never gives the engine NaN, and judges every other reading as before.
``counted_once_base_reference`` holds the check as it stood before: every
model whose heads and totals are finite at baseline must publish exactly what
it published.
"""

import json
from types import SimpleNamespace

import counted_once_base_reference as reference
import numpy as np
import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st
from test_aggregate_impact_guard import (
    GATED,
    HEADS_OF,
    MEDIATED_NAN,
    MEDIATED_NAN_READS,
    OVERLAP,
    READS,
    SHAPES,
    YEAR,
    EntitySim,
    FakeSim,
    by_variable,
    core_counted_once,
    declared_reads,
    gated_taxes,
    household_by_household,
    kinds,
    mediated_in_two_totals,
    messages,
    model,
    overlap_model,
    partition,
    run_not_finite,
    shapes_formulas,
    two_tax_totals,
)

from policyengine_uk.utils.aggregate_impact import guard, measure, render
from policyengine_uk.utils.aggregate_impact.compare import (
    ALWAYS_BLOCKING_PREFIXES,
    classify_check,
)

NOT_FINITE_VALUES = [np.nan, np.inf, -np.inf]


def named(result):
    """{variable: head id} of what the result says is not finite at baseline."""
    return {
        item["variable"]: item["head"]
        for item in result.get("not_finite_at_baseline", [])
    }


def note(variable, where="fewer than 10 households"):
    return (
        f"{variable} is not finite at baseline in {where}, so the counted-once "
        "check could not confirm it there"
    )


def recorded(result):
    rec = measure.Recorder()
    measure.record_guard_checks(rec, result)
    return rec.checks


# tax_a is sqrt(-1): NaN at baseline, whatever tax_b does.
NAN_TAX_A = {
    "tax_b": None,
    "tax_a": lambda f, period: np.sqrt(-1 + 0 * f("tax_b")),
}


@pytest.mark.parametrize("monthly", [False, True], ids=["yearly", "monthly"])
def test_a_component_nan_at_baseline_is_named_and_never_given_to_the_engine(
    monthly,
):
    """Issue #2773, case 1, on policyengine-core. Raising tax_a, NaN at
    baseline, gave the engine NaN, and the check stopped with "ValueError:
    Unable to set value for variable "tax_a", as the input contains NaN
    values." Now the check raises no unit where tax_a is not finite, so it
    skips tax_a, which has no other unit, and passes tax_b. It names tax_a,
    and gov_tax, which adds it, once each."""
    sim, result = core_counted_once(NAN_TAX_A, partition(["tax_a", "tax_b"]), monthly)
    rows = by_variable(result)
    assert list(rows) == ["tax_a", "tax_b"]
    assert rows["tax_a"]["status"] == "skipped"
    assert rows["tax_a"]["detail"] == (
        "the check could raise it only in households with no weight or where it "
        "is not finite at baseline"
    )
    assert rows["tax_b"]["status"] == "pass" and rows["tax_b"]["detail"] == ""
    assert named(result) == {"tax_a": "tax_a", "gov_tax": None}
    assert [item["message"] for item in result["not_finite_at_baseline"]] == [
        note("tax_a"),
        note("gov_tax"),
    ]
    assert result["reset_reproduces_baseline"]
    assert np.isnan(sim.calculate("tax_a", YEAR)).all()


def test_holding_a_head_nan_at_baseline_raises_nothing():
    """Issue #2773, case 2: tax_c is tax_b, so it moves with tax_b. To measure
    tax_c again, the check held tax_a at its baseline, NaN, and the engine
    raised the same ValueError. Now it leaves tax_a to its formula, which
    gives it back NaN, so tax_a is held at its baseline and the check finds
    tax_c moving with tax_b, as it does."""
    formulas = {**NAN_TAX_A, "tax_c": lambda f, period: f("tax_b")}
    _, result = core_counted_once(
        formulas,
        partition(["tax_a", "tax_b", "tax_c"]),
        False,
        variables_to_check=["tax_b"],
    )
    row = by_variable(result)["tax_b"]
    assert messages(row) == {
        ("tax_c", "moves"): (
            "gov_tax: tax_c moves when tax_b does in fewer than 10 households"
        )
    }
    (problem,) = row["problems"]
    assert problem["heads_not_held"] == [] and problem["households_not_held"] == 0
    assert "heads_not_held_at_baseline" not in problem
    assert not problem["not_finite"] and not row["heads_held_skipped"]
    assert named(result) == {"tax_a": "tax_a", "gov_tax": None}
    assert result["reset_reproduces_baseline"]


def test_a_head_nan_at_baseline_fails_no_component_it_ignores():
    """Issue #2773, cases 3 and 4. Checking tax_b alone, the check read tax_a's
    change as NaN - NaN and failed tax_b with "gov_tax: tax_a moves, or is
    not finite, when tax_b does in fewer than 10 households" and "gov_tax:
    the model's gov_tax moves by other than its heads, or is not finite, when
    tax_b does in fewer than 10 households", and its reset check returned
    False. Now no rule reads tax_a, or gov_tax, which adds it, in that
    household: tax_b passes, its own head rising by exactly 1. No response or
    coefficient comes from a household that cannot be read, and the reset
    check finds tax_a NaN where it started."""
    _, result = core_counted_once(
        NAN_TAX_A,
        partition(["tax_a", "tax_b"]),
        False,
        variables_to_check=["tax_b"],
    )
    (row,) = result["components"]
    assert row["status"] == "pass" and row["problems"] == []
    assert row["responses"] == {"gov_tax": {"tax_b": 1.0}}
    assert row["coefficients"] == {"gov_tax": 1.0}
    assert row["model_coefficients"] == {}
    assert result["reset_reproduces_baseline"] is True
    assert named(result) == {"tax_a": "tax_a", "gov_tax": None}


class LastComputationSim(FakeSim):
    """FakeSim whose ``watched`` variable takes ``after`` the ``at``-th time
    it is computed: with ``at`` the count of a run that changed nothing, the
    final recomputation, which the reset check reads."""

    def __init__(self, formulas, inputs, weights, watched, after=None, at=None):
        super().__init__(formulas, inputs, weights)
        self.watched, self.after, self.at, self.computations = watched, after, at, 0

    def calculate(self, variable, period, unweighted=True, map_to=None):
        key = (variable, str(period))
        if variable == self.watched and key not in self.inputs | self.cache:
            self.computations += 1
            if self.computations == self.at:
                self.cache[key] = np.asarray(self.after, dtype=float)
        return super().calculate(variable, period, unweighted, map_to)


@pytest.mark.parametrize(
    "before, after, same",
    [
        ([np.nan, 1.0], [np.nan, 1.0], True),
        ([np.inf, 1.0], [np.inf, 1.0], True),
        ([1.0, 1.0], [np.nan, 1.0], False),
        ([np.nan, 1.0], [1.0, np.nan], False),
        ([np.nan, 1.0], [0.0, 1.0], False),
        ([np.inf, 1.0], [-np.inf, 1.0], False),
        ([np.nan, 1.0], [np.nan, 1.5], False),
    ],
)
def test_the_reset_check_matches_nan_only_with_nan_in_the_same_place(
    before, after, same
):
    """The reset check treats NaN as equal to NaN in the same household and to
    nothing else, so a value that turns NaN after the reset, or a NaN that
    moves, still counts as a change."""
    formulas = {
        "tax_b": lambda f: 5.0 + 0 * f("x"),
        "tax_a": lambda f: np.array(before) + 0 * f("x"),
        "gov_tax": lambda f: f("tax_a") + f("tax_b"),
    }
    part = partition(["tax_a", "tax_b"])

    def check(sim):
        snapshot = guard.snapshot_inputs(sim, part.component_variables())
        with np.errstate(invalid="ignore"):
            return guard.counted_once(sim, part, YEAR, 1e-6, snapshot)

    probe = LastComputationSim(formulas, {"x": (1, 1)}, (1, 1), "tax_a")
    assert check(probe)["reset_reproduces_baseline"]
    sim = LastComputationSim(
        formulas, {"x": (1, 1)}, (1, 1), "tax_a", after, probe.computations
    )
    assert check(sim)["reset_reproduces_baseline"] is same


# Three households of weights 1.5, 2 and 0.5; ``FIRST`` marks the first.
WEIGHTS = (1.5, 2.0, 0.5)
FIRST = np.array([True, False, False])


def run_three(formulas, part, **options):
    sim = FakeSim(formulas, {"x": (1000, 2000, 3000)}, WEIGHTS)
    snapshot = guard.snapshot_inputs(sim, part.component_variables())
    with np.errstate(divide="ignore", invalid="ignore"):
        return guard.counted_once(sim, part, YEAR, 1e-6, snapshot, **options)


@pytest.mark.parametrize("bad", NOT_FINITE_VALUES)
def test_a_head_not_finite_in_one_household_is_judged_in_the_others(bad):
    """tax_a contains tax_b, and is not finite at baseline in the first
    household. The check fails tax_b for tax_a in the other two, with their
    share of the weight, and reads neither tax_a nor gov_tax in the first."""
    formulas = model(contains=True)
    formulas["tax_a"] = lambda f: np.where(FIRST, bad, f("tax_b") + 0 * f("x"))
    result = run_three(formulas, partition(["tax_a", "tax_b"]))
    row = by_variable(result)["tax_b"]
    assert messages(row) == {
        ("tax_a", "moves"): (
            "gov_tax: tax_a moves when tax_b does in fewer than 10 households"
        )
    }
    (problem,) = row["problems"]
    assert problem["households"] == 2 and problem["share"] == pytest.approx(2.5 / 4)
    assert row["responses"]["gov_tax"] == {"tax_a": 1.0, "tax_b": 1.0}
    assert row["model_coefficients"] == {"gov_tax": 2.0}
    assert named(result) == {"tax_a": "tax_a", "gov_tax": None}
    assert result["not_finite_at_baseline"][0]["households"] == 1
    assert result["reset_reproduces_baseline"]


@pytest.mark.parametrize("bad", NOT_FINITE_VALUES)
def test_a_component_not_finite_in_one_household_is_checked_in_the_others(bad):
    """tax_a is not finite at baseline in the first household, and tax_c
    holds tax_a, or 3 where tax_a is not finite. Raising tax_a, the check
    sets the first household's tax_a to 0, which moves tax_c there by -3;
    it judges nothing there, and fails tax_a for tax_c in the other two."""
    formulas = model(contains=False)
    formulas["tax_a"] = lambda f: np.where(FIRST, bad, 0.1 * f("x"))
    formulas["tax_c"] = lambda f: np.where(np.isfinite(f("tax_a")), f("tax_a"), 3.0)
    formulas["gov_tax"] = lambda f: f("tax_a") + f("tax_b") + f("tax_c")
    result = run_three(
        formulas, partition(["tax_a", "tax_b", "tax_c"]), variables_to_check=["tax_a"]
    )
    (row,) = result["components"]
    assert row["units"] == 2
    assert kinds(row) == {("tax_c", "moves")}
    (problem,) = row["problems"]
    assert problem["households"] == 2 and problem["share"] == 1.0
    assert named(result) == {"tax_a": "tax_a", "gov_tax": None}
    assert result["reset_reproduces_baseline"]


def mediated_with(tax_n):
    """tax_a responds to tax_b only through tax_d, which declares its read of
    tax_b; tax_n, a tax no head reads, is ``tax_n``."""
    return {
        "tax_b": lambda f: 5.0 + 0 * f("x"),
        "tax_d": lambda f: 0.2 * f("tax_b"),
        "tax_a": lambda f: 0.5 * f("tax_d"),
        "tax_n": tax_n,
        "gov_tax": lambda f: f("tax_a") + f("tax_b") + f("tax_d") + f("tax_n"),
    }


MEDIATED = partition(["tax_b", "tax_d", "tax_a", "tax_n"], reads={"tax_d": ["tax_b"]})


@pytest.mark.parametrize("bad", NOT_FINITE_VALUES)
def test_a_held_head_not_finite_at_baseline_is_held_by_its_formula(bad):
    """tax_n, a tax no head reads, is not finite at baseline in the first
    household. Its formula gives it back its baseline in every held
    measurement, so the check holds it exactly and clears tax_a, which
    responds only through tax_d, in all three households: tax_b's result is
    the one it gets with tax_n finite."""
    result = run_three(
        mediated_with(lambda f: np.where(FIRST, bad, 7.0)),
        MEDIATED,
        variables_to_check=["tax_b"],
    )
    finite = run_three(
        mediated_with(lambda f: 7.0 + 0 * f("x")),
        MEDIATED,
        variables_to_check=["tax_b"],
    )
    (row,) = result["components"]
    assert row["status"] == "pass" and row["mediated"][0]["households"] == 3
    assert row == finite["components"][0]
    assert named(result) == {"tax_n": "tax_n", "gov_tax": None}
    assert "not_finite_at_baseline" not in finite


MOVES_WITH_TAX_B = (
    "the check could not hold tax_n, which is not finite at baseline in some "
    "households and moves there with tax_b"
)


def test_a_held_head_that_moves_leaves_only_those_households_unjudged():
    """tax_n is NaN at baseline in the first household and tax_b in the
    others, so it moves with tax_b there. Left to its formula in the held
    measurements, it gives back its baseline only in the first household,
    which the check judges: tax_a, carried by tax_d, is mediated there. In
    the other two, tax_a's failure stays, and the check could not confirm
    tax_d, a declared reader with a slope of 0.2; both name tax_n. tax_n
    fails as it contains tax_b."""
    result = run_three(
        mediated_with(lambda f: np.where(FIRST, np.nan, f("tax_b"))),
        MEDIATED,
        variables_to_check=["tax_b"],
    )
    (row,) = result["components"]
    assert messages(row) == {
        ("tax_n", "moves"): (
            "gov_tax: tax_n moves when tax_b does in fewer than 10 households"
        ),
        ("tax_a", "moves"): (
            "gov_tax: tax_a moves when tax_b does in fewer than 10 households (in "
            f"fewer than 10 of them {MOVES_WITH_TAX_B}, so it could not show that "
            "tax_a responds only through other heads)"
        ),
        ("tax_d", "unconfirmed"): (
            "gov_tax: tax_d responds to tax_b in fewer than 10 households where "
            f"{MOVES_WITH_TAX_B}, so it could not confirm whether tax_d contains "
            "tax_b"
        ),
    }
    assert {p["head"]: p["households"] for p in row["problems"]} == {
        "tax_n": 2,
        "tax_a": 2,
        "tax_d": 2,
    }
    for problem in row["problems"]:
        if problem["head"] != "tax_n":
            assert problem["heads_not_held_at_baseline"] == ["tax_n"]
            assert problem["households_not_held"] == 2
    (mediated,) = row["mediated"]
    assert (mediated["head"], mediated["households"]) == ("tax_a", 1)
    assert row["heads_not_held"] == {} and row["heads_held_skipped"]


def test_a_problem_names_heads_the_check_could_not_hold_for_either_reason():
    """One household: ben_c turns NaN once tax_b rises, and tax_n, NaN at
    baseline, turns 0. tax_a's failure names both, each with its reason."""
    formulas = mediated_with(lambda f: np.where(f("tax_b") > 5.5, 0.0, np.nan))
    formulas["ben_c"] = lambda f: np.sqrt(5 - f("tax_b"))
    formulas["gov_spending"] = lambda f: f("ben_c")
    part = partition(
        ["tax_b", "tax_d", "tax_a", "tax_n"], ["ben_c"], reads={"tax_d": ["tax_b"]}
    )
    _, result = run_not_finite(formulas, part, x=(1,), weights=(1,))
    row = by_variable(result)["tax_b"]
    assert messages(row)[("tax_a", "moves")] == (
        "gov_tax: tax_a moves when tax_b does in fewer than 10 households (in "
        "fewer than 10 of them the check could not hold ben_c, which is not "
        "finite there once tax_b rises, and tax_n, which is not finite at "
        "baseline in some households and moves there with tax_b, so it could "
        "not show that tax_a responds only through other heads)"
    )
    problem = next(p for p in row["problems"] if p["head"] == "tax_a")
    assert problem["heads_not_held"] == ["ben_c"]
    assert problem["heads_not_held_at_baseline"] == ["tax_n"]
    assert row["heads_not_held"]["tax_a"] == ["ben_c"]
    assert all(p["head"] != "tax_n" for p in row["problems"])


def test_a_model_total_not_finite_at_baseline_is_named_and_fails_no_component():
    """gov_tax adds a NaN term in the first household that no head holds. The
    check reads gov_tax in the other two only, fails no component for it,
    names it, and records it under finite:metrics."""
    formulas = model(contains=False)
    formulas["gov_tax"] = lambda f: f("tax_a") + f("tax_b") + np.where(FIRST, np.nan, 0)
    result = run_three(formulas, partition(["tax_a", "tax_b"]))
    assert all(row["status"] == "pass" for row in result["components"])
    assert named(result) == {"gov_tax": None}
    checks = recorded(result)
    assert checks["finite:metrics"]["failing"] == {
        f"counted_once:{YEAR}:gov_tax": f"2026-27: {note('gov_tax')}"
    }
    assert checks["finite:metrics"]["label"] == "Every reported figure is finite"


def declared_double_count(container):
    """tax_a contains tax_b, as the partition declares, and is ``container``
    of tax_b and x."""
    formulas = model(contains=True)
    formulas["tax_a"] = container
    return formulas, partition(["tax_a"], [], [("tax_b", "tax_a")])


def test_a_container_not_finite_in_one_household_is_judged_in_the_others():
    formulas, part = declared_double_count(
        lambda f: np.where(FIRST, np.nan, 0.1 * f("x") + f("tax_b"))
    )
    result = run_three(formulas, part)
    (row,) = result["double_counts"]
    assert row["status"] == "pass" and row["coefficient"] == pytest.approx(1.0)
    assert by_variable(result)["tax_b"]["status"] == "pass"


def test_a_container_not_finite_everywhere_skips_the_double_count():
    """The check cannot show that tax_a still contains tax_b, and says so; a
    finite: check names tax_a."""
    formulas, part = declared_double_count(lambda f: np.nan + f("tax_b"))
    result = run_three(formulas, part)
    (row,) = result["double_counts"]
    assert row["status"] == "skipped" and row["coefficient"] is None
    assert row["detail"] == (
        "tax_a is not finite at baseline in every household with weight where "
        "the check raised tax_b, so it cannot show that tax_a still contains tax_b"
    )
    checks = recorded(result)
    assert checks["double_count_present:tax_b"]["status"] == "skipped"
    assert checks["finite:tax_a"]["status"] == "fail"
    text = render._guard({"head": {"guard": measure.publishable_guard(result)}})
    assert (
        f"- declared double count `tax_b` not checked: {row['detail']} "
        f"({row['issue']})" in text
    )


def test_a_double_count_not_finite_everywhere_is_skipped_and_named():
    """tax_b, the declared double count, is NaN at baseline everywhere: the
    check skips it, says why, and names it under finite:metrics."""
    formulas, part = declared_double_count(lambda f: 0.1 * f("x") + f("tax_b"))
    formulas["tax_b"] = lambda f: np.nan + 0 * f("x")
    result = run_three(formulas, part)
    assert by_variable(result)["tax_b"]["status"] == "skipped"
    (row,) = result["double_counts"]
    assert row["status"] == "skipped" and row["detail"] == (
        "the check could raise tax_b only in households with no weight or where "
        "it is not finite at baseline, so it cannot show that tax_a still "
        "contains tax_b"
    )
    assert named(result) == {"tax_a": "tax_a", "gov_tax": None, "tax_b": None}
    assert set(recorded(result)["finite:metrics"]["failing"]) == {
        f"counted_once:{YEAR}:gov_tax",
        f"counted_once:{YEAR}:tax_b",
    }


def test_a_benefit_unit_not_finite_at_baseline_leaves_only_its_household():
    """ben_u, a benefit of each benefit unit, is NaN at baseline in the second
    household's second unit; ben_w, a household benefit, adds each unit's
    finite ben_u. Raising ben_u, the check judges neither the second
    household nor ben_u's change there, and fails ben_u for ben_w in the
    first and third households alone."""
    people = [(0, 0), (1, 1), (2, 1), (3, 2)]
    bad = np.array([False, False, True, False])
    formulas = {
        "tax_b": lambda f: 5.0 + 0 * f("x"),
        "gov_tax": lambda f: f("tax_b"),
        "ben_u": lambda f: np.where(bad, np.nan, 100.0),
        "ben_w": lambda f: sim.map_result(
            np.nan_to_num(f("ben_u")), "benunit", "household"
        ),
        "gov_spending": lambda f: (
            sim.map_result(f("ben_u"), "benunit", "household") + f("ben_w")
        ),
    }
    sim = EntitySim(formulas, {"x": (1, 1, 1)}, (1, 2, 4), {"ben_u": "benunit"}, people)
    part = partition(["tax_b"], ["ben_u", "ben_w"], entities={"ben_u": "benunit"})
    result = guard.counted_once(
        sim, part, YEAR, 1e-6, guard.snapshot_inputs(sim, part.component_variables())
    )
    row = by_variable(result)["ben_u"]
    assert row["units"] == 2
    (problem,) = row["problems"]
    assert (problem["head"], problem["kind"], problem["households"]) == (
        "ben_w",
        "rises",
        2,
    )
    assert problem["share"] == 1.0
    assert result["not_finite_at_baseline"][0] == {
        "variable": "ben_u",
        "head": "ben_u",
        "label": "ben_u",
        "households": 1,
        "message": note("ben_u"),
    }


def test_the_named_result_blocks_whatever_the_base_did():
    """A head not finite at baseline fails its own finite: check in a scope
    naming the year and the head, which a comparison blocks on even when
    the base fails it too. No counted-once check fails for it."""
    _, result = core_counted_once(NAN_TAX_A, partition(["tax_a", "tax_b"]), False)
    checks = recorded(result)
    scope = f"counted_once:{YEAR}:tax_a"
    assert checks["finite:tax_a"]["failing"] == {scope: f"2026-27: {note('tax_a')}"}
    assert checks["finite:tax_a"]["label"] == "tax_a is finite for every unit"
    assert checks["finite:tax_a"]["section"] == "finite"
    assert all(
        check["status"] != "fail"
        for check_id, check in checks.items()
        if check_id.startswith("counted_once:")
    )
    for check_id, check in checks.items():
        if check["status"] == "fail":
            assert check_id.startswith(ALWAYS_BLOCKING_PREFIXES)
            assert (
                classify_check("fail", "fail", True, check["failing"], check["failing"])
                == "regression"
            )


@pytest.mark.parametrize("households", [3, 12])
def test_the_published_guard_keeps_no_small_count_of_not_finite_households(
    households,
):
    """The published guard and the report keep a count of 10 or more
    households, and say "fewer than 10" for fewer."""
    formulas = model(contains=False)
    some = np.arange(12) < households
    formulas["tax_a"] = lambda f: np.where(some, np.nan, 0.1 * f("x"))
    sim = FakeSim(formulas, {"x": (1,) * 12}, (1,) * 12)
    part = partition(["tax_a", "tax_b"])
    result = guard.counted_once(
        sim, part, YEAR, 1e-6, guard.snapshot_inputs(sim, part.component_variables())
    )
    published = measure.publishable_guard(result)
    shown = None if households < 10 else households
    assert [item["households"] for item in published["not_finite_at_baseline"]] == [
        shown,
        shown,
    ]
    where = "fewer than 10 households" if households < 10 else "12 households"
    text = render._guard({"head": {"guard": published}})
    assert f"- {note('`tax_a`', where)}" in text.splitlines()
    assert f"- {note('`gov_tax`', where)}" in text.splitlines()


# The property's extra heads: no head reads them, and each is not finite at
# baseline in any set of households (none, for a finite head).
EXTRA_TOTAL = {"tax_n": "gov_tax", "ben_n": "gov_spending"}


@st.composite
def extra_heads(draw):
    shapes = draw(st.lists(SHAPES, min_size=1, max_size=3))
    extra = {}
    for head in sorted(draw(st.sets(st.sampled_from(sorted(EXTRA_TOTAL))))):
        where = draw(
            st.lists(st.booleans(), min_size=len(shapes), max_size=len(shapes))
        )
        extra[head] = (np.array(where), draw(st.sampled_from(NOT_FINITE_VALUES)))
    return shapes, extra


def with_extra_heads(shapes, extra, reads):
    """The properties' model and partition, with ``extra`` heads."""
    formulas = shapes_formulas(shapes)
    heads_of = {total: list(heads) for total, heads in HEADS_OF.items()}
    for head, (where, value) in extra.items():
        formulas[head] = lambda f, where=where, value=value: np.where(where, value, 7.0)
        heads_of[EXTRA_TOTAL[head]].append(head)
    for total, heads in heads_of.items():
        formulas[total] = lambda f, heads=heads: sum(f(v) for v in heads)
    part = partition(heads_of["gov_tax"], heads_of["gov_spending"], reads=reads)
    return formulas, part


NAN_IN_FIRST = {"tax_n": (np.array([True, False]), np.nan)}


@settings(max_examples=40, deadline=None)
@given(case=extra_heads(), reads=READS)
@example(case=([MEDIATED_NAN, MEDIATED_NAN], NAN_IN_FIRST), reads=MEDIATED_NAN_READS)
@example(
    case=(
        [("half", "flat", "flat", "flat"), ("flat", "flat", "flat", "flat")],
        {"ben_n": (np.array([True, True]), -np.inf)},
    ),
    reads=[True, False, False, False, False, False],
)
def test_heads_not_finite_at_baseline_are_named_and_change_nothing_else(case, reads):
    """For any heads, with any of the extra heads (which no head reads, and
    which respond to nothing) not finite at baseline in any households, the
    check returns, names exactly those heads, and the totals that add them,
    in blocking finite: checks, and fails no component for them. In each
    household it finds what it finds with those heads removed, except that
    it reads no total that adds a head not finite there."""
    shapes, extra = case
    households = len(shapes)
    declared = declared_reads(reads)
    bad = {head: where for head, (where, _) in extra.items() if where.any()}
    formulas, part = with_extra_heads(shapes, extra, declared)
    kept = {head: spec for head, spec in extra.items() if head not in bad}
    formulas_without, part_without = with_extra_heads(shapes, kept, declared)
    _, result = run_not_finite(
        formulas, part, x=(1,) * households, weights=(1,) * households
    )
    bad_totals = {EXTRA_TOTAL[head] for head in bad}
    assert named(result) == {
        **{head: head for head in bad},
        **{total: None for total in bad_totals},
    }
    checks = recorded(result)
    failing = {
        c
        for c, check in checks.items()
        if check["status"] == "fail" and c.startswith(ALWAYS_BLOCKING_PREFIXES)
    }
    assert failing == {f"finite:{head}" for head in bad} | (
        {"finite:metrics"} if bad_totals else set()
    )
    for row in result["components"]:
        assert all(p["head"] not in bad for p in row["problems"])
        if row["variable"] in bad:
            assert row["status"] != "fail"
        assert row["heads_held_skipped"] == bool(row["heads_not_held"]) or any(
            p.get("heads_not_held_at_baseline") for p in row["problems"]
        )
    assert result["reset_reproduces_baseline"]

    found = household_by_household(formulas, part, households)
    without = household_by_household(formulas_without, part_without, households)
    for k in range(households):
        here = {head for head, where in bad.items() if where[k]}
        for component, before in without[k].items():
            after = found[k][component]
            if not here:
                assert after == before
                continue
            totals_here = {EXTRA_TOTAL[head] for head in here}
            assert after == {
                **before,
                "problems": [
                    p
                    for p in before["problems"]
                    if not (p[2] == "model_total" and p[0] in totals_here)
                ],
            }


def published(check, record, publish, describe, formulas, part, x, weights):
    """What one implementation publishes for a model, as JSON: the check's
    result, the checks it records, the published guard and the report's
    section."""
    sim = FakeSim(formulas, {"x": x}, weights)
    snapshot = guard.snapshot_inputs(sim, part.component_variables())
    with np.errstate(divide="ignore", invalid="ignore"):
        result = check(sim, part, YEAR, 1e-6, snapshot)
    rec = measure.Recorder()
    record(rec, result)
    publishable = publish(result)
    return json.dumps(
        {
            "result": result,
            "checks": list(rec.checks.values()),
            "published": publishable,
            "report": describe({"head": {"guard": publishable}}),
        }
    )


NOW = (
    guard.counted_once,
    measure.record_guard_checks,
    measure.publishable_guard,
    render._guard,
)
BEFORE = (
    reference.counted_once,
    reference.record_guard_checks,
    reference.publishable_guard,
    reference._guard,
)


def assert_publishes_as_before(formulas, part, x, weights):
    assert published(*NOW, formulas, part, x, weights) == published(
        *BEFORE, formulas, part, x, weights
    )


def stale_double_count():
    return declared_double_count(lambda f: 0.1 * f("x"))


# The guard tests' own models, on their three households.
MODELS = {
    "containment": lambda: (model(contains=True), partition(["tax_a", "tax_b"])),
    "means test": lambda: (
        model(contains=False),
        partition(["tax_a"], ["ben_c", "ben_d"]),
    ),
    "rising benefit": lambda: (
        model(interaction=0.5),
        partition(["tax_a"], ["ben_c", "ben_d"]),
    ),
    "declared double count": lambda: declared_double_count(
        lambda f: 0.1 * f("x") + f("tax_b")
    ),
    "stale double count": stale_double_count,
    "overlapping benefits": lambda: (overlap_model(), OVERLAP),
    "overlap containing ib": lambda: (overlap_model(uc_contains_ib=1.0), OVERLAP),
    "gated containment": lambda: (
        {
            **gated_taxes(),
            "ben_c": lambda f: 100 + 0 * f("x"),
            "gov_spending": lambda f: f("ben_c"),
        },
        GATED,
    ),
}


@pytest.mark.parametrize("name", MODELS)
def test_every_finite_model_publishes_what_it_did_before(name):
    """Differential against ``counted_once_base_reference``: with every head
    and total finite at baseline, the check, the checks it records, the
    published guard and the report say exactly what they said before, in
    the same order."""
    formulas, part = MODELS[name]()
    assert_publishes_as_before(formulas, part, (1000, 2000, 3000), (1.5, 2.0, 0.5))


@pytest.mark.parametrize("nan_in", [(), (4,)], ids=["finite", "NaN once raised"])
def test_twelve_households_in_two_totals_publish_what_they_did_before(nan_in):
    assert_publishes_as_before(
        mediated_in_two_totals(nan_in), two_tax_totals(), (1,) * 12, (1,) * 12
    )


@settings(max_examples=60, deadline=None)
@given(
    shapes=st.lists(SHAPES, min_size=1, max_size=3),
    reads=READS,
    weights=st.lists(st.sampled_from([0.0, 0.5, 1.0, 2.0]), min_size=3, max_size=3),
)
@example(shapes=[MEDIATED_NAN], reads=MEDIATED_NAN_READS, weights=[1.0, 1.0, 1.0])
def test_finite_baselines_publish_what_they_did_before(shapes, reads, weights):
    """Differential against ``counted_once_base_reference`` for the guard
    tests' random heads, which are finite at baseline and may turn infinite
    or NaN once raised, on up to three households of any weights."""
    households = len(shapes)
    declared = declared_reads(reads)
    part = partition(HEADS_OF["gov_tax"], HEADS_OF["gov_spending"], reads=declared)
    assert_publishes_as_before(
        shapes_formulas(shapes),
        part,
        (1,) * households,
        tuple(weights[:households]),
    )


@settings(max_examples=100, deadline=None)
@given(
    values=st.lists(
        st.one_of(
            st.floats(allow_nan=False, allow_infinity=False),
            st.sampled_from(NOT_FINITE_VALUES),
        ),
        min_size=1,
        max_size=6,
    ),
    monthly=st.booleans(),
)
def test_the_check_sets_finite_values_bit_for_bit_and_others_at_zero(values, monthly):
    values = np.array(values)
    layout = [("2026-01", values), ("2026-02", values[::-1])] if monthly else values
    settable = guard._settable(layout)
    pairs = zip(layout, settable) if monthly else [((None, values), (None, settable))]
    for (_, before), (_, after) in pairs:
        finite = np.isfinite(before)
        assert np.isfinite(after).all()
        assert (after[~finite] == 0).all()
        assert before[finite].tobytes() == after[finite].tobytes()


def test_a_finite_held_head_keeps_the_words_it_had():
    assert guard._unheld_words(["ben_c"], "tax_b") == reference._unheld_words(
        ["ben_c"], "tax_b"
    )
    assert guard._unheld_words(["ben_c", "tax_g"], "tax_b") == (
        reference._unheld_words(["ben_c", "tax_g"], "tax_b")
    )
    assert guard._unheld_words([], "tax_b", at_baseline=["tax_n", "tax_m"]) == (
        "the check could not hold tax_n and tax_m, one or more of which is not "
        "finite at baseline in some households and moves there with tax_b"
    )
