from policyengine_uk.model_api import *
from policyengine_uk.utils.carbon import CARBON_CATEGORIES, carbon_intensities


class carbon_consumption(Variable):
    entity = Household
    label = "Carbon consumption"
    documentation = "Estimated total carbon footprint of the household"
    unit = "tonne CO2"
    definition_period = YEAR
    value_type = float

    def formula(household, period, parameters):
        carbon_intensity_by_sector = carbon_intensities(parameters, period)
        spending_by_sector = [
            household(category, period) for category in CARBON_CATEGORIES
        ]
        return sum(
            [
                spending * carbon_intensity
                for spending, carbon_intensity in zip(
                    spending_by_sector, carbon_intensity_by_sector
                )
            ]
        )
