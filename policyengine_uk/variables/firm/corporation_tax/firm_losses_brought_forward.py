from policyengine_uk.entities import Firm
from policyengine_uk.model_api import *


class firm_losses_brought_forward(Variable):
    value_type = float
    entity = Firm
    label = "Firm losses brought forward"
    documentation = (
        "Carried-forward losses available for relief against the firm's "
        "total profits in the year, before the deductions allowance "
        "restriction."
    )
    definition_period = YEAR
    hidden_input = True
    unit = GBP
