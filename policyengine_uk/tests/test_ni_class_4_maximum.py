import numpy as np
import pytest

from policyengine_uk import Simulation

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")


def test_class_4_annual_maximum_applies_case_3_steps():
    year = 2026
    monthly_primary_class_1 = {f"{year}-{month:02d}": 500 for month in range(1, 13)}
    sim = Simulation(
        situation={
            "people": {
                "person": {
                    "age": {year: 40},
                    "self_employment_income": {year: 100_000},
                    "ni_class_1_employee_primary": monthly_primary_class_1,
                }
            },
            "benunits": {"benunit": {"members": ["person"]}},
            "households": {"household": {"members": ["person"]}},
        }
    )

    assert sim.calculate("ni_class_4_maximum", year)[0] == pytest.approx(
        1_748.60,
        abs=0.01,
    )
    assert sim.calculate("ni_class_4", year)[0] == pytest.approx(1_748.60, abs=0.01)


def test_class_4_annual_maximum_does_not_bind_without_class_1():
    year = 2026
    sim = Simulation(
        situation={
            "people": {
                "person": {
                    "age": {year: 40},
                    "self_employment_income": {year: 60_000},
                }
            },
            "benunits": {"benunit": {"members": ["person"]}},
            "households": {"household": {"members": ["person"]}},
        }
    )

    assert sim.calculate("ni_class_4_maximum", year)[0] == pytest.approx(
        2_456.60,
        abs=0.01,
    )
    assert sim.calculate("ni_class_4", year)[0] == pytest.approx(2_456.60, abs=0.01)


CLASS_4 = "gov.hmrc.national_insurance.class_4"


def _sole_trader_simulation(year, profits, reform=None):
    return Simulation(
        situation={
            "people": {
                "person": {
                    "age": {year: 40},
                    "self_employment_income": {year: profits},
                }
            },
            "benunits": {"benunit": {"members": ["person"]}},
            "households": {"household": {"members": ["person"]}},
        },
        reform=reform,
    )


def _statutory_class_4(profits, lpl, upl, main_rate, additional_rate):
    return main_rate * min(max(profits - lpl, 0), upl - lpl) + additional_rate * max(
        profits - upl, 0
    )


@pytest.mark.parametrize(
    "year, lpl, upl, profits, expected",
    [
        # Thresholds as CPI-uprated by the model at the time of #1878. Before
        # the fix each of these lost the whole 2% band to float32 rounding.
        (2028, 13_077.795560896562, 52_300.77826939301, 65_432, 2_616.00),
        (2027, 12_821.380164235901, 51_275.32067272385, 100_000, 3_281.73),
        (2030, 13_606.113508494018, 54_413.62975910853, 300_000, 7_360.18),
        # The first profit level above the limit is affected too.
        (2028, 13_077.795560896562, 52_300.77826939301, 52_302, 2_353.40),
    ],
)
def test_class_4_keeps_additional_rate_band_with_non_round_thresholds(
    year, lpl, upl, profits, expected
):
    sim = _sole_trader_simulation(
        year,
        profits,
        reform={
            f"{CLASS_4}.thresholds.lower_profits_limit": lpl,
            f"{CLASS_4}.thresholds.upper_profits_limit": upl,
        },
    )

    assert _statutory_class_4(profits, lpl, upl, 0.06, 0.02) == pytest.approx(
        expected, abs=0.005
    )
    assert sim.calculate("ni_class_4", year)[0] == pytest.approx(expected, abs=0.01)
    assert sim.calculate("ni_class_4_maximum", year)[0] >= expected - 0.01


def test_class_4_at_default_2028_thresholds_matches_statute():
    year = 2028
    profits = 65_432
    sim = _sole_trader_simulation(year, profits)
    class_4 = sim.tax_benefit_system.parameters(
        f"{year}-01-01"
    ).gov.hmrc.national_insurance.class_4

    expected = _statutory_class_4(
        profits,
        class_4.thresholds.lower_profits_limit,
        class_4.thresholds.upper_profits_limit,
        class_4.rates.main,
        class_4.rates.additional,
    )

    assert sim.calculate("ni_class_4", year)[0] == pytest.approx(expected, abs=0.01)


def test_class_4_with_zero_main_rate_is_not_nan():
    year = 2028
    profits = 80_000
    sim = _sole_trader_simulation(year, profits, reform={f"{CLASS_4}.rates.main": 0.0})
    upl = sim.tax_benefit_system.parameters(
        f"{year}-01-01"
    ).gov.hmrc.national_insurance.class_4.thresholds.upper_profits_limit

    assert sim.calculate("ni_class_4", year)[0] == pytest.approx(
        0.02 * (profits - upl), abs=0.01
    )
    assert not np.isnan(sim.calculate("national_insurance", year)).any()


