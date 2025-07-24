from policyengine_uk.model_api import *


class incapacity_benefit_reported(Variable):
    value_type = float
    entity = Person
    label = "Incapacity Benefit (reported)"
    definition_period = YEAR
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.consumer_price_index"
