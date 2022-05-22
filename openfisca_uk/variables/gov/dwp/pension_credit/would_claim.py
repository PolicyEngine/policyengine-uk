from openfisca_uk.model_api import *
from openfisca_uk.variables.gov.dwp.pension_credit.pension_credit import (
    pension_credit,
)


class baseline_is_pension_credit_eligible(Variable):
    label = "Pension Credit (baseline)"
    entity = BenUnit
    definition_period = YEAR
    value_type = bool


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
        baseline = benunit("baseline_is_pension_credit_eligible", period)
        eligible = benunit("is_pension_credit_eligible", period)
        takeup_rate = parameters(period).dwp.pension_credit.takeup
        return select(
            [reported_pc | claims_all_entitled_benefits, ~baseline & eligible, True],
            [
                True,
                random(benunit) < takeup_rate,
                False,
            ],
        )
