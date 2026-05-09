from policyengine_uk.model_api import *


class ashford_council_tax_reduction_source_disregarded_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Ashford Council Tax Reduction source-disregarded annual income"
    documentation = (
        "Source input for income disregards not separately exposed in PolicyEngine UK."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.ashford.gov.uk/media/0n4nud13/ashford-ctr-scheme-2026-final.pdf"
    )
    default_value = 0
