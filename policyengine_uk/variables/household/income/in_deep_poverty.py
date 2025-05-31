from policyengine_uk.model_api import *


class in_deep_poverty(Variable):
    label = "in deep poverty"
    documentation = "Whether the household is in deep absolute poverty (below half the poverty line, before housing costs)."
    entity = Household
    definition_period = YEAR
    value_type = bool

    def formula(household, period, parameters):
        return household("deep_poverty_gap", period) > 0
