from policyengine_uk.model_api import *


class hertsmere_council_tax_reduction_source_additional_earnings_disregard(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether Hertsmere's source additional working earnings disregard applies"
    definition_period = YEAR
    reference = "https://www.hertsmere.gov.uk/asset-library/cts-scheme-2026-27.pdf"
    documentation = "Source input for Schedule 3 paragraph 16 conditions not otherwise exposed, such as Working Tax Credit disability or 50-plus element status."
    default_value = False
