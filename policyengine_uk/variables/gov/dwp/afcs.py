from policyengine_uk.model_api import *


class afcs(Variable):
    value_type = float
    entity = Person
    label = "Armed Forces Compensation Scheme"
    definition_period = YEAR
    unit = GBP
    uprating = "gov.obr.consumer_price_index"

    adds = ["afcs_reported"]
