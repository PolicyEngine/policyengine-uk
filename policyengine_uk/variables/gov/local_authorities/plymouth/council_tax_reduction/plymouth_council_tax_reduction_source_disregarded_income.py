from policyengine_uk.model_api import *


class plymouth_council_tax_reduction_source_disregarded_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Plymouth Council Tax Support source-disregarded annual income"
    documentation = "Source-listed income disregards not otherwise separately exposed in PolicyEngine UK, such as war pensions, Bereavement Support Payments, or specified compensation payments."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.plymouth.gov.uk/sites/default/files/2026-03/Plymouth-CTR-Scheme-2026-2027.pdf"
    default_value = 0
