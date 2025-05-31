from policyengine_uk.model_api import *


class net_financial_wealth(Variable):
    label = "Net financial wealth"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    uprating = "household.wealth.financial_assets"
