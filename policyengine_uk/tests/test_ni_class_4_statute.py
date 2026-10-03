"""Class 4 National Insurance against s.15 SSCBA 1992 and regulation 100 of
SI 2001/1004, tax year by tax year.

CLASS_4 and CLASS_2 hold each tax year's figures as enacted, read from
legislation.gov.uk (the amending instrument's made or enacted text and the
point-in-time text of s.11 and s.15), independently of the parameter files.

Invariants, for every tax year from 2015-16 to 2026-27, profits >= 0 and
primary Class 1 contributions >= 0:

1. Parameters: the model's Class 4 limits and rates are the statutory ones.
2. Differential: ni_class_4 equals an exact-rational reference. That is the
   s.15(3) amount on the full profits, capped by the regulation 100 maximum
   where primary Class 1 or, before 2024-25, Class 2 contributions are
   payable. Regulation 100's percentages are the year's Class 4 rates: 9% and
   2%, but 9.73% and 2.73% in 2022-23 (Health and Social Care Levy (Repeal)
   Act 2022 Sch para 6(2)); from 2024-25, 6% and 100/6 in Steps Two and Five
   (National Insurance Contributions (Reduction in Rates) Act 2024 s 2(3))
   with Steps Eight and Nine still at 2%. Before 2024-25 Step Three adds 53
   weekly Class 2 contributions and Step Four subtracts the Class 2 paid.
3. Bounds: 0 <= ni_class_4 <= the s.15(3) amount.
4. ni_class_4_main is the main-rate band of s.15(3)(a) alone.

The model stores amounts as float32, so the reference reads profits and
Class 1 back from the simulation and comparisons allow a few float32 ulps.
"""

from fractions import Fraction

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.system import system

# Tax year starting in April of the key: (lower profits limit, upper profits
# limit, main Class 4 percentage, additional Class 4 percentage).
CLASS_4 = {
    2015: (8_060, 42_385, "0.09", "0.02"),  # SI 2015/588 art 3; NICA 2011 s.2
    2016: (8_060, 43_000, "0.09", "0.02"),  # SI 2016/343 reg 2
    2017: (8_164, 45_000, "0.09", "0.02"),  # SI 2017/415 reg 5
    2018: (8_424, 46_350, "0.09", "0.02"),  # SI 2018/337 reg 5
    2019: (8_632, 50_000, "0.09", "0.02"),  # SI 2019/262 reg 5
    2020: (9_500, 50_000, "0.09", "0.02"),  # SI 2020/299 reg 5
    2021: (9_568, 50_270, "0.09", "0.02"),  # SI 2021/157 reg 5
    # NICs (Increase of Thresholds) Act 2022 s.2(1)-(2); Health and Social
    # Care Levy (Repeal) Act 2022 s.2(2).
    2022: (11_908, 50_270, "0.0973", "0.0273"),
    2023: (
        12_570,
        50_270,
        "0.09",
        "0.02",
    ),  # NICs (Increase of Thresholds) Act 2022 s.2(3)
    2024: (12_570, 50_270, "0.06", "0.02"),  # NICs (Reduction in Rates) Act 2024 s.1(3)
    2025: (12_570, 50_270, "0.06", "0.02"),
    2026: (12_570, 50_270, "0.06", "0.02"),
}
# Class 2 under s.11(2), which regulation 100 counts before 2024-25:
# (weekly rate, threshold, True where liability needs profits that exceed the
# lower profits threshold rather than profits of, or exceeding, the small
# profits threshold). From 2024-25 s.11(2) is omitted (NICs (Reduction in
# Rates) Act 2023 s.3) and Class 2 leaves regulation 100 (SI 2024/377 reg 6(5)).
CLASS_2 = {
    2015: ("2.80", 5_965, False),  # NICA 2015 Sch 1 para 3
    2016: ("2.80", 5_965, False),
    2017: ("2.85", 6_025, False),  # SI 2017/415 reg 3
    2018: ("2.95", 6_205, False),  # SI 2018/337 reg 3
    2019: ("3.00", 6_365, False),  # SI 2019/262 reg 3
    2020: ("3.05", 6_475, False),  # SI 2020/299 reg 3
    2021: ("3.05", 6_515, False),  # SI 2021/157 reg 3
    2022: ("3.15", 11_908, True),  # SI 2022/232 reg 3; SI 2022/1329 reg 2
    2023: ("3.45", 12_570, True),  # SI 2023/236 reg 3
}
YEARS = sorted(CLASS_4)
WEEKS = 52
PROPERTY_SETTINGS = settings(
    max_examples=6,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)


def exact(x):
    return Fraction(float(x))


