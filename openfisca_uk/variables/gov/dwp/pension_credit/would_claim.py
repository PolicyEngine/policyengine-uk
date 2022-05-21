from openfisca_uk.model_api import *
from openfisca_uk.variables.gov.dwp.pension_credit.pension_credit import (
    pension_credit,
)


class baseline_pension_credit(Variable):
    label = "Pension Credit (baseline)"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP


class baseline_has_pension_credit(Variable):
    label = "Receives Pension Credit (baseline)"
    entity = BenUnit
    definition_period = YEAR
    value_type = bool
    default_value = True

    formula = baseline_is_nonzero(pension_credit)


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
        baseline = benunit("baseline_has_pension_credit", period)
        takeup_rate = parameters(period).dwp.pension_credit.takeup
        return select(
            [reported_pc | claims_all_entitled_benefits, ~baseline, True],
            [
                True,
                random(benunit) < takeup_rate,
                False,
            ],
        )
