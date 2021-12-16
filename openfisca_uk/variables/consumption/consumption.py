from openfisca_uk.model_api import *


class food_and_non_alcoholic_beverages_consumption(Variable):
    entity = Household
    label = "Food and alcoholic beverages"
    documentation = "Total yearly expenditure on food and alcoholic beverages"
    unit = "currency-GBP"
    definition_period = YEAR
    value_type = float


class alcohol_and_tobacco_consumption(Variable):
    entity = Household
    label = "Alcohol and tobacco"
    documentation = "Total yearly expenditure on alcohol and tobacco"
    unit = "currency-GBP"
    definition_period = YEAR
    value_type = float


class clothing_and_footwear_consumption(Variable):
    entity = Household
    label = "Clothing and footwear"
    documentation = "Total yearly expenditure on clothing and footwear"
    unit = "currency-GBP"
    definition_period = YEAR
    value_type = float


class housing_water_and_electricity_consumption(Variable):
    entity = Household
    label = "Housing, water and electricity"
    documentation = (
        "Total yearly expenditure on housing, water and electricity"
    )
    unit = "currency-GBP"
    definition_period = YEAR
    value_type = float


class household_furnishings_consumption(Variable):
    entity = Household
    label = "Household furnishings"
    documentation = "Total yearly expenditure on household furnishings"
    unit = "currency-GBP"
    definition_period = YEAR
    value_type = float


class health_consumption(Variable):
    entity = Household
    label = "Health"
    documentation = "Total yearly expenditure on health"
    unit = "currency-GBP"
    definition_period = YEAR
    value_type = float


class transport_consumption(Variable):
    entity = Household
    label = "Transport"
    documentation = "Total yearly expenditure on transport"
    unit = "currency-GBP"
    definition_period = YEAR
    value_type = float


class communication_consumption(Variable):
    entity = Household
    label = "Communication"
    documentation = "Total yearly expenditure on communication"
    unit = "currency-GBP"
    definition_period = YEAR
    value_type = float


class recreation_consumption(Variable):
    entity = Household
    label = "Recreation"
    documentation = "Total yearly expenditure on recreation"
    unit = "currency-GBP"
    definition_period = YEAR
    value_type = float


class education_consumption(Variable):
    entity = Household
    label = "Education"
    documentation = "Total yearly expenditure on education"
    unit = "currency-GBP"
    definition_period = YEAR
    value_type = float


class restaurants_and_hotels_consumption(Variable):
    entity = Household
    label = "Restaurants and hotels"
    documentation = "Total yearly expenditure on restaurants and hotels"
    unit = "currency-GBP"
    definition_period = YEAR
    value_type = float


class miscellaneous_consumption(Variable):
    entity = Household
    label = "Miscellaneous"
    documentation = "Total yearly expenditure on miscellaneous goods"
    unit = "currency-GBP"
    definition_period = YEAR
    value_type = float
