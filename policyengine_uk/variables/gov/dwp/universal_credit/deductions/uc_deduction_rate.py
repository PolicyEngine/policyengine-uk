from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.universal_credit.deductions.uc_deduction_combination import (
    UCDeductionCombination,
)

# Upper edge of the capped portion of the latent distribution: rates above
# this are last resort deductions, which the law allows to exceed the cap.
LAST_RESORT_THRESHOLD = 0.25


class uc_deduction_rate(Variable):
    label = "UC deduction rate"
    documentation = (
        "Deductions taken from this benefit unit's Universal Credit award as "
        "a fraction of the standard allowance, after removing any abolished "
        "deduction types and applying the deductions cap. Last resort "
        "deductions (above 25% of the standard allowance) are exempt from "
        "the cap."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = float

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.universal_credit.deductions
        latent = benunit("uc_latent_deduction_rate", period)
        combination = benunit("uc_deduction_combination", period)

        m = p.mean_monthly_amount_by_type
        advance_weight = 0.0 if p.abolish.advance else m.ADVANCE
        third_party_weight = 0.0 if p.abolish.third_party else m.THIRD_PARTY
        government_weight = 0.0 if p.abolish.government else m.GOVERNMENT

        def retained(kept, total):
            return kept / total

        retained_share = select(
            [
                combination == UCDeductionCombination.ADVANCE_ONLY,
                combination == UCDeductionCombination.THIRD_PARTY_ONLY,
                combination == UCDeductionCombination.GOVERNMENT_ONLY,
                combination == UCDeductionCombination.ADVANCE_AND_GOVERNMENT,
                combination == UCDeductionCombination.ADVANCE_AND_THIRD_PARTY,
                combination == UCDeductionCombination.THIRD_PARTY_AND_GOVERNMENT,
                combination == UCDeductionCombination.ALL_THREE,
            ],
            [
                retained(advance_weight, m.ADVANCE),
                retained(third_party_weight, m.THIRD_PARTY),
                retained(government_weight, m.GOVERNMENT),
                retained(
                    advance_weight + government_weight,
                    m.ADVANCE + m.GOVERNMENT,
                ),
                retained(
                    advance_weight + third_party_weight,
                    m.ADVANCE + m.THIRD_PARTY,
                ),
                retained(
                    third_party_weight + government_weight,
                    m.THIRD_PARTY + m.GOVERNMENT,
                ),
                retained(
                    advance_weight + third_party_weight + government_weight,
                    m.ADVANCE + m.THIRD_PARTY + m.GOVERNMENT,
                ),
            ],
            default=0.0,
        )
        rate = latent * retained_share
        is_last_resort = latent > LAST_RESORT_THRESHOLD
        return where(is_last_resort, rate, min_(rate, p.cap))
