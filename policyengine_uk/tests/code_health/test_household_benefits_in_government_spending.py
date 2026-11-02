"""Every benefit that government pays a household is government spending.

household_benefits adds HOUSEHOLD_BENEFIT_VARIABLES to household net income.
gov_balance subtracts gov_spending, which adds GOV_SPENDING_VARIABLES. A
benefit in the first list but not the second raises household income at no
cost to the government, so gov_balance overstates the public finances by the
amount paid. The Scottish Child Payment, Healthy Start vouchers and the Two
Child Limit Payment were left out in that way.

Invariant: every entry of HOUSEHOLD_BENEFIT_VARIABLES is in
GOV_SPENDING_VARIABLES, or is in NOT_PAID_BY_GOVERNMENT below with the reason
government does not pay it.
"""

from policyengine_uk import CountryTaxBenefitSystem
from policyengine_uk.variables.gov.gov_spending import GOV_SPENDING_VARIABLES
from policyengine_uk.variables.household.income.household_benefits import (
    HOUSEHOLD_BENEFIT_VARIABLES,
)

SYSTEM = CountryTaxBenefitSystem()

# Household benefits that government does not pay, each with the reason.
# gov_spending leaves these out. Empty: government pays every benefit in
# HOUSEHOLD_BENEFIT_VARIABLES. Add an entry only for a benefit that someone
# other than government funds; a benefit government pays goes in
# GOV_SPENDING_VARIABLES instead.
NOT_PAID_BY_GOVERNMENT = {}

# The benefits this invariant found missing from government spending.
ADDED_TO_GOVERNMENT_SPENDING = [
    "healthy_start_vouchers",
    "scottish_child_payment",
    "two_child_limit_payment",
]


def left_out_of_government_spending(benefits, spending, exclusions):
    """Household benefits that are neither government spending nor excluded."""
    return sorted(set(benefits) - set(spending) - set(exclusions))


def test_every_household_benefit_is_government_spending_or_excluded():
    left_out = left_out_of_government_spending(
        HOUSEHOLD_BENEFIT_VARIABLES, GOV_SPENDING_VARIABLES, NOT_PAID_BY_GOVERNMENT
    )
    assert not left_out, (
        f"household_benefits counts {left_out} but gov_spending does not. Add "
        "each to GOV_SPENDING_VARIABLES, or to NOT_PAID_BY_GOVERNMENT with the "
        "reason government does not pay it."
    )


def test_exclusions_are_household_benefits_outside_government_spending():
    for name, reason in NOT_PAID_BY_GOVERNMENT.items():
        assert name in SYSTEM.variables, f"{name} is not a variable"
        assert name in HOUSEHOLD_BENEFIT_VARIABLES, (
            f"{name} is excluded but is not a household benefit"
        )
        assert name not in GOV_SPENDING_VARIABLES, (
            f"{name} is excluded as not paid by government but is in gov_spending"
        )
        assert isinstance(reason, str) and reason.strip(), (
            f"{name} needs a reason government does not pay it"
        )


def test_the_check_reports_a_benefit_left_out_of_government_spending():
    # The lists as they were before the three benefits were added.
    before = [
        name
        for name in GOV_SPENDING_VARIABLES
        if name not in ADDED_TO_GOVERNMENT_SPENDING
    ]
    assert left_out_of_government_spending(
        HOUSEHOLD_BENEFIT_VARIABLES, before, NOT_PAID_BY_GOVERNMENT
    ) == sorted(ADDED_TO_GOVERNMENT_SPENDING)
    # An exclusion with a reason takes a benefit out of the report.
    assert (
        left_out_of_government_spending(
            ["paid_by_government", "paid_by_employer"],
            ["paid_by_government"],
            {"paid_by_employer": "the employer pays it"},
        )
        == []
    )
