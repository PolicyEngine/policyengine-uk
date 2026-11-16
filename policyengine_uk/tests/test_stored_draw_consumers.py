"""The UC rebalancing modifier, student loan uprating and the PIP scenario
read the dataset's stored draws when it supplies them, and run their own
seeded draws when it does not.

Invariants:

1. Output-neutral without the columns: each consumer gives what its own draw
   gives (the seed-43 stream, the person-id hash, the seed-42 stream).
2. With the columns, each decision is the stored value's: the draw compared
   with the rate in float64, or the stored student loan decision.
3. Precision: a float32 stored draw compared with a share just above it keeps
   its legacy side (3/8 - 2^-28 stored as 3/8 below 3/8 + 2^-28), and the
   reference encoder's value for 0.0625 - 2^-30 stays below 2026's PIP
   threshold where plain float32 rounding would not.
4. Reformability: new-claimant status is monotone in the share, and PIP
   phase-out in the phase-in share; student loan take-up has no rate but the
   module constant, and the stored decision is the same in every year.
5. Precedence: a status supplied for the year wins over the draw; one
   supplied only earlier leaves the later year to the draw; a repeated
   modifier, a reform after construction and an export replayed under
   another share keep the statuses, as without stored draws.
6. Validation: would_claim_student_loan takes booleans or the integers 0 and
   1 only, with nothing missing, on every data route and in set_input.
7. Determinism: applying the PIP scenario with stored draws for every year
   leaves numpy's global random state as it was.
"""

import ast
import inspect

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

import policyengine_uk.data.economic_assumptions as economic_assumptions
from policyengine_uk import Simulation
from policyengine_uk.data import UKSingleYearDataset
from policyengine_uk.data.economic_assumptions import (
    extend_single_year_dataset,
    stored_student_loan_take_up,
    uprate_student_loan_plans,
)
from policyengine_uk.model_api import Scenario
from policyengine_uk.scenarios.pip_reform import (
    modify_simulation,
    phased_out_by_draw,
    reform_pip_phase_in,
)
from policyengine_uk.scenarios.uc_reform import (
    REBALANCING_YEARS,
    add_universal_credit_reform,
    new_claimants_by_draw,
)
from policyengine_uk.system import system
from policyengine_uk.tests.stored_draw_fixtures import (
    PIP_THRESHOLDS,
    SHARE_GRID,
    encode,
    one_person_units_frame,
)
from policyengine_uk.utils.stochastic import splitmix64_uniform
from policyengine_uk.utils.stored_draws import StoredDrawError

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

STATUS = "uc_receives_new_claimant_health_element"
UC_DRAW = "uc_new_claimant_health_element_draw"
PIP_DRAW = "pip_phase_in_draw"
TAKE_UP = "would_claim_student_loan"
SHARE = "gov.dwp.universal_credit.rebalancing.new_claimant_share"
LEGACY = 3 / 8 - 2.0**-28
STORED = np.float32(3 / 8)
ABOVE = 3 / 8 + 2.0**-28
PROPERTY = settings(max_examples=200, deadline=None, derandomize=True)


def uc_frame(count, draws=None, status=None, years=(2025,)):
    columns = {
        "uc_limited_capability_for_WRA": {y: np.ones(count, bool) for y in years}
    }
    if draws is not None:
        columns[UC_DRAW] = {years[0]: draws}
    if status is not None:
        columns[STATUS] = status
    return one_person_units_frame(count=count, years=years, columns=columns)


def statuses(sim):
    return {
        year: np.asarray(sim.calculate(STATUS, year), dtype=bool)
        for year in REBALANCING_YEARS
    }


def shares(sim):
    parameter = sim.tax_benefit_system.parameters.get_child(SHARE)
    return {year: parameter(str(year)) for year in REBALANCING_YEARS}


# --- Universal Credit rebalancing ------------------------------------------


