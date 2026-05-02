from policyengine_uk.model_api import *


class buckinghamshire_council_tax_reduction_esa_support_component(Variable):
    value_type = float
    entity = BenUnit
    label = "Buckinghamshire CTR annual ESA support component amount to disregard"
    definition_period = YEAR
    unit = GBP
    reference = "https://buckinghamshire.moderngov.co.uk/documents/s115727/Appendix%204%20Council%20Tax%20Reduction%20Scheme%20Policy.pdf"
    default_value = 0
