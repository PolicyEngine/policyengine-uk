from policyengine_uk.model_api import *


class income_support_reported(Variable):
    value_type = float
    entity = Person
    label = "Income Support (reported amount)"
    definition_period = YEAR
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.consumer_price_index"
