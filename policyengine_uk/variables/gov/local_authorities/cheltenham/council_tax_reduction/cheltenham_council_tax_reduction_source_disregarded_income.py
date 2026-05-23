from policyengine_uk.model_api import *


class cheltenham_council_tax_reduction_source_disregarded_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Cheltenham Council Tax Support source-disregarded annual income"
    documentation = "Source-listed income disregards not otherwise separately exposed in PolicyEngine UK, such as war pensions or specified compensation payments."
    definition_period = YEAR
    unit = GBP
    reference = "https://democracy.cheltenham.gov.uk/documents/s53359/Appendix%209%20-%20Council%20270226%20Council%20Tax%20Support%20Scheme%20for%20Working%20Age%20Customers%202026-27%20Final.pdf"
    default_value = 0
