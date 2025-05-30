from policyengine_uk.model_api import *


class deep_poverty_line(Variable):
    label = "deep poverty line"
    documentation = "The line below which a household is in deep poverty."
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        return household("poverty_line", period) / 2
