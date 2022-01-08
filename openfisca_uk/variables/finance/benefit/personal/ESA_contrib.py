from openfisca_uk.model_api import *


class ESA_contrib(Variable):
    value_type = float
    entity = Person
    label = "ESA (contribution-based)"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(person, period, parameters):
        return person("ESA_contrib_reported", period)


class ESA_contrib_reported(Variable):
    value_type = float
    entity = Person
    label = "Employment and Support Allowance (contribution-based) (reported)"
    definition_period = YEAR
    unit = "currency-GBP"
