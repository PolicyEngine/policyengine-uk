from policyengine_uk.model_api import *


class pension_credit_reported(Variable):
    label = "Pension Credit (reported)"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.consumer_price_index"
