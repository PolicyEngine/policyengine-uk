from policyengine_uk.model_api import *


class would_claim_pc(Variable):
    label = "Would claim Pension Credit"
    entity = BenUnit
    definition_period = YEAR
    value_type = bool

    def formula(benunit, period, parameters):
        reported_pc = add(benunit, period, ["pension_credit_reported"]) > 0
        claims_all_entitled_benefits = benunit(
            "claims_all_entitled_benefits", period
        )
        baseline = benunit("baseline_pension_credit_entitlement", period) > 0
        eligible = benunit("pension_credit_entitlement", period) > 0
        takeup_rate = parameters(period).gov.dwp.pension_credit.takeup
        return select(
            [
                reported_pc | claims_all_entitled_benefits,
                ~baseline & eligible,
                True,
            ],
            [
                True,
                random(benunit) < takeup_rate,
                False,
            ],
        )
