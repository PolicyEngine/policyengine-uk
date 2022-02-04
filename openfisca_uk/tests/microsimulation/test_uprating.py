from openfisca_uk import Microsimulation
from openfisca_uk_data import FRSEnhanced
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

sim = Microsimulation(dataset=FRSEnhanced, year=2019)


@pytest.mark.parametrize(
    "variable,year", product(UPRATED_VARIABLES, range(2020, 2022))
)
def test_uprating(variable: str, year: int):
    assert any(
        sim.calc(variable, period=year).values
        != sim.calc(variable, period=2019).values
    )
