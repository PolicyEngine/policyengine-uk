from policyengine_uk.model_api import *


class dft_subsidy_spending(Variable):
    label = "transport subsidy spending"
    documentation = "Total spending on transport subsidies for this household."
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    adds = [
        "rail_subsidy_spending",
        "bus_subsidy_spending",
    ]
