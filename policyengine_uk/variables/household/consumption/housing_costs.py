from policyengine_uk.model_api import *


class housing_costs(Variable):
    value_type = float
    entity = Household
    label = "Total housing costs"
    definition_period = YEAR
    unit = GBP

    adds = ["rent", "mortgage", "water_and_sewerage_charges"]
