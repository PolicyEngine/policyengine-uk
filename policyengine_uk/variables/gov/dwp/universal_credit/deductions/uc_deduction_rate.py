from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.universal_credit.deductions._deduction_amounts import (
    deduction_type_shares,
    estimated_advance_repayment_amount,
)


class uc_deduction_rate(Variable):
    label = "UC deduction rate"
    documentation = (
        "Deductions as a fraction of the current Universal Credit standard allowance, "
        "after removing abolished ordinary debt types and applying the cap. "
        "Advance demand is held in cash through an allowance reform; the rate "
        "therefore adjusts when the allowance changes. An explicitly supplied "
        "rate retains its existing precedence in the final award. The legacy "
        "above-cap excess is unchanged."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = float

    def formula(benunit, period, parameters):
        law = parameters(period).gov.dwp.universal_credit.deductions
        calibration_cap = parameters(
            period
        ).gov.simulation.uc_deductions.calibration_cap
        _, third_share, government_share = deduction_type_shares(
            benunit, period, parameters
        )
        remaining_share = third_share * (
            not law.abolish.third_party
        ) + government_share * (not law.abolish.government)
        allowance = benunit("uc_standard_allowance", period)
        latent = benunit("uc_latent_deduction_rate", period)
        other_rate = min_(latent, calibration_cap) * remaining_share
        advance = benunit("uc_advance_repayment_amount", period)
        # A partially supplied input array contains -1 for omitted units.
        # Resolve those units independently, retaining explicitly supplied zero.
        advance = where(
            advance >= 0,
            advance,
            estimated_advance_repayment_amount(benunit, period, parameters),
        )
        if law.abolish.advance:
            advance = 0
        advance_rate = np.divide(
            max_(advance, 0),
            allowance,
            out=np.zeros_like(allowance),
            where=allowance > 0,
        )
        # Preserve the original unclassified above-cap proxy. Its legal
        # categories and time path need separate data/policy work (#2410).
        above_cap_excess = max_(latent - calibration_cap, 0)
        return min_(advance_rate + other_rate, law.cap) + above_cap_excess
