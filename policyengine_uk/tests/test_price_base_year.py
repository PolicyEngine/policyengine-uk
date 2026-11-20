"""Real incomes use the prices of gov.simulation.price_base_year (#2875).

``inflation_adjustment`` divides ``consumer_price_index`` on 1 January of the
base year by the index in the period. ``inflation_adjustment_ahc`` divides one
index on 1 January of the base year by the same index in the period: it uses
``consumer_price_index_ahc`` where that index has a value on both dates, and
``consumer_price_index`` on both dates otherwise. No formula reads the clock,
so a simulation gives the same answers whatever year it runs in.

Invariants:

1. Identity: each adjustment equals 1 when the period equals the base year,
   for every base year from 2009, where the CPI index starts. For
   ``inflation_adjustment_ahc`` that includes base years before 2022.
2. Positivity: each adjustment stays positive wherever the indices have
   values.
3. Rebasing: for any two base years, the ratio of the two adjustments does
   not depend on the period. It holds for ``inflation_adjustment`` from 2009
   and for ``inflation_adjustment_ahc`` across periods and base years from
   2022.
4. The four real income variables equal their nominal income times
   ``inflation_adjustment``.

The property tests set the base year on a fresh simulation's own parameter
tree, which is faster than a reform; ``test_tree_update_matches_reform``
checks that the two routes agree.
"""

import functools

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from policyengine_core.periods import instant

from policyengine_uk import Simulation
from policyengine_uk.system import system

INDICES = system.parameters.gov.economic_assumptions.indices.obr
CPI = INDICES.consumer_price_index
CPI_AHC = INDICES.consumer_price_index_ahc
BASE_YEAR = "gov.simulation.price_base_year"
DEFAULT_BASE_YEAR = 2026

SITUATION = {
    "people": {
        "adult": {"age": {"2026": 40}, "employment_income": {"2026": 30_000}},
    },
    "benunits": {"benunit": {"members": ["adult"]}},
    "households": {"household": {"members": ["adult"]}},
}

# Base years the property tests draw from: the first CPI year, years before
# and within the stretch where the AHC index reads 1, the default, a forecast
# year and a year after the last index value.
BASE_YEARS = [2009, 2014, 2018, 2022, 2026, 2031, 2080]
PERIODS = st.integers(min_value=2009, max_value=2080)

PROPERTY_SETTINGS = settings(
    max_examples=40,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow],
)

REAL_INCOMES = {
    "real_household_net_income": "household_net_income",
    "real_household_net_income_ahc": "household_net_income_ahc",
    "real_hbai_household_net_income": "hbai_household_net_income",
    "real_hbai_household_net_income_ahc": "hbai_household_net_income_ahc",
}


def cpi(year):
    return CPI(f"{year}-01-01")


@functools.lru_cache(maxsize=None)
def simulation_at_base_year(base_year):
    """A fresh simulation whose own parameter tree prices to ``base_year``."""
    sim = Simulation(situation=SITUATION)
    sim.tax_benefit_system.parameters.get_child(BASE_YEAR).update(
        start=instant("2000-01-01"), stop=instant("2100-12-31"), value=base_year
    )
    sim.tax_benefit_system._parameters_at_instant_cache.clear()
    return sim


@functools.lru_cache(maxsize=None)
def baseline_simulation():
    return Simulation(situation=SITUATION)


@pytest.fixture(scope="module", autouse=True)
def release_simulations():
    yield
    simulation_at_base_year.cache_clear()
    baseline_simulation.cache_clear()


def adjustment(variable, base_year, period):
    sim = simulation_at_base_year(base_year)
    return float(sim.calculate(variable, period)[0])


# Example tests.


def test_default_base_year():
    parameter = system.parameters.get_child(BASE_YEAR)
    for year in (2009, 2015, 2026, 2027, 2050, 2100):
        assert parameter(f"{year}-01-01") == DEFAULT_BASE_YEAR


@pytest.mark.parametrize(
    "period", [2009, 2014, 2015, 2021, 2022, 2026, 2027, 2030, 2074, 2080]
)
def test_inflation_adjustment_against_cpi(period):
    expected = cpi(DEFAULT_BASE_YEAR) / cpi(period)
    actual = baseline_simulation().calculate("inflation_adjustment", period)
    assert actual[0] == pytest.approx(expected, rel=1e-6)


def test_ahc_adjustment_uses_one_index():
    sim = baseline_simulation()
    # Both dates have an AHC index value.
    for period in (2022, 2027, 2030):
        expected = CPI_AHC("2026-01-01") / CPI_AHC(f"{period}-01-01")
        actual = sim.calculate("inflation_adjustment_ahc", period)[0]
        assert actual == pytest.approx(expected, rel=1e-6)
    # The AHC index has no value in 2012, so CPI prices both dates.
    assert CPI_AHC("2012-01-01") is None
    actual = sim.calculate("inflation_adjustment_ahc", 2012)[0]
    assert actual == pytest.approx(cpi(2026) / cpi(2012), rel=1e-6)


