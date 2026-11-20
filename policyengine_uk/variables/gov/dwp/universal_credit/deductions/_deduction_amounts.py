"""Calibration helpers; cash estimates are not statutory instalment rules."""

from policyengine_uk.model_api import *


def assigned_latent_deduction_rate(benunit, period):
    """The latent rate of a unit flagged as having deductions, else zero.

    uc_latent_deduction_rate's own formula already returns zero without the
    flag. This applies the same rule to a rate a dataset or situation
    supplies, so a supplied rate cannot give deductions to a unit whose
    uc_has_deduction is False (#2739).
    """
    return where(
        benunit("uc_has_deduction", period),
        benunit("uc_latent_deduction_rate", period),
        0,
    )


def deduction_type_shares(benunit, period, parameters):
    """Split the legacy total by its existing marginal-mean approximation."""
    m = parameters(period).gov.simulation.uc_deductions.mean_monthly_amount_by_type
    combination = benunit("uc_deduction_combination", period)
    advance = (
        np.isin(
            combination.decode_to_str(),
            [
                "ADVANCE_ONLY",
                "ADVANCE_AND_GOVERNMENT",
                "ADVANCE_AND_THIRD_PARTY",
                "ALL_THREE",
            ],
        )
        * m.ADVANCE
    )
    third_party = (
        np.isin(
            combination.decode_to_str(),
            [
                "THIRD_PARTY_ONLY",
                "ADVANCE_AND_THIRD_PARTY",
                "THIRD_PARTY_AND_GOVERNMENT",
                "ALL_THREE",
            ],
        )
        * m.THIRD_PARTY
    )
    government = (
        np.isin(
            combination.decode_to_str(),
            [
                "GOVERNMENT_ONLY",
                "ADVANCE_AND_GOVERNMENT",
                "THIRD_PARTY_AND_GOVERNMENT",
                "ALL_THREE",
            ],
        )
        * m.GOVERNMENT
    )
    total = advance + third_party + government
    return tuple(
        np.divide(part, total, out=np.zeros_like(part, dtype=float), where=total > 0)
        for part in (advance, third_party, government)
    )


def reference_standard_allowance(benunit, period, parameters):
    """Same-year current-law allowance, sampled as UK fiscal parameters are.

    The baseline tree is projected but not fiscal-year annualised. A legacy
    rate has no cash-origin year, so this preserves its annual cross-section;
    it does not establish a debt instalment's path across projection years.
    """
    p = parameters(f"{period.start.year}-04-30").baseline.gov.dwp.universal_credit
    claimant_type = benunit("uc_standard_allowance_claimant_type", period)
    return p.standard_allowance.amount[claimant_type] * MONTHS_IN_YEAR


def estimated_advance_repayment_amount(benunit, period, parameters):
    """Convert the legacy advance share to same-year unreformed cash."""
    p = parameters(period).gov.simulation.uc_deductions
    advance_share, _, _ = deduction_type_shares(benunit, period, parameters)
    latent = max_(assigned_latent_deduction_rate(benunit, period), 0)
    return (
        min_(latent, p.calibration_cap)
        * advance_share
        * reference_standard_allowance(benunit, period, parameters)
    )
