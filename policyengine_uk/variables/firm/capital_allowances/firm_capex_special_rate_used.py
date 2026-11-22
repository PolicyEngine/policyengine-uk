from policyengine_uk.model_api import *


class firm_capex_special_rate_used(Variable):
    value_type = float
    entity = Firm
    label = "Firm second-hand special-rate plant and machinery expenditure"
    documentation = "Expenditure in the year on second-hand special rate plant and machinery. Excludes cars."
    definition_period = YEAR
    hidden_input = True
    unit = GBP
