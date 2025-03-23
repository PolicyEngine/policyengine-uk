from policyengine_uk.model_api import *


class housing_benefit_reported(Variable):
    value_type = float
    entity = Person
    label = "reported Housing Benefit amount"
    definition_period = YEAR
    unit = GBP
    uprating = "gov.obr.consumer_price_index"
