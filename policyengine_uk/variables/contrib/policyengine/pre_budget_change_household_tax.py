from policyengine_uk.model_api import *


class pre_budget_change_household_tax(Variable):
    value_type = float
    entity = Household
    label = "household taxes"
    documentation = "Total taxes owed by the household"
    definition_period = YEAR
    unit = GBP
    adds = [
        "expected_sdlt",
        "expected_ltt",
        "expected_lbtt",
        "corporate_sdlt",
        "business_rates",
        "council_tax_applicable",
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
