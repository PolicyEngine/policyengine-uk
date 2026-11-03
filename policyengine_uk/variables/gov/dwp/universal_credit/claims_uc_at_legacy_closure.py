from policyengine_uk.model_api import *


class claims_uc_at_legacy_closure(Variable):
    value_type = bool
    entity = BenUnit
    label = "Claims Universal Credit when its legacy benefits close"
    documentation = (
        "Whether this family claims Universal Credit because DWP moved it off "
        "its legacy benefits (legacy_benefits_closed) and it would claim then "
        "(would_claim_uc_at_legacy_closure)."
    )
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2014/1230/regulation/44"

    def formula(benunit, period, parameters):
        return benunit("legacy_benefits_closed", period) & benunit(
            "would_claim_uc_at_legacy_closure", period
        )
