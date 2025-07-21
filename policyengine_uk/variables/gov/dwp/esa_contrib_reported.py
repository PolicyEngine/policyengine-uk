from policyengine_uk.model_api import *


class esa_contrib_reported(Variable):
    value_type = float
    entity = Person
    label = "Employment and Support Allowance (contribution-based) (reported)"
    definition_period = YEAR
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.consumer_price_index"
