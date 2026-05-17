from policyengine_uk.model_api import *


PRE_BUDGET_CHANGE_HOUSEHOLD_TAX_VARIABLES = [
    "expected_sdlt",
    "expected_ltt",
    "expected_lbtt",
    "corporate_sdlt",
    "business_rates",
    "council_tax",
    "domestic_rates",
    "fuel_duty",
    "tv_licence",
    "wealth_tax",
    "non_primary_residence_wealth_tax",
    "income_tax",
    "national_insurance",
    "LVT",
    "carbon_tax",
    "vat_change",
    "capital_gains_tax",
]


class pre_budget_change_household_tax(Variable):
    value_type = float
    entity = Household
    label = "household taxes"
    documentation = "Total taxes owed by the household"
    definition_period = YEAR
    unit = GBP

    def formula(household, period, parameters):
        abolish_council_tax = parameters.gov.contrib.abolish_council_tax(period)
        if abolish_council_tax:
            return add(
                household,
                period,
                [
                    tax
                    for tax in PRE_BUDGET_CHANGE_HOUSEHOLD_TAX_VARIABLES
                    if tax not in ["council_tax"]
                ],
            )
        else:
            return add(household, period, PRE_BUDGET_CHANGE_HOUSEHOLD_TAX_VARIABLES)
