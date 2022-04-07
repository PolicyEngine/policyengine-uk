from openfisca_uk.model_api import *


class food_and_non_alcoholic_beverages_consumption(Variable):
    entity = Household
    label = "Food and alcoholic beverages"
    documentation = "Total yearly expenditure on food and alcoholic beverages"
    unit = "currency-GBP"
    definition_period = YEAR
    value_type = float
    quantity_type = FLOW


class alcohol_and_tobacco_consumption(Variable):
    entity = Household
    label = "Alcohol and tobacco"
    documentation = "Total yearly expenditure on alcohol and tobacco"
    unit = "currency-GBP"
    definition_period = YEAR
    value_type = float
    quantity_type = FLOW


class clothing_and_footwear_consumption(Variable):
    entity = Household
    label = "Clothing and footwear"
    documentation = "Total yearly expenditure on clothing and footwear"
    unit = "currency-GBP"
    definition_period = YEAR
    value_type = float
    quantity_type = FLOW


class housing_water_and_electricity_consumption(Variable):
    entity = Household
    label = "Housing, water and electricity"
    documentation = (
        "Total yearly expenditure on housing, water and electricity"
    )
    unit = "currency-GBP"
    definition_period = YEAR
    value_type = float
    quantity_type = FLOW


class household_furnishings_consumption(Variable):
    entity = Household
    label = "Household furnishings"
    documentation = "Total yearly expenditure on household furnishings"
    unit = "currency-GBP"
    definition_period = YEAR
    value_type = float
    quantity_type = FLOW


class health_consumption(Variable):
    entity = Household
    label = "Health"
    documentation = "Total yearly expenditure on health"
    unit = "currency-GBP"
    definition_period = YEAR
    value_type = float
    quantity_type = FLOW


class transport_consumption(Variable):
    entity = Household
    label = "Transport"
    documentation = "Total yearly expenditure on transport"
    unit = "currency-GBP"
    definition_period = YEAR
    value_type = float
    quantity_type = FLOW


class communication_consumption(Variable):
    entity = Household
    label = "Communication"
    documentation = "Total yearly expenditure on communication"
    unit = "currency-GBP"
    definition_period = YEAR
    value_type = float
    quantity_type = FLOW


class recreation_consumption(Variable):
    entity = Household
    label = "Recreation"
    documentation = "Total yearly expenditure on recreation"
    unit = "currency-GBP"
    definition_period = YEAR
    value_type = float
    quantity_type = FLOW


class education_consumption(Variable):
    entity = Household
    label = "Education"
    documentation = "Total yearly expenditure on education"
    unit = "currency-GBP"
    definition_period = YEAR
    value_type = float
    quantity_type = FLOW


class restaurants_and_hotels_consumption(Variable):
    entity = Household
    label = "Restaurants and hotels"
    documentation = "Total yearly expenditure on restaurants and hotels"
    unit = "currency-GBP"
    definition_period = YEAR
    value_type = float
    quantity_type = FLOW


class miscellaneous_consumption(Variable):
    entity = Household
    label = "Miscellaneous"
    documentation = "Total yearly expenditure on miscellaneous goods"
    unit = "currency-GBP"
    definition_period = YEAR
    value_type = float
    quantity_type = FLOW


class petrol_spending(Variable):
    label = "Petrol spending"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"


class diesel_spending(Variable):
    label = "Diesel spending"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"