@pytest.fixture(scope="module")
def uc_without_column():
    return Simulation(dataset=uc_frame(200))


def test_uc_without_the_column_keeps_the_seed_43_stream(uc_without_column):
    sim = uc_without_column
    stream = np.random.default_rng(43).random(200)
    share = shares(sim)
    for year, status in statuses(sim).items():
        np.testing.assert_array_equal(status, stream < share[year])


def test_uc_with_the_column_compares_the_stored_draw():
    stream = np.random.default_rng(43).random(200)
    stored, feasible, _ = encode(stream, SHARE_GRID)
    assert feasible.all()
    with_column = Simulation(dataset=uc_frame(200, draws=stored))
    without = Simulation(dataset=uc_frame(200))
    share = shares(with_column)
    got, legacy = statuses(with_column), statuses(without)
    for year in REBALANCING_YEARS:
        np.testing.assert_array_equal(
            got[year], stored.astype(np.float64) < share[year]
        )
        # The encoder keeps the legacy decision at every share on the grid.
        np.testing.assert_array_equal(got[year], legacy[year])
        np.testing.assert_array_equal(
            np.asarray(with_column.calculate("uc_LCWRA_element", year)),
            np.asarray(without.calculate("uc_LCWRA_element", year)),
        )


def test_uc_promotes_the_stored_draw_before_comparing():
    assert LEGACY < ABOVE and float(STORED) == 3 / 8
    # numpy compares a float32 array with a Python float in float32.
    assert not (np.array([STORED]) < ABOVE)[0]
    assert new_claimants_by_draw(np.array([STORED]), ABOVE).tolist() == [True]
    sim = Simulation(
        dataset=uc_frame(1, draws=np.array([STORED])),
        reform={SHARE: {"2026-01-01.2026-12-31": ABOVE}},
    )
    assert sim.calculate(STATUS, 2026).tolist() == [True]


@settings(PROPERTY)
@given(
    draws=st.lists(
        st.floats(0, 1, exclude_max=True, width=32), min_size=1, max_size=20
    ),
    low=st.floats(0, 1),
    high=st.floats(0, 1),
)
def test_new_claimant_status_is_monotone_in_the_share(draws, low, high):
    low, high = sorted((low, high))
    draws = np.asarray(draws, dtype=np.float32)
    below_low = new_claimants_by_draw(draws, low)
    below_high = new_claimants_by_draw(draws, high)
    assert not (below_low & ~below_high).any()
    np.testing.assert_array_equal(below_low, draws.astype(np.float64) < low)


def test_uc_precedence_with_a_stored_draw():
    draws = np.array([0.05, 0.5, 0.95], dtype=np.float32)
    supplied_2026 = np.array([False, True, False])
    sim = Simulation(
        dataset=uc_frame(
            3,
            draws=draws,
            status={2026: supplied_2026},
            years=(2025, 2026),
        )
    )
    share = shares(sim)
    got = statuses(sim)
    # Supplied for the year: wins over the draw.
    np.testing.assert_array_equal(got[2026], supplied_2026)
    # Supplied only for an earlier year: the later year takes the draw.
    np.testing.assert_array_equal(got[2027], draws.astype(np.float64) < share[2027])
    # A repeated modifier reuses its own statuses.
    add_universal_credit_reform(sim)
    for year, status in statuses(sim).items():
        np.testing.assert_array_equal(status, got[year])
    # A reform after construction keeps them.
    sim.apply_reform({SHARE: {"2027-01-01.2027-12-31": 1.0}})
    for year, status in statuses(sim).items():
        np.testing.assert_array_equal(status, got[year])


