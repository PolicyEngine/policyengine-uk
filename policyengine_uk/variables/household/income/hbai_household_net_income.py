from policyengine_uk.model_api import *
import datetime
import numpy as np


class hbai_household_net_income(Variable):
    value_type = float
    entity = Household
    label = "Household net income (HBAI definition)"
    documentation = "Disposable income for the household, following the definition used for official poverty statistics"
    unit = GBP
    definition_period = YEAR

    adds = [
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
        # Reference for tax-free-childcare: https://assets.publishing.service.gov.uk/media/5e7b191886650c744175d08b/households-below-average-income-1994-1995-2018-2019.pdf
    ]
    subtracts = [
        "council_tax",
        "domestic_rates",
        "income_tax",
        "national_insurance",
        "student_loan_repayments",
        "employee_pension_contributions",
        "personal_pension_contributions",
        "maintenance_expenses",
        "external_child_payments",
    ]


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
