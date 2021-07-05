from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


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
