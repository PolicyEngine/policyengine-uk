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
        baseline = benunit("housing_benefit_baseline_entitlement", period) > 0
        entitlement_received = (
            benunit("housing_benefit_entitlement", period) > 0
        )
        takeup_rate = parameters(period).gov.dwp.housing_benefit.takeup
        return select(
            [
                reported_hb | claims_all_entitled_benefits,
                ~baseline & entitlement_received,
                True,
            ],
            [
                True,
                random(benunit) < takeup_rate,
                False,
            ],
        )
