from openfisca_uk.tools.general import *
from openfisca_uk.entities import *


class DLA(Variable):
    value_type = float
    entity = Person
    label = u"Disability Living Allowance"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("DLA_M", period) + person("DLA_SC", period)


class DLA_M(Variable):
    value_type = float
    entity = Person
    label = u"Disability Living Allowance (mobility component)"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("DLA_M_reported", period)


class DLA_SC(Variable):
    value_type = float
    entity = Person
    label = u"Disability Living Allowance (self-care)"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("DLA_SC_reported", period)


class DLA_SC_middle_plus(Variable):
    value_type = bool
    entity = Person
    label = u"Receives at least DLA (self-care) middle rate"
    definition_period = YEAR

    def formula(person, period, parameters):
        DLA_SC = parameters(period).benefit.DLA.self_care
        return person("DLA_SC", period) >= DLA_SC.middle


class DLA_M_reported(Variable):
    value_type = float
    entity = Person
    label = u"Disability Living Allowance (mobility component) (reported)"
    definition_period = YEAR


class DLA_SC_reported(Variable):
    value_type = float
    entity = Person
    label = u"Disability Living Allowance (self-care) (reported)"
    definition_period = YEAR
