"""Uprating of the Scottish Carer Supplement and Carer Support Payment.

Social Security (Scotland) Act 2018 s.86B requires Scottish Ministers to bring
forward legislation raising each figure of assistance given under Chapter 2 of
Part 2, carer's assistance included, to at least its s.86A inflation-adjusted
level. Their measure is the 12 months to September CPI, rounded to the nearest
5p (Social Security Assistance in Scotland: up-rating for inflation in
2026-27, sections 2 and 3). SSI 2026/170 reg 12(3) raised the Carer Support
Payment component from 83.30 to 86.45 and the Scottish Carer Supplement from
11.29 to 11.70: both are the 3.8% September 2025 rate, rounded to 5p. The
supplement had no uprating metadata, so the model froze it at 11.70 a week from
2027 while the Carer Support Payment component kept rising.

Both rates now rise as Scottish Child Payment and Pension Age Winter Heating
Payment do: each April by the previous September's CPI
(gov.benefit_uprating_cpi), rounded to the nearest 5p. Invariants, for every
year from 2027 to the last year of the uprating index:

1. Each April's rate is the previous rounded rate times one plus the
   September CPI rise, rounded to the nearest 5p. The reference here compounds
   the published 2026 rates in Decimal, independently of the index.
2. Neither rate falls, since the rise is never negative.
3. Metamorphic: setting the previous September's CPI to a published rate g
   moves that April's rates to the previous rates times 1 + g, rounded to 5p,
   and leaves the year before alone.

The YAML tests in tests/policy/baseline/gov/social_security_scotland check
that a Carer Support Payment recipient in Scotland gets 52 weeks of each rate.
"""

from decimal import ROUND_HALF_UP, Decimal

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.model_api import Scenario
from policyengine_uk.parameters.gov.economic_assumptions.create_economic_assumption_indices import (
    growth_horizon,
)
from policyengine_uk.system import system

CARER = "gov.social_security_scotland.carer_support_payment"
CPI_SEPTEMBER = "gov.economic_assumptions.statutory_uprating_inputs.cpi_september"
# SSI 2026/170 reg 12(3)(a) and (b).
RATES_2026 = {
    f"{CARER}.supplement": Decimal("11.70"),
    f"{CARER}.rate": Decimal("86.45"),
}
# Hand calculations: the 2026 rate x 1.035 (September 2026 CPI, ONS release
# of 21 October 2026), to the nearest 5p: 11.70 -> 12.1095; 86.45 -> 89.47575.
APRIL_2027 = {f"{CARER}.supplement": 12.10, f"{CARER}.rate": 89.50}
YEARS = range(
    2027, growth_horizon(system.parameters.gov.economic_assumptions.yoy_growth) + 1
)
FIVE_PENCE = Decimal("0.05")

PERSON = {
    "people": {"person": {"age": {2026: 40}}},
    "benunits": {"benunit": {"members": ["person"]}},
    "households": {"household": {"members": ["person"]}},
}


def nearest_5p(amount: Decimal) -> Decimal:
    return (amount / FIVE_PENCE).quantize(Decimal(1), ROUND_HALF_UP) * FIVE_PENCE


def weekly_rate(parameters, name, year):
    return parameters.get_child(name)(f"{year}-04-30")


@pytest.mark.parametrize("name", RATES_2026)
def test_2026_rates_are_the_enacted_ones(name):
    assert weekly_rate(system.parameters, name, 2026) == float(RATES_2026[name])


@pytest.mark.parametrize("name, expected", APRIL_2027.items())
def test_april_2027_rates_use_september_2026_cpi(name, expected):
    assert weekly_rate(system.parameters, name, 2027) == pytest.approx(
        expected, abs=1e-9
    )


@pytest.mark.parametrize("name", RATES_2026)
def test_each_april_compounds_the_previous_rounded_rate(name):
    parameters = system.parameters
    rise = parameters.gov.economic_assumptions.yoy_growth.september_cpi_uprating
    previous = RATES_2026[name]
    for year in YEARS:
        growth = 1 + Decimal(str(rise(f"{year}-01-01")))
        expected = nearest_5p(previous * growth)
        actual = weekly_rate(parameters, name, year)
        # A rise can land exactly on a 2.5p tie, as 28.75 x 1.02 does, and the
        # index's five decimal places may then break it down.
        if (previous * growth) % FIVE_PENCE == FIVE_PENCE / 2 and actual < expected:
            expected -= FIVE_PENCE
        assert actual == pytest.approx(float(expected), abs=1e-9), year
        assert actual >= weekly_rate(parameters, name, year - 1), year
        previous = expected


def parameters_under(changes):
    simulation = Simulation(
        situation=PERSON,
        scenario=Scenario(parameter_changes=changes, applied_before_data_load=True),
    )
    return simulation.tax_benefit_system.parameters


@settings(
    max_examples=8,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(
    year=st.integers(min_value=YEARS.start, max_value=2035),
    september_permille=st.integers(min_value=0, max_value=120),
)
def test_rates_follow_the_previous_september_cpi(year, september_permille):
    september = Decimal(september_permille) / 1000
    expected = {}
    for name in RATES_2026:
        before = Decimal(f"{weekly_rate(system.parameters, name, year - 1):.2f}")
        unrounded = before * (1 + september)
        # The index is stored to 5 decimal places, so skip rises that land
        # within a tenth of a step of a 5p half-way point.
        steps = unrounded / FIVE_PENCE
        remainder = abs(steps - steps.to_integral_value())
        assume(Decimal("0.5") - remainder > Decimal("0.1"))
        expected[name] = (before, nearest_5p(unrounded))

    parameters = parameters_under(
        {CPI_SEPTEMBER: {f"year:{year - 1}-09-01:1": float(september)}}
    )

    for name, (before, after) in expected.items():
        assert weekly_rate(parameters, name, year - 1) == pytest.approx(
            float(before), abs=1e-9
        )
        assert weekly_rate(parameters, name, year) == pytest.approx(
            float(after), abs=1e-9
        )
