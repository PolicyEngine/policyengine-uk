"""Class 2 National Insurance against s.11 SSCBA 1992, tax year by tax year.

STATUTE holds each tax year's figures as enacted, read from legislation.gov.uk
(the amending instrument's made text and the point-in-time text of s.11),
independently of the parameter files. CONTRIBUTION_WEEKS holds each year's
contribution weeks, counted from the calendar: a contribution week starts at
midnight between Saturday and Sunday (SI 2001/1004 reg. 1(2)) and the year's
first week on the first Sunday after 5 April (HMRC NIM70200).

The thresholds apply to relevant profits: the profits on which Class 4 is
payable under s.15, computed under Schedule 2 (s.11(3)). Here the inputs are
profit, whole-pound capital allowances (CAA 2001 s.247) and a whole-pound
trading loss made in the same year (Sch 2 para 3), with no gross receipts, so
relevant profits are profit less both. A profit of £1,000 or less is treated
as covered by the trading allowance from 2017-18, when the allowance starts,
and then gives nil relevant profits; that never changes liability, because
every threshold is far above £1,000. The trading allowance with gross
receipts, and losses brought forward, are covered by the YAML cases.

Invariants, for every model year 2015-2030, profits >= 0, capital allowances
>= 0 and in-year trading losses >= 0, all whole pounds apart from profits:

1. Differential: ni_class_2 is the statutory weekly rate for each contribution
   week in the year when s.11(2) makes the earner liable, and 0 otherwise.
   Before 2022-23 the earner is liable on relevant profits of, or exceeding,
   the small profits threshold. In 2022-23 and 2023-24 only relevant profits
   that exceed the lower profits threshold are liable; relevant profits from
   the small profits threshold up to it are treated as paid (s.11(5A)-(5B)),
   which costs nothing. From 2024-25 s.11(2) is omitted and no one is liable.
2. ni_class_2 is either 0 or a full year at the weekly rate.
3. ni_class_2 is non-decreasing in relevant profits, so non-decreasing in
   profit and non-increasing in capital allowances and losses.
4. Shared base: ni_class_2 is the s.11(2) rule applied to the model's own
   ni_class_4_profits, the base Class 4 is charged on.

Profits are stored as float32, so the reference is evaluated on the float32
value. Allowances and losses are whole pounds, so subtracting them from a
float32 profit is exact in float32.
"""

from fractions import Fraction

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.system import system
from policyengine_uk.utils.class_2 import class_2_contribution_weeks

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
# Contribution weeks: one per Sunday from 6 April to the next 5 April. A year
# has 53 when 6 April is a Sunday, or when 6 April is a Saturday and the year
# has 366 days. 2019-20 runs from Sunday 7 April 2019 to Sunday 5 April 2020
# (29 February 2020 included); 2025-26 from Sunday 6 April 2025 to Sunday 5
# April 2026. Every other year from 2015-16 to 2030-31 has 52; 2024-25, for
# one, runs from Sunday 7 April 2024 to Sunday 30 March 2025.
CONTRIBUTION_WEEKS = {2019: 53, 2025: 53}
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


def weeks(year):
    return CONTRIBUTION_WEEKS.get(year, 52)


def relevant_profits(profits, capital_allowances=0, trading_loss=0):
    # s.11(3): the Class 4 profits, here profit less capital allowances and
    # the year's trading loss.
    exact = Fraction(float(np.float32(profits))) - capital_allowances - trading_loss
    return max(exact, Fraction(0))


def statutory_class_2(year, profits, capital_allowances=0, trading_loss=0):
    rate, small_profits_threshold, lower_profits_threshold = statute(year)
    profits = relevant_profits(profits, capital_allowances, trading_loss)
    if lower_profits_threshold is None:
        liable = profits >= small_profits_threshold
    else:
        liable = profits > lower_profits_threshold
    return weeks(year) * Fraction(rate) if liable else Fraction(0)


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


# Whole-pound capital allowances and trading losses that move profits across
# each threshold.
CAPITAL_ALLOWANCES = [0, 500, 1_000, 2_500]
TRADING_LOSSES = [0, 750]


