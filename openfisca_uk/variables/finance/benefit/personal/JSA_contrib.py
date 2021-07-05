from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class JSA_contrib(Variable):
    value_type = float
    entity = Person
    label = u"Job Seeker's Allowance (contribution-based)"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("JSA_contrib_reported", period)


class JSA_contrib_reported(Variable):
    value_type = float
    entity = Person
    label = u"Job Seeker's Allowance (contribution-based) (reported)"
    definition_period = YEAR
