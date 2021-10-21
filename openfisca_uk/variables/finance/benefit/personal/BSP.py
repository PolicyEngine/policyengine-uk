from openfisca_uk.tools.general import *
from openfisca_uk.entities import *


class BSP(Variable):
    value_type = float
    entity = Person
    label = u"Bereavement Support Payment"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("BSP_reported", period)


class BSP_reported(Variable):
    value_type = float
    entity = Person
    label = u"Bereavement Support Payment (reported)"
    definition_period = YEAR
