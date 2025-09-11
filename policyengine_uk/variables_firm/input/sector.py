from policyengine_uk.model_api import *

label = "Sector"
description = "Economic sector variables."


class sector_id(Variable):
    value_type = int
    entity = Sector
    label = "sector ID"
    documentation = "Unique identifier for each sector"
    definition_period = YEAR
    quantity_type = STOCK
