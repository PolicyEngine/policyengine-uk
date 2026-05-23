from policyengine_uk.model_api import *


class ashford_council_tax_reduction_uc_regulation_60a_pensioner(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether Ashford disregards a pension-age UC award under regulation 60A"
    documentation = "Covers pension-age Universal Credit cases where the source disregards the UC award for pensioner-status classification under regulation 60A of the Universal Credit (Transitional Provisions) Regulations 2014."
    definition_period = YEAR
    reference = (
        "https://www.ashford.gov.uk/media/0n4nud13/ashford-ctr-scheme-2026-final.pdf"
    )
    default_value = False
