from openfisca_uk.model_api import *


class BSP(Variable):
    value_type = float
    entity = Person
    label = "Bereavement Support Payment"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(person, period, parameters):
        return person("BSP_reported", period)


class BSP_reported(Variable):
    value_type = float
    entity = Person
    label = "Bereavement Support Payment (reported)"
    definition_period = YEAR
    unit = "currency-GBP"
