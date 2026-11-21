from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_uses_flat_rate_scheme(Variable):
    label = "Elects the VAT flat rate scheme"
    documentation = "Whether the firm elects to account for VAT under the flat rate scheme (VAT Regulations 1995, Part VIIA)."
    entity = Firm
    definition_period = YEAR
    value_type = bool
    default_value = False
