from policyengine_uk import Simulation


def test_uc_capital_stocks_are_not_prorated_in_monthly_calculations():
    situation = {
        "people": {"person": {"age": {"2026": 30}}},
        "benunits": {
            "benunit": {
                "members": ["person"],
                "would_claim_uc": {"2026": True},
            }
        },
        "households": {
            "household": {
                "members": ["person"],
                "savings": {"2026": 12_000},
                "other_residential_property_value": {"2026": 12_000},
                "other_residential_property_secured_debt": {"2026": 5_000},
                "corporate_wealth": {"2026": 12_000},
            }
        },
    }
    simulation = Simulation(situation=situation)

    assert simulation.calculate("savings", "2026-01")[0] == 12_000
    assert simulation.calculate("corporate_wealth", "2026-01")[0] == 12_000
    assert (
        simulation.calculate("other_residential_property_secured_debt", "2026-01")[0]
        == 5_000
    )
    # Savings at face value; property and shares less 10% for the expenses
    # of sale, and the property less its mortgage (UC Regs 2013 reg. 49(1)):
    # 12,000 + (10,800 - 5,000) + 10,800.
    assert simulation.calculate("uc_assessable_capital", "2026-01")[0] == 28_600
    assert not simulation.calculate("is_uc_eligible", "2026-01")[0]


def test_pension_credit_capital_stocks_are_not_prorated_monthly():
    situation = {
        "people": {"person": {"age": {"2026": 70}}},
        "benunits": {"benunit": {"members": ["person"]}},
        "households": {
            "household": {
                "members": ["person"],
                "savings": {"2026": 12_000},
                "owned_land": {"2026": 12_000},
                "corporate_wealth": {"2026": 12_000},
            }
        },
    }
    simulation = Simulation(situation=situation)

    assert simulation.calculate("savings", "2026-01")[0] == 12_000
    # Land and shares less 10% for the expenses of sale (SPC Regs 2002
    # reg. 19(a)): 12,000 + 2 * 10,800.
    assert (
        simulation.calculate("pension_credit_assessable_capital", "2026-01")[0]
        == 33_600
    )
