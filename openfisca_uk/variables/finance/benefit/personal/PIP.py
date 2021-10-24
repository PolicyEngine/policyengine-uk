from openfisca_uk.tools.general import *
from openfisca_uk.entities import *


class PIP(Variable):
    value_type = float
    entity = Person
    label = u"Personal Independence Payment"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("PIP_M", period) + person("PIP_DL", period)


class PIP_DL(Variable):
    value_type = float
    entity = Person
    label = u"Personal Independence Payment (Daily Living)"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("PIP_DL_reported", period)


class PIP_M(Variable):
    value_type = float
    entity = Person
    label = u"Personal Independence Payment (Mobility)"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("PIP_M_reported", period)


class PIP_DL_reported(Variable):
    value_type = float
    entity = Person
    label = u"Personal Independence Payment (Daily Living) (reported)"
    definition_period = YEAR


class PIP_M_reported(Variable):
    value_type = float
    entity = Person
    label = u"Personal Independence Payment (Mobility) (reported)"
    definition_period = YEAR