def statutory_class_2(year, profits):
    if year not in CLASS_2:
        return Fraction(0)
    rate, threshold, exceed = CLASS_2[year]
    liable = profits > threshold if exceed else profits >= threshold
    return WEEKS * Fraction(rate) if liable else Fraction(0)


def statutory_class_4(year, profits, class_1):
    """Class 4 for `year` on `profits` with `class_1` primary Class 1.

    Returns every amount regulation 100 allows: two where Step Four equals
    the Case 1 aggregate to within float32 noise, one otherwise.
    """
    lpl, upl, main, additional = CLASS_4[year]
    main, additional = Fraction(main), Fraction(additional)
    main_band = main * min(max(profits - lpl, 0), upl - lpl)
    s15_amount = main_band + additional * max(profits - upl, 0)
    class_2 = statutory_class_2(year, profits)
    if not (class_1 > 0 or class_2 > 0):
        return s15_amount, {s15_amount}

    step_3 = (upl - lpl) * main
    if year in CLASS_2:
        step_3 += 53 * Fraction(CLASS_2[year][0])
    step_4 = step_3 - class_2 - class_1
    aggregate = class_1 + class_2 + main_band

    def case_2_or_3():
        floored = max(step_4, 0)
        step_7 = max(min(upl, profits) - lpl - floored / main, 0)
        return floored + step_7 * additional + max(profits - upl, 0) * additional

    maxima = set()
    if step_4 > 0 and step_4 >= aggregate - Fraction(1, 10**6):
        maxima.add(step_4)  # Case 1
    if not (step_4 > 0 and step_4 > aggregate + Fraction(1, 10**6)):
        maxima.add(case_2_or_3())
    return s15_amount, {min(s15_amount, maximum) for maximum in maxima}


def tolerance(*amounts):
    return 0.01 + 4e-7 * max(abs(float(a)) for a in amounts)


def simulate(people, years=YEARS):
    """One person per (profits, annual primary Class 1) pair, the same in
    every year, so one simulation covers every tax year. Class 1 is entered
    in January so the annual sum is exact."""
    return Simulation(
        situation={
            "people": {
                f"p{i}": {
                    "age": {year: 40 for year in years},
                    "self_employment_income": {year: profits for year in years},
                    "ni_class_1_employee_primary": {
                        f"{year}-01": class_1 for year in years
                    },
                }
                for i, (profits, class_1) in enumerate(people)
            },
            "benunits": {f"b{i}": {"members": [f"p{i}"]} for i in range(len(people))},
            "households": {f"h{i}": {"members": [f"p{i}"]} for i in range(len(people))},
        }
    )


@pytest.mark.parametrize("year", YEARS)
def test_class_4_parameters_match_statute(year):
    class_4 = system.parameters(f"{year}-01-01").gov.hmrc.national_insurance.class_4
    lpl, upl, main, additional = CLASS_4[year]

    assert class_4.thresholds.lower_profits_limit == lpl
    assert class_4.thresholds.upper_profits_limit == upl
    assert class_4.rates.main == pytest.approx(float(main), abs=1e-12)
    assert class_4.rates.additional == pytest.approx(float(additional), abs=1e-12)
    assert class_4.annual_maximum.includes_class_2 == (year in CLASS_2)


