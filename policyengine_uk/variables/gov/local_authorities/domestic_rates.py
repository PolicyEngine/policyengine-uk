from policyengine_uk.model_api import *


class domestic_rates(Variable):
    label = "domestic rates"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
