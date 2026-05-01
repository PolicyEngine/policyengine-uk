from policyengine_uk.model_api import *


class kingston_upon_hull_council_tax_reduction_claimant_source_non_dep_exemption(
    Variable
):
    value_type = bool
    entity = Person
    label = "Whether a Kingston upon Hull CTR claimant has a paragraph 29 non-dependant deduction exemption not otherwise modeled"
    documentation = "Covers source-listed claimant exemptions not otherwise represented in PolicyEngine UK, such as being registered severely sight-impaired."
    definition_period = YEAR
    reference = "https://www.hull.gov.uk/downloads/file/239/council-tax-reduction-scheme-2025-to-2026"
    default_value = False
