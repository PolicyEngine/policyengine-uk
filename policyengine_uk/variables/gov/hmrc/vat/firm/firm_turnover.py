from policyengine_uk.model_api import *


class firm_turnover(Variable):
    value_type = float
    entity = Firm
    label = "Firm turnover"
    definition_period = YEAR
    unit = GBP
    documentation = "Annual turnover of the firm from all business activities"
