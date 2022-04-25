from openfisca_uk.model_api import *

# The below variables follow the COICOP MECE categories.


@uprated(
    by="uprating.monthly_cpi_by_category.food_and_non_alcoholic_beverages"
)
class food_and_non_alcoholic_beverages_consumption(Variable):
    entity = Household
    label = "Food and alcoholic beverages"
    documentation = "Total yearly expenditure on food and alcoholic beverages"
    unit = GBP
    definition_period = YEAR
    value_type = float
    quantity_type = FLOW


@uprated(by="uprating.monthly_cpi_by_category.alcohol_and_tobacco")
class alcohol_and_tobacco_consumption(Variable):
    entity = Household
    label = "Alcohol and tobacco"
    documentation = "Total yearly expenditure on alcohol and tobacco"
    unit = GBP
    definition_period = YEAR
    value_type = float
    quantity_type = FLOW


@uprated(by="uprating.monthly_cpi_by_category.clothing_and_footwear")
class clothing_and_footwear_consumption(Variable):
    entity = Household
    label = "Clothing and footwear"
    documentation = "Total yearly expenditure on clothing and footwear"
    unit = GBP
    definition_period = YEAR
    value_type = float
    quantity_type = FLOW


@uprated(by="uprating.monthly_cpi_by_category.housing_water_and_electricity")
class housing_water_and_electricity_consumption(Variable):
    entity = Household
    label = "Housing, water and electricity"
    documentation = (
        "Total yearly expenditure on housing, water and electricity"
    )
    unit = GBP
    definition_period = YEAR
    value_type = float
    quantity_type = FLOW


class household_furnishings_consumption(Variable):
    entity = Household
    label = "Household furnishings"
    documentation = "Total yearly expenditure on household furnishings"
    unit = GBP
    definition_period = YEAR
    value_type = float
    quantity_type = FLOW


@uprated(by="uprating.monthly_cpi_by_category.health")
class health_consumption(Variable):
    entity = Household
    label = "Health"
    documentation = "Total yearly expenditure on health"
    unit = GBP
    definition_period = YEAR
    value_type = float
    quantity_type = FLOW


@uprated(by="uprating.monthly_cpi_by_category.transport")
class transport_consumption(Variable):
    entity = Household
    label = "Transport"
    documentation = "Total yearly expenditure on transport"
    unit = GBP
    definition_period = YEAR
    value_type = float
    quantity_type = FLOW


@uprated(by="uprating.monthly_cpi_by_category.communication")
class communication_consumption(Variable):
    entity = Household
    label = "Communication"
    documentation = "Total yearly expenditure on communication"
    unit = GBP
    definition_period = YEAR
    value_type = float
    quantity_type = FLOW


@uprated(by="uprating.monthly_cpi_by_category.recreation")
class recreation_consumption(Variable):
    entity = Household
    label = "Recreation"
    documentation = "Total yearly expenditure on recreation"
    unit = GBP
    definition_period = YEAR
    value_type = float
    quantity_type = FLOW


@uprated(by="uprating.monthly_cpi_by_category.education")
class education_consumption(Variable):
    entity = Household
    label = "Education"
    documentation = "Total yearly expenditure on education"
    unit = GBP
    definition_period = YEAR
    value_type = float
    quantity_type = FLOW


@uprated(by="uprating.monthly_cpi_by_category.restaurants_and_hotels")
class restaurants_and_hotels_consumption(Variable):
    entity = Household
    label = "Restaurants and hotels"
    documentation = "Total yearly expenditure on restaurants and hotels"
    unit = GBP
    definition_period = YEAR
    value_type = float
    quantity_type = FLOW


@uprated(by="uprating.monthly_cpi_by_category.miscellaneous")
class miscellaneous_consumption(Variable):
    entity = Household
    label = "Miscellaneous"
    documentation = "Total yearly expenditure on miscellaneous goods"
    unit = GBP
    definition_period = YEAR
    value_type = float
    quantity_type = FLOW


@uprated(by="uprating.monthly_cpi_by_category.transport")
class petrol_spending(Variable):
    label = "Petrol spending"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP


@uprated(by="uprating.monthly_cpi_by_category.transport")
class diesel_spending(Variable):
    label = "Diesel spending"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
