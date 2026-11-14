"""Frozen HB/CTR helper from main (6030cbc0b), with commentary omitted.

Keep this independent of the production helper: it is the differential oracle
for #2621, including the original arithmetic and operation order.
"""

from policyengine_uk.model_api import *


def person_net_earnings(person, period, pension_contribution_deduction_rate):
    employment_income = person("employment_income", period)
    self_employment_income = person("self_employment_income", period)
    statutory_pay = person("employment_benefits", period)
    earnings = (
        max_(employment_income, 0) + max_(self_employment_income, 0) + statutory_pay
    )
    income_before_losses = statutory_pay + sum(
        max_(person(component, period), 0)
        for component in [
            "employment_income",
            "private_pension_income",
            "social_security_income",
            "self_employment_income",
            "property_income",
            "savings_interest_income",
            "other_investment_income",
            "dividend_income",
            "taxable_miscellaneous_income",
        ]
    )
    earnings_share = np.divide(
        earnings,
        income_before_losses,
        out=np.zeros_like(earnings),
        where=income_before_losses > 0,
    )
    tax = person("income_tax_before_winter_fuel_payment_charge", period)
    income_tax = tax * min_(earnings_share, 1)
    national_insurance = add(
        person, period, ["ni_class_1_employee", "ni_class_2", "ni_class_4"]
    )
    pension_contributions = (
        person("pension_contributions", period) * pension_contribution_deduction_rate
    )
    return max_(
        earnings - income_tax - national_insurance - pension_contributions,
        0,
    )
