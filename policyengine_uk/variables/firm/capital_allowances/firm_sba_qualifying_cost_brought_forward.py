from policyengine_uk.model_api import *


class firm_sba_qualifying_cost_brought_forward(Variable):
    value_type = float
    entity = Firm
    label = "Firm structures and buildings qualifying cost brought forward"
    documentation = "Qualifying cost of non-residential structures and buildings brought into use in earlier years on which the structures and buildings allowance is still being claimed."
    definition_period = YEAR
    unit = GBP
