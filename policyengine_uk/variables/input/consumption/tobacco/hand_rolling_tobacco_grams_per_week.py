from policyengine_uk.model_api import *


class hand_rolling_tobacco_grams_per_week(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR
    label = "Grams of hand rolling tobacco bought per week"
    unit = "gram"
    uprating = "gov.economic_assumptions.indices.obr.per_capita.tobacco_clearances.hand_rolling_tobacco"
    quantity_type = STOCK
