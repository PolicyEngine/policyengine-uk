from policyengine_uk.model_api import *


class dla_sc_reported(Variable):
    value_type = float
    entity = Person
    label = "DLA (self-care) (reported)"
    definition_period = YEAR
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.consumer_price_index"