def test_uc_export_replayed_under_another_share_keeps_the_statuses():
    draws = np.array([0.05, 0.5, 0.95], dtype=np.float32)
    every_share = {SHARE: {"2026-01-01.2100-12-31": 1.0}}
    no_share = {SHARE: {"2026-01-01.2100-12-31": 0.0}}
    built = Simulation(dataset=uc_frame(3, draws=draws), reform=every_share)
    exported = built.to_input_dataframe()
    assert all(f"{STATUS}__{year}" in exported for year in REBALANCING_YEARS)
    assert f"{UC_DRAW}__2025" in exported
    replayed = Simulation(dataset=exported, reform=no_share)
    for year, status in statuses(replayed).items():
        assert status.all(), year


def test_uc_situation_keeps_the_protected_amount_with_a_draw():
    situation = {
        "people": {"adult": {"age": {2026: 30}}},
        "benunits": {
            "benunit": {"members": ["adult"], UC_DRAW: {2026: 0.0}},
        },
        "households": {"household": {"members": ["adult"]}},
    }
    sim = Simulation(situation=situation)
    assert sim.calculate(STATUS, 2026).tolist() == [False]


# --- PIP phase-in -----------------------------------------------------------


def pip_frame(count, draws=None):
    years = tuple(range(2025, 2030))
    columns = {"pip": {year: np.full(count, 1_000.0) for year in years}}
    if draws is not None:
        columns[PIP_DRAW] = {2025: draws}
    return one_person_units_frame(count=count, years=years, columns=columns)


def pip_by_year(sim):
    return {year: np.asarray(sim.calculate("pip", year)) for year in range(2025, 2030)}


def test_pip_without_the_column_keeps_the_seed_42_stream():
    sim = Simulation(dataset=pip_frame(40), scenario=reform_pip_phase_in)
    np.random.seed(42)
    stream = np.random.random(40)
    for year, pip in pip_by_year(sim).items():
        threshold = 0.25 * (year - 2025) / 4
        np.testing.assert_array_equal(pip == 0, stream < threshold)


def test_pip_with_the_column_matches_the_legacy_decisions_and_leaves_numpy_alone():
    np.random.seed(42)
    stream = np.random.random(40)
    stored, feasible, _ = encode(stream, PIP_THRESHOLDS)
    assert feasible.all()
    with_column = Simulation(dataset=pip_frame(40, draws=stored))
    without = Simulation(dataset=pip_frame(40))
    np.random.seed(7)
    state = np.random.get_state()
    reform_pip_phase_in.simulation_modifier(with_column)
    after = np.random.get_state()
    assert state[0] == after[0] and (state[1] == after[1]).all()
    assert state[2:] == after[2:]
    modify_simulation(without)
    got, legacy = pip_by_year(with_column), pip_by_year(without)
    for year in got:
        np.testing.assert_array_equal(got[year], legacy[year])


def test_pip_keeps_the_legacy_side_of_a_threshold_after_encoding():
    legacy = 0.0625 - 2.0**-30
    assert float(np.float32(legacy)) == 0.0625
    stored, feasible, _ = encode([legacy], PIP_THRESHOLDS)
    assert feasible[0] and float(stored[0]) == 0.0625 - 2.0**-28
    sim = Simulation(dataset=pip_frame(1, draws=stored))
    modify_simulation(sim)
    assert sim.calculate("pip", 2025).tolist() == [1_000]
    assert sim.calculate("pip", 2026).tolist() == [0]
    # Plain float32 rounding would have moved this person past 2026's share.
    rounded = Simulation(dataset=pip_frame(1, draws=np.float32([legacy])))
    modify_simulation(rounded)
    assert rounded.calculate("pip", 2026).tolist() == [1_000]


def test_pip_promotes_the_stored_draw_before_comparing():
    assert phased_out_by_draw(np.array([STORED]), ABOVE).tolist() == [True]
    assert not (np.array([STORED]) < ABOVE)[0]


@settings(PROPERTY)
@given(
    draws=st.lists(
        st.floats(0, 1, exclude_max=True, width=32), min_size=1, max_size=20
    ),
)
def test_pip_phase_out_is_monotone_in_the_phase(draws):
    draws = np.asarray(draws, dtype=np.float32)
    previous = np.zeros(len(draws), dtype=bool)
    for threshold in PIP_THRESHOLDS:
        out = phased_out_by_draw(draws, threshold)
        assert not (previous & ~out).any()
        previous = out


