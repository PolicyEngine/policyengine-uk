"""Class 2 National Insurance against s.11 SSCBA 1992, tax year by tax year.

STATUTE holds each tax year's figures as enacted, read from legislation.gov.uk
(the amending instrument's made text and the point-in-time text of s.11),
independently of the parameter files.

Invariants, for every model year and profits >= 0:

1. Differential: ni_class_2 is 52 weeks at the statutory weekly rate when
   s.11(2) makes the earner liable, and 0 otherwise. Before 2022-23 the
   earner is liable on profits of, or exceeding, the small profits threshold.
   In 2022-23 and 2023-24 only profits that exceed the lower profits
   threshold are liable; profits from the small profits threshold up to it
   are treated as paid (s.11(5A)-(5B)), which costs nothing. From 2024-25
   s.11(2) is omitted and no one is liable.
2. ni_class_2 is either 0 or 52 x the weekly rate.
3. ni_class_2 is non-decreasing in profits.

The model counts 52 weeks of self-employment in a year. Profits are stored
as float32, so the reference is evaluated on the float32 value.
"""

from fractions import Fraction

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.system import system

WEEKS = 52

# Tax year starting in April of the key: (weekly rate under s.11(2), small
# profits threshold, lower profits threshold or None where s.11(2) keys on the
# small profits threshold). A rate of 0 means s.11(2) is omitted.
STATUTE = {
    2015: ("2.80", 5_965, None),  # NICA 2015 Sch 1 para 3
    2016: ("2.80", 5_965, None),  # unchanged (s.11 as at 6 April 2016)
    2017: ("2.85", 6_025, None),  # SI 2017/415 reg 3
    2018: ("2.95", 6_205, None),  # SI 2018/337 reg 3
    2019: ("3.00", 6_365, None),  # SI 2019/262 reg 3
    2020: ("3.05", 6_475, None),  # SI 2020/299 reg 3
    2021: ("3.05", 6_515, None),  # SI 2021/157 reg 3; rate unchanged
    2022: ("3.15", 6_725, 11_908),  # SI 2022/232 reg 3; SI 2022/1329 reg 2
    2023: ("3.45", 6_725, 12_570),  # SI 2023/236 reg 3; SPT unchanged
    2024: ("0", 6_725, None),  # s.11(2) omitted: NICRRA 2023 (c. 57) s.3
    2025: ("0", 6_845, None),  # SI 2025/288 reg 3(a)
    2026: ("0", 7_105, None),  # SI 2026/231 reg 3(a)
}
MODEL_YEARS = list(range(2015, 2031))
PROPERTY_SETTINGS = settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)


def statute(year):
    # Class 2 stays abolished after the last tabulated year.
    return STATUTE[min(year, max(STATUTE))]


def statutory_class_2(year, profits):
    rate, small_profits_threshold, lower_profits_threshold = statute(year)
    profits = Fraction(float(np.float32(profits)))
    if lower_profits_threshold is None:
        liable = profits >= small_profits_threshold
    else:
        liable = profits > lower_profits_threshold
    return WEEKS * Fraction(rate) if liable else Fraction(0)


# Every threshold s.11 has used, with points either side of each.
THRESHOLD_PROFITS = sorted(
    {0.0}
    | {
        float(threshold) + offset
        for _, spt, lpt in STATUTE.values()
        for threshold in filter(None, (spt, lpt))
        for offset in (-1, -0.01, 0, 0.01, 1)
    }
)


def simulate(profits_list):
    # One person per profit level, with the same profits in every model year,
    # so a single simulation covers every year.
    people = {
        f"p{i}": {
            "age": {year: 40 for year in MODEL_YEARS},
            "self_employment_income": {year: profits for year in MODEL_YEARS},
        }
        for i, profits in enumerate(profits_list)
    }
    return Simulation(
        situation={
            "people": people,
            "benunits": {f"b{i}": {"members": [f"p{i}"]} for i in range(len(people))},
            "households": {f"h{i}": {"members": [f"p{i}"]} for i in range(len(people))},
        }
    )


