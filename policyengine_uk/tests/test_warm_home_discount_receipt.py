"""Warm Home Discount receipt draws follow how a simulation was built, not
how much weight it carries.

A constituency or region filtered from the national data (as policyengine.py's
RowFilterStrategy does) carries well under a million households of weight and
is still data: each household keeps the draw, rebate and HBAI income it has in
the national run. Household situations get a draw of 0, below any receipt
rate, so calculators show the rebate unless the draw is set.
"""

import numpy as np
import pandas as pd
import pytest

from policyengine_uk import Microsimulation, Simulation
from policyengine_uk.data import UKMultiYearDataset, UKSingleYearDataset
from policyengine_uk.utils.data_source import built_from_data
from policyengine_uk.utils.stochastic import splitmix64_uniform

YEAR = 2026
REGIONS = np.array(["LONDON", "NORTH_EAST", "WALES", "SOUTH_WEST"])
# 400 households at this weight carry about 1.6m households of weight; one
# region (a quarter of them) about 0.4m, under the old cutoff of a million.
NATIONAL_SCALE = 3_500
OUTPUTS = (
    "warm_home_discount_random_draw",
    "would_receive_warm_home_discount",
    "warm_home_discount",
    "hbai_household_net_income",
)


def tables(n: int = 400) -> dict:
    """n single adults aged 35 with no earnings, all on Universal Credit, in
    England and Wales."""
    ids = np.arange(n)
    rng = np.random.default_rng(0)
    person = pd.DataFrame(
        {
            "person_id": ids * 10 + 1,
            "person_benunit_id": ids,
            "person_household_id": ids,
            "age": np.full(n, 35),
            "employment_income": np.zeros(n),
        }
    )
    benunit = pd.DataFrame(
        {
            "benunit_id": ids,
            "would_claim_uc": np.ones(n, dtype=bool),
            "universal_credit_pre_benefit_cap": np.full(n, 5_000.0),
            "uc_benefit_cap_reduction": np.zeros(n),
        }
    )
    household = pd.DataFrame(
        {
            "household_id": ids,
            "household_weight": NATIONAL_SCALE * rng.lognormal(0, 0.5, n),
            "region": REGIONS[ids % len(REGIONS)],
        }
    )
    return {"person": person, "benunit": benunit, "household": household}


def simulation(t: dict) -> Microsimulation:
    # Copies: building encodes enum columns in place.
    year = UKSingleYearDataset(
        person=t["person"].copy(),
        benunit=t["benunit"].copy(),
        household=t["household"].copy(),
        fiscal_year=YEAR,
    )
    return Microsimulation(dataset=UKMultiYearDataset(datasets=[year]))


def region_of(t: dict, region: str) -> dict:
    """Keep one region's households with their benefit units and people."""
    household = t["household"][t["household"].region == region]
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
    t = tables()
    assert t["household"].household_weight.sum() > 1e6
    return t, simulation(t)


def test_national_data_gets_hashed_draws(national):
    t, sim = national
    ids = t["household"].household_id.values
    expected = splitmix64_uniform(ids, salt=2).astype(np.float32)
    assert np.array_equal(values(sim, "warm_home_discount_random_draw"), expected)
    rebate = values(sim, "warm_home_discount")
    # Everyone is on Universal Credit; about 70% receive the rebate.
    assert set(np.unique(rebate)) == {0, 150}
    assert 0.6 < (rebate > 0).mean() < 0.8


def test_region_filtered_from_data_matches_the_national_run(national):
    """Each household in a region filtered from the data keeps its draw,
    rebate and HBAI income from the national run, including the households
    whose draw is above the receipt rate and so get no rebate."""
    t, sim = national
    region = region_of(t, "LONDON")
    assert region["household"].household_weight.sum() < 1e6
    regional = simulation(region)
    assert built_from_data(regional)
    kept = np.isin(t["household"].household_id, region["household"].household_id)
    for variable in OUTPUTS:
        assert np.array_equal(
            values(regional, variable), values(sim, variable)[kept]
        ), variable
    rebate = values(regional, "warm_home_discount")
    assert (rebate == 0).any() and (rebate == 150).any()


def test_situations_receive_the_rebate_unless_the_draw_is_set():
    situation = {
        "people": {"adult": {"age": {YEAR: 35}}},
        "benunits": {
            "benunit": {
                "members": ["adult"],
                "would_claim_uc": {YEAR: True},
                "universal_credit_pre_benefit_cap": {YEAR: 5_000},
                "uc_benefit_cap_reduction": {YEAR: 0},
            }
        },
        "households": {
            "household": {
                "members": ["adult"],
                "region": {YEAR: "LONDON"},
                # A situation is not data, even with the weight of a nation.
                "household_weight": {YEAR: 1e9},
            }
        },
    }
    sim = Simulation(situation=situation)
    assert not built_from_data(sim)
    assert values(sim, "warm_home_discount_random_draw")[0] == 0
    assert values(sim, "warm_home_discount")[0] == 150
