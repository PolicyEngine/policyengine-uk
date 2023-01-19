from policyengine_uk import Microsimulation
import pytest
from policyengine_uk.data import EnhancedFRS

YEARS = range(2022, 2026)

baseline = Microsimulation(dataset=EnhancedFRS, dataset_year=2022)


@pytest.mark.parametrize("year", YEARS)
def test_not_nan(year):
    for variable in baseline.tax_benefit_system.variables:
        if (
            baseline.tax_benefit_system.variables[variable].definition_period
            == "year"
        ):
            assert ~baseline.calc(variable, period=year).isna().any()
