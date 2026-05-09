from policyengine_uk.model_api import *


class bassetlaw_council_tax_reduction_source_disregarded_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Bassetlaw Council Tax Reduction source-disregarded annual income"
    documentation = "Source input for income disregards not separately exposed in PolicyEngine UK."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.bassetlaw.gov.uk/media/15ehht0s/council-tax-reduction-scheme-working-age-2026-2027.pdf"
    default_value = 0
