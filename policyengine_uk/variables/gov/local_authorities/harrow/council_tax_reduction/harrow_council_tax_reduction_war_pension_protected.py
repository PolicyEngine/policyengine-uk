from policyengine_uk.model_api import *


class harrow_council_tax_reduction_war_pension_protected(Variable):
    value_type = bool
    entity = BenUnit
    label = "Harrow CTS claimant or partner receives a protected war pension"
    definition_period = YEAR
    reference = "https://www.harrow.gov.uk/downloads/file/33606/council-tax-support-scheme-2026-27"
