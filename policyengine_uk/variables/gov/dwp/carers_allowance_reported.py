from policyengine_uk.model_api import *


class carers_allowance_reported(Variable):
    value_type = float
    entity = Person
    label = "Carer's Allowance (reported)"
    definition_period = YEAR
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.consumer_price_index"
