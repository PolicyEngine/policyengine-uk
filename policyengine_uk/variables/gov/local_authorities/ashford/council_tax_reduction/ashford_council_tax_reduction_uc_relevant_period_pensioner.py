from policyengine_uk.model_api import *


class ashford_council_tax_reduction_uc_relevant_period_pensioner(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether an Ashford UC claimant remains in the pensioner scheme during the relevant period"
    documentation = "Covers the source transitional protection for pension-age Universal Credit cases where the UC award is disregarded for pensioner-status classification."
    definition_period = YEAR
    reference = (
        "https://www.ashford.gov.uk/media/0n4nud13/ashford-ctr-scheme-2026-final.pdf"
    )
    default_value = False
