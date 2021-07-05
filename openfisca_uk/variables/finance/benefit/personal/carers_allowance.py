from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class carers_allowance(Variable):
    value_type = float
    entity = Person
    label = u"Carer's Allowance"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("carers_allowance_reported", period)


class carers_allowance_reported(Variable):
    value_type = float
    entity = Person
    label = u"Carer's Allowance (reported)"
    definition_period = YEAR
