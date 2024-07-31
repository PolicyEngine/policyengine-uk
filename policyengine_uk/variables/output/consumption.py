from policyengine_uk.model_api import *


class consumption(Variable):
    label = "consumption"
    documentation = "Total consumption."
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW
    adds = [
        "food_and_non_alcoholic_beverages_consumption",
        "alcohol_and_tobacco_consumption",
        "clothing_and_footwear_consumption",
        "communication_consumption",
        "education_consumption",
        "health_consumption",
        "household_furnishing_consumption",
        "housing_water_and_electricity_consumption",
        "transport_consumption",
        "recreation_consumption",
        "restaurants_and_hotels_consumption",
        "other_consumption",
    ]


class pre_tax_consumption(Variable):
    label = "pre-tax consumption"
    documentation = "Imputed consumption before taxes."
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW


class consumption_taxes(Variable):
    label = "consumption taxes"
    documentation = "Consumption taxes passed through to consumers."
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW


class net_consumption(Variable):
    label = "net consumption"
    documentation = "Consumption including indirect taxes."
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW
    adds = [
        "pre_tax_consumption",
        "consumption_taxes",
    ]
