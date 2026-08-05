"""UC deductions per-household statistics against DWP deductions statistics.

Reference: DWP, Universal Credit deductions statistics March 2025 to February
2026 (published 12 May 2026). Tolerances are wide enough to absorb dataset
revisions but catch structural breakage. Aggregate levels (total deducted,
counts) scale with the model's UC caseload and are not asserted here.
"""

import numpy as np
import pytest

from policyengine_uk import Microsimulation


@pytest.mark.microsimulation
def test_deduction_statistics_match_dwp():
    sim = Microsimulation()

    for year, cap, at_cap_range, mean_range in [
        # Pre-FRR regime: DWP observed incidence .47, at-25%-cap .13-.14,
        # mean monthly deduction 67-68 GBP (March-May 2025).
        (2024, 0.25, (0.09, 0.18), (55, 80)),
        # FRR regime: DWP observed incidence .46, at-15%-cap .21,
        # mean monthly deduction 51-54 GBP (June 2025-February 2026). The
        # latent-demand model predicts a somewhat higher at-cap share than
        # observed (post-FRR attrition), so the band is wider above.
        (2025, 0.15, (0.17, 0.30), (40, 65)),
    ]:
        w = sim.calculate("benunit_weight", year).values
        uc = sim.calculate("universal_credit", year).values
        has = sim.calculate("uc_has_deduction", year).values
        rate = sim.calculate("uc_deduction_rate", year).values
        deductions = sim.calculate("uc_deductions", year).values

        on_uc = uc > 0
        uc_weight = w[on_uc].sum()
        deducting_weight = w[on_uc & has].sum()

        incidence = deducting_weight / uc_weight
        assert 0.40 < incidence < 0.52, (year, incidence)

        at_cap = w[on_uc & (np.abs(rate - cap) < 1e-4)].sum() / uc_weight
        assert at_cap_range[0] < at_cap < at_cap_range[1], (year, at_cap)

        mean_monthly = deductions[on_uc & has] @ w[on_uc & has] / deducting_weight / 12
        assert mean_range[0] < mean_monthly < mean_range[1], (
            year,
            mean_monthly,
        )


@pytest.mark.microsimulation
def test_draws_are_dispersed_in_microdata():
    sim = Microsimulation()
    draws = sim.calculate("uc_deduction_random_draw", 2025).values
    assert draws.std() > 0.2
    assert 0.45 < draws.mean() < 0.55
