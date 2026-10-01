from policyengine_uk.model_api import *


class alcohol_duty(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR
    label = "Alcohol duty"
    unit = GBP
    adds = [
        "beer_duty",
        "cider_duty",
        "sparkling_cider_duty",
        "wine_duty",
        "spirits_duty",
        "other_fermented_duty",
    ]
