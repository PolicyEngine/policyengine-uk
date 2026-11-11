"""Corporate land value is the household's shareholding of the land UK
corporations hold.

Shares sum to one only over a population, so the allocation tests build small
datasets. A household situation has no population to take a share of: it
holds no corporate land unless shareholding is set (policyengine-uk#2896).
"""

import pandas as pd
import pytest

from policyengine_uk import Simulation
from policyengine_uk.data import UKSingleYearDataset

YEAR = 2025


def dataset_simulation(households, people=None, reform=None):
    """A simulation built from data, one person per household."""
    n = len(households)
    people = people or [{} for _ in range(n)]
    person = {
        "person_id": list(range(1, n + 1)),
        "person_benunit_id": list(range(1, n + 1)),
        "person_household_id": list(range(1, n + 1)),
        "age": [40 + 10 * i for i in range(n)],
    }
    for name in sorted(set().union(*people)):
        person[name] = [p.get(name, 0) for p in people]
    household = {
        "household_id": list(range(1, n + 1)),
        # Columns dataset uprating reads.
        "region": ["LONDON"] * n,
        "council_tax": [0.0] * n,
        "rent": [0.0] * n,
        "tenure_type": ["OWNED_OUTRIGHT"] * n,
        "household_owns_tv": [False] * n,
    }
    for name in sorted(set().union(*households)):
        household[name] = [h.get(name, 0) for h in households]
    return Simulation(
        dataset=UKSingleYearDataset(
            person=pd.DataFrame(person),
            benunit=pd.DataFrame({"benunit_id": list(range(1, n + 1))}),
            household=pd.DataFrame(household),
            fiscal_year=YEAR,
        ),
        reform=reform,
    )


def aggregate_corporate_land_value(sim):
    land = sim.tax_benefit_system.parameters(str(YEAR)).household.wealth.land.value
    return land.aggregate_corporate_land_value


def test_corporate_land_value_matches_aggregate_for_weighted_dataset():
    sim = dataset_simulation(
        [
            {"corporate_wealth": 100_000, "household_weight": 2},
            {"corporate_wealth": 300_000, "household_weight": 1},
        ]
    )

    corporate_land_value = sim.calculate("corporate_land_value", YEAR)
    household_weight = sim.calculate("household_weight", YEAR)
    aggregate = aggregate_corporate_land_value(sim)

    assert corporate_land_value[0] == pytest.approx(aggregate * 0.2)
    assert corporate_land_value[1] == pytest.approx(aggregate * 0.6)
    assert (corporate_land_value * household_weight).sum() == pytest.approx(aggregate)


def test_corporate_land_value_is_zero_without_corporate_wealth():
    sim = dataset_simulation([{"corporate_wealth": 0, "household_weight": 1}])

    assert sim.calculate("corporate_land_value", YEAR)[0] == 0


def test_corporate_land_value_key_is_unchanged_by_the_pension_split():
    """Moving wealth between corporate_wealth and private_pension_wealth must not
    move corporate land value: the allocation key is corporate_sector_wealth."""

    def land_values(household_1: dict, household_2: dict):
        sim = dataset_simulation(
            [
                {"household_weight": 2, **household_1},
                {"household_weight": 1, **household_2},
            ]
        )
        return (
            sim.calculate("corporate_land_value", YEAR),
            sim.calculate("shareholding", YEAR),
        )

    folded_land, folded_share = land_values(
        {"corporate_wealth": 100_000},
        {"corporate_wealth": 300_000},
    )
    split_land, split_share = land_values(
        {"corporate_wealth": 20_000, "private_pension_wealth": 80_000},
        {"corporate_wealth": 50_000, "private_pension_wealth": 250_000},
    )

    assert folded_share[0] > 0
    assert split_land[0] == pytest.approx(folded_land[0])
    assert split_land[1] == pytest.approx(folded_land[1])
    assert split_share[0] == pytest.approx(folded_share[0])
    assert split_share[1] == pytest.approx(folded_share[1])


def test_employer_ni_capital_incidence_is_unchanged_by_the_pension_split():
    """The employer-NI capital response allocates by corporate_sector_wealth,
    so moving wealth between corporate_wealth and private_pension_wealth must
    not move any household's incidence."""
    reform = {
        "gov.hmrc.national_insurance.class_1.employer_scale[1].rate": {
            f"{YEAR}-01-01.{YEAR}-12-31": 0.25
        },
        "gov.contrib.policyengine.employer_ni.employee_incidence": {f"{YEAR}": 0.5},
        "gov.contrib.policyengine.employer_ni.capital_incidence": {f"{YEAR}": 0.5},
    }
    people = [{"employment_income": 30_000}, {"employment_income": 60_000}]

    def incidence(household_1: dict, household_2: dict):
        sim = dataset_simulation(
            [
                {"household_weight": 2, **household_1},
                {"household_weight": 1, **household_2},
            ],
            people=people,
            reform=reform,
        )
        return sim.calculate("employer_ni_response_capital_incidence", YEAR)

    folded = incidence(
        {"corporate_wealth": 100_000},
        {"corporate_wealth": 300_000},
    )
    split = incidence(
        {"corporate_wealth": 20_000, "private_pension_wealth": 80_000},
        {"corporate_wealth": 50_000, "private_pension_wealth": 250_000},
    )

    assert folded[0] != 0
    assert split[0] == pytest.approx(folded[0])
    assert split[1] == pytest.approx(folded[1])


def test_situation_holds_corporate_land_only_where_shareholding_is_set():
    def corporate_land(**household):
        sim = Simulation(
            situation={
                "people": {"person": {"age": {YEAR: 40}}},
                "benunits": {"benunit": {"members": ["person"]}},
                "households": {
                    "household": {
                        "members": ["person"],
                        "corporate_wealth": {YEAR: 300_000},
                        **{name: {YEAR: value} for name, value in household.items()},
                    }
                },
            }
        )
        return sim.calculate("corporate_land_value", YEAR)[0], sim

    unset, _ = corporate_land()
    set_value, sim = corporate_land(shareholding=1e-6)

    assert unset == 0
    assert set_value == pytest.approx(1e-6 * aggregate_corporate_land_value(sim))
