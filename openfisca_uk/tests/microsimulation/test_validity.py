from openfisca_uk import CountryTaxBenefitSystem, Microsimulation
from itertools import product
import pytest

YEARS = range(2017, 2022)

baseline = Microsimulation()


@pytest.mark.parametrize(
    "year,variable", product(YEARS, CountryTaxBenefitSystem().variables)
)
def test_not_nan(year, variable):
    assert ~baseline.calc(variable, period=year).isna().any()
