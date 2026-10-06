from policyengine_uk.model_api import *
from policyengine_uk.variables.household.income.hbai_household_net_income import (
    HBAI_HOUSEHOLD_NET_INCOME_ADDS,
    HBAI_HOUSEHOLD_NET_INCOME_SUBTRACTS,
)


class hbai_household_net_income_before_reset_to_zero(Variable):
    value_type = float
    entity = Household
    label = "Household net income (HBAI definition) before negative incomes are reset to zero"
    documentation = (
        "HBAI household net income before housing costs, before HBAI resets a "
        "negative figure to zero. It can be negative: self-employment losses "
        "count as negative income, and deductions such as Council Tax, Income "
        "Tax, pension contributions and maintenance paid can exceed income. "
        "hbai_household_net_income is this figure floored at zero. Use this "
        "variable for a household's actual budget constraint (marginal rates, "
        "labour supply responses) and to diagnose negative incomes."
    )
    unit = GBP
    definition_period = YEAR
    reference = "https://www.gov.uk/government/statistics/households-below-average-income-for-financial-years-ending-1995-to-2025/households-below-average-income-background-information-and-methodology-report-fye-2025#negative-incomes"

    def formula(household, period, parameters):
        abolish_council_tax = parameters.gov.contrib.abolish_council_tax(period)
        if abolish_council_tax:
            adds = [
                a for a in HBAI_HOUSEHOLD_NET_INCOME_ADDS if a != "council_tax_benefit"
            ]
            subtracts = [
                s for s in HBAI_HOUSEHOLD_NET_INCOME_SUBTRACTS if s != "council_tax"
            ]
            return add(household, period, adds) - add(household, period, subtracts)
        return add(household, period, HBAI_HOUSEHOLD_NET_INCOME_ADDS) - add(
            household, period, HBAI_HOUSEHOLD_NET_INCOME_SUBTRACTS
        )
