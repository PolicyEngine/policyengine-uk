"""Public-only RED: guard intervention must not manufacture legacy user choices.

Uses the already independent DfE calendar oracle and tiny synthetic situations.
No dataset, certified fixture, private ID or amount, country default or download.
"""

from datetime import date
import types
import numpy as np
import pytest
from policyengine_core.periods import period
from policyengine_uk.tests.test_childcare_birthday_terms import (
    simulate,
    calendar_reference,
    VALUES,
    U,
    T,
    W,
    E,
)
from policyengine_uk.utils.childcare import uses_legacy_childcare_inputs
from policyengine_uk.utils.supplied_inputs import supplied_input, set_model_value
from policyengine_uk.utils.aggregate_impact import guard
from policyengine_uk.utils.aggregate_impact.partition import parse_partition

YEAR = 2026
BIRTHS = [date(2023, 8, 31), date(2023, 10, 7)]
LEGACY = [
    "early_years_term_share_before_school",
    "extended_childcare_entitlement_term_share",
    U,
    T,
    W,
]
X = "extended_childcare_entitlement"
HEADS = [U, T, X]


def make(born=date(2023, 10, 7), annual_inputs=None):
    sim = simulate(born, working=True, annual_inputs=annual_inputs)
    sim.set_input("household_weight", YEAR, [1])
    return sim


def values(sim):
    return {v: float(sim.calculate(v, YEAR)[0]) for v in VALUES}


def is_legacy(sim):
    return uses_legacy_childcare_inputs(
        sim.get_variable_population(U), period(str(YEAR))
    )


def genuine(sim, name):
    return supplied_input(sim.get_variable_population(name), name, period(str(YEAR)))


def baselines(sim, names=HEADS):
    return {v: sim.calculate(v, YEAR).astype(np.float64).copy() for v in names}


def small_partition():
    return parse_partition(
        {
            "schema_version": 1,
            "totals": {"gov_spending": {}},
            "tax_heads": [],
            "spending_heads": [
                {
                    "id": v,
                    "label": v,
                    "variable": v,
                    "totals": ["gov_spending"],
                    "entity": "benunit" if v == X else "person",
                }
                for v in HEADS
            ],
            "model_double_counts": [],
        }
    )


@pytest.mark.parametrize("born", BIRTHS, ids=["aug", "oct"])
@pytest.mark.parametrize("component", [U, T], ids=["U", "T"])
def test_native_probe_keeps_genuine_input_route(born, component):
    sim = make(born)
    expected, _ = calendar_reference(
        born, targeted=True, working=True, claims_universal=True, claims_targeted=True
    )
    assert values(sim) == pytest.approx(expected, abs=0.01)
    baseline = baselines(sim)
    assert not is_legacy(sim)
    guard._perturb(sim, component, YEAR, baseline, np.array([1.0]), False)
    assert genuine(sim, component) is None
    assert not is_legacy(sim)


@pytest.mark.parametrize(
    "born,component,other",
    [(BIRTHS[0], T, U), (BIRTHS[1], U, T)],
    ids=["target-probe-universal-stable", "universal-probe-target-stable"],
)
def test_probe_does_not_raise_unrelated_base_head(born, component, other):
    sim = make(born)
    expected, _ = calendar_reference(
        born, targeted=True, working=True, claims_universal=True, claims_targeted=True
    )
    before = values(sim)
    assert before == pytest.approx(expected, abs=0.01)
    baseline = baselines(sim)
    for added in [1.0, 2.0]:
        guard._perturb(sim, component, YEAR, baseline, np.array([added]), False)
        assert float(sim.calculate(other, YEAR)[0]) == pytest.approx(
            expected[other], abs=0.01
        )


@pytest.mark.parametrize("born", BIRTHS, ids=["aug", "oct"])
def test_native_counted_once_childcare_partition(born):
    sim = make(born)
    part = small_partition()
    snapshot = guard.snapshot_inputs(sim, part.component_variables())
    result = guard.counted_once(
        sim, part, YEAR, 1e-6, snapshot, variables_to_check=[U, T]
    )
    assert result["reset_reproduces_baseline"]
    assert {r["variable"] for r in result["components"]} == {U, T}
    assert all(r["status"] == "pass" for r in result["components"])
    assert all(
        r["coefficients"]["gov_spending"] == pytest.approx(1, abs=1e-3)
        for r in result["components"]
    )


