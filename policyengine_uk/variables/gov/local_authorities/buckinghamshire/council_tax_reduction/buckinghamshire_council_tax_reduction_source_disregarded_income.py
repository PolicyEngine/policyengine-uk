from policyengine_uk.model_api import *


class buckinghamshire_council_tax_reduction_source_disregarded_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Buckinghamshire CTR source-disregarded annual income"
    documentation = "Source-listed non-UC income disregards not otherwise separately exposed in PolicyEngine UK, such as war pensions or other specified payments."
    definition_period = YEAR
    unit = GBP
    reference = "https://buckinghamshire.moderngov.co.uk/documents/s115727/Appendix%204%20Council%20Tax%20Reduction%20Scheme%20Policy.pdf"
    default_value = 0
