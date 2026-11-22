from policyengine_uk.model_api import *


class firm_capex_special_rate_new(Variable):
    value_type = float
    entity = Firm
    label = "Firm new special-rate plant and machinery expenditure"
    documentation = "Expenditure in the year on unused, not second-hand special rate plant and machinery, such as integral features and long-life assets. Excludes cars."
    definition_period = YEAR
    hidden_input = True
    unit = GBP
