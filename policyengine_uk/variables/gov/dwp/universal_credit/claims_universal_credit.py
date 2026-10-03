from policyengine_uk.model_api import *


class claims_universal_credit(Variable):
    value_type = bool
    entity = BenUnit
    label = "Claims Universal Credit"
    documentation = (
        "Whether this family claims Universal Credit: it would claim it "
        "anyway (would_claim_uc), or its legacy benefits have closed "
        "(legacy_benefits_closed) and it would claim when that happens "
        "(would_claim_uc_at_legacy_closure). Universal Credit is paid only "
        "to claiming families, and a claim ends any legacy award."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/8",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/46",
    )

    def formula(benunit, period, parameters):
        claims_at_closure = benunit("legacy_benefits_closed", period) & benunit(
            "would_claim_uc_at_legacy_closure", period
        )
        return benunit("would_claim_uc", period) | claims_at_closure