@pytest.mark.parametrize(
    "name", LEGACY, ids=["school-share", "work-share", "U", "T", "working-total"]
)
@pytest.mark.parametrize("entered", ["zero", "equal"])
def test_original_genuine_input_is_restored(name, entered):
    sim = make()
    value = 0.0 if entered == "zero" else float(sim.calculate(name, YEAR)[0])
    sim.set_input(name, YEAR, [value])
    sim._invalidate_all_caches()
    assert is_legacy(sim)
    original = genuine(sim, name).copy()
    snapshot = guard.snapshot_inputs(sim, [name])
    guard._perturb(
        sim,
        name,
        YEAR,
        {name: sim.calculate(name, YEAR).astype(np.float64)},
        np.array([1.0]),
        False,
    )
    assert is_legacy(sim)
    guard._restore(sim, name, snapshot)
    assert is_legacy(sim)
    np.testing.assert_array_equal(genuine(sim, name), original)


@pytest.mark.parametrize("name", [U, T], ids=["U", "T"])
def test_original_model_owned_amount_restores_origin(name):
    sim = make()
    before = values(sim)
    set_model_value(sim, name, YEAR, sim.calculate(name, YEAR).copy())
    assert genuine(sim, name) is None
    snapshot = guard.snapshot_inputs(sim, [name])
    baseline = {name: sim.calculate(name, YEAR).astype(np.float64)}
    guard._perturb(sim, name, YEAR, baseline, np.array([1.0]), False)
    guard._restore(sim, name, snapshot)
    assert genuine(sim, name) is None
    assert not is_legacy(sim)
    assert values(sim) == pytest.approx(before, abs=0.01)


@pytest.mark.parametrize("held", [U, T], ids=["U", "T"])
def test_held_head_write_does_not_manufacture_legacy_input(held):
    sim = make()
    baseline = baselines(sim)
    snapshot = guard.snapshot_inputs(sim, HEADS)
    guard._perturb(sim, X, YEAR, baseline, np.array([1.0]), False, hold=[held])
    assert genuine(sim, held) is None
    assert not is_legacy(sim)
    for name in HEADS:
        guard._restore(sim, name, snapshot)
    assert not is_legacy(sim)


@pytest.mark.parametrize("kind", ["clone", "branch"])
def test_probe_and_restore_do_not_change_parent_origin(kind):
    parent = make()
    before = values(parent)
    child = parent.clone() if kind == "clone" else parent.get_branch("guard_probe")
    baseline = baselines(child)
    snapshot = guard.snapshot_inputs(child, HEADS)
    guard._perturb(child, U, YEAR, baseline, np.array([1.0]), False)
    assert not is_legacy(parent)
    assert values(parent) == before
    for name in HEADS:
        guard._restore(child, name, snapshot)
    assert not is_legacy(child)
    assert values(child) == pytest.approx(before, abs=0.01)


def test_warm_cache_does_not_create_a_user_choice():
    sim = make()
    before = values(sim)
    for name in reversed(VALUES):
        sim.calculate(name, YEAR)
    assert not is_legacy(sim)
    assert values(sim) == before


