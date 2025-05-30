from policyengine_uk.model_api import *


class land_value(Variable):
    label = "Land value"
    documentation = (
        "Estimated total land value (directly and indirectly owned)"
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK

    adds = ["household_land_value", "corporate_land_value"]
