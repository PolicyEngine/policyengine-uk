from policyengine_uk.model_api import *

# The below variables follow the COICOP MECE categories.


class food_and_non_alcoholic_beverages_consumption(Variable):
    entity = Household
    label = "food and alcoholic beverage consumption"
    documentation = "Total yearly expenditure on food and alcoholic beverages"
    unit = GBP
    definition_period = YEAR
    value_type = float
    quantity_type = FLOW
    uprating = "gov.economic_assumptions.indices.obr.consumer_price_index"
