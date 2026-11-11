from policyengine_uk.model_api import *


class cigarettes_per_week(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR
    label = "Cigarettes bought per week"
    unit = "cigarette"
    uprating = (
        "gov.economic_assumptions.indices.obr.per_capita.tobacco_clearances.cigarettes"
    )
    quantity_type = STOCK
