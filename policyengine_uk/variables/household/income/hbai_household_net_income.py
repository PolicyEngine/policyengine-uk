from policyengine_uk.model_api import *
import datetime
import numpy as np


HBAI_HOUSEHOLD_NET_INCOME_ADDS = [
    "employment_income",
    "self_employment_income",
    "savings_interest_income",
    "dividend_income",
    "miscellaneous_income",
    "property_income",
    "private_pension_income",
    "private_transfer_income",
    "maintenance_income",
    "free_school_meals",
    "free_school_fruit_veg",
    "free_school_milk",
    "free_tv_licence_value",
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
    "cost_of_living_support_payment",
    "winter_fuel_allowance",
    "tax_free_childcare",
    "healthy_start_vouchers",
    "scottish_child_payment",
    "carer_support_payment",
    "scottish_carer_supplement",
    # Reference for tax-free-childcare: https://assets.publishing.service.gov.uk/media/5e7b191886650c744175d08b/households-below-average-income-1994-1995-2018-2019.pdf
]

HBAI_HOUSEHOLD_NET_INCOME_SUBTRACTS = [
    "council_tax",
    "domestic_rates",
    "income_tax",
    "national_insurance",
    "student_loan_repayments",
    "employee_pension_contributions",
    "personal_pension_contributions",
    "maintenance_expenses",
    "external_child_payments",
    "LVT",
]


class hbai_household_net_income(Variable):
    value_type = float
    entity = Household
    label = "Household net income (HBAI definition)"
    documentation = (
        "Disposable income for the household before housing costs, following "
        "the definition used for official poverty statistics. As in HBAI, a "
        'negative income is reset to zero ("Negative incomes BHC are reset '
        'to zero"), so this is never negative; the figure before the reset '
        "is hbai_household_net_income_before_reset_to_zero. Income after "
        "housing costs is derived from this reset figure and can be negative."
    )
    unit = GBP
    definition_period = YEAR
    reference = "https://www.gov.uk/government/statistics/households-below-average-income-for-financial-years-ending-1995-to-2025/households-below-average-income-background-information-and-methodology-report-fye-2025#negative-incomes"

    def formula(household, period, parameters):
        return max_(
            0, household("hbai_household_net_income_before_reset_to_zero", period)
        )


class real_hbai_household_net_income(Variable):
    label = "real household net income (HBAI definition)"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        return household("hbai_household_net_income", period) * household(
            "inflation_adjustment", period
        )
