from policyengine_uk.model_api import *


class poverty_threshold_bhc(Variable):
    label = "Poverty threshold (BHC)"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        return (
            parameters(period).household.poverty.absolute_poverty_threshold_bhc
            * WEEKS_IN_YEAR
        )
