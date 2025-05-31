from policyengine_uk.model_api import *


class would_claim_IS(Variable):
    value_type = bool
    entity = BenUnit
    label = "Would claim Income Support"
    documentation = (
        "Whether this family would claim Income Support if eligible"
    )
    definition_period = YEAR

    def formula(benunit, period, parameters):
        reported_is = add(benunit, period, ["income_support_reported"]) > 0
        claims_all_entitled_benefits = benunit(
            "claims_all_entitled_benefits", period
        )
        return reported_is | claims_all_entitled_benefits
