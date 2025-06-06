from policyengine_uk.model_api import *


class in_poverty(Variable):
    label = "in poverty"
    documentation = (
        "Whether the household is in absolute poverty (before housing costs)."
    )
    entity = Household
    definition_period = YEAR
    value_type = bool

    def formula(household, period, parameters):
        return household("poverty_gap", period) > 0
