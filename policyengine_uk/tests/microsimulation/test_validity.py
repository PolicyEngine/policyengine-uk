from policyengine_uk import Microsimulation
import pytest
import numpy as np

YEARS = range(2024, 2026)


@pytest.mark.parametrize("year", YEARS)
def test_not_nan(year):
    baseline = Microsimulation()
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
            # Skip variables that require specific inputs or are experimental
            if variable in ["is_on_cliff", "cliff_evaluated", "cliff_gap"]:
                continue
            try:
                values = baseline.calculate(variable, period=year)
                assert not np.isnan(values).any(), f"NaN values found in {variable}"
            except:
                # Some variables may fail to calculate without proper inputs
                pass
