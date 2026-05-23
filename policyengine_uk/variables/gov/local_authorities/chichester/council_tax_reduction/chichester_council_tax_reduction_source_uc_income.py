from policyengine_uk.model_api import *


class chichester_council_tax_reduction_source_uc_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Chichester CTR source total UC assessed income"
    documentation = "Use this input for Chichester's total DWP-assessed Class F income for banding when the default counted-UC-award proxy does not match the source case."
    definition_period = YEAR
    unit = GBP
    reference = "https://chichester.moderngov.co.uk/documents/s30863/09.1%20Appendix%201%20Local%20Council%20Tax%20Reduction%20Scheme%20Rules%202026%20-%202027.pdf"
    default_value = 0
