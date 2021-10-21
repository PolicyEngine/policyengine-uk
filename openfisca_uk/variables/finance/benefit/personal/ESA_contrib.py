from openfisca_uk.tools.general import *
from openfisca_uk.entities import *


class ESA_contrib(Variable):
    value_type = float
    entity = Person
    label = u"ESA (contribution-based)"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("ESA_contrib_reported", period)


class ESA_contrib_reported(Variable):
    value_type = float
    entity = Person
    label = u"Employment and Support Allowance (contribution-based) (reported)"
    definition_period = YEAR
