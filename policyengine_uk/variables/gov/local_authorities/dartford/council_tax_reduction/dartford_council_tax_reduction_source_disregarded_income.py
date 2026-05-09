from policyengine_uk.model_api import *


class dartford_council_tax_reduction_source_disregarded_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Dartford Council Tax Reduction source-disregarded annual income"
    documentation = "Source-listed income disregards not otherwise separately exposed in PolicyEngine UK, such as war disablement pensions, war widow(er) pensions, or specified compensation payments."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.dartford.gov.uk/downloads/file/2814/local-council-tax-reduction-scheme-dbc-2026-2027"
    default_value = 0
