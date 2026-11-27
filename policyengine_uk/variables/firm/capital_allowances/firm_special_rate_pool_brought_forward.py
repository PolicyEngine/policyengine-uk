from policyengine_uk.model_api import *


class firm_special_rate_pool_brought_forward(Variable):
    value_type = float
    entity = Firm
    label = "Firm special rate pool brought forward"
    documentation = "Tax written-down value of the special rate pool of plant and machinery brought forward from the previous year, including first-year allowance balances carried into the pool."
    definition_period = YEAR
    hidden_input = True
    unit = GBP
