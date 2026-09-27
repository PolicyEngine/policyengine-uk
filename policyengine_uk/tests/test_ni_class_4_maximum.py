import numpy as np
import pytest

from policyengine_uk import Simulation


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
