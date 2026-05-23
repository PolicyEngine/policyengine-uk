from policyengine_uk.model_api import *


GOV_SPENDING_VARIABLES = [
    "child_benefit",
    "council_tax_benefit",
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
    "pawhp",
    "other_public_spending_budget_change",
    "tax_free_childcare",
    "extended_childcare_entitlement",
    "universal_childcare_entitlement",
    "targeted_childcare_entitlement",
    "care_to_learn",
    "childcare_grant",
    "parents_learning_allowance",
    "adult_dependants_grant",
    "travel_grant",
    "disabled_students_allowance",
    "bursary_fund_16_to_19",
    "dfe_education_spending",
    "dft_subsidy_spending",
    "nhs_spending",
    "carer_support_payment",
    "disability_basic_income",
]


class gov_spending(Variable):
    label = "government spending"
    documentation = "Government spending impact in respect of this household."
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        variables = list(GOV_SPENDING_VARIABLES)
        abolish_council_tax = parameters.gov.contrib.abolish_council_tax(period)
        if abolish_council_tax:
            variables = [v for v in variables if v != "council_tax_benefit"]
        return add(household, period, variables)
