from policyengine_uk.model_api import *


class would_claim_IS(Variable):
    value_type = bool
    entity = BenUnit
    label = "Would claim Income Support"
    documentation = (
        "Whether this family would claim Income Support if eligible: the "
        "claimant or partner reports an award. Another member of the benefit "
        "unit who reports Income Support, such as a non-dependent adult, "
        "claims for themselves, not for this family."
    )
    definition_period = YEAR

    def formula(benunit, period, parameters):
        person = benunit.members
        reported_is = (
            benunit.sum(
                person("income_support_reported", period)
                * person("is_claimant_or_partner", period)
            )
            > 0
        )
        claims_all_entitled_benefits = benunit("claims_all_entitled_benefits", period)
        return reported_is | claims_all_entitled_benefits
