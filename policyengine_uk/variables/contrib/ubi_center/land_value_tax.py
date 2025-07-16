from policyengine_uk.model_api import *


class lvt(Variable):
    entity = Household
    label = "Land value tax"
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        p = parameters(period).gov.contrib.ubi_center.land_value_tax
        full_lvt = p.rate * household("land_value", period)
        household_lvt = p.household_rate * household(
            "household_land_value", period
        )
        corporate_lvt = p.corporate_rate * household(
            "corporate_land_value", period
        )
        return full_lvt + household_lvt + corporate_lvt
