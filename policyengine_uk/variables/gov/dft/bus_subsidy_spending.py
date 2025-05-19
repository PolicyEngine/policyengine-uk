from policyengine_uk.model_api import *


class bus_subsidy_spending(Variable):
    label = "bus subsidy spending"
    documentation = "Total spending on bus subsidies for this household"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
