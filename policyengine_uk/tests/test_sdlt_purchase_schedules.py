"""Recent SDLT purchase schedules: raw legal dates versus annual sampling.

Cash vectors are independent literals from FA 2003 s55/Sch6ZA, the SDLT
(Temporary Relief) Act 2023 s1 and Finance Act 2025 ss50-51. They describe
ordinary unprotected purchases, not contract protections or return rounding.
"""

from pathlib import Path

import numpy as np
import pytest
from policyengine_core.parameters import ParameterNode

import policyengine_uk
from policyengine_uk import CountryTaxBenefitSystem


PRICES = np.array([125_000, 250_000, 925_000, 1_500_000, 1_600_000])
OLD_MAIN = [0, 2_500, 36_250, 93_750, 105_750]
TEMPORARY_MAIN = [0, 0, 33_750, 91_250, 103_250]


@pytest.fixture(scope="module")
def raw_purchase_parameters():
    # Bypass annual conversion only for raw legal-date scale tests.
    return ParameterNode(
        "purchase",
        directory_path=str(
            Path(policyengine_uk.__file__).parent
            / "parameters/gov/hmrc/stamp_duty/residential/purchase"
        ),
    )


@pytest.mark.parametrize(
    "date,main_cash,additional_cash,thresholds,additional_rates,ftb_nil,ftb_max",
    [
        (
            "2022-09-22",
            OLD_MAIN,
            [3_750, 10_000, 64_000, 138_750, 153_750],
            [0, 125_000, 250_000, 925_000, 1_500_000],
            [0.03, 0.05, 0.08, 0.13, 0.15],
            300_000,
            500_000,
        ),
        (
            "2022-09-23",
            TEMPORARY_MAIN,
            [3_750, 7_500, 61_500, 136_250, 151_250],
            [0, 250_000, 925_000, 1_500_000],
            [0.03, 0.08, 0.13, 0.15],
            425_000,
            625_000,
        ),
        (
            "2024-10-30",
            TEMPORARY_MAIN,
            [3_750, 7_500, 61_500, 136_250, 151_250],
            [0, 250_000, 925_000, 1_500_000],
            [0.03, 0.08, 0.13, 0.15],
            425_000,
            625_000,
        ),
        (
            "2024-10-31",
            TEMPORARY_MAIN,
            [6_250, 12_500, 80_000, 166_250, 183_250],
            [0, 250_000, 925_000, 1_500_000],
            [0.05, 0.10, 0.15, 0.17],
            425_000,
            625_000,
        ),
        (
            "2025-03-31",
            TEMPORARY_MAIN,
            [6_250, 12_500, 80_000, 166_250, 183_250],
            [0, 250_000, 925_000, 1_500_000],
            [0.05, 0.10, 0.15, 0.17],
            425_000,
            625_000,
        ),
        (
            "2025-04-01",
            OLD_MAIN,
            [6_250, 15_000, 82_500, 168_750, 185_750],
            [0, 125_000, 250_000, 925_000, 1_500_000],
            [0.05, 0.07, 0.10, 0.15, 0.17],
            300_000,
            500_000,
        ),
    ],
)
def test_raw_purchase_schedules(
    raw_purchase_parameters,
    date,
    main_cash,
    additional_cash,
    thresholds,
    additional_rates,
    ftb_nil,
    ftb_max,
):
    purchase = raw_purchase_parameters(date)
    np.testing.assert_allclose(
        purchase.main.subsequent.calc(PRICES), main_cash, rtol=0, atol=1e-8
    )
    np.testing.assert_allclose(
        purchase.additional.rate.calc(PRICES),
        additional_cash,
        rtol=0,
        atol=1e-8,
    )
    # This also proves that null brackets disappear, rather than duplicating
    # an active threshold during the temporary period.
    assert purchase.main.subsequent.thresholds == thresholds
    assert purchase.additional.rate.thresholds == thresholds
    assert purchase.additional.rate.rates == additional_rates
    assert purchase.main.first.max == ftb_max
    np.testing.assert_allclose(
        purchase.main.first.rate.calc(np.array([ftb_nil, ftb_nil + 20, ftb_max])),
        [0, 1, 10_000],
        rtol=0,
        atol=1e-8,
    )


@pytest.fixture(scope="module")
def annual_system():
    return CountryTaxBenefitSystem()


@pytest.mark.parametrize(
    "year,main300k,additional400k,first500k",
    [
        (2022, 5_000, 22_000, 10_000),
        (2023, 2_500, 19_500, 3_750),
        (2024, 2_500, 19_500, 3_750),
        (2025, 5_000, 30_000, 10_000),
        (2027, 5_000, 30_000, 10_000),
    ],
)
def test_annual_purchase_parameters_sample_april_30(
    annual_system, year, main300k, additional400k, first500k
):
    purchase = annual_system.parameters(year).gov.hmrc.stamp_duty.residential.purchase
    np.testing.assert_allclose(
        purchase.main.subsequent.calc(np.array([300_000])), main300k, rtol=0, atol=1e-8
    )
    np.testing.assert_allclose(
        purchase.additional.rate.calc(np.array([400_000])),
        additional400k,
        rtol=0,
        atol=1e-8,
    )
    np.testing.assert_allclose(
        purchase.main.first.rate.calc(np.array([500_000])), first500k, rtol=0, atol=1e-8
    )
