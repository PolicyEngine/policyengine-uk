from policyengine_uk.model_api import *


class iidb_reported(Variable):
    value_type = float
    entity = Person
    label = "Industrial Injuries Disablement Benefit (reported)"
    definition_period = YEAR
    unit = GBP
    uprating = "gov.obr.consumer_price_index"
