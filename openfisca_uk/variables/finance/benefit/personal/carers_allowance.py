from openfisca_uk.model_api import *


class receives_carers_allowance(Variable):
    value_type = bool
    entity = Person
    label = "Receives Carer's Allowance"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("carers_allowance", period) > 0


class carers_allowance(Variable):
    value_type = float
    entity = Person
    label = "Carer's Allowance"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(person, period, parameters):
        return person("carers_allowance_reported", period)


class carers_allowance_reported(Variable):
    value_type = float
    entity = Person
    label = "Carer's Allowance (reported)"
    definition_period = YEAR
    unit = "currency-GBP"
