from policyengine_uk.model_api import *


class cider_draught_share(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR
    label = "Share of cider qualifying for draught relief"
    unit = "/1"
    quantity_type = STOCK
