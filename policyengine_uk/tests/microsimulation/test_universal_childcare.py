from policyengine import Simulation
import pytest


def test_universal_childcare_entitlement_aggregate():
    """
    Test that the total universal childcare entitlement has a reasonable value.
    """
    sim = Simulation(scope="macro", country="uk", time_period= "2024")
    sim = sim.baseline_simulation
    year = 2024
    
    # Calculate individual entitlements and sum them up
    individual_entitlements = sim.calculate("universal_childcare_entitlement", period=year)
    total_entitlement = individual_entitlements.sum()
    
    lower_bound = 2_200_000_000
    upper_bound = 3_000_000_000
    
    assert lower_bound <= total_entitlement <= upper_bound, (
        f"Universal childcare entitlement total (£{total_entitlement:,.1f}) "
        f"is outside the expected range of £{lower_bound:,.1f} to £{upper_bound:,.1f}"
    )