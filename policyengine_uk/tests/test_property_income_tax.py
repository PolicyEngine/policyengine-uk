"""Test that property_income_tax is properly included in total income_tax."""

from policyengine_uk import Microsimulation


def test_property_income_tax_included_in_total_2027():
    """Test that property income tax is included in total income tax for 2027."""
    situation = {
        "people": {"person": {"age": 30, "property_income": {2027: 20000}}},
        "benunits": {"benunit": {"members": ["person"]}},
        "households": {"household": {"members": ["person"]}},
    }
    sim = Microsimulation(situation=situation)

    # Calculate values
    property_income_tax = sim.calculate("property_income_tax", 2027).sum()
    income_tax = sim.calculate("income_tax", 2027).sum()

    # Property income tax should be non-zero
    assert property_income_tax > 0, "property_income_tax should be calculated"

    # Income tax should include property income tax (for person with only property income)
    assert abs(income_tax - property_income_tax) < 10, (
        f"income_tax (£{income_tax}) should equal property_income_tax (£{property_income_tax}) "
        "for person with only property income"
    )


def test_property_income_tax_with_employment_2027():
    """Test property income tax stacking on employment income."""
    situation = {
        "people": {
            "person": {
                "age": 30,
                "employment_income": {2027: 30000},
                "property_income": {2027: 20000},
            }
        },
        "benunits": {"benunit": {"members": ["person"]}},
        "households": {"household": {"members": ["person"]}},
    }
    sim = Microsimulation(situation=situation)

    # Calculate values
    earned_income_tax = sim.calculate("earned_income_tax", 2027).sum()
    property_income_tax = sim.calculate("property_income_tax", 2027).sum()
    income_tax = sim.calculate("income_tax", 2027).sum()

    # Both should be non-zero
    assert earned_income_tax > 0, "earned_income_tax should be calculated"
    assert property_income_tax > 0, "property_income_tax should be calculated"

    # Income tax should be sum of both components
    expected_total = earned_income_tax + property_income_tax
    assert abs(income_tax - expected_total) < 10, (
        f"income_tax (£{income_tax}) should equal sum of "
        f"earned_income_tax (£{earned_income_tax}) + "
        f"property_income_tax (£{property_income_tax}) = £{expected_total}"
    )


def test_property_income_uses_standard_rates_before_2027():
    """Test that property income uses standard rates before 2027."""
    situation = {
        "people": {"person": {"age": 30, "property_income": {2026: 20000}}},
        "benunits": {"benunit": {"members": ["person"]}},
        "households": {"household": {"members": ["person"]}},
    }
    sim = Microsimulation(situation=situation)

    # Calculate values
    property_income_tax = sim.calculate("property_income_tax", 2026).sum()
    income_tax = sim.calculate("income_tax", 2026).sum()

    # Property income tax should be non-zero
    assert property_income_tax > 0, "property_income_tax should be calculated"

    # Income tax should include property income tax
    assert abs(income_tax - property_income_tax) < 10, (
        f"income_tax (£{income_tax}) should equal property_income_tax (£{property_income_tax})"
    )


def test_property_income_uses_higher_rates_from_2027():
    """Test that property income tax increases from 2026 to 2027 due to rate change."""
    situation_2026 = {
        "people": {"person": {"age": 30, "property_income": {2026: 20000}}},
        "benunits": {"benunit": {"members": ["person"]}},
        "households": {"household": {"members": ["person"]}},
    }
    situation_2027 = {
        "people": {"person": {"age": 30, "property_income": {2027: 20000}}},
        "benunits": {"benunit": {"members": ["person"]}},
        "households": {"household": {"members": ["person"]}},
    }

    sim_2026 = Microsimulation(situation=situation_2026)
    sim_2027 = Microsimulation(situation=situation_2027)

    # Calculate values
    property_tax_2026 = sim_2026.calculate("property_income_tax", 2026).sum()
    property_tax_2027 = sim_2027.calculate("property_income_tax", 2027).sum()

    # 2027 should be higher due to 2pp increase
    # (Note: difference may be small due to parameter uprating between years)
    assert property_tax_2027 > property_tax_2026, (
        f"2027 property tax (£{property_tax_2027}) should be higher than "
        f"2026 (£{property_tax_2026}) due to 2pp rate increase"
    )
