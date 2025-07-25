from policyengine_uk.model_api import *


class dla_m_reported(Variable):
    value_type = float
    entity = Person
    label = "DLA (mobility) (reported)"
    definition_period = YEAR
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.consumer_price_index"
