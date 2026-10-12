from policyengine_uk.model_api import *


class other_tobacco_grams_per_week(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR
    label = "Grams of other tobacco bought per week"
    unit = "gram"
    quantity_type = STOCK
