"""Shares of national totals on the certified dataset (policyengine-uk#2896).

Over a whole UK dataset, shareholding and consumption_shareholding sum to one
at the dataset's weights. A part of the UK taken from a dataset that carries
its UK totals (add_uk_totals) gets the same allocations as in the UK run.
"""

import numpy as np
import pytest

from policyengine_uk import Microsimulation
from policyengine_uk.utils.uk_totals import add_uk_totals

YEAR = 2026
ALLOCATIONS = [
    "shareholding",
    "corporate_land_value",
    "business_rates",
    "corporate_sdlt",
]


@pytest.fixture(scope="module")
def uk():
    return Microsimulation()


@pytest.mark.microsimulation
def test_weighted_shares_sum_to_one(uk):
    weight = np.asarray(uk.calculate("household_weight", YEAR))
    for variable in ["shareholding", "consumption_shareholding"]:
        share = np.asarray(uk.calculate(variable, YEAR))
        assert np.sum(share * weight) == pytest.approx(1, rel=1e-6), variable


@pytest.mark.microsimulation
def test_corporate_land_value_is_the_shareholding_of_corporate_land(uk):
    land = uk.tax_benefit_system.parameters(f"{YEAR}-01-01").household.wealth.land
    expected = (
        np.asarray(uk.calculate("shareholding", YEAR))
        * land.value.aggregate_corporate_land_value
    )
    assert np.asarray(uk.calculate("corporate_land_value", YEAR)) == pytest.approx(
        expected, rel=1e-6
    )


@pytest.mark.microsimulation
def test_a_nation_carrying_the_uk_totals_gets_its_uk_run_allocations(uk):
    dataset = add_uk_totals(uk.dataset[YEAR])
    in_scotland = (dataset.household["region"].astype(str) == "SCOTLAND").to_numpy()
    scotland = dataset.copy()
    scotland.household = scotland.household[in_scotland]
    kept = set(scotland.household.household_id)
    scotland.person = scotland.person[scotland.person.person_household_id.isin(kept)]
    scotland.benunit = scotland.benunit[
        scotland.benunit.benunit_id.isin(set(scotland.person.person_benunit_id))
    ]
    alone = Microsimulation(dataset=scotland)

    position = {
        household_id: i
        for i, household_id in enumerate(np.asarray(uk.calculate("household_id", YEAR)))
    }
    rows = [position[i] for i in np.asarray(alone.calculate("household_id", YEAR))]
    for variable in ALLOCATIONS:
        in_uk_run = np.asarray(uk.calculate(variable, YEAR))[rows]
        assert np.asarray(alone.calculate(variable, YEAR)) == pytest.approx(
            in_uk_run, rel=1e-4
        ), variable
