"""Tests for the National Insurance threshold freeze to April 2031 (#1879).

Budget 2025 maintains the Class 1 primary threshold (PT), upper earnings limit
(UEL) and secondary threshold (ST), and the Class 4 lower and upper profits
limits (LPL, UPL), at their 2026-27 levels until 5 April 2031. The Lower
Earnings Limit is not frozen: it rose with CPI to £129 a week in 2026-27.

Model year Y is the fiscal year starting 6 April Y. The model stores PT and UEL
and ST as the annual amounts over 52 (12,570 / 52, 50,270 / 52 and 5,000 / 52,
as SI 2001/1004 reg 11(3)(c), 11(2A)(c) and 11(3A)(c) do for periods of whole
weeks), and annualises weekly thresholds as 52 weeks. So the model's annual ST
is the £5,000 in reg 11(3A)(b), not 52 x the rounded reg 10(d) weekly £96
(£4,992) (#1967).

Invariants:

1. Statute table: in every year 2026-2030, each threshold equals the figure in
   STATUTORY_2026_27, which is taken from SI 2001/1004 regs 10-11 as they
   stand for 2026-27 and SSCBA 1992 s.15(3), not from the parameter files.
2. Cash freeze: PT, UEL, ST, LPL and UPL are identical in every year
   2026-2030.
3. After the freeze: from 2031 the PT, UEL, LPL and UPL stay aligned with
   the income tax thresholds, which Income Tax Act 2007 ss21 and 57 index by
   September CPI, and the ST rises by September CPI, each from its frozen
   level with no catch-up. test_threshold_indexation.py tests this.
4. Alignment with the personal allowance and the higher rate threshold in
   every year 2021-2040: test_threshold_indexation.py.
5. No cash cuts: no threshold falls from one year to the next, 2026-2040.
6. Differential: for any earnings or profits >= 0 in 2026-2030, primary and
   additional Class 1, secondary Class 1 and Class 4 equal an exact-rational
   computation from the statute table.
7. Frozen liabilities: rates do not change over 2026-2030, so the NI due on
   a given cash income is the same in every one of those years.

Comparisons allow float32 rounding: the model stores values as float32.
"""

from fractions import Fraction
from pathlib import Path

import numpy as np
import pytest
import yaml
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

import policyengine_uk
from policyengine_uk import CountryTaxBenefitSystem, Simulation

NI = "gov.hmrc.national_insurance"
FROZEN_YEARS = [2026, 2027, 2028, 2029, 2030]
PROJECTION_YEARS = list(range(2026, 2041))
PARAMETER_DIR = Path(policyengine_uk.__file__).parent / "parameters"

# Figures for 2026-27 from the Social Security (Contributions) Regulations
# 2001 regs 10-11, whose tax year SI 2026/231 reg 5 set to 2026-27, and SSCBA
# 1992 s.15(3). Budget 2025 holds all but the LEL at these levels until April
# 2031.
STATUTORY_2026_27 = {
    "lower_earnings_limit": Fraction(129),  # weekly, CPI-uprated
    "primary_threshold": Fraction(12_570, 52),  # annual / 52
    "secondary_threshold": Fraction(5_000, 52),  # annual / 52 (#1967)
    "upper_earnings_limit": Fraction(50_270, 52),  # annual / 52
    "lower_profits_limit": Fraction(12_570),  # annual
    "upper_profits_limit": Fraction(50_270),  # annual
}
PATHS = {
    "lower_earnings_limit": "class_1.thresholds.lower_earnings_limit",
    "primary_threshold": "class_1.thresholds.primary_threshold",
    "secondary_threshold": "class_1.thresholds.secondary_threshold",
    "upper_earnings_limit": "class_1.thresholds.upper_earnings_limit",
    "lower_profits_limit": "class_4.thresholds.lower_profits_limit",
    "upper_profits_limit": "class_4.thresholds.upper_profits_limit",
}
FROZEN = [name for name in PATHS if name != "lower_earnings_limit"]
# 2026-27 rates, unchanged over the freeze.
RATES = {
    "class_1_main": Fraction(8, 100),
    "class_1_additional": Fraction(2, 100),
    "class_1_employer": Fraction(15, 100),
    "class_4_main": Fraction(6, 100),
    "class_4_additional": Fraction(2, 100),
}


