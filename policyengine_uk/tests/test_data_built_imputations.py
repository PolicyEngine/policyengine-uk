"""Imputations that apply to simulations built from data, not to situations.

UC deduction draws and private school attendance are imputed across a
population. How the simulation was built decides whether they apply, not how
much weight it carries: a constituency or local authority filtered from the
national data (as policyengine.py's RowFilterStrategy does) carries well under
a million people of weight and is still data.
"""

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from policyengine_uk import Microsimulation, Simulation
from policyengine_uk.data import (
    UKMultiYearDataset,
    UKSingleYearDataset,
    filter_dataset,
)
from policyengine_uk.utils.data_source import built_from_data
from policyengine_uk.utils.stochastic import splitmix64_uniform

YEAR = 2025
REGIONS = np.array(["LONDON", "NORTH_EAST", "SCOTLAND", "WALES"])
DRAWS = ("uc_deduction_random_draw", "uc_deduction_type_random_draw")
UC_OUTPUTS = (
    *DRAWS,
    "uc_has_deduction",
    "uc_deduction_combination",
    "uc_deductions",
)
# Weight per household for a national-scale population: 400 households carry
# about 1.6m of weight. One region (a quarter of them) carries about 0.4m, or
# 0.8m of people, under the old threshold of a million for both.
NATIONAL_SCALE = 3_500
SITUATION = {
    "people": {
        "adult": {"age": {YEAR: 35}},
        "child": {
            "age": {YEAR: 10},
            "attends_private_school_random_draw": {YEAR: 0},
        },
    },
    "benunits": {
        "benunit": {
            "members": ["adult", "child"],
            "would_claim_uc": {YEAR: True},
            "universal_credit_pre_benefit_cap": {YEAR: 6_000},
            "benefit_cap_reduction": {YEAR: 0},
        }
    },
    "households": {
        "household": {
            "members": ["adult", "child"],
            "household_weight": {YEAR: 1e9},
        }
    },
}


def tables(n: int = 400, weight_scale: float = 1.0) -> dict:
    """n households of one adult and one child, all on Universal Credit, with
    incomes spread from 0 to 150k and draws for private school attendance."""
    ids = np.arange(n)
    rng = np.random.default_rng(0)
    person = pd.DataFrame(
        {
            "person_id": np.concatenate([ids * 10 + 1, ids * 10 + 2]),
            "person_benunit_id": np.concatenate([ids, ids]),
            "person_household_id": np.concatenate([ids, ids]),
            "age": np.concatenate([np.full(n, 35), np.full(n, 10)]),
            "employment_income": np.concatenate(
                [np.linspace(0, 150_000, n), np.zeros(n)]
            ),
            "attends_private_school_random_draw": np.concatenate(
                [np.ones(n), rng.uniform(0, 0.5, n)]
            ),
        }
    )
    benunit = pd.DataFrame(
        {
            "benunit_id": ids,
            "would_claim_uc": np.ones(n, dtype=bool),
            "universal_credit_pre_benefit_cap": np.full(n, 6_000.0),
            "benefit_cap_reduction": np.zeros(n),
        }
    )
    household = pd.DataFrame(
        {
            "household_id": ids,
            "household_weight": weight_scale * rng.lognormal(0, 0.5, n),
            "region": REGIONS[ids % len(REGIONS)],
        }
    )
    return {"person": person, "benunit": benunit, "household": household}


def multi_year(t: dict) -> UKMultiYearDataset:
    # Copies: building encodes enum columns in place.
    year = UKSingleYearDataset(
        person=t["person"].copy(),
        benunit=t["benunit"].copy(),
        household=t["household"].copy(),
        fiscal_year=YEAR,
    )
    return UKMultiYearDataset(datasets=[year])


def data_simulation(t: dict) -> Microsimulation:
    return Microsimulation(dataset=multi_year(t))


def row_filter(t: dict, keep) -> dict:
    """Keep households where keep(household table) holds, with their benefit
    units and people: what policyengine.py does for a constituency."""
    household = t["household"][keep(t["household"])]
    person = t["person"][t["person"].person_household_id.isin(household.household_id)]
    benunit = t["benunit"][t["benunit"].benunit_id.isin(person.person_benunit_id)]
    return {
        "person": person.reset_index(drop=True),
        "benunit": benunit.reset_index(drop=True),
        "household": household.reset_index(drop=True),
    }


def values(sim, variable: str) -> np.ndarray:
    return np.asarray(sim.calculate(variable, YEAR))


@pytest.fixture(scope="module")
def national():
    t = tables(weight_scale=NATIONAL_SCALE)
    assert t["household"].household_weight.sum() > 1e6
    return t, data_simulation(t)


def test_small_data_built_simulation_gets_hashed_draws():
    small = tables(weight_scale=1e-3)
    assert small["household"].household_weight.sum() < 1e6
    sim = data_simulation(small)
    ids = small["benunit"].benunit_id.values
    for salt, draw in enumerate(DRAWS):
        expected = splitmix64_uniform(ids, salt=salt).astype(np.float32)
        assert np.array_equal(values(sim, draw), expected), draw
    # Every benefit unit is on UC, so some have deductions.
    assert values(sim, "uc_deductions").max() > 0
    assert values(sim, "attends_private_school").any()


@settings(max_examples=6, deadline=None)
@given(power=st.integers(min_value=-14, max_value=30))
def test_imputations_do_not_depend_on_total_weight(national, power):
    """Scaling every weight by the same factor changes nothing: hashed draws
    depend only on ids, and income percentiles only on relative weights.
    Powers of two scale exactly in floating point, so this holds exactly for
    totals from about a hundred to about 10^15."""
    t, reference = national
    sim = data_simulation(tables(weight_scale=NATIONAL_SCALE * 2.0**power))
    for variable in (*UC_OUTPUTS, "attends_private_school"):
        assert np.array_equal(values(sim, variable), values(reference, variable)), (
            variable
        )


