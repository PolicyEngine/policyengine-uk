from policyengine_uk.model_api import *


class total_wealth(Variable):
    label = "Total wealth"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK

    adds = [
        "property_wealth",
        "corporate_wealth",
        "savings",
    ]
