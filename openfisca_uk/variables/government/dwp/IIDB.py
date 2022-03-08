from openfisca_uk.model_api import *


class IIDB(Variable):
    value_type = float
    entity = Person
    label = "Industrial Injuries Disablement Benefit"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(person, period, parameters):
        return person("IIDB_reported", period)


class IIDB_reported(Variable):
    value_type = float
    entity = Person
    label = "Industrial Injuries Disablement Benefit (reported)"
    definition_period = YEAR
    unit = "currency-GBP"
