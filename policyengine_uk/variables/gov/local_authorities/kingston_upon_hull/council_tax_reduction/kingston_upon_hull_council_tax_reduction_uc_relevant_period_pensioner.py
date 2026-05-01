from policyengine_uk.model_api import *


class kingston_upon_hull_council_tax_reduction_uc_relevant_period_pensioner(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether a Kingston upon Hull UC claimant remains in the pensioner scheme during the paragraph 3 relevant period"
    documentation = "Covers the source transitional protection for pension-age tax-credit-to-Universal-Credit cases where the UC award is disregarded for pensioner-status classification."
    definition_period = YEAR
    reference = "https://www.hull.gov.uk/downloads/file/239/council-tax-reduction-scheme-2025-to-2026"
    default_value = False
