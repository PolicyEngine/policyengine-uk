"""Government spending on households is household income.

gov_spending counted the Pension Age Winter Heating Payment (pawhp), but
household_benefits and the HBAI income lists did not: when the Winter Fuel
Payment stopped covering Scotland, Scottish pensioners' winter heating
payment fell out of household net income and HBAI income. These tests tie
the lists together so a payment added to one is not left out of the others.
"""

from policyengine_uk import CountryTaxBenefitSystem
from policyengine_uk.variables.gov.gov_spending import GOV_SPENDING_VARIABLES
from policyengine_uk.variables.household.income.hbai_household_net_income import (
    HBAI_HOUSEHOLD_NET_INCOME_ADDS,
)
from policyengine_uk.variables.household.income.household_benefits import (
    HOUSEHOLD_BENEFIT_VARIABLES,
)

SYSTEM = CountryTaxBenefitSystem()

# Spending in gov_spending that is not a benefit received by the household.
NOT_HOUSEHOLD_BENEFITS = {
    "other_public_spending_budget_change": (
        "the contrib lever gov.contrib.policyengine.budget.other_public_spending, "
        "spread across households by income decile; zero unless set"
    ),
}

# The winter heating payment a pensioner household receives: the Winter Fuel
# Payment, or in Scotland from the 2024 qualifying week the Pension Age
# Winter Heating Payment.
WINTER_HEATING_PAYMENTS = ["winter_fuel_allowance", "pawhp"]


def test_government_spending_on_households_is_household_income():
    outside = set(GOV_SPENDING_VARIABLES) - set(HOUSEHOLD_BENEFIT_VARIABLES)
    assert outside == set(NOT_HOUSEHOLD_BENEFITS), (
        "gov_spending counts these but household_benefits does not: "
        f"{sorted(outside - set(NOT_HOUSEHOLD_BENEFITS))}; listed as not "
        "household benefits but now in household_benefits: "
        f"{sorted(set(NOT_HOUSEHOLD_BENEFITS) - outside)}"
    )


def test_winter_heating_payments_are_counted_in_every_income_list():
    lists = {
        "HOUSEHOLD_BENEFIT_VARIABLES": HOUSEHOLD_BENEFIT_VARIABLES,
        "HBAI_HOUSEHOLD_NET_INCOME_ADDS": HBAI_HOUSEHOLD_NET_INCOME_ADDS,
        "hbai_benefits.adds": SYSTEM.variables["hbai_benefits"].adds,
        "GOV_SPENDING_VARIABLES": GOV_SPENDING_VARIABLES,
    }
    missing = {
        name: [payment for payment in WINTER_HEATING_PAYMENTS if payment not in names]
        for name, names in lists.items()
    }
    assert not any(missing.values()), missing
    repeated = {
        name: [
            payment for payment in WINTER_HEATING_PAYMENTS if names.count(payment) > 1
        ]
        for name, names in lists.items()
    }
    assert not any(repeated.values()), repeated
