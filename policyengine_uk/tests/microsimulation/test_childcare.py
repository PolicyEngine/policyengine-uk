from policyengine import Simulation
import pytest


def test_universal_childcare_entitlement_aggregate():
    """
    Test that the total universal childcare entitlement has a reasonable value.
    """
    sim = Simulation(scope="macro", country="uk", time_period="2024")
    sim = sim.baseline_simulation
    year = 2024

    # Hard coded take-up rate
    # Move this take-up rate to the uk-data package
    universal_childcare_entitlement_take_up_rate = 0.6

    # Calculate individual entitlements and sum them up
    individual_entitlements = sim.calculate(
        "universal_childcare_entitlement", period=year
    )

    # Apply the take-up rate to the total
    total_entitlement = (
        individual_entitlements.sum()
        * universal_childcare_entitlement_take_up_rate
    )

    lower_bound = 1_500_000_000
    upper_bound = 2_000_000_000

    print(f"Universal childcare entitlement total: £{total_entitlement:,.2f}")

    assert lower_bound <= total_entitlement <= upper_bound, (
        f"Universal childcare entitlement total (£{total_entitlement:,.1f}) "
        f"is outside the expected range of £{lower_bound:,.1f} to £{upper_bound:,.1f}"
    )


def test_extended_childcare_entitlement_aggregate():
    """
    Test that the total extended childcare entitlement has a reasonable value.
    """
    sim = Simulation(scope="macro", country="uk", time_period="2024")
    sim = sim.baseline_simulation
    year = 2024

    # Hard coded take-up rate
    extended_childcare_entitlement_take_up_rate = 0.6

    # Calculate individual entitlements and sum them up
    individual_entitlements = sim.calculate(
        "extended_childcare_entitlement", period=year
    )

    # Apply the take-up rate to the total
    total_entitlement = (
        individual_entitlements.sum()
        * extended_childcare_entitlement_take_up_rate
    )

    lower_bound = 2_800_000_000
    upper_bound = 3_300_000_000

    print(f"Extended childcare entitlement total: £{total_entitlement:,.2f}")

    assert lower_bound <= total_entitlement <= upper_bound, (
        f"Extended childcare entitlement total (£{total_entitlement:,.1f}) "
        f"is outside the expected range of £{lower_bound:,.1f} to £{upper_bound:,.1f}"
    )


def test_targeted_childcare_entitlement_aggregate():
    """
    Test that the total targeted childcare entitlement has a reasonable value.
    """
    sim = Simulation(scope="macro", country="uk", time_period="2024")
    sim = sim.baseline_simulation
    year = 2024

    # Hard coded take-up rate
    targeted_childcare_entitlement_take_up_rate = 0.6

    # Calculate individual entitlements and sum them up
    individual_entitlements = sim.calculate(
        "targeted_childcare_entitlement", period=year
    )

    # Apply the take-up rate to the total
    total_entitlement = (
        individual_entitlements.sum()
        * targeted_childcare_entitlement_take_up_rate
    )

    lower_bound = 400_000_000
    upper_bound = 700_000_000

    print(f"Targeted childcare entitlement total: £{total_entitlement:,.2f}")

    assert lower_bound <= total_entitlement <= upper_bound, (
        f"Targeted childcare entitlement total (£{total_entitlement:,.1f}) "
        f"is outside the expected range of £{lower_bound:,.1f} to £{upper_bound:,.1f}"
    )


def test_care_to_learn_childcare_entitlement_aggregate():
    """
    Test that the total Care to Learn childcare entitlement has a reasonable value.
    """
    sim = Simulation(scope="macro", country="uk", time_period="2024")
    sim = sim.baseline_simulation
    year = 2024

    # Hard coded take-up rate
    care_to_learn_take_up_rate = 0.6

    # Calculate individual entitlements and sum them up
    individual_entitlements = sim.calculate("care_to_learn", period=year)

    # Apply the take-up rate to the total
    total_entitlement = (
        individual_entitlements.sum() * care_to_learn_take_up_rate
    )

    # Currently, the entitlement is zero, so we test for that
    # If implementation changes in the future, update these bounds
    lower_bound = 0
    upper_bound = 1_000_000

    print(
        f"Care to Learn childcare entitlement total: £{total_entitlement:,.2f}"
    )

    assert lower_bound <= total_entitlement <= upper_bound, (
        f"Care to Learn childcare entitlement total (£{total_entitlement:,.1f}) "
        f"is outside the expected range of £{lower_bound:,.1f} to £{upper_bound:,.1f}"
    )


def test_tax_free_childcare_aggregate():
    """
    Test that the total tax-free childcare entitlement has a reasonable value.
    """
    sim = Simulation(scope="macro", country="uk", time_period="2024")
    sim = sim.baseline_simulation
    year = 2024

    # Hard coded take-up rate
    tax_free_childcare_take_up_rate = 0.6

    # Calculate individual entitlements and sum them up
    individual_entitlements = sim.calculate("tax_free_childcare", period=year)

    # Apply the take-up rate to the total
    total_entitlement = (
        individual_entitlements.sum() * tax_free_childcare_take_up_rate
    )

    # Expected range for tax-free childcare
    lower_bound = 300_000_000
    upper_bound = 600_000_000

    print(f"Tax-free childcare entitlement total: £{total_entitlement:,.2f}")

    assert lower_bound <= total_entitlement <= upper_bound, (
        f"Tax-free childcare entitlement total (£{total_entitlement:,.1f}) "
        f"is outside the expected range of £{lower_bound:,.1f} to £{upper_bound:,.1f}"
    )
