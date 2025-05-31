from policyengine_uk.model_api import *


class poverty_line(Variable):
    label = "poverty line"
    documentation = "The line below which a household is in poverty."
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        equivalisation = household("household_equivalisation_bhc", period)
        return (
            parameters(period).household.poverty.absolute_poverty_threshold_bhc
            * WEEKS_IN_YEAR
            * equivalisation
        )
