"""Recent SDLT purchase schedules: raw legal dates versus annual sampling.

Cash vectors are independent literals from FA 2003 s55/Sch6ZA, the SDLT
(Temporary Relief) Act 2023 s1 and Finance Act 2025 ss50-51. They describe
ordinary unprotected purchases, not contract protections or return rounding.
The 2020-21 vectors come from FA 2003 s55(1B) Table A, Sch4ZA para 1(2),
Sch5 para 2(3) and Sch6ZA para 4, and the SDLT (Temporary Relief) Act 2020
s1 (8 July 2020 to 30 June 2021, as amended by Finance Act 2021 s87(2)(a))
and s1A (1 July to 30 September 2021, inserted by Finance Act 2021 s87(3)).
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


HOLIDAY_PRICES = np.array(
    [125_000, 250_000, 300_000, 400_000, 500_000, 600_000, 925_000]
    + [1_500_000, 1_600_000]
)
# FA 2003 s55(1B) Table A, Sch6ZA para 4 (first-time buyers, to £500,000)
# and Sch4ZA para 1(2) (additional dwellings).
STANDARD_2020_21 = {
    "main": [0, 2_500, 5_000, 10_000, 15_000, 20_000, 36_250, 93_750, 105_750],
    "first": [0, 0, 0, 5_000, 10_000, 20_000, 36_250, 93_750, 105_750],
    "additional": [3_750, 10_000, 14_000, 22_000, 30_000, 38_000, 64_000]
    + [138_750, 153_750],
}
# 2020 Act s1(2) and (3). s1(5) omits Sch6ZA, so first-time buyers pay s1(2).
INITIAL_RELIEF = {
    "main": [0, 0, 0, 0, 0, 5_000, 21_250, 78_750, 90_750],
    "first": [0, 0, 0, 0, 0, 5_000, 21_250, 78_750, 90_750],
    "additional": [3_750, 7_500, 9_000, 12_000, 15_000, 23_000, 49_000]
    + [123_750, 138_750],
}
# 2020 Act s1A(2) and (3). Sch6ZA applies again.
FURTHER_RELIEF = {
    "main": [0, 0, 2_500, 7_500, 12_500, 17_500, 33_750, 91_250, 103_250],
    "first": [0, 0, 0, 5_000, 10_000, 17_500, 33_750, 91_250, 103_250],
    "additional": [3_750, 7_500, 11_500, 19_500, 27_500, 35_500, 61_500]
    + [136_250, 151_250],
}
LEASE_RENTS = np.array([125_000, 250_000, 500_000, 600_000])
# FA 2003 Sch5 para 2(3) Table A: 1% above £125,000, above £500,000 under
# 2020 Act s1(4), and above £250,000 under s1A(4) and 2023 Act s1(4).
LEASE_STANDARD = [0, 1_250, 3_750, 4_750]
LEASE_500K = [0, 0, 0, 1_000]
LEASE_250K = [0, 0, 2_500, 3_500]


def _residential_purchase_tax(purchase, price, buyer):
    # The schedule sdlt_on_residential_property_transactions applies to each
    # kind of purchase.
    if buyer == "first":
        return np.where(
            price <= purchase.main.first.max,
            purchase.main.first.rate.calc(price),
            purchase.main.subsequent.calc(price),
        )
    if buyer == "additional":
        chargeable = np.where(price < purchase.additional.min, 0, price)
        return purchase.additional.rate.calc(chargeable)
    return purchase.main.subsequent.calc(price)


@pytest.fixture(scope="module")
def raw_residential_parameters():
    # Bypass annual conversion only for raw legal-date scale tests.
    return ParameterNode(
        "residential",
        directory_path=str(
            Path(policyengine_uk.__file__).parent
            / "parameters/gov/hmrc/stamp_duty/residential"
        ),
    )


@pytest.mark.parametrize(
    "date,cash,lease_cash",
    [
        ("2020-07-07", STANDARD_2020_21, LEASE_STANDARD),
        ("2020-07-08", INITIAL_RELIEF, LEASE_500K),
        ("2021-03-31", INITIAL_RELIEF, LEASE_500K),
        ("2021-04-01", INITIAL_RELIEF, LEASE_500K),
        ("2021-06-30", INITIAL_RELIEF, LEASE_500K),
        ("2021-07-01", FURTHER_RELIEF, LEASE_250K),
        ("2021-09-30", FURTHER_RELIEF, LEASE_250K),
        ("2021-10-01", STANDARD_2020_21, LEASE_STANDARD),
    ],
)
def test_raw_2020_21_relief_schedules(
    raw_residential_parameters, date, cash, lease_cash
):
    residential = raw_residential_parameters(date)
    for buyer, expected in cash.items():
        np.testing.assert_allclose(
            _residential_purchase_tax(residential.purchase, HOLIDAY_PRICES, buyer),
            expected,
            rtol=0,
            atol=1e-8,
            err_msg=f"{buyer} on {date}",
        )
    np.testing.assert_allclose(
        residential.rent.calc(LEASE_RENTS), lease_cash, rtol=0, atol=1e-8
    )


@pytest.mark.parametrize(
    "date,lease_cash",
    [
        ("2022-09-22", LEASE_STANDARD),
        ("2022-09-23", LEASE_250K),
        ("2025-03-31", LEASE_250K),
        ("2025-04-01", LEASE_STANDARD),
    ],
)
def test_raw_2022_25_lease_rent_schedule(raw_residential_parameters, date, lease_cash):
    np.testing.assert_allclose(
        raw_residential_parameters(date).rent.calc(LEASE_RENTS),
        lease_cash,
        rtol=0,
        atol=1e-8,
    )


@pytest.mark.parametrize(
    "year,cash,lease_cash",
    [
        (2020, STANDARD_2020_21, LEASE_STANDARD),
        (2021, INITIAL_RELIEF, LEASE_500K),
        (2022, STANDARD_2020_21, LEASE_STANDARD),
        (2023, None, LEASE_250K),
        (2024, None, LEASE_250K),
        (2025, None, LEASE_STANDARD),
    ],
)
def test_annual_2020_25_schedules_sample_april_30(
    annual_system, year, cash, lease_cash
):
    residential = annual_system.parameters(year).gov.hmrc.stamp_duty.residential
    for buyer, expected in (cash or {}).items():
        np.testing.assert_allclose(
            _residential_purchase_tax(residential.purchase, HOLIDAY_PRICES, buyer),
            expected,
            rtol=0,
            atol=1e-8,
            err_msg=f"{buyer} in {year}",
        )
    np.testing.assert_allclose(
        residential.rent.calc(LEASE_RENTS), lease_cash, rtol=0, atol=1e-8
    )
