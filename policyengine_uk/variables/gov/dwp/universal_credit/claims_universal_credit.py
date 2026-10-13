from policyengine_uk.model_api import *


class claims_universal_credit(Variable):
    value_type = bool
    entity = BenUnit
    label = "Claims Universal Credit"
    documentation = (
        "Whether this family claims Universal Credit: it would claim it "
        "anyway (would_claim_uc), or it claims when DWP moves it off its "
        "legacy benefits (claims_uc_at_legacy_closure). Universal Credit is "
        "paid only to claiming families. A claim ends the family's Housing "
        "Benefit continuing award and Child Tax Credit. Once DWP moves a "
        "family off legacy benefits (legacy_benefits_closed) all its legacy "
        "awards end; for other claimants the overlap of Universal Credit "
        "with Working Tax Credit, Income Support, income-related ESA and "
        "income-based JSA is not modelled, nor is Housing Benefit for "
        "specified or temporary accommodation."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/8",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/46",
    )

    def formula(benunit, period, parameters):
        return benunit("would_claim_uc", period) | benunit(
            "claims_uc_at_legacy_closure", period
        )
