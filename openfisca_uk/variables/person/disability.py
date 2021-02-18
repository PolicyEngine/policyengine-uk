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
            "ESA_contrib_reported",
            "incapacity_benefit_reported",
            "SDA_reported",
            "AA_reported",
            "DLA_M_reported",
            "DLA_SC_reported",
        ]
        return add(person, period, QUALIFYING_BENEFITS, options=[ADD]) > 0


class is_severely_disabled(Variable):
    value_type = float
    entity = Person
    label = u"Whether is eligible for higher payments of disability benefits"
    definition_period = YEAR

    def formula(person, period, parameters):
        claiming_SDA = person("SDA_reported", period, options=[ADD]) > 0
        no_non_dependents = person.benunit.nb_persons(BenUnit.ADULT) == 1
        sufficient_DLA = person("DLA_SC_reported", period, options=[ADD]) > 50
        return (claiming_SDA + sufficient_DLA > 0) * no_non_dependents


class is_enhanced_disabled(Variable):
    value_type = float
    entity = Person
    label = u"Whether meets the highest disability benefit entitlement"
    definition_period = YEAR

    def formula(person, period, parameters):
        sufficient_DLA = person("DLA_SC_reported", period, options=[ADD]) > 80
        return sufficient_DLA


class is_carer(Variable):
    value_type = bool
    entity = Person
    label = u"Whether meets eligibility requirements for Carers Allowance"
    definition_period = YEAR

    def formula(person, period, parameters):
        already_claiming = (
            person("carers_allowance_reported", period, options=[ADD]) > 0
        )
        meets_requirements = (
            person("care_hours_given", period, options=[ADD])
            >= parameters(period).benefits.carers_allowance.min_hours
        )
        return already_claiming + meets_requirements > 0


class registered_disabled(Variable):
    value_type = bool
    entity = Person
    label = u"Whether registered disabled"
    definition_period = YEAR


class dis_equality_act_core(Variable):
    value_type = bool
    entity = Person
    label = u"Whether disabled under the Equality Act (core definition)"
    definition_period = YEAR


class vision_difficulty(Variable):
    value_type = bool
    entity = Person
    label = u"Whether has difficulty with vision"
    definition_period = YEAR


class hearing_difficulty(Variable):
    value_type = bool
    entity = Person
    label = u"Whether has difficulty with hearing"
    definition_period = YEAR


class mobility_difficulty(Variable):
    value_type = bool
    entity = Person
    label = u"Whether has difficulty with mobility"
    definition_period = YEAR


class dexterity_difficulty(Variable):
    value_type = bool
    entity = Person
    label = u"Whether has difficulty with dexterity"
    definition_period = YEAR


class learning_difficulty(Variable):
    value_type = bool
    entity = Person
    label = u"Whether has difficulty with learning"
    definition_period = YEAR


class memory_difficulty(Variable):
    value_type = bool
    entity = Person
    label = u"Whether has difficulty with memory"
    definition_period = YEAR


class mental_health_difficulty(Variable):
    value_type = bool
    entity = Person
    label = u"Whether has difficulty with mental health"
    definition_period = YEAR


class stamina_difficulty(Variable):
    value_type = bool
    entity = Person
    label = u"Whether has difficulty with stamina"
    definition_period = YEAR


class social_difficulty(Variable):
    value_type = bool
    entity = Person
    label = u"Whether has social difficulty"
    definition_period = YEAR


class other_difficulty(Variable):
    value_type = bool
    entity = Person
    label = u"Whether has another difficulty"
    definition_period = YEAR


class is_standard_disabled(Variable):
    value_type = bool
    entity = Person
    label = u"Whether meets a basic level of disability"
    definition_period = YEAR

    def formula(person, period, parameters):
        QUALIFYING = [
            "is_disabled",
            "is_severely_disabled",
            "is_enhanced_disabled",
            "IIDB_reported",
            "registered_disabled",
            "dis_equality_act_core",
        ]
        return add(person, period, QUALIFYING, options=[ADD]) > 0


class is_disabled_for_ubi(Variable):
    value_type = float
    entity = Person
    label = u"Whether person is classified as disabled for the purposes of UBI supplements"
    definition_period = YEAR

    def formula(person, period, parameters):
        QUALIFYING_BENEFITS = [
            "incapacity_benefit_reported",
            "SDA_reported",
            "AA_reported",
            "DLA_M_reported",
            "DLA_SC_reported",
            "IIDB_reported",
            "PIP_DL_reported",
            "PIP_M_reported",
        ]
        return add(person, period, QUALIFYING_BENEFITS, options=[ADD]) > 0
