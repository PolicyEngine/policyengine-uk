from openfisca_uk.tools.general import *
from openfisca_uk.entities import *

"""
This file contains variables that are commonly used in benefit eligibility calculations.
"""


class family_benefits(Variable):
    value_type = float
    entity = Person
    label = u"Total simulated family benefits for this person"
    definition_period = YEAR

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
        ]
        benefits = add(person.benunit, period, FAMILY_BENEFITS) * person(
            "is_benunit_head", period
        )
        benefits += add(
            person.benunit, period, ["working_tax_credit", "child_tax_credit"]
        ) * person("is_benunit_head", period)
        return benefits


class family_benefits_reported(Variable):
    value_type = float
    entity = Person
    label = u"Total reported family benefits for this person"
    definition_period = YEAR

    def formula(person, period, parameters):
        FAMILY_BENEFITS = [
            "child_benefit",
            "ESA_income",
            "housing_benefit",
            "income_support",
            "JSA_income",
            "pension_credit",
            "universal_credit",
        ]
        benefits = add(
            person,
            period,
            map(lambda ben: ben + "_reported", FAMILY_BENEFITS),
        )
        benefits += add(
            person,
            period,
            ["working_tax_credit_reported", "child_tax_credit_reported"],
        )
        return benefits


class benefits(Variable):
    value_type = float
    entity = Person
    label = u"Total benefits"
    documentation = "Total state benefits"
    unit = "currency-GBP"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("personal_benefits", period) + person(
            "family_benefits", period
        )


class household_benefits(Variable):
    value_type = float
    entity = Household
    label = u"Benefits"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(household, period, parameters):
        return household.sum(household.members("benefits", period))


class other_benefits(Variable):
    value_type = float
    entity = Person
    label = u"Income from benefits not modelled or detailed in the model"
    definition_period = YEAR

    def formula(person, period, parameters):
        return (
            person("benefits_reported", period)
            - person("personal_benefits", period)
            - person("family_benefits", period)
        )


class benefits_reported(Variable):
    value_type = float
    entity = Person
    label = u"Total simulated"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("personal_benefits_reported", period) + person(
            "family_benefits_reported", period
        )


class benefits_modelling(Variable):
    value_type = float
    entity = Person
    label = (
        u"Difference between reported and simulated benefits for this person"
    )
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("benefits", period) - person("benefits_reported", period)


class is_QYP(Variable):
    value_type = bool
    entity = Person
    label = u"Whether this person is a qualifying young person for benefits purposes"
    definition_period = YEAR

    def formula(person, period, parameters):
        education = person("current_education", period)
        return (person("age", period) < 20) & ~(
            education == education.possible_values.NOT_IN_EDUCATION
        )


class is_child_or_QYP(Variable):
    value_type = bool
    entity = Person
    label = u"Whether this person is a child or qualifying young person for most benefits"
    definition_period = YEAR

    def formula(person, period, parameters):
        return (person("age", period) < 16) | person("is_QYP", period)


class benefits_premiums(Variable):
    value_type = float
    entity = BenUnit
    label = u"Value of premiums for disability and carer status"
    definition_period = YEAR

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
    label = u"Average weekly hours worked by adults in the benefit unit"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("weekly_hours", period))


class is_single(Variable):
    value_type = bool
    entity = BenUnit
    label = (
        u"Whether this benefit unit contains a single claimant for benefits"
    )
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        relation_type = benunit("relation_type", period)
        relations = relation_type.possible_values
        return relation_type == relations.SINGLE


class is_couple(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Whether this benefit unit contains a joint couple claimant for benefits"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        relation_type = benunit("relation_type", period)
        relations = relation_type.possible_values
        return relation_type == relations.COUPLE


class is_lone_parent(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Whether the family is a lone parent family"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        family_type = benunit("family_type", period)
        families = family_type.possible_values
        return family_type == families.LONE_PARENT


class is_single_person(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Whether the family is a single person"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        family_type = benunit("family_type", period)
        families = family_type.possible_values
        return family_type == families.SINGLE


class personal_benefits(Variable):
    value_type = float
    entity = Person
    label = u"Value of personal, non-means-tested benefits"
    definition_period = YEAR

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
        return add(person, period, BENEFITS)


class personal_benefits_reported(Variable):
    value_type = float
    entity = Person
    label = u"Value of personal, non-means-tested benefits"
    definition_period = YEAR

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
        return add(
            person, period, map(lambda ben: ben + "_reported", BENEFITS)
        )


class claims_all_entitled_benefits(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Claims all eligible benefits"
    definition_period = YEAR
    documentation = (
        "Whether this family would claim any benefit they are entitled to"
    )


class claims_legacy_benefits(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Claims legacy benefits"
    documentation = "Whether this family is currently receiving legacy benefits (overrides UC claimant status)"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        # assign legacy/UC claimant status, consistently for each household
        return (
            benunit.value_from_first_person(
                benunit.members.household.project(
                    random(benunit.members.household)
                )
            )
            > parameters(period).benefit.universal_credit.rollout_rate
        )
