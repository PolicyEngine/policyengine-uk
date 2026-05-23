from policyengine_uk.model_api import *


class bassetlaw_council_tax_reduction_uc_relevant_period_pensioner(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether a Bassetlaw UC claimant remains in the pensioner scheme during the paragraph 3 relevant period"
    documentation = "Covers the source transitional protection for pension-age Universal Credit cases where the UC award is disregarded for pensioner-status classification."
    definition_period = YEAR
    reference = "https://www.bassetlaw.gov.uk/media/15ehht0s/council-tax-reduction-scheme-working-age-2026-2027.pdf"
    default_value = False