@pytest.fixture(scope="module")
def system():
    return CountryTaxBenefitSystem()


def get_node(parameters, path):
    node = parameters
    for part in path.split("."):
        node = getattr(node, part)
    return node


def threshold(system, name, year):
    ni = system.get_parameters_at_instant(str(year)).gov.hmrc.national_insurance
    return float(get_node(ni, PATHS[name]))


def cpi(system, year):
    return float(
        system.get_parameters_at_instant(
            str(year)
        ).gov.economic_assumptions.indices.obr.consumer_price_index
    )


def tolerance(*amounts):
    # float32 has a 24-bit significand: a few ulps of the largest amount
    # involved, plus a penny.
    return 0.01 + 4e-7 * max(abs(float(a)) for a in amounts)


# Invariant 1: statute table.
@pytest.mark.parametrize("year", FROZEN_YEARS)
@pytest.mark.parametrize("name", FROZEN)
def test_frozen_thresholds_match_statute(system, name, year):
    expected = float(STATUTORY_2026_27[name])
    assert threshold(system, name, year) == pytest.approx(expected, abs=0.005)


def test_lower_earnings_limit_2025_26_and_2026_27(system):
    # SI 2025/288 reg 5(2)(b) and SI 2026/231 reg 5(2)(b).
    assert threshold(system, "lower_earnings_limit", 2025) == 125
    assert threshold(system, "lower_earnings_limit", 2026) == 129


@pytest.mark.parametrize("year", [2025, *FROZEN_YEARS])
def test_annual_secondary_threshold_is_statutory(system, year):
    # SI 2001/1004 reg 11(3A)(b): £5,000 where the earnings period is a year
    # (#1967). 52 x the rounded weekly £96 would give £4,992.
    annual = 52 * threshold(system, "secondary_threshold", year)
    assert annual == pytest.approx(5_000, abs=0.01)


# Invariant 2: cash freeze.
@pytest.mark.parametrize("name", FROZEN)
def test_frozen_thresholds_hold_in_cash_terms(system, name):
    values = {year: threshold(system, name, year) for year in FROZEN_YEARS}
    assert len(set(values.values())) == 1, values


# Invariants 3 and 4 are in test_threshold_indexation.py.


def test_lower_earnings_limit_is_cpi_uprated_from_2026_27(system):
    base = threshold(system, "lower_earnings_limit", 2026)
    for year in range(2027, 2041):
        expected = base * cpi(system, year) / cpi(system, 2026)
        assert threshold(system, "lower_earnings_limit", year) == pytest.approx(
            expected, rel=1e-9
        )


# Invariant 5: no cash cuts.
@pytest.mark.parametrize("name", list(PATHS))
def test_no_threshold_falls_in_cash_terms(system, name):
    values = [threshold(system, name, year) for year in PROJECTION_YEARS]
    assert all(b >= a for a, b in zip(values, values[1:])), values


def test_frozen_year_values_cite_a_source():
    """Every value dated in 2026-27 to 2030-31 carries a titled reference."""
    for name, path in PATHS.items():
        file = (
            PARAMETER_DIR
            / "gov/hmrc/national_insurance"
            / (path.replace(".", "/") + ".yaml")
        )
        values = yaml.safe_load(file.read_text())["values"]
        dated = {str(instant): entry for instant, entry in values.items()}
        years = [2025, 2026] if name == "lower_earnings_limit" else FROZEN_YEARS
        for year in years:
            entry = dated.get(f"{year}-04-06")
            assert isinstance(entry, dict), (name, year)
            references = entry.get("metadata", {}).get("reference", [])
            assert references, (name, year)
            for reference in references:
                assert reference.get("title") and reference.get("href"), (
                    name,
                    year,
                )


# Invariants 6 and 7: liabilities.


