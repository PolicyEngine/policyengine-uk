from openfisca_uk import Microsimulation
from openfisca_uk_data import FRS
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

sim = Microsimulation(dataset=FRS, year=2018)


@pytest.mark.parametrize(
    "variable,year", product(UPRATED_VARIABLES, range(2019, 2022))
)
def test_uprating(variable: str, year: int):
    assert (
        sim.calc(variable, period=year).sum()
        != sim.calc(variable, period=2018).sum()
    )