def test_reform_changes_the_base_year():
    # A reform can pass the year as a float.
    reformed = Simulation(
        situation=SITUATION,
        reform={BASE_YEAR: {"2000-01-01.2100-12-31": 2030.0}},
    )
    baseline = baseline_simulation()
    adjustment_2026 = reformed.calculate("inflation_adjustment", 2026)[0]
    assert adjustment_2026 == pytest.approx(cpi(2030) / cpi(2026), rel=1e-6)
    assert reformed.calculate("inflation_adjustment", 2030)[0] == pytest.approx(1)
    assert reformed.calculate("inflation_adjustment_ahc", 2030)[0] == pytest.approx(1)
    assert reformed.calculate("real_household_net_income", 2026)[0] == pytest.approx(
        baseline.calculate("household_net_income", 2026)[0] * cpi(2030) / cpi(2026),
        rel=1e-5,
    )
    assert baseline.calculate("inflation_adjustment", 2026)[0] == pytest.approx(1)


def test_tree_update_matches_reform():
    reformed = Simulation(
        situation=SITUATION,
        reform={BASE_YEAR: {"2000-01-01.2100-12-31": 2031}},
    )
    for variable in ("inflation_adjustment", "inflation_adjustment_ahc"):
        for period in (2012, 2026, 2040):
            assert adjustment(variable, 2031, period) == pytest.approx(
                reformed.calculate(variable, period)[0], rel=1e-7
            )


def test_labels_name_no_year():
    for name in (
        "inflation_adjustment",
        "inflation_adjustment_ahc",
        "real_household_net_income",
        "real_household_net_income_ahc",
    ):
        label = system.variables[name].label
        assert "base-year" in label
        assert not any(char.isdigit() for char in label), label
    assert (
        system.variables["real_household_net_income"].label
        != system.variables["real_household_net_income_ahc"].label
    )


# Property tests.


@PROPERTY_SETTINGS
@given(base_year=st.sampled_from(BASE_YEARS))
def test_identity_in_the_base_year(base_year):
    for variable in ("inflation_adjustment", "inflation_adjustment_ahc"):
        assert adjustment(variable, base_year, base_year) == pytest.approx(1)


@PROPERTY_SETTINGS
@given(base_year=st.sampled_from(BASE_YEARS), period=PERIODS)
def test_positive(base_year, period):
    for variable in ("inflation_adjustment", "inflation_adjustment_ahc"):
        value = adjustment(variable, base_year, period)
        assert np.isfinite(value) and value > 0


@PROPERTY_SETTINGS
@given(
    base_years=st.lists(st.sampled_from(BASE_YEARS), min_size=2, max_size=2),
    periods=st.lists(PERIODS, min_size=2, max_size=2),
)
def test_rebasing_does_not_depend_on_the_period(base_years, periods):
    (b1, b2), (p1, p2) = base_years, periods
    variable = "inflation_adjustment"
    ratio_1 = adjustment(variable, b1, p1) / adjustment(variable, b2, p1)
    ratio_2 = adjustment(variable, b1, p2) / adjustment(variable, b2, p2)
    assert ratio_1 == pytest.approx(ratio_2, rel=1e-6)
    assert ratio_1 == pytest.approx(cpi(b1) / cpi(b2), rel=1e-6)


@PROPERTY_SETTINGS
@given(
    base_years=st.lists(
        st.sampled_from([b for b in BASE_YEARS if b >= 2022]), min_size=2, max_size=2
    ),
    periods=st.lists(st.integers(2022, 2080), min_size=2, max_size=2),
)
def test_ahc_rebasing_does_not_depend_on_the_period(base_years, periods):
    (b1, b2), (p1, p2) = base_years, periods
    variable = "inflation_adjustment_ahc"
    ratio_1 = adjustment(variable, b1, p1) / adjustment(variable, b2, p1)
    ratio_2 = adjustment(variable, b1, p2) / adjustment(variable, b2, p2)
    assert ratio_1 == pytest.approx(ratio_2, rel=1e-6)


@settings(PROPERTY_SETTINGS, max_examples=8)
@given(
    base_year=st.sampled_from(BASE_YEARS),
    period=st.sampled_from([2024, 2026, 2028]),
)
def test_real_income_is_nominal_times_adjustment(base_year, period):
    sim = simulation_at_base_year(base_year)
    multiplier = sim.calculate("inflation_adjustment", period)[0]
    for real, nominal in REAL_INCOMES.items():
        assert sim.calculate(real, period)[0] == pytest.approx(
            sim.calculate(nominal, period)[0] * multiplier, rel=1e-5, abs=0.01
        )
