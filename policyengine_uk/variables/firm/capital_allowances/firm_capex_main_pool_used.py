from policyengine_uk.model_api import *


class firm_capex_main_pool_used(Variable):
    value_type = float
    entity = Firm
    label = "Firm second-hand main-rate plant and machinery expenditure"
    documentation = "Expenditure in the year on second-hand plant and machinery that falls in the main pool. Excludes cars."
    definition_period = YEAR
    unit = GBP
