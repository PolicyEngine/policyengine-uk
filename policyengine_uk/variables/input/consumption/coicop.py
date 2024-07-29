from policyengine_uk.model_api import *

# The below variables follow the COICOP MECE categories.

label = "General"
description = "General consumption categories"

class petrol_spending(Variable):
    label = "petrol consumption"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW
    uprating = "calibration.uprating.monthly_cpi_by_category.transport"


class diesel_spending(Variable):
    label = "diesel consumption"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW
    uprating = "calibration.uprating.monthly_cpi_by_category.transport"


class childcare_expenses(Variable):
    value_type = float
    entity = Person
    label = "childcare consumption"
    documentation = "Total amount spent on childcare"
    definition_period = YEAR
    unit = GBP


class private_pension_contributions(Variable):
    value_type = float
    entity = Person
    label = "private pension contributions"
    documentation = "Total amount spent on private pension contributions"
    definition_period = YEAR
    unit = GBP


class occupational_pension_contributions(Variable):
    value_type = float
    entity = Person
    label = "occupational pension contributions"
    documentation = "Total amount spent on occupational pension contributions"
    definition_period = YEAR
    unit = GBP


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
