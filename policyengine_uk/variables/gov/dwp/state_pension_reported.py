from policyengine_uk.model_api import *


class state_pension_reported(Variable):
    value_type = float
    entity = Person
    label = "Reported income from the State Pension"
    definition_period = YEAR
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.consumer_price_index"

    def formula_2022(person, period, parameters):
        return person("state_pension_reported", period.last_year)