def assert_invariants(profits_list):
    sim = simulate(profits_list)
    order = np.argsort(np.asarray(profits_list, dtype=np.float32), kind="stable")
    for year in MODEL_YEARS:
        class_2 = sim.calculate("ni_class_2", year)
        full_year = WEEKS * float(statute(year)[0])
        for i, profits in enumerate(profits_list):
            expected = float(statutory_class_2(year, profits))
            assert class_2[i] == pytest.approx(expected, abs=0.01), (year, profits)
            assert class_2[i] == 0 or class_2[i] == pytest.approx(full_year, abs=0.01)
        assert np.all(np.diff(class_2[order]) >= 0), (year, profits_list, class_2)


@pytest.mark.parametrize("year", sorted(STATUTE))
def test_class_2_parameters_match_statute(year):
    class_2 = system.parameters(f"{year}-01-01").gov.hmrc.national_insurance.class_2
    rate, small_profits_threshold, lower_profits_threshold = STATUTE[year]

    assert class_2.flat_rate == pytest.approx(float(rate))
    assert class_2.small_profits_threshold == small_profits_threshold
    if Fraction(rate) > 0:
        assert class_2.lower_profits_threshold_applies == (
            lower_profits_threshold is not None
        )
    if lower_profits_threshold is not None:
        assert class_2.lower_profits_threshold == lower_profits_threshold


def test_ni_class_2_matches_statute_at_every_threshold():
    rng = np.random.default_rng(1_992)
    spread = list(rng.uniform(0, 200_000, 200).round(2))
    assert_invariants(THRESHOLD_PROFITS + spread + [60_000.0, 1_000_000.0])


@PROPERTY_SETTINGS
@given(
    st.lists(
        st.one_of(
            st.floats(0, 200_000, allow_nan=False, allow_infinity=False),
            st.integers(0, 200_000).map(float),
            st.sampled_from(THRESHOLD_PROFITS),
        ),
        min_size=1,
        max_size=24,
    )
)
def test_ni_class_2_properties(profits_list):
    assert_invariants(profits_list)


def test_2023_annual_maximum_uses_the_2023_24_class_2_rate():
    # Regulation 100 of SI 2001/1004 for 2023-24, with Class 2 at the
    # default £3.45 a week. The Class 4 limits and rates are pinned to their
    # 2023-24 statutory values (s.15(3) and (3ZA) SSCBA 1992) so the test
    # exercises Class 2 alone. Profits £60,000; primary Class 1 £3,000.
    #   Step 3: 9% x (50,270 - 12,570) + 53 x 3.45 = 3,393 + 182.85
    #   Step 4: 3,575.85 - 179.40 (Class 2) - 3,000 (Class 1) = 396.45
    #   Case 2: 396.45 + 2% x (37,700 - 396.45 / 9%) + 2% x 9,730
    year = 2023
    all_years = "2000-01-01.2100-12-31"
    class_4 = "gov.hmrc.national_insurance.class_4"
    sim = Simulation(
        situation={
            "people": {
                "person": {
                    "age": {year: 40},
                    "self_employment_income": {year: 60_000},
                    "ni_class_1_employee_primary": {
                        f"{year}-{month:02d}": 250 for month in range(1, 13)
                    },
                }
            },
            "benunits": {"benunit": {"members": ["person"]}},
            "households": {"household": {"members": ["person"]}},
        },
        reform={
            f"{class_4}.thresholds.lower_profits_limit": {all_years: 12_570},
            f"{class_4}.thresholds.upper_profits_limit": {all_years: 50_270},
            f"{class_4}.rates.main": {all_years: 0.09},
            f"{class_4}.rates.additional": {all_years: 0.02},
        },
    )

    step_4 = Fraction("0.09") * 37_700 + 53 * Fraction("3.45") - Fraction("179.40")
    step_4 -= 3_000
    step_5 = step_4 / Fraction("0.09")
    maximum = step_4 + Fraction("0.02") * (37_700 - step_5) + Fraction("0.02") * 9_730

    assert sim.calculate("ni_class_2", year)[0] == pytest.approx(179.40, abs=0.01)
    assert float(maximum) == pytest.approx(1_256.95, abs=0.005)
    assert sim.calculate("ni_class_4_maximum", year)[0] == pytest.approx(
        float(maximum), abs=0.01
    )
    assert sim.calculate("ni_class_4", year)[0] == pytest.approx(
        float(maximum), abs=0.01
    )
