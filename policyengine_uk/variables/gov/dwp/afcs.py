from policyengine_uk.model_api import *


class afcs(Variable):
    value_type = float
    entity = Person
    label = "Armed Forces Compensation Scheme"
    definition_period = YEAR
    unit = GBP

    adds = ["afcs_reported"]
