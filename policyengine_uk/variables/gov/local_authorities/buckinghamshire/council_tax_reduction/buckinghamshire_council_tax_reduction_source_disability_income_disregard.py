from policyengine_uk.model_api import *


class buckinghamshire_council_tax_reduction_source_disability_income_disregard(
    Variable
):
    value_type = bool
    entity = BenUnit
    label = "Buckinghamshire CTR source-defined disability income disregard applies"
    documentation = "Covers source-listed disability disregard triggers not otherwise represented in PolicyEngine UK."
    definition_period = YEAR
    reference = "https://buckinghamshire.moderngov.co.uk/documents/s115727/Appendix%204%20Council%20Tax%20Reduction%20Scheme%20Policy.pdf"
    default_value = False