def test_pip_situation_uses_a_stored_draw():
    situation = {
        "people": {
            "adult": {
                "age": {2025: 30},
                "pip": {year: 1_000 for year in range(2025, 2030)},
                PIP_DRAW: {2025: 0.1},
            }
        },
        "benunits": {"benunit": {"members": ["adult"]}},
        "households": {"household": {"members": ["adult"]}},
    }
    sim = Simulation(situation=situation, scenario=reform_pip_phase_in)
    assert [float(sim.calculate("pip", year)[0]) for year in range(2025, 2030)] == [
        1_000,
        1_000,
        0,
        0,
        0,
    ]


# --- Student loans ----------------------------------------------------------


def loan_dataset(base_year=2024, take_up=None, ages=range(18, 51), per_age=20):
    ages = np.repeat(list(ages), per_age)
    ids = np.arange(1, len(ages) + 1)
    person = pd.DataFrame(
        {
            "person_id": ids,
            "person_benunit_id": ids,
            "person_household_id": ids,
            "age": ages,
            "student_loan_plan": "NONE",
            "highest_education": "TERTIARY",
            "student_loan_repayments": 0.0,
        }
    )
    if take_up is not None:
        person[TAKE_UP] = take_up(ids)
    household = pd.DataFrame(
        {
            "household_id": ids,
            "household_weight": 1.0,
            "region": "LONDON",
            "tenure_type": "OWNED_OUTRIGHT",
            "rent": 0.0,
            "council_tax": 0.0,
        }
    )
    return UKSingleYearDataset(
        person=person,
        benunit=pd.DataFrame({"benunit_id": ids}),
        household=household,
        fiscal_year=base_year,
    )


def plans(dataset):
    projected = extend_single_year_dataset(dataset, system.parameters, end_year=2029)
    return {
        year: projected.datasets[year].person["student_loan_plan"].to_numpy()
        for year in projected.datasets
    }


def legacy_take_up(ids):
    return splitmix64_uniform(np.asarray(ids), salt=3) < 0.4


def test_the_stored_take_up_decision_is_todays_decision():
    without = plans(loan_dataset())
    stored = plans(loan_dataset(take_up=legacy_take_up))
    for year in without:
        np.testing.assert_array_equal(stored[year], without[year])
    assert any((without[year] != "NONE").any() for year in without)


def test_the_stored_take_up_decision_replaces_the_hash():
    everyone = plans(loan_dataset(take_up=lambda ids: np.ones(len(ids), bool)))
    nobody = plans(loan_dataset(take_up=lambda ids: np.zeros(len(ids), bool)))
    base = loan_dataset()
    for year in everyone:
        if year == 2024:
            continue
        assert (nobody[year] == "NONE").all()
        assert (everyone[year] != "NONE").sum() >= (plans(base)[year] != "NONE").sum()


def test_a_person_takes_up_in_every_projected_year_or_none():
    stored = loan_dataset(take_up=legacy_take_up)
    took_up = stored.person[TAKE_UP].to_numpy()
    for year, plan in plans(stored).items():
        assert ((plan != "NONE") <= took_up).all(), year


@pytest.mark.parametrize(
    "values",
    [
        [True, np.nan, False],
        [1.0, 0.0, 1.0],
        [2, 0, 1],
        pd.array([True, None, False], dtype="boolean"),
        ["True", "False", "True"],
    ],
    ids=["nan", "floats", "two", "nullable_missing", "strings"],
)
def test_take_up_values_are_checked_before_any_cast(values):
    person = pd.DataFrame({TAKE_UP: values})
    with pytest.raises(StoredDrawError, match=TAKE_UP):
        stored_student_loan_take_up(person)
    sim = Simulation(dataset=one_person_units_frame(count=3))
    with pytest.raises(StoredDrawError, match=TAKE_UP):
        sim.set_input(TAKE_UP, 2025, values)
    assert sim.get_holder(TAKE_UP).get_known_periods() == []


