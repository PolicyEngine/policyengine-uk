from policyengine_uk.model_api import *


class working_tax_credit_reported(Variable):
    value_type = float
    entity = Person
    label = "Working Tax Credit"
    definition_period = YEAR
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.consumer_price_index"
