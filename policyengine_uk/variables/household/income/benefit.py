from policyengine_uk.model_api import *

"""
This file contains variables that are commonly used in benefit eligibility calculations.
"""


class household_benefits(Variable):
    value_type = float
    entity = Household
    label = "household benefits"
    documentation = "Total value of benefits received by household"
    definition_period = YEAR
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
        "tax_free_childcare",
        "extended_childcare_entitlement",
        "universal_childcare_entitlement",
        "targeted_childcare_entitlement",
        "care_to_learn",
        "nhs_spending",
        "dfe_education_spending",
        "dft_subsidy_spending",
    ]

    def formula(household, period, parameters):
        contrib = parameters(period).gov.contrib
        uprating = contrib.benefit_uprating
        benefits = household_benefits.adds
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


class is_QYP(Variable):
    value_type = bool
    entity = Person
    label = "Whether this person is a qualifying young person for benefits purposes"
    definition_period = YEAR

    def formula(person, period, parameters):
        education = person("current_education", period)
        under_20 = person("age", period) < 20
        in_education = ~(
            education == education.possible_values.NOT_IN_EDUCATION
        )
        return under_20 & in_education


class is_child_or_QYP(Variable):
    value_type = bool
    entity = Person
    label = "Whether this person is a child or qualifying young person for most benefits"
    definition_period = YEAR

    def formula(person, period, parameters):
        return (person("age", period) < 16) | person("is_QYP", period)


class benefits_premiums(Variable):
    value_type = float
    entity = BenUnit
    label = "Value of premiums for disability and carer status"
    definition_period = YEAR
    unit = GBP

    adds = [
        "disability_premium",
        "enhanced_disability_premium",
        "severe_disability_premium",
        "carer_premium",
    ]


class benunit_weekly_hours(Variable):
    value_type = float
    entity = BenUnit
    label = "Average weekly hours worked by adults in the benefit unit"
    definition_period = YEAR
    unit = "hour"

    adds = ["weekly_hours"]


class is_single(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether this benefit unit contains a single claimant for benefits"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        relation_type = benunit("relation_type", period)
        relations = relation_type.possible_values
        return relation_type == relations.SINGLE


class is_couple(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether this benefit unit contains a joint couple claimant for benefits"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        relation_type = benunit("relation_type", period)
        relations = relation_type.possible_values
        return relation_type == relations.COUPLE


class is_lone_parent(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether the family is a lone parent family"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        family_type = benunit("family_type", period)
        families = family_type.possible_values
        return family_type == families.LONE_PARENT


class is_single_person(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether the family is a single person"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        family_type = benunit("family_type", period)
        families = family_type.possible_values
        return family_type == families.SINGLE


class claims_all_entitled_benefits(Variable):
    value_type = bool
    entity = BenUnit
    label = "Claims all eligible benefits"
    definition_period = YEAR
    documentation = (
        "Whether this family would claim any benefit they are entitled to"
    )

    def formula(benunit, period, parameters):
        # Return false if we have any reported values in the simulation for benefits.
        return (
            add(
                benunit,
                period,
                [
                    "child_tax_credit_reported",
                    "working_tax_credit_reported",
                    "universal_credit_reported",
                    "housing_benefit_reported",
                    "jsa_income_reported",
                    "income_support_reported",
                    "esa_income_reported",
                ],
            ).sum()
            < 1
        )


class claims_legacy_benefits(Variable):
    value_type = bool
    entity = BenUnit
    label = "Claims legacy benefits"
    documentation = "Whether this family is currently receiving legacy benefits (overrides UC claimant status)"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        BENEFITS = [
            "child_tax_credit_reported",
            "working_tax_credit_reported",
            "housing_benefit_reported",
            "esa_income_reported",
            "income_support_reported",
            "jsa_income_reported",
        ]

        return add(benunit, period, BENEFITS) > 0