def simulate(earnings, profits, year):
    """One simulation: employees on `earnings`, then sole traders on `profits`."""
    people = {}
    for i, amount in enumerate(earnings):
        # Class 1 earnings are set directly: from 2029 the salary sacrifice
        # broad-base haircut trims employment income before NI.
        people[f"e{i}"] = {
            "age": {year: 40},
            "ni_class_1_income": {year: float(amount)},
            "employer_pension_contributions": {year: 0},
        }
    for i, amount in enumerate(profits):
        people[f"s{i}"] = {
            "age": {year: 40},
            "self_employment_income": {year: float(amount)},
        }
    names = list(people)
    situation = {
        "people": people,
        "benunits": {f"b_{n}": {"members": [n]} for n in names},
        "households": {f"h_{n}": {"members": [n]} for n in names},
    }
    sim = Simulation(situation=situation)
    n_employees = len(earnings)
    out = {
        variable: np.asarray(sim.calculate(variable, year), dtype=float)
        for variable in [
            "ni_class_1_employee_primary",
            "ni_class_1_employee_additional",
            "ni_class_1_employer",
            "ni_class_4",
        ]
    }
    return {
        "employees": {k: v[:n_employees] for k, v in out.items()},
        "sole_traders": {k: v[n_employees:] for k, v in out.items()},
    }


def statutory_class_1(earnings):
    e = Fraction(float(earnings))
    pt = 52 * STATUTORY_2026_27["primary_threshold"]
    uel = 52 * STATUTORY_2026_27["upper_earnings_limit"]
    st_ = 52 * STATUTORY_2026_27["secondary_threshold"]
    return {
        "ni_class_1_employee_primary": RATES["class_1_main"]
        * min(max(e - pt, 0), uel - pt),
        "ni_class_1_employee_additional": RATES["class_1_additional"] * max(e - uel, 0),
        "ni_class_1_employer": RATES["class_1_employer"] * max(e - st_, 0),
    }


def statutory_class_4(profits):
    """SSCBA 1992 s.15(3) for a sole trader with no Class 1."""
    p = Fraction(float(profits))
    lpl = STATUTORY_2026_27["lower_profits_limit"]
    upl = STATUTORY_2026_27["upper_profits_limit"]
    return RATES["class_4_main"] * min(max(p - lpl, 0), upl - lpl) + RATES[
        "class_4_additional"
    ] * max(p - upl, 0)


def check_liabilities(earnings, profits, years):
    results = {year: simulate(earnings, profits, year) for year in years}
    for year, result in results.items():
        for i, amount in enumerate(earnings):
            for variable, expected in statutory_class_1(amount).items():
                model = result["employees"][variable][i]
                assert abs(model - float(expected)) <= tolerance(expected, amount), (
                    year,
                    variable,
                    amount,
                    model,
                    float(expected),
                )
        for i, amount in enumerate(profits):
            expected = statutory_class_4(amount)
            model = result["sole_traders"]["ni_class_4"][i]
            assert abs(model - float(expected)) <= tolerance(expected, amount), (
                year,
                amount,
                model,
                float(expected),
            )
    # Invariant 7: identical liabilities in every frozen year.
    first = results[years[0]]
    for year in years[1:]:
        for group in ("employees", "sole_traders"):
            for variable, values in results[year][group].items():
                np.testing.assert_array_equal(
                    values, first[group][variable], err_msg=f"{year} {variable}"
                )


# Every threshold, a penny and a pound either side, plus seeded random levels.
EDGES = [
    edge + offset
    for edge in [4_992, 5_000, 12_570, 50_270]
    for offset in (-1, -0.01, 0, 0.01, 1)
]


def test_liabilities_at_threshold_edges_and_random_levels():
    rng = np.random.default_rng(1879)
    levels = [0.0, *EDGES, *rng.uniform(0, 250_000, 60).round(2).tolist()]
    check_liabilities(levels, levels, FROZEN_YEARS)


@settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
@given(
    earnings=st.lists(
        st.floats(0, 500_000, allow_nan=False, allow_infinity=False),
        min_size=1,
        max_size=12,
    ),
    profits=st.lists(
        st.floats(0, 500_000, allow_nan=False, allow_infinity=False),
        min_size=1,
        max_size=12,
    ),
)
# #1879: a £60,000 employee and a £60,000 sole trader. Before the fix, 2028
# used CPI-uprated PT/UEL and 2027 CPI-uprated LPL/UPL.
@example(earnings=[60_000.0], profits=[60_000.0])
def test_liabilities_follow_the_frozen_statute(earnings, profits):
    check_liabilities(earnings, profits, FROZEN_YEARS)
