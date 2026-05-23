from policyengine_uk.model_api import *


class plymouth_council_tax_reduction_source_disability_or_esa_component(Variable):
    value_type = bool
    entity = BenUnit
    label = "Plymouth Council Tax Support source-defined disability or ESA component earnings disregard trigger"
    documentation = "Covers source-listed disability premium, severe disability premium, work-related activity component, or support component triggers not otherwise represented in PolicyEngine UK."
    definition_period = YEAR
    reference = "https://www.plymouth.gov.uk/sites/default/files/2026-03/Plymouth-CTR-Scheme-2026-2027.pdf"
    default_value = False