def simulate(cases):
    # One person per (profits, capital allowances, trading loss) case, with
    # the same values in every model year, so a single simulation covers every
    # year. Each year's loss is no more than its profits after allowances, so
    # none is carried forward, except where a profit of £1,000 or less is
    # relieved by the trading allowance from 2017-18: that loss carries
    # forward, but those cases stay below every threshold.
    people = {
        f"p{i}": {
            "age": {year: 40 for year in MODEL_YEARS},
            "self_employment_income": {year: profits for year in MODEL_YEARS},
            "capital_allowances": {year: allowances for year in MODEL_YEARS},
            "trading_loss": {year: loss for year in MODEL_YEARS},
        }
        for i, (profits, allowances, loss) in enumerate(cases)
    }
    return Simulation(
        situation={
            "people": people,
            "benunits": {f"b{i}": {"members": [f"p{i}"]} for i in range(len(people))},
            "households": {f"h{i}": {"members": [f"p{i}"]} for i in range(len(people))},
        }
    )


def gross(relevant, allowances=0, loss=0):
    # The profit whose relevant profits are `relevant`.
    return (float(relevant) + allowances + loss, allowances, loss)


def assert_invariants(cases):
    cases = [
        tuple(case) + (0,) * (3 - len(case))
        if isinstance(case, tuple)
        else (case, 0, 0)
        for case in cases
    ]
    sim = simulate(cases)
    relevant = [relevant_profits(*case) for case in cases]
    order = sorted(range(len(cases)), key=lambda i: relevant[i])
    for year in MODEL_YEARS:
        class_2 = sim.calculate("ni_class_2", year)
        class_4_profits = sim.calculate("ni_class_4_profits", year)
        full_year = weeks(year) * float(statute(year)[0])
        for i, case in enumerate(cases):
            expected = float(statutory_class_2(year, *case))
            assert class_2[i] == pytest.approx(expected, abs=0.01), (year, case)
            assert class_2[i] == 0 or class_2[i] == pytest.approx(full_year, abs=0.01)
            shared_base = float(statutory_class_2(year, class_4_profits[i]))
            assert class_2[i] == pytest.approx(shared_base, abs=0.01), (year, case)
        assert np.all(np.diff(class_2[order]) >= 0), (year, cases, class_2)


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


@pytest.mark.parametrize("year", MODEL_YEARS)
def test_contribution_weeks_follow_the_calendar(year):
    assert class_2_contribution_weeks(year) == weeks(year)


def test_contribution_weeks_match_hmrc_example():
    # NIM70200: "The first contribution week of the 2021 to 2022 tax year
    # starts on Sunday, 11 April 2021 and the last contribution week of that
    # year ends on Saturday, 9 April 2022": 364 days, 52 weeks.
    assert class_2_contribution_weeks(2021) == 52


def test_ni_class_2_matches_statute_at_every_threshold():
    rng = np.random.default_rng(1_992)
    spread = list(rng.uniform(0, 200_000, 200).round(2))
    assert_invariants(THRESHOLD_PROFITS + spread + [60_000.0, 1_000_000.0])


def test_ni_class_2_tests_thresholds_on_profits_after_deductions():
    # Profits set so that profit less capital allowances and the year's loss
    # lands on, and either side of, every threshold s.11 has used.
    assert_invariants(
        [
            gross(relevant, allowances, loss)
            for relevant in THRESHOLD_PROFITS
            for allowances in CAPITAL_ALLOWANCES
            for loss in TRADING_LOSSES
            if allowances or loss
        ]
    )


@PROPERTY_SETTINGS
@given(
    st.lists(
        st.builds(
            gross,
            st.one_of(
                st.sampled_from(THRESHOLD_PROFITS),
                st.floats(0, 200_000, allow_nan=False, allow_infinity=False),
                st.integers(0, 200_000).map(float),
            ),
            st.one_of(st.sampled_from(CAPITAL_ALLOWANCES), st.integers(0, 20_000)),
            st.one_of(st.sampled_from(TRADING_LOSSES), st.integers(0, 20_000)),
        ),
        min_size=1,
        max_size=24,
    )
)
def test_ni_class_2_properties(cases):
    # Relevant profits are drawn first, so threshold points stay on their
    # thresholds whatever allowances and losses are drawn with them.
    assert_invariants(cases)


def test_2023_annual_maximum_uses_the_2023_24_class_2_rate():
    # Regulation 100 of SI 2001/1004 for 2023-24, at default parameters:
    # Class 2 at £3.45 a week and the 2023-24 Class 4 limits and rates
    # (s.15(3) and (3ZA) SSCBA 1992). Profits £60,000; primary Class 1 £3,000.
    #   Step 3: 9% x (50,270 - 12,570) + 53 x 3.45 = 3,393 + 182.85
    #   Step 4: 3,575.85 - 179.40 (Class 2) - 3,000 (Class 1) = 396.45
    #   Case 2: 396.45 + 2% x (37,700 - 396.45 / 9%) + 2% x 9,730
    year = 2023
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
