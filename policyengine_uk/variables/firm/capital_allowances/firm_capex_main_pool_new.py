from policyengine_uk.model_api import *


class firm_capex_main_pool_new(Variable):
    value_type = float
    entity = Firm
    label = "Firm new main-rate plant and machinery expenditure"
    documentation = "Expenditure in the year on unused, not second-hand plant and machinery that falls in the main pool. Excludes cars."
    definition_period = YEAR
    unit = GBP
