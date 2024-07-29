from policyengine_uk.model_api import *


class LVT(Variable):
    entity = Household
    label = "Land value tax"
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        lvt = parameters(period).gov.contrib.ubi_center.land_value_tax
        full_lvt = lvt.rate * household("land_value", period)
        household_lvt = lvt.household_rate * household(
            "household_land_value", period
        )
        corporate_lvt = lvt.corporate_rate * household(
            "corporate_land_value", period
        )
        return full_lvt + household_lvt + corporate_lvt
