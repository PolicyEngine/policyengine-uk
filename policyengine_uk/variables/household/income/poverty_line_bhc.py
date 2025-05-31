from policyengine_uk.model_api import *


class poverty_line_bhc(Variable):
    value_type = float
    entity = Household
    label = "The poverty line for the household, before housing costs"
    definition_period = YEAR

    def formula(household, period, parameters):
        threshold = parameters(
            period
        ).household.poverty.absolute_poverty_threshold_bhc
        equivalisation = household("household_equivalisation_bhc", period)
        return threshold * equivalisation * WEEKS_IN_YEAR
