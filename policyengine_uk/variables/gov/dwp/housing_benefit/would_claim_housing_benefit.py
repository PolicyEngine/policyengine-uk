from policyengine_uk.model_api import *


class would_claim_housing_benefit(Variable):
    value_type = bool
    entity = BenUnit
    label = "Would claim the Housing Benefit"
    documentation = (
        "Whether this family would claim Housing Benefit if eligible"
    )
    definition_period = YEAR

    def formula(benunit, period, parameters):
        claims_all_entitled_benefits = benunit(
            "claims_all_entitled_benefits", period
        )
        reported_hb = add(benunit, period, ["housing_benefit_reported"]) > 0
        return claims_all_entitled_benefits | reported_hb
