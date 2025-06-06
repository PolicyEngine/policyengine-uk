from policyengine_uk.model_api import *


class corporate_wealth(Variable):
    label = "corporate wealth"
    documentation = "Total owned wealth in corporations"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    uprating = "household.wealth.corporate_wealth"
    quantity_type = STOCK