@pytest.mark.parametrize(
    "values",
    [[True, False, True], [1, 0, 1], np.array([1, 0, 1], dtype=np.int8)],
)
def test_take_up_accepts_booleans_and_zero_or_one(values):
    np.testing.assert_array_equal(
        stored_student_loan_take_up(pd.DataFrame({TAKE_UP: values})),
        [True, False, True],
    )
    sim = Simulation(dataset=one_person_units_frame(count=3))
    sim.set_input(TAKE_UP, 2025, values)
    assert sim.calculate(TAKE_UP, 2025).tolist() == [True, False, True]


def test_a_dataset_with_a_missing_take_up_value_is_refused_on_each_route():
    dataset = loan_dataset(take_up=lambda ids: np.where(ids == 1, np.nan, 1.0))
    with pytest.raises(StoredDrawError, match=TAKE_UP):
        uprate_student_loan_plans(dataset.copy(), dataset, system.parameters)
    with pytest.raises(StoredDrawError, match=TAKE_UP):
        Simulation(dataset=dataset)
    frame = one_person_units_frame(count=2, columns={TAKE_UP: [True, None]})
    with pytest.raises(StoredDrawError, match=TAKE_UP):
        Simulation(dataset=frame)


def test_no_take_up_call_passes_a_rate():
    """The stored decision is today's only at the module constant; a call
    passing another rate would need the stored draw instead."""
    assert economic_assumptions._GRADUATE_LOAN_TAKE_UP == 0.4
    tree = ast.parse(inspect.getsource(uprate_student_loan_plans))
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "assign_new_borrowers"
    ]
    assert len(calls) == 3
    assert all(len(call.args) == 1 and not call.keywords for call in calls)
    helper = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "assign_new_borrowers"
    )
    assert [argument.arg for argument in helper.args.args] == ["mask"]
    rates = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and node.id == "_GRADUATE_LOAN_TAKE_UP"
    ]
    assert len(rates) == 1
    module = ast.parse(inspect.getsource(economic_assumptions))
    readers = [
        node
        for node in ast.walk(module)
        if isinstance(node, ast.Name) and node.id == "_GRADUATE_LOAN_TAKE_UP"
    ]
    assert len(readers) == 2  # the assignment and the fallback's comparison


@settings(PROPERTY)
@given(
    legacy=st.lists(st.floats(0, 1, exclude_max=True), min_size=1, max_size=30),
    share_index=st.integers(0, len(SHARE_GRID) - 1),
)
def test_encoded_draws_keep_every_grid_decision_in_each_consumer(legacy, share_index):
    """Representation: a reference-encoded draw lies in [0, 1), survives a
    float32 round trip, sits within 2^-24 of its legacy draw, and gives the
    legacy decision in both consumers at every covered threshold."""
    legacy = np.asarray(legacy, dtype=np.float64)
    for thresholds, consumer in (
        (SHARE_GRID, new_claimants_by_draw),
        (PIP_THRESHOLDS, phased_out_by_draw),
    ):
        stored, feasible, _ = encode(legacy, thresholds)
        assert feasible.all()
        as_loaded = np.asarray(stored, dtype=np.float32)
        assert ((as_loaded >= 0) & (as_loaded < 1)).all()
        np.testing.assert_array_equal(
            as_loaded.astype(np.float64).astype(np.float32), as_loaded
        )
        assert (np.abs(as_loaded.astype(np.float64) - legacy) < 2.0**-24).all()
        threshold = thresholds[share_index % len(thresholds)]
        np.testing.assert_array_equal(
            consumer(as_loaded, threshold), legacy < threshold
        )
