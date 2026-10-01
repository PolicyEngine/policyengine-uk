from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.universal_credit.deductions.uc_deduction_combination import (
    UCDeductionCombination,
)


class uc_deduction_rate(Variable):
    label = "UC deduction rate"
    documentation = (
        "Deductions taken from this benefit unit's Universal Credit award as "
        "a fraction of the standard allowance, after removing any abolished "
        "deduction types and applying the deductions cap. The above-cap "
        "excess (latent demand above 25% of the standard allowance, covering "
        "last resort and child maintenance deductions) sits on top of the "
        "cap."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = float

    def formula(benunit, period, parameters):
        # Law: the cap and abolition switches. Estimation: the mean amounts
        # by type (gov.simulation), used only to split a household's total
        # rate across its deduction types.
        law = parameters(period).gov.dwp.universal_credit.deductions
        m = parameters(period).gov.simulation.uc_deductions.mean_monthly_amount_by_type
        latent = benunit("uc_latent_deduction_rate", period)
        combination = benunit("uc_deduction_combination", period)

        advance_weight = 0.0 if law.abolish.advance else m.ADVANCE
        third_party_weight = 0.0 if law.abolish.third_party else m.THIRD_PARTY
        government_weight = 0.0 if law.abolish.government else m.GOVERNMENT

        def retained(kept, total):
            return kept / max(total, 1e-9)

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
        # The cappable portion covers the three modeled deduction types
        # (advances, third party, government debt) and responds to the cap
        # and abolition switches. Latent demand above the calibration-window
        # cap belongs to categories permitted to exceed the cap (last resort
        # and child maintenance deductions), exempt from both.
        calibration_cap = parameters(
            period
        ).gov.simulation.uc_deductions.calibration_cap
        cappable = min_(latent, calibration_cap) * retained_share
        above_cap_excess = max_(latent - calibration_cap, 0)
        return min_(cappable, law.cap) + above_cap_excess