def test_counted_once_exception_restores_probe_origin(monkeypatch):
    sim = make()
    before = values(sim)
    part = small_partition()
    snapshot = guard.snapshot_inputs(sim, part.component_variables())
    original = guard._head_arrays

    class DeliberatePublicFailure(Exception):
        pass

    calls = 0

    def injected(simulation, *args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise DeliberatePublicFailure()
        return original(simulation, *args, **kwargs)

    monkeypatch.setattr(guard, "_head_arrays", injected)
    with pytest.raises(DeliberatePublicFailure):
        guard.counted_once(sim, part, YEAR, 1e-6, snapshot, variables_to_check=[U])
    assert genuine(sim, U) is None
    assert not is_legacy(sim)
    assert values(sim) == pytest.approx(before, abs=0.01)


def test_real_wrong_head_count_still_fails():
    from policyengine_uk.tests.aggregate_impact.test_aggregate_impact_guard import (
        run,
        model,
        partition,
        by_variable,
        kinds,
    )

    _, result = run(model(contains=True), partition(["tax_a", "tax_b"]))
    row = by_variable(result)["tax_b"]
    assert row["status"] == "fail" and ("tax_a", "moves") in kinds(row)


@pytest.mark.parametrize(
    "origin,operation",
    [
        (o, p)
        for p in ["normal", "held", "exception"]
        for o in ["zero", "equal", "model"]
    ],
    ids=[
        o + "-" + p
        for p in ["normal", "held", "exception"]
        for o in ["zero", "equal", "model"]
    ],
)
def test_inherited_input_origin_and_slot_placement_are_restored(origin, operation):
    parent = make()
    native = parent.calculate(U, YEAR).copy()
    if origin == "model":
        set_model_value(parent, U, YEAR, native)
    else:
        parent.set_input(U, YEAR, [0.0] if origin == "zero" else native)
    child = parent.get_branch("inherited_probe")
    sibling = parent.get_branch("untouched_sibling")
    p = period(str(YEAR))
    ancestor = parent.branch_name
    local = child.branch_name
    before_parent = values(parent)
    before_sibling = values(sibling)
    parent_keys = set(parent._user_input_keys)
    sibling_keys = set(sibling._user_input_keys)
    holder = child.get_holder(U)
    inherited_before = holder._get_array_from_storage(p, ancestor).copy()
    assert holder._get_array_from_storage(p, local) is None
    model_before = {
        k: v.copy() for k, v in getattr(child, "_model_values", {}).items() if k[0] == U
    }
    keys_before = {k for k in child._user_input_keys if k[0] == U}
    expected_genuine = origin != "model"
    assert (genuine(child, U) is not None) == expected_genuine
    snapshot = guard.snapshot_inputs(child, HEADS)
    baseline = baselines(child)
    try:
        if operation == "held":
            guard._perturb(child, T, YEAR, baseline, np.array([1.0]), False, hold=[U])
        else:
            guard._perturb(child, U, YEAR, baseline, np.array([1.0]), False)
        if operation == "exception":
            raise RuntimeError("deliberate public cleanup control")
    except RuntimeError as error:
        assert (
            operation == "exception"
            and str(error) == "deliberate public cleanup control"
        )
    finally:
        for name in HEADS:
            guard._restore(child, name, snapshot)
    # Exact branch placement matters even if fallback values happen to be equal.
    assert holder._get_array_from_storage(p, local) is None
    np.testing.assert_array_equal(
        holder._get_array_from_storage(p, ancestor), inherited_before
    )
    assert {k for k in child._user_input_keys if k[0] == U} == keys_before
    after_model = {
        k: v for k, v in getattr(child, "_model_values", {}).items() if k[0] == U
    }
    assert set(after_model) == set(model_before)
    for key in model_before:
        np.testing.assert_array_equal(after_model[key], model_before[key])
    assert (genuine(child, U) is not None) == expected_genuine
    assert (
        parent._user_input_keys == parent_keys
        and sibling._user_input_keys == sibling_keys
    )
    assert values(parent) == before_parent and values(sibling) == before_sibling


@pytest.mark.parametrize("origin", ["absent", "genuine-zero", "genuine-equal", "model"])
def test_registered_nonchildcare_guard_origin_round_trip(origin):
    sim = make()
    name = "adjusted_net_income"
    p = period(str(YEAR))
    native = sim.calculate(name, YEAR).copy()
    if origin == "genuine-zero":
        sim.set_input(name, YEAR, [0.0])
    elif origin == "genuine-equal":
        sim.set_input(name, YEAR, native)
    elif origin == "model":
        set_model_value(sim, name, YEAR, native)
    genuine_before = genuine(sim, name)
    genuine_before = None if genuine_before is None else genuine_before.copy()
    holder = sim.get_holder(name)
    stored_before = holder._get_array_from_storage(p, sim.branch_name)
    stored_before = None if origin == "absent" else stored_before.copy()
    snapshot = guard.snapshot_inputs(sim, [name])
    baseline = {name: sim.calculate(name, YEAR).astype(np.float64)}
    guard._perturb(sim, name, YEAR, baseline, np.array([1.0]), False)
    assert (genuine(sim, name) is not None) == origin.startswith("genuine")
    guard._restore(sim, name, snapshot)
    after = genuine(sim, name)
    if genuine_before is None:
        assert after is None
    else:
        np.testing.assert_array_equal(after, genuine_before)
    if stored_before is None:
        assert holder._get_array_from_storage(p, sim.branch_name) is None
    else:
        np.testing.assert_array_equal(
            holder._get_array_from_storage(p, sim.branch_name), stored_before
        )


def _subset_origin_fixture():
    parent = make()
    parent.set_input("employment_income", YEAR, [0.0])
    set_model_value(
        parent,
        "adjusted_net_income",
        YEAR,
        parent.calculate("adjusted_net_income", YEAR).copy(),
    )
    child = parent.get_branch("subset_probe")
    sibling = parent.get_branch("subset_sibling")
    names = HEADS + ["employment_income", "adjusted_net_income"]
    part = parse_partition(
        {
            "schema_version": 1,
            "totals": {"gov_spending": {}},
            "tax_heads": [],
            "spending_heads": [
                {
                    "id": v,
                    "label": v,
                    "variable": v,
                    "totals": ["gov_spending"],
                    "entity": "benunit" if v == X else "person",
                }
                for v in names
            ],
            "model_double_counts": [],
        }
    )
    p = period(str(YEAR))
    ancestor = parent.branch_name
    saved = {
        v: child.get_holder(v)._get_array_from_storage(p, ancestor).copy()
        for v in names[-2:]
    }
    keys = {k for k in child._user_input_keys if k[0] in names[-2:]}
    model = {
        k: v.copy()
        for k, v in getattr(child, "_model_values", {}).items()
        if k[0] in names[-2:]
    }
    return parent, child, sibling, part, saved, keys, model


def _assert_unselected_origin_placement(parent, child, sibling, saved, keys, model):
    p = period(str(YEAR))
    for name, value in saved.items():
        holder = child.get_holder(name)
        assert holder._get_array_from_storage(p, child.branch_name) is None
        np.testing.assert_array_equal(
            holder._get_array_from_storage(p, parent.branch_name), value
        )
        np.testing.assert_array_equal(parent.calculate(name, YEAR), value)
        np.testing.assert_array_equal(sibling.calculate(name, YEAR), value)
    assert {k for k in child._user_input_keys if k[0] in saved} == keys
    current = {
        k: v for k, v in getattr(child, "_model_values", {}).items() if k[0] in saved
    }
    assert set(current) == set(model)
    for key, value in model.items():
        np.testing.assert_array_equal(current[key], value)


def test_subset_selection_leaves_unselected_input_origins_untouched():
    parent, child, sibling, part, saved, keys, model = _subset_origin_fixture()
    snapshot = guard.snapshot_inputs(child, part.component_variables())
    result = guard.counted_once(
        child, part, YEAR, 1e-6, snapshot, variables_to_check=[U]
    )
    assert result["reset_reproduces_baseline"]
    assert [r["variable"] for r in result["components"]] == [U]
    assert result["components"][0]["status"] == "pass"
    _assert_unselected_origin_placement(parent, child, sibling, saved, keys, model)


def test_partial_setter_failure_restores_only_touched_input(monkeypatch):
    parent, child, sibling, part, saved, keys, model = _subset_origin_fixture()
    before = values(child)
    snapshot = guard.snapshot_inputs(child, part.component_variables())
    original = type(child).set_input
    failed = False

    class DeliberatePartialSetterFailure(Exception):
        pass

    def partial(simulation, name, when, value):
        nonlocal failed
        original(simulation, name, when, value)
        if simulation is child and name == U and not failed:
            failed = True
            raise DeliberatePartialSetterFailure()

    # Bound to the child, so a branch made from it while the guard calculates
    # (the Marriage Allowance election makes two) gets the setter bound to the
    # branch, and its inputs stay in the branch.
    monkeypatch.setattr(child, "set_input", types.MethodType(partial, child))
    with pytest.raises(DeliberatePartialSetterFailure):
        guard.counted_once(child, part, YEAR, 1e-6, snapshot, variables_to_check=[U])
    assert failed and genuine(child, U) is None
    assert values(child) == pytest.approx(before, abs=0.01)
    _assert_unselected_origin_placement(parent, child, sibling, saved, keys, model)
