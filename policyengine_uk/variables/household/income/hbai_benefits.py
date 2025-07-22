from policyengine_uk.model_api import *


class hbai_benefits(Variable):
    label = "HBAI-included benefits"
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
        "pip",
        "sda",
        "state_pension",
        "maternity_allowance",
        "statutory_sick_pay",
        "statutory_maternity_pay",
        "ssmg",
        "cost_of_living_support_payment",
        "winter_fuel_allowance",
        "tax_free_childcare",
        "healthy_start_vouchers",
    ]
