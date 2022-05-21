from openfisca_uk.model_api import *


@uprated(by="uprating.september_cpi")
class BSP(Variable):
    value_type = float
    entity = Person
    label = "Bereavement Support Payment"
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        return person("BSP_reported", period)


class BSP_reported(Variable):
    value_type = float
    entity = Person
    label = "Bereavement Support Payment (reported)"
    definition_period = YEAR
    unit = GBP
