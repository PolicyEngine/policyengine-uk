from openfisca_uk.tools.general import *
from openfisca_uk.entities import *


class incapacity_benefit(Variable):
    value_type = float
    entity = Person
    label = u"Incapacity Benefit"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("incapacity_benefit_reported", period)


class incapacity_benefit_reported(Variable):
    value_type = float
    entity = Person
    label = u"Incapacity Benefit (reported)"
    definition_period = YEAR
