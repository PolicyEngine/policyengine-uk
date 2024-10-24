from policyengine_uk.model_api import *


class housing_benefit_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "eligible for the Housing Benefit"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        social = benunit.any(benunit.members("in_social_housing", period))
        already_claiming = (
            add(benunit, period, ["housing_benefit_reported"]) > 0
        )
        claiming_uc = benunit("would_claim_uc", period)
        lha_eligible = benunit("LHA_eligible", period)
        return already_claiming & (social | lha_eligible) & ~claiming_uc
