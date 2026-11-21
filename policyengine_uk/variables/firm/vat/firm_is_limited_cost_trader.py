from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_is_limited_cost_trader(Variable):
    label = "Limited cost trader"
    documentation = "Whether the firm is a limited cost trader for the VAT flat rate scheme (VAT Regulations 1995, regulation 55KA)."
    entity = Firm
    definition_period = YEAR
    value_type = bool
    default_value = False