# Hand-derived liabilities, with regulation 100 Cases 1, 2 and 3 in each
# regime (to 2021-22, 2022-23, 2023-24 and from 2024-25). Class 1 is the
# year's primary Class 1 at the main percentage. Amounts in pounds;
# regulation 100 steps are numbered as in reg 100(3) and "max" is the reg 100
# maximum.
HAND_DERIVED = [
    # 2015-16. s.15(3): 9% x (42,385 - 8,060) + 2% x (50,000 - 42,385)
    # = 3,089.25 + 152.30 = 3,241.55. Class 2 52 x 2.80 = 145.60.
    # Step 4 = 3,089.25 + 53 x 2.80 - 145.60 = 3,092.05 < 145.60 + 3,089.25
    # (Case 2); Step 5 = 34,356.11 > Step 6 = 34,325, so max = 3,092.05
    # + 2% x 7,615 = 3,244.35. Not binding.
    (2015, 50_000, 0, 145.60, 3_241.55),
    # 2016-17. 9% x (43,000 - 8,060) + 2% x 7,000 = 3,144.60 + 140
    # = 3,284.60. Max = 3,147.40 + 140 = 3,287.40.
    (2016, 50_000, 0, 145.60, 3_284.60),
    # 2017-18. 9% x (30,000 - 8,164) = 1,965.24. Class 2 52 x 2.85
    # = 148.20. Step 4 = 9% x 36,836 + 53 x 2.85 - 148.20 = 3,318.09
    # exceeds 148.20 + 1,965.24 (Case 1). Not binding.
    (2017, 30_000, 0, 148.20, 1_965.24),
    # 2018-19. 9% x (46,350 - 8,424) + 2% x (60,000 - 46,350) = 3,413.34
    # + 273 = 3,686.34. Class 2 52 x 2.95 = 153.40. Step 4 = 3,413.34
    # + 156.35 - 153.40 = 3,416.29 (Case 2); Step 5 = 37,958.78 > 37,926;
    # max = 3,416.29 + 273 = 3,689.29. Not binding.
    (2018, 60_000, 0, 153.40, 3_686.34),
    # 2019-20 with £2,000 of Class 1. s.15(3): 9% x (50,000 - 8,632)
    # = 3,723.12. Class 2 52 x 3 = 156. Step 4 = 3,723.12 + 159 - 156
    # - 2,000 = 1,726.12 (Case 2). Step 5 = 1,726.12 / 9% = 19,179.11;
    # Step 7 = 41,368 - 19,179.11 = 22,188.89; Step 8 = 443.78.
    # Max = 1,726.12 + 443.78 = 2,169.90. Binding.
    (2019, 50_000, 2_000, 156.00, 2_169.90),
    # 2019-20 with £6,000 of Class 1. Step 4 = 3,723.12 + 159 - 156 - 6,000
    # < 0 (Case 3, nil). Step 7 = Step 6 = 50,000 - 8,632 = 41,368;
    # Step 8 = 2% x 41,368 = 827.36; Step 9 = 0. Max = 827.36. Binding.
    (2019, 50_000, 6_000, 156.00, 827.36),
    # 2020-21. 9% x (20,000 - 9,500) = 945. Class 2 52 x 3.05 = 158.60.
    (2020, 20_000, 0, 158.60, 945.00),
    # 2021-22 at the lower profits limit: Class 2 (profits of, or exceeding,
    # £6,515) but no Class 4.
    (2021, 9_568, 0, 158.60, 0),
    # 2022-23 at £11,908: Class 2 needs profits that exceed the lower
    # profits threshold, and Class 4 profits above the limit.
    (2022, 11_908, 0, 0, 0),
    # 2022-23. 9.73% x (30,000 - 11,908) = 1,760.35. Class 2 52 x 3.15
    # = 163.80. Step 4 = 9.73% x 38,362 + 53 x 3.15 - 163.80 = 3,735.77
    # (Case 1). Not binding.
    (2022, 30_000, 0, 163.80, 1_760.35),
    # 2022-23. 9.73% x 38,362 + 2.73% x 9,730 = 3,732.62 + 265.63
    # = 3,998.25. Step 4 = 3,735.77 does not exceed 163.80 + 3,732.62
    # (Case 2). Step 5 = 3,735.77 / 9.73% = 38,394.37 exceeds Step 6
    # (38,362), so Step 8 is 0; Step 9 = 265.63. Max = 4,001.40.
    (2022, 60_000, 0, 163.80, 3_998.25),
    # 2022-23 with £6,000 of Class 1. Step 4 = 3,899.57 - 163.80 - 6,000 < 0
    # (Case 3). Max = 2.73% x 38,362 + 2.73% x 49,730 = 1,047.28
    # + 1,357.63 = 2,404.91.
    (2022, 100_000, 6_000, 163.80, 2_404.91),
    # 2023-24. 9% x (30,000 - 12,570) = 1,568.70. Class 2 52 x 3.45
    # = 179.40. Case 1, not binding.
    (2023, 30_000, 0, 179.40, 1_568.70),
    # 2023-24 at £12,570: no Class 2 (not exceeding) and no Class 4.
    (2023, 12_570, 0, 0, 0),
    # 2023-24 with £3,000 of Class 1. Step 4 = 3,393 + 182.85 - 179.40
    # - 3,000 = 396.45 (Case 2). Step 5 = 4,405; Step 7 = 37,700 - 4,405
    # = 33,295; Step 8 = 665.90; Step 9 = 2% x 9,730 = 194.60.
    # Max = 396.45 + 665.90 + 194.60 = 1,256.95. Binding.
    (2023, 60_000, 3_000, 179.40, 1_256.95),
    # 2023-24 with £6,000 of Class 1. Step 4 = 3,575.85 - 179.40 - 6,000
    # < 0 (Case 3, nil). Max = 2% x 37,700 + 2% x 49,730 = 754 + 994.60
    # = 1,748.60. Binding (s.15(3): 3,393 + 994.60 = 4,387.60).
    (2023, 100_000, 6_000, 179.40, 1_748.60),
    # 2024-25 with £1,000 of Class 1. s.15(3): 6% x 37,700 + 2% x 9,730
    # = 2,262 + 194.60 = 2,456.60. No Class 2 and no Step Three.
    # Step 4 = 2,262 - 1,000 = 1,262 (Case 2). Step 5 = 21,033.33;
    # Step 7 = 16,666.67; Step 8 = 333.33. Max = 1,262 + 333.33 + 194.60
    # = 1,789.93. Binding.
    (2024, 60_000, 1_000, 0, 1_789.93),
    # 2024-25 with £200 of Class 1. 6% x 7,430 = 445.80. Step 4 = 2,062
    # exceeds 200 + 445.80 (Case 1). Not binding.
    (2024, 20_000, 200, 0, 445.80),
    # 2025-26, no Class 1: regulation 100 does not apply.
    # 6% x (30,000 - 12,570) = 1,045.80.
    (2025, 30_000, 0, 0, 1_045.80),
    # 2026-27 with £6,000 of Class 1. Step 4 = 2,262 - 6,000 < 0 (Case 3).
    # Max = 2% x 37,700 + 2% x 49,730 = 754 + 994.60 = 1,748.60.
    (2026, 100_000, 6_000, 0, 1_748.60),
]


