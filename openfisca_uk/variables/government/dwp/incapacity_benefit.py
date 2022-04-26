from openfisca_uk.model_api import *


@uprated(by="uprating.september_cpi")
class incapacity_benefit(Variable):
    value_type = float
    entity = Person
    label = "Incapacity Benefit"
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        return person("incapacity_benefit_reported", period)


class incapacity_benefit_reported(Variable):
    value_type = float
    entity = Person
    label = "Incapacity Benefit (reported)"
    definition_period = YEAR
    unit = GBP
