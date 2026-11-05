"""Stored columns on policyengine-core's ``Dataset`` route, and the
with/without differential on both loading routes.

Invariants:

1. Keys and order: the route refuses a dataset carrying a stored column
   where any person, benefit unit or household identifier does not survive
   the int32 cast, naming the entity; without a stored column such a dataset
   loads as before.
2. Supplied periods: a stored column or exempting outcome supplied for any
   period must be supplied for the first, and a draw's later periods must
   repeat its first, or the route refuses the dataset before it exports
   anything. An outcome may vary across periods; later periods drop, as for
   any input.
3. Neutral by construction: with columns the reference encoder built from
   today's draws, each loading route gives the same UC new-claimant
   statuses, LCWRA amounts and PIP amounts, bit for bit, as without them.
4. The stored columns survive the route: the rebuilt simulation reads the
   values the file supplied.
"""

import h5py
import numpy as np
import pytest

from policyengine_uk import Simulation
from policyengine_uk.data.core_route_checks import CoreRouteError
from policyengine_uk.scenarios.pip_reform import modify_simulation
from policyengine_uk.scenarios.uc_reform import REBALANCING_YEARS
from policyengine_uk.system import system
from policyengine_uk.tests.stored_draw_fixtures import (
    ID_COLUMNS,
    PIP_THRESHOLDS,
    SHARE_GRID,
    encode,
    one_person_units_frame,
)

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

STATUS = "uc_receives_new_claimant_health_element"
UC_DRAW = "uc_new_claimant_health_element_draw"
PIP_DRAW = "pip_phase_in_draw"
INT32_MAX = np.iinfo(np.int32).max


def add_households(file, year, count):
    """Household columns the route's export and projection read."""
    region = system.variables["region"].possible_values
    tenure = system.variables["tenure_type"].possible_values
    file.create_dataset(f"household_weight/{year}", data=np.ones(count))
    file.create_dataset(
        f"region/{year}", data=np.asarray(region.encode(np.full(count, "LONDON")))
    )
    file.create_dataset(
        f"tenure_type/{year}",
        data=np.asarray(tenure.encode(np.full(count, "OWNED_OUTRIGHT"))),
    )
    file.create_dataset(f"rent/{year}", data=np.zeros(count))
    file.create_dataset(f"council_tax/{year}", data=np.zeros(count))


def core_file(path, count=3, columns=None, ids=None, years=(2025,)):
    """A core Dataset file: each variable's array under ``variable/year``,
    one adult per benefit unit and household."""
    ids = {name: np.arange(1, count + 1) for name in ID_COLUMNS} | (ids or {})
    with h5py.File(path, "w") as file:
        for year in years:
            for name, values in ids.items():
                file.create_dataset(f"{name}/{year}", data=np.asarray(values))
            file.create_dataset(f"age/{year}", data=np.full(count, 30))
            add_households(file, year, count)
        for name, by_year in (columns or {}).items():
            for year, values in by_year.items():
                file.create_dataset(f"{name}/{year}", data=np.asarray(values))
    return str(path)


# --- Identities -------------------------------------------------------------


@pytest.mark.parametrize(
    "entity, ids",
    [
        ("person", {"person_id": [1, 2, INT32_MAX + 1]}),
        (
            "benunit",
            {
                "benunit_id": [1, 2, INT32_MAX + 1],
                "person_benunit_id": [1, 2, INT32_MAX + 1],
            },
        ),
        (
            "household",
            {
                "household_id": [1, 2, INT32_MAX + 1],
                "person_household_id": [1, 2, INT32_MAX + 1],
            },
        ),
    ],
)
@pytest.mark.parametrize("column", [UC_DRAW, PIP_DRAW, "months_since_last_birthday"])
def test_identifiers_beyond_int32_refuse_a_stored_column(entity, ids, column, tmp_path):
    values = {UC_DRAW: [0.5] * 3, PIP_DRAW: [0.5] * 3}.get(column, [6.0] * 3)
    path = core_file(tmp_path / "core.h5", columns={column: {2025: values}}, ids=ids)
    with pytest.raises(CoreRouteError, match=f"{entity} identifier"):
        Simulation(dataset=path)


def test_identifiers_beyond_int32_load_without_a_stored_column(tmp_path):
    path = core_file(
        tmp_path / "core.h5",
        ids={"person_id": [1, 2, INT32_MAX + 1]},
    )
    with pytest.warns(Warning):
        sim = Simulation(dataset=path)
    assert len(sim.calculate("person_id", 2025)) == 3


def test_benefit_unit_order_reversed_by_the_cast_is_refused(tmp_path):
    # Raw [1, 2^31] sorts the other way once 2^31 wraps to -2^31.
    ids = {"benunit_id": [1, 2**31], "person_benunit_id": [1, 2**31]}
    path = core_file(
        tmp_path / "core.h5",
        count=2,
        ids={
            **ids,
            **{k: [1, 2] for k in ("person_id", "household_id", "person_household_id")},
        },
        columns={UC_DRAW: {2025: [0.1, 0.9]}},
    )
    with pytest.raises(CoreRouteError, match="benunit identifier"):
        Simulation(dataset=path)


# --- Supplied periods -------------------------------------------------------


