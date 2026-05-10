from policyengine_uk.model_api import *


class hertsmere_council_tax_reduction_is_uc_scheme(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether Hertsmere's Class G Universal Credit scheme applies"
    definition_period = YEAR
    reference = "https://www.hertsmere.gov.uk/asset-library/cts-scheme-2026-27.pdf"

    def formula(benunit, period, parameters):
        return benunit("hertsmere_council_tax_reduction_is_local_scheme", period) & (
            max_(
                benunit("universal_credit_pre_benefit_cap", period),
                benunit("universal_credit", period),
            )
            > 0
        )
