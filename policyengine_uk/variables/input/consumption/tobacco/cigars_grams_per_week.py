from policyengine_uk.model_api import *


class cigars_grams_per_week(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR
    label = "Grams of cigars bought per week"
    unit = "gram"
    quantity_type = STOCK