@pytest.mark.parametrize(
    "column, values",
    [
        (PIP_DRAW, [0.5] * 3),
        # Its default, 0.0, is a legal value: the export would store it.
        ("warm_home_discount_random_draw", [0.0] * 3),
        ("would_claim_student_loan", [True] * 3),
        (STATUS, [True] * 3),
        ("attends_private_school", [False] * 3),
    ],
)
def test_a_column_supplied_only_for_a_later_period_is_refused(column, values, tmp_path):
    path = core_file(
        tmp_path / "core.h5", columns={column: {2026: values}}, years=(2025, 2026)
    )
    with pytest.raises(CoreRouteError, match=f"{column} for 2026 but not for 2025"):
        Simulation(dataset=path)


def test_a_draw_that_changes_between_periods_is_refused(tmp_path):
    path = core_file(
        tmp_path / "core.h5",
        columns={PIP_DRAW: {2025: [0.1, 0.2, 0.3], 2026: [0.1, 0.2, 0.4]}},
        years=(2025, 2026),
    )
    with pytest.raises(CoreRouteError, match="differ from 2025"):
        Simulation(dataset=path)


def test_a_repeated_draw_and_a_changing_outcome_load(tmp_path):
    path = core_file(
        tmp_path / "core.h5",
        columns={
            PIP_DRAW: {2025: [0.1, 0.2, 0.3], 2026: [0.1, 0.2, 0.3]},
            STATUS: {2025: [True, False, True], 2026: [False, False, True]},
        },
        years=(2025, 2026),
    )
    sim = Simulation(dataset=path)
    np.testing.assert_array_equal(
        sim.calculate(PIP_DRAW, 2027), np.float32([0.1, 0.2, 0.3])
    )


def test_a_group_draw_repeated_in_another_row_order_loads(tmp_path):
    ids_2026 = {"benunit_id": [3, 1, 2]}
    with h5py.File(tmp_path / "core.h5", "w") as file:
        for year in (2025, 2026):
            for name in ID_COLUMNS:
                values = np.arange(1, 4)
                if year == 2026 and name in ids_2026:
                    values = np.asarray(ids_2026[name])
                file.create_dataset(f"{name}/{year}", data=values)
            file.create_dataset(f"age/{year}", data=np.full(3, 30))
            add_households(file, year, 3)
        file.create_dataset(f"{UC_DRAW}/2025", data=np.float32([0.1, 0.2, 0.3]))
        file.create_dataset(f"{UC_DRAW}/2026", data=np.float32([0.3, 0.1, 0.2]))
    sim = Simulation(dataset=str(tmp_path / "core.h5"))
    np.testing.assert_array_equal(
        sim.calculate(UC_DRAW, 2025), np.float32([0.1, 0.2, 0.3])
    )


# --- With/without differential on both routes --------------------------------


def legacy_streams(count):
    uc = np.random.default_rng(43).random(count)
    np.random.seed(42)
    pip = np.random.random(count)
    return uc, pip


def outputs(sim):
    modify_simulation(sim)
    result = {}
    for year in REBALANCING_YEARS:
        result[(STATUS, year)] = np.asarray(sim.calculate(STATUS, year))
        result[("uc_LCWRA_element", year)] = np.asarray(
            sim.calculate("uc_LCWRA_element", year)
        )
    for year in range(2025, 2030):
        result[("pip", year)] = np.asarray(sim.calculate("pip", year))
    return result


@pytest.mark.parametrize("route", ["frame", "core"])
def test_with_and_without_the_columns_agree_bit_for_bit(route, tmp_path):
    count = 120
    uc, pip = legacy_streams(count)
    uc_stored, uc_ok, _ = encode(uc, SHARE_GRID)
    pip_stored, pip_ok, _ = encode(pip, PIP_THRESHOLDS)
    assert uc_ok.all() and pip_ok.all()
    base = {
        "uc_limited_capability_for_WRA": {2025: np.ones(count, bool)},
        "pip": {2025: np.full(count, 1_000.0)},
    }
    stored = {UC_DRAW: {2025: uc_stored}, PIP_DRAW: {2025: pip_stored}}

    def build(columns, name):
        if route == "frame":
            return Simulation(
                dataset=one_person_units_frame(count=count, columns=columns)
            )
        return Simulation(
            dataset=core_file(tmp_path / f"{name}.h5", count=count, columns=columns)
        )

    without = outputs(build(base, "without"))
    with_columns_sim = build(base | stored, "with")
    np.testing.assert_array_equal(with_columns_sim.calculate(UC_DRAW, 2025), uc_stored)
    np.testing.assert_array_equal(
        with_columns_sim.calculate(PIP_DRAW, 2025), pip_stored
    )
    with_columns = outputs(with_columns_sim)
    assert without.keys() == with_columns.keys()
    for key in without:
        assert without[key].dtype == with_columns[key].dtype, key
        np.testing.assert_array_equal(with_columns[key], without[key], err_msg=str(key))
    # The decisions are the legacy streams' own.
    for year in REBALANCING_YEARS:
        share = with_columns_sim.tax_benefit_system.parameters.get_child(
            "gov.dwp.universal_credit.rebalancing.new_claimant_share"
        )(str(year))
        np.testing.assert_array_equal(without[(STATUS, year)], uc < share)
