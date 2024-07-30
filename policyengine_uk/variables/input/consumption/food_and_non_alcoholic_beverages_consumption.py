from policyengine_uk.model_api import *


class food_and_non_alcoholic_beverages_consumption(Variable):
    label = "food and non-alcoholic beverages consumption"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW
