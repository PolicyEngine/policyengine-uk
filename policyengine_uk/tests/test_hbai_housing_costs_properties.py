"""HBAI AHC deducts every housing cost once, including service charges.

BHC is supplied directly to isolate the housing-cost contract from the
calculation and zero floor of income before housing costs. Each vector
population contains a household with zero BHC and positive service charges.
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

PROPERTY_SETTINGS = settings(
    max_examples=16,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow],
)

# Keep this independent of the production variable's subtracts list: importing
# that list would allow a missing deduction to disappear from the oracle too.
HOUSING_COSTS = (
    "rent",
    "water_and_sewerage_charges",
    "mortgage_interest_repayment",
    "structural_insurance_payments",
    "housing_service_charges",
)


def money(maximum):
    return st.integers(0, maximum * 100).map(lambda pennies: pennies / 100)


households = st.fixed_dictionaries(
    {
        "hbai_household_net_income": money(120_000),
        "rent": money(30_000),
        "water_and_sewerage_charges": money(2_000),
        "mortgage_interest_repayment": money(20_000),
        "structural_insurance_payments": money(3_000),
        "housing_service_charges": money(10_000),
        "household_equivalisation_ahc": st.sampled_from([0.58, 1.0, 1.2, 1.42]),
    }
)
ZERO_BHC_HOUSEHOLD = {
    "hbai_household_net_income": 0,
    "rent": 6_000,
    "water_and_sewerage_charges": 400,
    "mortgage_interest_repayment": 0,
    "structural_insurance_payments": 0,
    "housing_service_charges": 1_200,
    "household_equivalisation_ahc": 0.58,
}
populations = st.lists(households, min_size=1, max_size=4).map(
    lambda generated: [ZERO_BHC_HOUSEHOLD, *generated]
)


def situation(population, year, extra_service_charges=0):
    people, benunits, homes = {}, {}, {}
    for index, household in enumerate(population):
        person = f"person_{index}"
        people[person] = {"age": {year: 40}}
        benunits[f"benunit_{index}"] = {"members": [person]}
        inputs = dict(household)
        inputs["housing_service_charges"] += extra_service_charges
        homes[f"household_{index}"] = {
            "members": [person],
            **{name: {year: amount} for name, amount in inputs.items()},
        }
    return {"people": people, "benunits": benunits, "households": homes}


def supplied_amounts(population, name, extra=0):
    # Variable inputs are stored as float32. Sum them independently in float64
    # so the oracle allows only the model's float32 arithmetic rounding.
    return np.asarray(
        [household[name] + extra for household in population], dtype=np.float32
    ).astype(np.float64)


@pytest.mark.parametrize("year", [2024, 2025, 2026])
@PROPERTY_SETTINGS
@given(population=populations)
def test_ahc_never_exceeds_bhc_less_housing_costs(population, year):
    simulation = Simulation(situation=situation(population, year))
    bhc = supplied_amounts(population, "hbai_household_net_income")
    housing_costs = sum(supplied_amounts(population, name) for name in HOUSING_COSTS)
    expected = bhc - housing_costs
    actual = np.asarray(simulation.calculate("hbai_household_net_income_ahc", year))
    tolerance = np.maximum(
        0.01, 4 * np.finfo(np.float32).eps * (np.abs(bhc) + housing_costs)
    )

    assert np.all(actual <= expected + tolerance)
    assert np.all(np.abs(actual - expected) <= tolerance)
    assert actual[0] == -7_600

    equivalisation = supplied_amounts(population, "household_equivalisation_ahc")
    equivalised = np.asarray(
        simulation.calculate("equiv_hbai_household_net_income_ahc", year)
    )
    np.testing.assert_allclose(
        equivalised, expected / equivalisation, rtol=1e-6, atol=0.03
    )


@pytest.mark.parametrize("year", [2024, 2025, 2026])
@PROPERTY_SETTINGS
@given(population=populations, extra=money(10_000))
def test_extra_service_charges_reduce_ahc_by_the_same_amount(population, extra, year):
    before = Simulation(situation=situation(population, year))
    after = Simulation(situation=situation(population, year, extra))
    before_ahc = np.asarray(before.calculate("hbai_household_net_income_ahc", year))
    after_ahc = np.asarray(after.calculate("hbai_household_net_income_ahc", year))
    extra_input = supplied_amounts(population, "housing_service_charges", extra)
    extra_input -= supplied_amounts(population, "housing_service_charges")

    assert np.all(after_ahc <= before_ahc)
    np.testing.assert_allclose(
        before_ahc - after_ahc, extra_input, rtol=1e-6, atol=0.03
    )
