from policyengine_uk import Microsimulation
import pytest
from policyengine_uk.data import EnhancedFRS

YEARS = range(2023, 2026)

baseline = Microsimulation(dataset=EnhancedFRS)


@pytest.mark.parametrize("year", YEARS)
def test_not_nan(year):
    for variable in baseline.tax_benefit_system.variables:
        requires_computation_after = baseline.tax_benefit_system.variables[
            variable
        ].requires_computation_after
        if requires_computation_after:
            continue
        if (
            baseline.tax_benefit_system.variables[variable].definition_period
            == "year"
        ):
            assert ~baseline.calc(variable, period=year).isna().any()