def test_region_filtered_from_data_matches_the_national_run(national):
    """Every benefit unit in a region filtered from the data has the UC
    deductions it has in the national simulation."""
    t, sim = national
    region = row_filter(t, lambda h: h.region == "LONDON")
    # A small share of a national-sized population: under the old threshold
    # for benefit units, and for people (the old private school test summed
    # household weight over people).
    weight = region["household"].set_index("household_id").household_weight
    assert weight.loc[region["person"].person_household_id].sum() < 1e6
    regional = data_simulation(region)
    kept = np.isin(t["benunit"].benunit_id, region["benunit"].benunit_id)
    for variable in UC_OUTPUTS:
        assert np.array_equal(
            values(regional, variable), values(sim, variable)[kept]
        ), variable
    assert values(regional, "uc_deductions").max() > 0
    # Private school attendance ranks incomes within the simulated population,
    # so a region ranks against itself; it is still imputed.
    assert values(regional, "attends_private_school").any()


def test_extracted_household_keeps_its_imputations(national):
    """filter_dataset extracts one household from the data. Its UC draws hash
    the same ids, and it carries its private school attendance across rather
    than ranking at the 100th percentile of a population of one."""
    t, sim = national
    attends = values(sim, "attends_private_school")
    person_household = values(sim, "person_household_id")
    deductions = pd.Series(
        values(sim, "uc_deductions"), index=values(sim, "benunit_id")
    )
    # One benefit unit per household, sharing its id.
    with_deductions = deductions.index[deductions > 0]
    attending = np.unique(person_household[attends])
    not_attending = np.setdiff1d(values(sim, "household_id"), attending)
    assert len(with_deductions) and len(attending)
    for household in [*with_deductions[:3], *attending[:3], *not_attending[-3:]]:
        extract = filter_dataset(sim, household_id=int(household), year=YEAR)
        extracted = Microsimulation(dataset=UKMultiYearDataset(datasets=[extract]))
        assert np.array_equal(
            values(extracted, "uc_deductions"),
            deductions.loc[values(extracted, "benunit_id")].values,
        )
        assert np.array_equal(
            values(extracted, "attends_private_school"),
            attends[person_household == household],
        )


def test_data_without_weight_attends_no_private_school():
    """Every household at zero weight: no income ranking is possible, so no
    household reaches a percentile with a positive rate, and nothing fails."""
    sim = data_simulation(tables(n=40, weight_scale=0))
    assert not values(sim, "attends_private_school").any()
    ids = values(sim, "benunit_id")
    assert np.array_equal(
        values(sim, "uc_deduction_random_draw"),
        splitmix64_uniform(ids, salt=0).astype(np.float32),
    )


def test_situations_get_defaults_whatever_their_weight():
    """A household situation is not data, even with the weight of a nation."""
    sim = Simulation(situation=SITUATION)
    assert not built_from_data(sim)
    for draw in DRAWS:
        assert values(sim, draw)[0] == 1.0
    assert values(sim, "uc_deductions")[0] == 0
    assert not values(sim, "attends_private_school").any()


def calculate_imputations(sim) -> None:
    """Fill the simulation's caches for its current population."""
    for variable in (
        *DRAWS,
        "attends_private_school",
        "months_since_last_birthday",
        "person_weight",
        "is_male",
    ):
        values(sim, variable)


def test_rebuilding_in_place_follows_the_new_source():
    """The builders set the flag and drop what was cached for the old
    population, so a calculated clone rebuilt from a situation gets household
    defaults, and one rebuilt from data gets the imputations."""
    data = tables(n=40, weight_scale=NATIONAL_SCALE)
    sim = data_simulation(data).clone()
    calculate_imputations(sim)
    sim.build_from_situation(SITUATION)
    assert not built_from_data(sim)
    for draw in DRAWS:
        assert values(sim, draw)[0] == 1.0
    assert not values(sim, "attends_private_school").any()

    assert values(sim, "months_since_last_birthday").tolist() == [6, 6]

    sim = Simulation(situation=SITUATION).clone()
    calculate_imputations(sim)
    sim.build_from_multi_year_dataset(multi_year(data))
    assert built_from_data(sim)
    assert values(sim, "months_since_last_birthday").shape == (80,)
    ids = values(sim, "benunit_id")
    for salt, draw in enumerate(DRAWS):
        expected = splitmix64_uniform(ids, salt=salt).astype(np.float32)
        assert np.array_equal(values(sim, draw), expected), draw
    assert values(sim, "attends_private_school").any()


def test_core_simulation_over_data_gets_imputations():
    """A policyengine-core Simulation built over the UK system from data
    records is_over_dataset rather than built_from_dataset."""
    from policyengine_core.simulations import Simulation as CoreSimulation

    from policyengine_uk.system import system

    t = tables(n=40, weight_scale=NATIONAL_SCALE)
    frame = (
        t["person"]
        .merge(t["benunit"], left_on="person_benunit_id", right_on="benunit_id")
        .merge(t["household"], left_on="person_household_id", right_on="household_id")
    )
    sim = CoreSimulation(
        tax_benefit_system=system,
        dataset=frame.rename(columns=lambda column: f"{column}__{YEAR}"),
    )
    assert built_from_data(sim)
    ids = values(sim, "benunit_id")
    for salt, draw in enumerate(DRAWS):
        expected = splitmix64_uniform(ids, salt=salt).astype(np.float32)
        assert np.array_equal(values(sim, draw), expected), draw
    assert values(sim, "attends_private_school").any()