@pytest.fixture(scope="module")
def hand_derived_simulation():
    # One person per row, with the row's inputs in every year; each case
    # reads its own person in its own year.
    return simulate([(profits, class_1) for _, profits, class_1, _, _ in HAND_DERIVED])


@pytest.mark.parametrize(
    "row",
    range(len(HAND_DERIVED)),
    ids=[
        f"{year}-{profits}-{class_1}" for year, profits, class_1, _, _ in HAND_DERIVED
    ],
)
def test_class_2_and_class_4_hand_derived(hand_derived_simulation, row):
    year, profits, class_1, class_2, class_4 = HAND_DERIVED[row]
    sim = hand_derived_simulation
    assert sim.calculate("ni_class_1_employee_primary", year)[row] == class_1
    assert sim.calculate("ni_class_2", year)[row] == pytest.approx(class_2, abs=0.01)
    assert sim.calculate("ni_class_4", year)[row] == pytest.approx(class_4, abs=0.01)
    # The table is independent arithmetic; the reference must agree with it.
    _, allowed = statutory_class_4(year, Fraction(profits), Fraction(class_1))
    assert any(abs(float(a) - class_4) < 0.005 for a in allowed), allowed


def assert_matches_statute(people):
    sim = simulate(people)
    for year in YEARS:
        lpl, upl, main, _ = CLASS_4[year]
        profits = sim.calculate("self_employment_income", year)
        class_1 = sim.calculate("ni_class_1_employee_primary", year)
        class_2 = sim.calculate("ni_class_2", year)
        class_4 = sim.calculate("ni_class_4", year)
        class_4_main = sim.calculate("ni_class_4_main", year)
        for i in range(len(people)):
            p, c1 = exact(profits[i]), exact(class_1[i])
            s15_amount, allowed = statutory_class_4(year, p, c1)
            tol = tolerance(p, upl, s15_amount)
            assert float(class_2[i]) == pytest.approx(
                float(statutory_class_2(year, p)), abs=0.01
            ), (year, people[i])
            assert any(abs(float(class_4[i]) - float(a)) <= tol for a in allowed), (
                year,
                people[i],
                float(class_4[i]),
                [float(a) for a in allowed],
            )
            assert -tol <= float(class_4[i]) <= float(s15_amount) + tol
            main_band = Fraction(main) * min(max(p - lpl, 0), upl - lpl)
            assert abs(float(class_4_main[i]) - float(main_band)) <= tol


# Every limit and threshold used from 2015-16 to 2026-27, with points either
# side, each with no Class 1 and with Class 1 that reaches each case.
THRESHOLD_PROFITS = sorted(
    {0.0, 100_000.0}
    | {
        float(limit) + offset
        for lpl, upl, _, _ in CLASS_4.values()
        for limit in (lpl, upl)
        for offset in (-1, -0.01, 0, 0.01, 1)
    }
    | {
        float(threshold) + offset
        for _, threshold, _ in CLASS_2.values()
        for offset in (-0.01, 0, 0.01)
    }
)


def test_class_4_matches_statute_at_every_limit():
    assert_matches_statute(
        [
            (profits, class_1)
            for profits in THRESHOLD_PROFITS
            for class_1 in (0, 250, 1_500, 6_000)
        ]
    )


@PROPERTY_SETTINGS
@given(
    st.lists(
        st.tuples(
            st.one_of(
                st.floats(0, 300_000, allow_nan=False, allow_infinity=False),
                st.integers(0, 300_000).map(float),
                st.sampled_from(THRESHOLD_PROFITS),
            ),
            st.one_of(
                st.just(0.0),
                st.integers(0, 800_000).map(lambda pence: pence / 100),
            ),
        ),
        min_size=1,
        max_size=16,
    )
)
def test_class_4_matches_statute_property(people):
    assert_matches_statute(people)
