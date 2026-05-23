from policyengine_uk.model_api import *


class plymouth_council_tax_reduction_source_special_earnings_disregard(Variable):
    value_type = bool
    entity = BenUnit
    label = "Plymouth Council Tax Support source-defined special occupation earnings disregard trigger"
    documentation = "Covers source-listed part-time firefighter, coastguard, lifeboat, and reserve forces earnings disregard triggers not otherwise represented in PolicyEngine UK."
    definition_period = YEAR
    reference = "https://www.plymouth.gov.uk/sites/default/files/2026-03/Plymouth-CTR-Scheme-2026-2027.pdf"
    default_value = False
