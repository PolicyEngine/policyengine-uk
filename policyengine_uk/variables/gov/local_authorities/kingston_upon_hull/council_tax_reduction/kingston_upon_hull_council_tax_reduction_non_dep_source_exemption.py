from policyengine_uk.model_api import *


class kingston_upon_hull_council_tax_reduction_non_dep_source_exemption(Variable):
    value_type = bool
    entity = Person
    label = "Whether a Kingston upon Hull CTR non-dependant has a paragraph 29 deduction exemption not otherwise modeled"
    documentation = "Covers source-listed non-dependant exemptions not otherwise represented in PolicyEngine UK, such as normal home elsewhere, youth training, long-term patient status, armed forces operations, or discount-disregarded cases."
    definition_period = YEAR
    reference = "https://www.hull.gov.uk/downloads/file/239/council-tax-reduction-scheme-2025-to-2026"
    default_value = False
