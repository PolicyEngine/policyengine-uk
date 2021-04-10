from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *

"""
This file contains variables that are commonly used in benefit eligibility calculations.
"""


class is_QYP(Variable):
    value_type = bool
    entity = Person
    label = u"Whether this person is a qualifying young person for benefits purposes"
    definition_period = YEAR

    def formula(person, period, parameters):
        return (person("age", period) < 20) * person("in_FE", period)


class is_child_or_QYP(Variable):
    value_type = bool
    entity = Person
    label = u"Whether this person is a child or qualifying young person for most benefits"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("is_child", period) + person("is_QYP", period)


class benefits_premiums(Variable):
    value_type = float
    entity = BenUnit
    label = u"Value of premiums for disability and carer status"
    definition_period = WEEK

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
    value_type = float
    entity = BenUnit
    label = u'Whether the family is a lone parent family'
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        family_type = benunit("family_type", period)
        families = family_type.possible_values
        return family_type == families.LONE_PARENT

class is_single_person(Variable):
    value_type = float
    entity = BenUnit
    label = u'Whether the family is a single person'
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        family_type = benunit("family_type", period)
        families = family_type.possible_values
        return family_type == families.SINGLE
    

class personal_benefits(Variable):
    value_type = float
    entity = Person
    label = u'Value of personal, non-means-tested benefits'
    definition_period = WEEK

    def formula(person, period, parameters):
        BENEFITS = [
            "AA",
            "AFCS",
            "BSP",
            "carers_allowance",
            "DLA",
            "ESA_contrib",
            "IIDB",
            "incapacity_benefit",
            "JSA_contrib",
            "PIP",
            "SDA",
            "state_pension"
        ]
        return add(person, period, BENEFITS)

class claims_legacy_benefits(Variable):
    value_type = float
    entity = BenUnit
    label = u'Whether this family is imputed to claim legacy benefits over Universal Credit'
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return random(benunit) > parameters(period).benefit.universal_credit.rollout_rate