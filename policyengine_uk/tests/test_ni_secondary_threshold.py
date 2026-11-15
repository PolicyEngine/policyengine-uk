"""The annual Class 1 secondary threshold is the statutory figure (#1967, #2178).

SSCBA 1992 s.9(1) charges secondary Class 1 contributions at the secondary
percentage on earnings above "the current secondary threshold (or the
prescribed equivalent)". The model works on annual earnings and annualises
the weekly secondary threshold (ST) parameter as 52 weeks. For an earnings
period of a year, the prescribed equivalent is the figure in SI 2001/1004 reg
11(3A)(b). So the model's annual ST, 52 x the stored weekly value, should be
that figure.

Model year Y is the tax year starting 6 April Y. STATUTORY holds, for each
tax year from 2015-16 to 2030-31, the reg 10(d) weekly ST, the reg 11(3A)(b)
annual ST and the s.9(2) secondary percentage. The figures come from the
legislation.gov.uk point-in-time text of regs 10 and 11 and of s.9 at 6 April
of each year, not from the parameter files. 2027-28 to 2030-31 are announced
policy (Autumn Budget 2024 and Budget 2025), as in test_ni_threshold_freeze.py.

Invariants:

1. Annual ST: in every year, 52 x the stored weekly ST equals the reg
   11(3A)(b) figure to the penny.
2. Weekly ST: before 2025-26, the reg 11(3A)(b) figure is exactly 52 x the
   reg 10(d) figure, and the stored value is the reg 10(d) figure itself.
   From 2025-26 the stored value is the annual figure / 52 (5,000 / 52), the
   convention reg 11(3A)(c) uses for multiples of a week. The rounded reg
   10(d) £96 would give £4,992 (#1967).
3. Differential: in every year, for any Class 1 earnings e >= 0 of an
   earner aged 21 or over who is not an apprentice, ni_class_1_employer
   equals rate x max(e - annual ST, 0), computed in exact arithmetic from
   STATUTORY. For 2022-23 the s.9(2) percentage at 6 April is 15.05% (Health
   and Social Care Levy Act 2021 s.5(2)(b)). It applied to earnings paid
   before 6 November 2022 (Repeal Act 2022 s.2(1)), and the model reads the
   tax year at 30 April, as for the employee main rate (#1807).
4. Threshold edge: employer NI is zero just below the annual ST, less than
   half a penny at it, and positive a penny above it. At the ST itself the
   stored 5,000 / 52 (96.153846) annualises to £4,999.999992, so exact
   arithmetic gives about £0.000001 from 2025-26; float32 rounds it to zero.

Comparisons allow float32 rounding: the model stores values as float32.
"""

from fractions import Fraction

import numpy as np
import pytest
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from policyengine_uk import CountryTaxBenefitSystem, Simulation

# Tax year: (reg 10(d) weekly ST, reg 11(3A)(b) annual ST, s.9(2) rate).
# The weekly figure from 2027-28 is the announced £96; the annual £5,000 is
# what the model must reproduce.
STATUTORY = {
    2015: (Fraction(156), Fraction(8_112), Fraction(138, 1_000)),
    2016: (Fraction(156), Fraction(8_112), Fraction(138, 1_000)),
    2017: (Fraction(157), Fraction(8_164), Fraction(138, 1_000)),
    2018: (Fraction(162), Fraction(8_424), Fraction(138, 1_000)),
    2019: (Fraction(166), Fraction(8_632), Fraction(138, 1_000)),
    2020: (Fraction(169), Fraction(8_788), Fraction(138, 1_000)),
    2021: (Fraction(170), Fraction(8_840), Fraction(138, 1_000)),
    # 15.05% for earnings paid from 6 April to 5 November 2022, then 13.8%.
    2022: (Fraction(175), Fraction(9_100), Fraction(1_505, 10_000)),
    2023: (Fraction(175), Fraction(9_100), Fraction(138, 1_000)),
    2024: (Fraction(175), Fraction(9_100), Fraction(138, 1_000)),
    2025: (Fraction(96), Fraction(5_000), Fraction(15, 100)),
    2026: (Fraction(96), Fraction(5_000), Fraction(15, 100)),
    2027: (Fraction(96), Fraction(5_000), Fraction(15, 100)),
    2028: (Fraction(96), Fraction(5_000), Fraction(15, 100)),
    2029: (Fraction(96), Fraction(5_000), Fraction(15, 100)),
    2030: (Fraction(96), Fraction(5_000), Fraction(15, 100)),
}
YEARS = list(STATUTORY)
RATED_YEARS = [year for year, (_, _, rate) in STATUTORY.items() if rate]
# The first year of the £5,000 annual threshold (NICA 2025 s.2).
ANNUAL_CONVENTION_FROM = 2025


