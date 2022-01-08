from openfisca_uk.model_api import *


class AA(Variable):
    value_type = float
    entity = Person
    label = "Attendance Allowance"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(person, period, parameters):
        return person("AA_reported", period)


class AA_reported(Variable):
    value_type = float
    entity = Person
    label = "Attendance Allowance (reported)"
    definition_period = YEAR
    unit = "currency-GBP"
