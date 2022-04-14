from openfisca_uk import Microsimulation
import pytest
from openfisca_uk.data import EnhancedFRS

YEARS = range(2022, 2026)

baseline = Microsimulation(dataset=EnhancedFRS, year=2022)


@pytest.mark.parametrize("year", YEARS)
def test_not_nan(year):
    for variable in baseline.simulation.tax_benefit_system.variables:
        assert ~baseline.calc(variable, period=year).isna().any()