@pytest.fixture(scope="module")
def system():
    return CountryTaxBenefitSystem()


def stored_weekly_st(system, year):
    class_1 = system.get_parameters_at_instant(
        str(year)
    ).gov.hmrc.national_insurance.class_1
    return float(class_1.thresholds.secondary_threshold)


def tolerance(*amounts):
    # float32 has a 24-bit significand: a few ulps of the largest amount
    # involved, plus a penny.
    return 0.01 + 4e-7 * max(abs(float(a)) for a in amounts)


# Invariant 1: annual ST.
@pytest.mark.parametrize("year", YEARS)
def test_annual_secondary_threshold_is_statutory(system, year):
    _, annual, _ = STATUTORY[year]
    assert 52 * stored_weekly_st(system, year) == pytest.approx(float(annual), abs=0.01)


# Invariant 2: weekly ST.
@pytest.mark.parametrize("year", YEARS)
def test_stored_weekly_secondary_threshold(system, year):
    weekly, annual, _ = STATUTORY[year]
    stored = stored_weekly_st(system, year)
    if year < ANNUAL_CONVENTION_FROM:
        assert annual == 52 * weekly
        assert stored == float(weekly)
    else:
        assert stored == pytest.approx(float(annual / 52), abs=1e-6)
        # The rounded weekly figure would annualise below the statute.
        assert 52 * weekly < annual


# Invariants 3 and 4: liabilities.
def simulate(year, earnings):
    people = {
        # Class 1 earnings are set directly: from 2029 the salary sacrifice
        # broad-base haircut trims employment income before NI.
        f"p{i}": {
            "age": {year: 40},
            "ni_class_1_income": {year: float(amount)},
            "employer_pension_contributions": {year: 0},
        }
        for i, amount in enumerate(earnings)
    }
    situation = {
        "people": people,
        "benunits": {f"b_{name}": {"members": [name]} for name in people},
        "households": {f"h_{name}": {"members": [name]} for name in people},
    }
    sim = Simulation(situation=situation)
    return np.asarray(sim.calculate("ni_class_1_employer", year), dtype=float)


def statutory_employer_ni(year, earnings):
    _, annual, rate = STATUTORY[year]
    return rate * max(Fraction(float(earnings)) - annual, 0)


def check_employer_ni(year, earnings):
    model = simulate(year, earnings)
    for amount, value in zip(earnings, model):
        expected = statutory_employer_ni(year, amount)
        assert abs(value - float(expected)) <= tolerance(expected, amount), (
            year,
            amount,
            value,
            float(expected),
        )
    return model


@pytest.mark.parametrize("year", RATED_YEARS)
def test_employer_ni_at_the_threshold_edge(year):
    weekly, annual, _ = STATUTORY[year]
    annual = float(annual)
    rounded_weekly_annual = 52 * float(weekly)
    edges = [
        0.0,
        annual - 1,
        annual - 0.01,
        annual,
        annual + 0.01,
        annual + 1,
        # Halfway between 52 x the rounded weekly figure and the annual
        # figure, if they differ (£4,996 from 2025-26).
        (rounded_weekly_annual + annual) / 2,
        40_000.0,
        250_000.0,
    ]
    model = check_employer_ni(year, edges)
    assert model[edges.index(annual - 0.01)] == 0
    assert abs(model[edges.index(annual)]) < 0.005
    assert model[edges.index(annual + 0.01)] > 0


@settings(
    max_examples=25,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
@given(
    year=st.sampled_from(RATED_YEARS),
    earnings=st.lists(
        st.one_of(
            st.floats(0, 500_000, allow_nan=False, allow_infinity=False),
            st.integers(0, 500_000).map(float),
            st.floats(4_000, 10_000, allow_nan=False),
        ),
        min_size=1,
        max_size=12,
    ),
)
# #1967: £40,000 in 2025-26 was £5,251.20, not £5,250. #2178: earnings
# between £8,060 and £8,112 in 2016-17 were charged.
@example(year=2025, earnings=[40_000.0, 4_996.0, 5_000.0])
@example(year=2016, earnings=[8_100.0, 8_112.0, 20_000.0])
# 2022-23 was charged at 13.8%, not the 15.05% levy rate.
@example(year=2022, earnings=[30_000.0, 9_100.0, 100_000.0])
def test_employer_ni_follows_the_statutory_threshold(year, earnings):
    check_employer_ni(year, earnings)
