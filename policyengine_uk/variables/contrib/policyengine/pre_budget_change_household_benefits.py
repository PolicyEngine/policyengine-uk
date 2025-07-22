from policyengine_uk.model_api import *


class pre_budget_change_household_benefits(Variable):
    value_type = float
    entity = Household
    label = "household benefits"
    documentation = "Total value of benefits received by household"
    definition_period = YEAR
    unit = GBP
    adds = [
        "child_benefit",
        "esa_income",
        "housing_benefit",
        "income_support",
        "jsa_income",
        "pension_credit",
        "universal_credit",
        "working_tax_credit",
        "child_tax_credit",
        "attendance_allowance",
        "afcs",
        "bsp",
        "carers_allowance",
        "dla",
        "esa_contrib",
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
    ]

    def formula(household, period, parameters):
        contrib = parameters(period).gov.contrib
        uprating = contrib.benefit_uprating
        benefits = pre_budget_change_household_benefits.adds
        if contrib.abolish_council_tax:
            benefits = [
                benefit
                for benefit in benefits
                if benefit != "council_tax_benefit"
            ]
        general_benefits = add(
            household,
            period,
            [
                benefit
                for benefit in benefits
                if benefit not in ["basic_income"]
            ],
        )
        non_sp_benefits = add(
            household,
            period,
            [
                benefit
                for benefit in benefits
                if benefit not in ["state_pension", "basic_income"]
            ],
        )
        return (
            add(household, period, benefits)
            + general_benefits * uprating.all
            + non_sp_benefits * uprating.non_sp
        )
