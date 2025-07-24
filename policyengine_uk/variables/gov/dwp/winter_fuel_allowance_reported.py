from policyengine_uk.model_api import *


class winter_fuel_allowance_reported(Variable):
    value_type = float
    entity = Person
    label = "Winter fuel allowance"
    definition_period = YEAR
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.consumer_price_index"
