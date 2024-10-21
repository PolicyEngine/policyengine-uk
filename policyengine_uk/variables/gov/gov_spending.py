from policyengine_uk.model_api import *


class gov_spending(Variable):
    label = "government spending"
    documentation = "Government spending impact in respect of this household."
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    adds = [
        "child_benefit",
        "esa_income",
        "esa_contrib",
        "housing_benefit",
        "income_support",
        "jsa_income",
        "jsa_contrib",
        "pension_credit",
        "universal_credit",
        "working_tax_credit",
        "child_tax_credit",
        "attendance_allowance",
        "afcs",
        "bsp",
        "carers_allowance",
        "dla",
        "iidb",
        "incapacity_benefit",
        "jsa_contrib",
        "pip",
        "sda",
        "state_pension",
        "maternity_allowance",
        "statutory_sick_pay",
        "statutory_maternity_pay",
        "ssmg",
        "basic_income",
        "epg_subsidy",
        "cost_of_living_support_payment",
        "energy_bills_rebate",
        "winter_fuel_allowance",
        "nhs_budget_change",
        "education_budget_change",
        "other_public_spending_budget_change",
    ]
