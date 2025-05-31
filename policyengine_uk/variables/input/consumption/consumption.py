from policyengine_uk.model_api import *

# The below variables follow the COICOP MECE categories.


class consumption(Variable):
    label = "consumption"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"
    adds = [
        "food_and_non_alcoholic_beverages_consumption",
        "alcohol_and_tobacco_consumption",
        "clothing_and_footwear_consumption",
        "housing_water_and_electricity_consumption",
        "household_furnishings_consumption",
        "health_consumption",
        "transport_consumption",
        "communication_consumption",
        "recreation_consumption",
        "education_consumption",
        "restaurants_and_hotels_consumption",
        "miscellaneous_consumption",
    ]
