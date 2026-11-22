from policyengine_uk.entities import Firm
from policyengine_uk.model_api import *


class firm_deductions_allowance_share(Variable):
    value_type = float
    entity = Firm
    label = "Firm share of the losses deductions allowance"
    documentation = (
        "Share of the £5m corporation tax deductions allowance allocated to "
        "this company. A group shares one allowance between its members; "
        "the default of 1 gives the company the whole allowance."
    )
    definition_period = YEAR
    unit = "/1"
    default_value = 1