ALL_YEARS = "2000-01-01.2100-12-31"


@pytest.mark.parametrize("year, expected", [(2023, 20.0), (2024, 24.0), (2026, 24.0)])
def test_class_2_counts_towards_annual_maximum_only_before_april_2024(year, expected):
    # Profits £1,000 with LPL £0 and UPL £100: 6% x 100 + 2% x 900 = £24.
    # Class 2 of £182 and no Class 1. Before 6 April 2024 regulation 100
    # applies and Step Four is negative (Case 3), capping Class 4 at
    # 2% x 100 + 2% x 900 = £20. From then SI 2024/377 removes Class 2
    # from regulation 100, so without Class 1 the maximum does not apply.
    # Receipts of £3,000 put expenses above the £1,000 trading allowance,
    # so the whole £1,000 profit is chargeable.
    sim = Simulation(
        situation={
            "people": {
                "person": {
                    "age": {year: 40},
                    "self_employment_income": {year: 1_000},
                    "self_employment_gross_receipts": {year: 3_000},
                    "ni_class_2": {year: 182},
                }
            },
            "benunits": {"benunit": {"members": ["person"]}},
            "households": {"household": {"members": ["person"]}},
        },
        reform={
            f"{CLASS_4}.thresholds.lower_profits_limit": {ALL_YEARS: 0},
            f"{CLASS_4}.thresholds.upper_profits_limit": {ALL_YEARS: 100},
            f"{CLASS_4}.rates.main": {ALL_YEARS: 0.06},
            f"{CLASS_4}.rates.additional": {ALL_YEARS: 0.02},
            "gov.hmrc.national_insurance.class_2.flat_rate": {ALL_YEARS: 3.15},
        },
    )

    assert sim.calculate("ni_class_4", year)[0] == pytest.approx(expected, abs=0.01)


def test_annual_maximum_case_1_requires_step_four_to_exceed_the_aggregate():
    # All amounts are exact in binary. 53 x £0.50 Class 2 = £26.50 equals
    # 2 x £13.25 Class 1 exactly, with no unused main band, so Step Four
    # equals (does not exceed) the Case 1 aggregate: Case 2 applies and
    # the maximum does not bind. Case 1 would cap Class 4 at Step Four.
    year = 2023
    sim = Simulation(
        situation={
            "people": {
                "person": {
                    "age": {year: 40},
                    "self_employment_income": {year: 6_000},
                    "ni_class_1_employee_primary": {f"{year}-01": 13.25},
                }
            },
            "benunits": {"benunit": {"members": ["person"]}},
            "households": {"household": {"members": ["person"]}},
        },
        reform={
            f"{CLASS_4}.thresholds.lower_profits_limit": {ALL_YEARS: 0},
            f"{CLASS_4}.thresholds.upper_profits_limit": {ALL_YEARS: 1},
            f"{CLASS_4}.rates.main": {ALL_YEARS: 0.1},
            f"{CLASS_4}.rates.additional": {ALL_YEARS: 0.2},
            "gov.hmrc.national_insurance.class_2.flat_rate": {ALL_YEARS: 0.5},
        },
    )
    assert sim.calculate("ni_class_2", year)[0] == 0
    class_1 = sim.calculate("ni_class_1_employee", year)[0]
    assert class_1 == 13.25

    expected = _statutory_class_4(6_000, 0, 1, 0.1, 0.2)
    assert sim.calculate("ni_class_4", year)[0] == pytest.approx(expected, abs=0.01)
    step_4 = 0.1 * 1 + 53 * 0.5 - 13.25
    assert sim.calculate("ni_class_4", year)[0] > step_4 + 1_000


def test_class_4_does_not_deduct_class_1_from_profits():
    # Employment £30,000 and profits £20,000 in 2026-27: the annual maximum
    # does not bind, so Class 4 is 6% of the full profits above the LPL.
    year = 2026
    sim = Simulation(
        situation={
            "people": {
                "person": {
                    "age": {year: 40},
                    "employment_income": {year: 30_000},
                    "self_employment_income": {year: 20_000},
                }
            },
            "benunits": {"benunit": {"members": ["person"]}},
            "households": {"household": {"members": ["person"]}},
        }
    )

    assert sim.calculate("ni_class_1_employee", year)[0] > 0
    assert sim.calculate("ni_class_4_main", year)[0] == pytest.approx(
        (20_000 - 12_570) * 0.06, abs=0.01
    )
    assert sim.calculate("ni_class_4", year)[0] == pytest.approx(
        (20_000 - 12_570) * 0.06, abs=0.01
    )
