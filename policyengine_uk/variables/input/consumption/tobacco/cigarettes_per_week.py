from policyengine_uk.model_api import *


class cigarettes_per_week(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR
    label = "Cigarettes bought per week"
    unit = "cigarette"
    quantity_type = STOCK
