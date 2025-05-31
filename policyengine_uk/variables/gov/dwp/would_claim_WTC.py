from policyengine_uk.model_api import *


class would_claim_WTC(Variable):
    value_type = bool
    entity = BenUnit
    label = "Would claim Working Tax Credit"
    documentation = (
        "Whether this family would claim Working Tax Credit if eligible"
    )
    definition_period = YEAR

    def formula(benunit, period, parameters):
        reported_wtc = (
            add(benunit, period, ["working_tax_credit_reported"]) > 0
        )
        claims_all_entitled_benefits = benunit(
            "claims_all_entitled_benefits", period
        )
        return reported_wtc | claims_all_entitled_benefits
