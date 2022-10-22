from policyengine_uk import Microsimulation
from policyengine_uk.data import EnhancedFRS
import pytest
from itertools import product

UPRATED_VARIABLES = (
    "council_tax",
    "employment_income",
    "pension_income",
    "self_employment_income",
    "property_income",
    "savings_interest_income",
    "dividend_income",
)

sim = Microsimulation(dataset=EnhancedFRS, dataset_year=2022)


@pytest.mark.parametrize(
    "variable,year", product(UPRATED_VARIABLES, range(2023, 2026))
)
def test_uprating(variable: str, year: int):
    assert any(
        sim.calc(variable, period=year).values
        != sim.calc(variable, period=2022).values
    )
