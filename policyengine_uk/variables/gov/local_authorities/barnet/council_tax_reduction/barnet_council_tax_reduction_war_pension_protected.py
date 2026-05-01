from policyengine_uk.model_api import *


class barnet_council_tax_reduction_war_pension_protected(Variable):
    value_type = bool
    entity = BenUnit
    label = "Barnet CTS claimant or partner receives a protected war pension"
    definition_period = YEAR
    reference = "https://barnet.moderngov.co.uk/documents/s94210/Appendix%20O%20-%20202627%20Council%20Tax%20Support%20Scheme.pdf"
