from policyengine_uk.model_api import *

# The below variables follow the COICOP MECE categories.

label = "General"
description = "General consumption categories"


class food_and_non_alcoholic_beverages_consumption(Variable):
    entity = Household
    label = "food and alcoholic beverage consumption"
    documentation = "Total yearly expenditure on food and alcoholic beverages"
    unit = GBP
    definition_period = YEAR
    value_type = float
    quantity_type = FLOW
    uprating = "calibration.uprating.monthly_cpi_by_category.food_and_non_alcoholic_beverages"


class alcohol_and_tobacco_consumption(Variable):
    entity = Household
    label = "alcohol and tobacco consumption"
    documentation = "Total yearly expenditure on alcohol and tobacco"
    unit = GBP
    definition_period = YEAR
    value_type = float
    quantity_type = FLOW
    uprating = (
        "calibration.uprating.monthly_cpi_by_category.alcohol_and_tobacco"
    )


class clothing_and_footwear_consumption(Variable):
    entity = Household
    label = "clothing and footwear consumption"
    documentation = "Total yearly expenditure on clothing and footwear"
    unit = GBP
    definition_period = YEAR
    value_type = float
    quantity_type = FLOW
    uprating = (
        "calibration.uprating.monthly_cpi_by_category.clothing_and_footwear"
    )


class housing_water_and_electricity_consumption(Variable):
    entity = Household
    label = "housing, water and electricity consumption"
    documentation = (
        "Total yearly expenditure on housing, water and electricity"
    )
    unit = GBP
    definition_period = YEAR
    value_type = float
    quantity_type = FLOW
    uprating = "calibration.uprating.monthly_cpi_by_category.housing_water_and_electricity"


class household_furnishings_consumption(Variable):
    entity = Household
    label = "household furnishings consumption"
    documentation = "Total yearly expenditure on household furnishings"
    unit = GBP
    definition_period = YEAR
    value_type = float
    quantity_type = FLOW


class health_consumption(Variable):
    entity = Household
    label = "health consumption"
    documentation = "Total yearly expenditure on health"
    unit = GBP
    definition_period = YEAR
    value_type = float
    quantity_type = FLOW
    uprating = "calibration.uprating.monthly_cpi_by_category.health"


class transport_consumption(Variable):
    entity = Household
    label = "transport consumption"
    documentation = "Total yearly expenditure on transport"
    unit = GBP
    definition_period = YEAR
    value_type = float
    quantity_type = FLOW
    uprating = "calibration.uprating.monthly_cpi_by_category.transport"


class communication_consumption(Variable):
    entity = Household
    label = "communication consumption"
    documentation = "Total yearly expenditure on communication"
    unit = GBP
    definition_period = YEAR
    value_type = float
    quantity_type = FLOW
    uprating = "calibration.uprating.monthly_cpi_by_category.communication"


class recreation_consumption(Variable):
    entity = Household
    label = "recreation consumption"
    documentation = "Total yearly expenditure on recreation"
    unit = GBP
    definition_period = YEAR
    value_type = float
    quantity_type = FLOW
    uprating = "calibration.uprating.monthly_cpi_by_category.recreation"


class education_consumption(Variable):
    entity = Household
    label = "education consumption"
    documentation = "Total yearly expenditure on education"
    unit = GBP
    definition_period = YEAR
    value_type = float
    quantity_type = FLOW
    uprating = "calibration.uprating.monthly_cpi_by_category.education"


class restaurants_and_hotels_consumption(Variable):
    entity = Household
    label = "restaurants and hotels consumption"
    documentation = "Total yearly expenditure on restaurants and hotels"
    unit = GBP
    definition_period = YEAR
    value_type = float
    quantity_type = FLOW
    uprating = (
        "calibration.uprating.monthly_cpi_by_category.restaurants_and_hotels"
    )


class miscellaneous_consumption(Variable):
    entity = Household
    label = "miscellaneous consumption"
    documentation = "Total yearly expenditure on miscellaneous goods"
    unit = GBP
    definition_period = YEAR
    value_type = float
    quantity_type = FLOW
    uprating = "calibration.uprating.monthly_cpi_by_category.miscellaneous"


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
