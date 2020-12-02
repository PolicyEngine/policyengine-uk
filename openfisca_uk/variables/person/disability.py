from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class is_disabled(Variable):
    value_type = float
    entity = Person
    label = u"Whether claims a core disability benefit"
    definition_period = YEAR

    def formula(person, period, parameters):
        QUALIFYING_BENEFITS = [
            "ESA_contrib",
            "incapacity_benefit",
            "SDA",
            "AA",
            "DLA_M",
            "DLA_SC"
        ]
        return add(person, period, QUALIFYING_BENEFITS, options=[MATCH]) > 0


class is_severely_disabled(Variable):
    value_type = float
    entity = Person
    label = u"Whether is eligible for higher payments of disability benefits"
    definition_period = YEAR

    def formula(person, period, parameters):
        claiming_SDA = person("SDA", period, options=[MATCH]) > 0
        no_non_dependents = person.benunit.nb_persons(BenUnit.ADULT) == 1
        sufficient_DLA = person("DLA_SC", period, options=[MATCH]) > 50
        return (claiming_SDA + sufficient_DLA > 0) * no_non_dependents


class is_enhanced_disabled(Variable):
    value_type = float
    entity = Person
    label = u"Whether meets the highest disability benefit entitlement"
    definition_period = YEAR

    def formula(person, period, parameters):
        sufficient_DLA = person("DLA_SC", period, options=[MATCH]) > 80
        return sufficient_DLA


class is_carer(Variable):
    value_type = bool
    entity = Person
    label = u"Whether meets eligibility requirements for Carers Allowance"
    definition_period = YEAR

    def formula(person, period, parameters):
        already_claiming = (
            person("carers_allowance", period, options=[MATCH]) > 0
        )
        meets_requirements = (
            person("care_hours", period)
            >= parameters(period).benefits.carers_allowance.min_hours
        )
        return already_claiming + meets_requirements

class registered_disabled(Variable):
    value_type = bool
    entity = Person
    label = u'Whether registered disabled'
    definition_period = YEAR

class dis_equality_act_core(Variable):
    value_type = bool
    entity = Person
    label = u'Whether disabled under the Equality Act (core definition)'
    definition_period = YEAR

class dis_equality_act_wider(Variable):
    value_type = bool
    entity = Person
    label = u'Whether disabled under the Equality Act (wider definition)'
    definition_period = YEAR

class is_standard_disabled(Variable):
    value_type = bool
    entity = Person
    label = u'Whether meets a basic level of disability'
    definition_period = YEAR

    def formula(person, period, parameters):
        QUALIFYING = [
            "is_disabled",
            "is_severely_disabled",
            "is_enhanced_disabled",
            "IIDB",
            "registered_disabled",
            "dis_equality_act_core"
        ]
        return add(person, period, QUALIFYING, options=[MATCH])