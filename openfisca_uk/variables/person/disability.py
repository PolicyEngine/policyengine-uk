from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class is_disabled(Variable):
    value_type = float
    entity = Person
    label = u"Whether claims a core disability benefit"
    definition_period = YEAR
    set_input = set_input_dispatch_by_period

    def formula(person, period, parameters):
        QUALIFYING_BENEFITS = [
            "ESA_contrib_reported",
            "incapacity_benefit_reported",
            "SDA_reported",
            "AA_reported",
            "DLA_M_reported",
            "DLA_SC_reported",
        ]
        return add(person, period, QUALIFYING_BENEFITS, options=[MATCH]) > 0


class is_severely_disabled(Variable):
    value_type = float
    entity = Person
    label = u"Whether is eligible for higher payments of disability benefits"
    definition_period = YEAR
    set_input = set_input_dispatch_by_period

    def formula(person, period, parameters):
        claiming_SDA = person("SDA_reported", period, options=[MATCH]) > 0
        no_non_dependents = person.benunit.nb_persons(BenUnit.ADULT) == 1
        sufficient_DLA = (
            person("DLA_SC_reported", period, options=[MATCH]) > 50
        )
        return (claiming_SDA + sufficient_DLA > 0) * no_non_dependents


class is_enhanced_disabled(Variable):
    value_type = float
    entity = Person
    label = u"Whether meets the highest disability benefit entitlement"
    definition_period = YEAR
    set_input = set_input_dispatch_by_period

    def formula(person, period, parameters):
        sufficient_DLA = (
            person("DLA_SC_reported", period, options=[MATCH]) > 80
        )
        return sufficient_DLA


class is_carer(Variable):
    value_type = bool
    entity = Person
    label = u"Whether meets eligibility requirements for Carers Allowance"
    definition_period = YEAR
    set_input = set_input_dispatch_by_period

    def formula(person, period, parameters):
        already_claiming = (
            person("carers_allowance_reported", period, options=[MATCH]) > 0
        )
        meets_requirements = (
            person("care_hours", period)
            >= parameters(period).benefits.carers_allowance.min_hours
        )
        return already_claiming + meets_requirements


class registered_disabled(Variable):
    value_type = bool
    entity = Person
    label = u"Whether registered disabled"
    definition_period = YEAR
    set_input = set_input_dispatch_by_period


class dis_equality_act_core(Variable):
    value_type = bool
    entity = Person
    label = u"Whether disabled under the Equality Act (core definition)"
    definition_period = YEAR
    set_input = set_input_dispatch_by_period


class dis_equality_act_wider(Variable):
    value_type = bool
    entity = Person
    label = u"Whether disabled under the Equality Act (wider definition)"
    definition_period = YEAR
    set_input = set_input_dispatch_by_period


class is_standard_disabled(Variable):
    value_type = bool
    entity = Person
    label = u"Whether meets a basic level of disability"
    definition_period = YEAR
    set_input = set_input_dispatch_by_period

    def formula(person, period, parameters):
        QUALIFYING = [
            "is_disabled",
            "is_severely_disabled",
            "is_enhanced_disabled",
            "IIDB_reported",
            "registered_disabled",
            "dis_equality_act_core",
        ]
        return add(person, period, QUALIFYING, options=[MATCH])


class is_disabled_for_ubi(Variable):
    value_type = float
    entity = Person
    label = u"Whether person is classified as disabled for the purposes of UBI supplements"
    definition_period = YEAR
    set_input = set_input_dispatch_by_period

    def formula(person, period, parameters):
        QUALIFYING_BENEFITS = [
            "ESA_contrib_reported",
            "incapacity_benefit_reported",
            "SDA_reported",
            "AA_reported",
            "DLA_M_reported",
            "DLA_SC_reported",
            "IIDB_reported",
            # Given to a single person at benunit level
            "PIP_DL_reported",
            "PIP_M_reported",
            "ESA_income_reported_personal",
        ]
        return add(person, period, QUALIFYING_BENEFITS, options=[MATCH]) > 0
