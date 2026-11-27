from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_input_vat_attributable_to_exempt_supplies(Variable):
    label = "Input VAT directly attributable to exempt supplies"
    documentation = (
        "The part of firm_input_vat on goods and services used, or to be "
        "used, exclusively in making exempt supplies, which is not recoverable under the "
        "partial exemption standard method (SI 1995/2518 reg 101(2)). The "
        "rest of firm_input_vat is residual input tax, recovered at "
        "firm_partial_exemption_recovery_share. Defaults to 0, so all input "
        "VAT is treated as residual. Negative values count as 0, and the "
        "two attributed amounts together are capped at firm_input_vat, "
        "taxable first."
    )
    entity = Firm
    definition_period = YEAR
    hidden_input = True
    value_type = float
    unit = GBP
    reference = "https://www.legislation.gov.uk/uksi/1995/2518/regulation/101"
