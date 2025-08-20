from policyengine_uk.model_api import *


class firm_vat_on_purchases(Variable):
    value_type = float
    entity = Firm
    label = "VAT on purchases"
    definition_period = YEAR
    unit = GBP
    documentation = "Total VAT paid on firm's purchases (input VAT)"
    defined_for = "firm_vat_registered"
