from policyengine_uk.model_api import *


class cheltenham_council_tax_reduction_uc_transitional_protection(Variable):
    value_type = float
    entity = BenUnit
    label = "Cheltenham Council Tax Support Universal Credit transitional protection"
    documentation = "Source input for the Universal Credit transitional protection payment disregarded from Cheltenham Council Tax Support income."
    definition_period = YEAR
    unit = GBP
    reference = "https://democracy.cheltenham.gov.uk/documents/s53359/Appendix%209%20-%20Council%20270226%20Council%20Tax%20Support%20Scheme%20for%20Working%20Age%20Customers%202026-27%20Final.pdf"
    default_value = 0
