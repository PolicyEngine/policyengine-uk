from policyengine_uk.model_api import *

"""
This file contains variables that are commonly used in benefit eligibility calculations.
"""


class family_benefits(Variable):
    value_type = float
    entity = Person
    label = "Total simulated family benefits for this person"
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        FAMILY_BENEFITS = [
            "child_benefit",
            "ESA_income",
            "housing_benefit",
            "income_support",
            "JSA_income",
            "pension_credit",
            "universal_credit",
            "council_tax_benefit",
            "child_tax_credit",
            "working_tax_credit",
        ]
        benefits = add(person.benunit, period, FAMILY_BENEFITS)
        return benefits * person("is_benunit_head", period)


class family_benefits_reported(Variable):
    value_type = float
    entity = Person
    label = "Total reported family benefits for this person"
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        FAMILY_BENEFITS = []
        return add(person, period, [i + "_reported" for i in FAMILY_BENEFITS])


class benefits(Variable):
    value_type = float
    entity = Person
    label = "Total benefits"
    documentation = "Total state benefits"
    unit = GBP
    definition_period = YEAR

    def formula(person, period, parameters):
        uprating = parameters(period).gov.dwp.additional_uprating
        total = add(person, period, ["personal_benefits", "family_benefits"])
        return total * (1 + uprating)


class household_benefits(Variable):
    value_type = float
    entity = Household
    label = "benefits"
    documentation = "Total value of benefits received by household"
    definition_period = YEAR
    unit = GBP
    adds = [
        "child_benefit",
        "ESA_income",
        "housing_benefit",
        "income_support",
        "JSA_income",
        "pension_credit",
        "universal_credit",
        "working_tax_credit",
        "child_tax_credit",
        "attendance_allowance",
        "AFCS",
        "BSP",
        "carers_allowance",
        "dla",
        "ESA_contrib",
        "IIDB",
        "incapacity_benefit",
        "JSA_contrib",
        "pip",
        "sda",
        "state_pension",
        "student_payments",
        "student_loans",
        "maternity_allowance",
        "SSP",
        "SMP",
        "ssmg",
        "basic_income",
    ]


class other_benefits(Variable):
    value_type = float
    entity = Person
    label = "Income from benefits not modelled or detailed in the model"
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        reported = person("benefits_reported", period)
        personal_family_benefits = add(
            person, period, ["personal_benefits", "family_benefits"]
        )
        return reported - personal_family_benefits


class benefits_reported(Variable):
    value_type = float
    entity = Person
    label = "Total simulated"
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        BENS = ["personal_benefits_reported", "family_benefits_reported"]
        return add(person, period, BENS)


class benefits_modelling(Variable):
    value_type = float
    entity = Person
    label = (
        "Difference between reported and simulated benefits for this person"
    )
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        return person("benefits", period) - person("benefits_reported", period)


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

    def formula(benunit, period, parameters):
        PREMIUMS = [
            "disability_premium",
            "enhanced_disability_premium",
            "severe_disability_premium",
            "carer_premium",
        ]
        return add(benunit, period, PREMIUMS)


class benunit_weekly_hours(Variable):
    value_type = float
    entity = BenUnit
    label = "Average weekly hours worked by adults in the benefit unit"
    definition_period = YEAR
    unit = "hour"

    def formula(benunit, period, parameters):
        return aggr(benunit, period, ["weekly_hours"])


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


class personal_benefits(Variable):
    value_type = float
    entity = Person
    label = "Value of personal, non-means-tested benefits"
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        BENEFITS = [
            "attendance_allowance",
            "AFCS",
            "BSP",
            "carers_allowance",
            "dla",
            "ESA_contrib",
            "IIDB",
            "incapacity_benefit",
            "JSA_contrib",
            "pip",
            "sda",
            "state_pension",
            "student_payments",
            "student_loans",
            "maternity_allowance",
            "SSP",
            "SMP",
            "ssmg",
            "basic_income",
        ]
        return add(person, period, BENEFITS)


class personal_benefits_reported(Variable):
    value_type = float
    entity = Person
    label = "Value of personal, non-means-tested benefits"
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        BENEFITS = [
            "AA",
            "AFCS",
            "BSP",
            "carers_allowance",
            "DLA_M",
            "DLA_SC",
            "ESA_contrib",
            "IIDB",
            "incapacity_benefit",
            "JSA_contrib",
            "PIP_M",
            "PIP_DL",
            "SDA",
            "state_pension",
        ]
        return add(person, period, [i + "_reported" for i in BENEFITS])


class claims_all_entitled_benefits(Variable):
    value_type = bool
    entity = BenUnit
    label = "Claims all eligible benefits"
    definition_period = YEAR
    documentation = (
        "Whether this family would claim any benefit they are entitled to"
    )

    def formula(benunit, period, parameters):
        # Return false we have any reported values in the simulation for benefits.
        return (
            aggr(
                benunit,
                period,
                [
                    "child_tax_credit_reported",
                    "working_tax_credit_reported",
                    "universal_credit_reported",
                    "housing_benefit_reported",
                    "JSA_income_reported",
                    "income_support_reported",
                    "ESA_income_reported",
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
            "child_tax_credit",
            "working_tax_credit",
            "housing_benefit",
            "ESA_income",
            "income_support",
            "JSA_income",
        ]

        return add(benunit, period, BENEFITS) > 0
