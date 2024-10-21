from policyengine_uk.model_api import *


class gov_balance(Variable):
    label = "government balance"
    documentation = "Government deficit impact in respect of this household."
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    adds = ["gov_tax"]
    subtracts = ["gov_spending"]
