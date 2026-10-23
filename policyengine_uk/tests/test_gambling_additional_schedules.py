"""New duty dates, operator catalogue and the household casino approximation."""

import numpy as np
import pytest

from policyengine_uk import CountryTaxBenefitSystem
from policyengine_uk.tests.test_gambling_schedules import gambling_simulation


def test_bingo_rate_preserves_abolition_date():
    """Finance Act 2026 section 88 abolishes bingo duty on 1 April 2026."""
    system = CountryTaxBenefitSystem()
    rate = system.parameters.gov.hmrc.gambling_duty.bingo.rate
    assert rate("2026-03-31") == 0.1
    assert rate("2026-04-01") == 0


def test_registered_casino_normal_six_month_operator_catalogue():
    """Finance Act 1997 section 11(2): cumulative six-month premises bands."""
    system = CountryTaxBenefitSystem()
    scale = system.parameters(
        "2024"
    ).gov.hmrc.gambling_duty.gaming.normal_six_month_bands
    yield_amounts = np.array(
        [
            0,
            2_686_000,
            2_686_001,
            4_538_000,
            4_538_001,
            7_781_000,
            7_781_001,
            14_626_000,
            14_626_001,
        ],
        dtype=float,
    )
    # Successive statutory widths: 2,686,000; 1,852,000; 3,243,000; 6,845,000.
    expected = [
        0,
        402_900,
        402_900.2,
        773_300,
        773_300.3,
        1_746_200,
        1_746_200.4,
        4_484_200,
        4_484_200.5,
    ]
    assert scale.calc(yield_amounts) == pytest.approx(expected)


def test_explicit_casino_incidence_reform_changes_household_duty():
    """An explicit 30% incidence assumption charges GBP 300 on GBP 1,000."""
    sim = gambling_simulation(
        2024,
        {"household.consumption.gambling.casino_effective_rate": {"2024": 0.3}},
        {"land_based_casino_net_losses": 1_000},
    )
    assert sim.calculate("gaming_duty", 2024).iloc[0] == pytest.approx(300)


def test_operator_band_reform_does_not_automatically_change_household_proxy():
    """The empirical household proxy does not model casino band responses."""
    sim = gambling_simulation(
        2024,
        {"gov.hmrc.gambling_duty.gaming.normal_six_month_bands[0].rate": {"2024": 0.3}},
        {"land_based_casino_net_losses": 1_000},
    )
    assert sim.calculate("gaming_duty", 2024).iloc[0] == pytest.approx(235.487)
