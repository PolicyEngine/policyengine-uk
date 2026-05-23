from policyengine_uk.model_api import *


class havering_council_tax_reduction_war_pension_protected(Variable):
    value_type = bool
    entity = BenUnit
    label = "Havering CTS claimant or partner receives a protected war pension"
    definition_period = YEAR
    reference = "https://www.havering.gov.uk/downloads/file/6930/council-tax-support-scheme-2025-2026"
