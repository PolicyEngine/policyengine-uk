from policyengine_uk.model_api import *


class would_claim_CTC(Variable):
    value_type = bool
    entity = BenUnit
    label = "Would claim Child Tax Credit"
    documentation = (
        "Whether this family would claim Child Tax Credit if eligible"
    )
    definition_period = YEAR

    def formula(benunit, period, parameters):
        reported_ctc = add(benunit, period, ["child_tax_credit_reported"]) > 0
        claims_all_entitled_benefits = benunit(
            "claims_all_entitled_benefits", period
        )
        return reported_ctc | claims_all_entitled_benefits
