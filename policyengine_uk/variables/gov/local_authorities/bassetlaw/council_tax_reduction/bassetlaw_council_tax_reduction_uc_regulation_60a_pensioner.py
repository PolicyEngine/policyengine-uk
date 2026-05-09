from policyengine_uk.model_api import *


class bassetlaw_council_tax_reduction_uc_regulation_60a_pensioner(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether Bassetlaw disregards a pension-age UC award under regulation 60A"
    documentation = "Covers pension-age Universal Credit cases where the source disregards the UC award for pensioner-status classification under regulation 60A of the Universal Credit (Transitional Provisions) Regulations 2014."
    definition_period = YEAR
    reference = "https://www.bassetlaw.gov.uk/media/4ikne3fx/council-tax-reduction-scheme-pension-age-2026-2027.pdf"
    default_value = False
