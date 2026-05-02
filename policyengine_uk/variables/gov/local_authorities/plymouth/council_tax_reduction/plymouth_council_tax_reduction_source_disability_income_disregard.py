from policyengine_uk.model_api import *


class plymouth_council_tax_reduction_source_disability_income_disregard(Variable):
    value_type = float
    entity = BenUnit
    label = (
        "Plymouth Council Tax Support source-defined annual disability income disregard"
    )
    documentation = "Covers source-listed disability premium and disabled child premium income disregards not otherwise represented in PolicyEngine UK."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.plymouth.gov.uk/sites/default/files/2026-03/Plymouth-CTR-Scheme-2026-2027.pdf"
    default_value = 0
