"""Property tests for the Energy Bills Rebate in Northern Ireland.

England's £150 Council Tax Rebate applied to England only (billing authority
guidance, paragraph 2), and Scotland and Wales paid their own £150 awards.
Northern Ireland levies domestic rates, not council tax, and had no Council
Tax Rebate. Its households received one £600 payment instead: £400 of Energy
Bills Support Scheme support and a £200 Alternative Fuel Payment, paid to each
domestic electricity customer on 2 January 2023 (EBSS AFP NI Direction,
23 December 2022, paragraph 3 and footnote 1).

Invariants, each checked over many generated households in one simulation
covering 2015 to 2030. Some households stay in one nation; others draw a
nation for each year, so they move between 2022 and 2023:

1. No household receives the Council Tax Rebate in a year it lives in
   Northern Ireland, in any band.
2. The Alternative Fuel Payment is £200, paid once, in January 2023, to each
   household in Northern Ireland in 2023 with a qualifying electricity supply
   that month, and never to a household in Great Britain in 2023.
3. A household in Northern Ireland in 2022 receives no rebate that year. One
   in Northern Ireland in 2023 receives exactly the direction's £600 that year
   if it had a qualifying electricity supply in January 2023, and nothing
   otherwise. So a household in Northern Ireland in both years receives £600
   over the whole scheme.
4. In every year, energy_bills_rebate is the sum of its three parts, and
   none is negative.
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

YEARS = list(range(2015, 2031))
BANDS = ["A", "B", "C", "D", "E", "F", "G", "H", "I"]
COUNTRIES = ["ENGLAND", "SCOTLAND", "WALES", "NORTHERN_IRELAND"]
HOUSEHOLDS = 16
PARTS = [
    "ebr_council_tax_rebate",
    "ebr_energy_bills_credit",
    "ebr_alternative_fuel_payment",
]

# A household's nation in each year: either the same nation throughout or an
# independent draw for each year.
yearly_countries = st.one_of(
    st.sampled_from(COUNTRIES).map(lambda country: [country] * len(YEARS)),
    st.lists(st.sampled_from(COUNTRIES), min_size=len(YEARS), max_size=len(YEARS)),
)
household = st.tuples(
    st.sampled_from(BANDS),
    yearly_countries,
    # Whether the household has a qualifying electricity supply in each month
    # of 2022 and 2023.
    st.lists(st.booleans(), min_size=24, max_size=24),
)
households = st.lists(household, min_size=HOUSEHOLDS, max_size=HOUSEHOLDS)


def in_northern_ireland(drawn, year):
    return (
        np.array([countries[YEARS.index(year)] for _, countries, _ in drawn])
        == "NORTHERN_IRELAND"
    )


def eligible_in_january_2023(drawn):
    return np.array([months[12] for _, _, months in drawn])


def simulation(drawn):
    """One household per drawn case, in the same band each year."""
    bands, countries, months = zip(*drawn)

    def each_year(value):
        return {year: value for year in YEARS}

    people = {f"adult_{i}": {"age": each_year(40)} for i in range(HOUSEHOLDS)}
    benunits = {
        f"unit_{i}": {"members": [f"adult_{i}"], "would_claim_uc": each_year(False)}
        for i in range(HOUSEHOLDS)
    }
    households = {
        f"household_{i}": {
            "members": [f"adult_{i}"],
            "council_tax_band": each_year(bands[i]),
            "country": dict(zip(YEARS, countries[i])),
            "ebr_energy_bills_credit_eligible": {
                f"{year}-{month:02d}": months[i][12 * (year - 2022) + month - 1]
                for year in [2022, 2023]
                for month in range(1, 13)
            },
        }
        for i in range(HOUSEHOLDS)
    }
    return Simulation(
        situation={"people": people, "benunits": benunits, "households": households}
    )


SETTINGS = settings(
    max_examples=10,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)


@SETTINGS
@given(households)
def test_northern_ireland_never_gets_the_council_tax_rebate(drawn):
    sim = simulation(drawn)
    for year in YEARS:
        rebate = sim.calculate("ebr_council_tax_rebate", year)
        np.testing.assert_array_equal(rebate[in_northern_ireland(drawn, year)], 0)


@SETTINGS
@given(households)
def test_the_alternative_fuel_payment_is_paid_once_in_northern_ireland(drawn):
    northern_ireland = in_northern_ireland(drawn, 2023)
    eligible = eligible_in_january_2023(drawn)
    sim = simulation(drawn)
    for year in YEARS:
        for month in range(1, 13):
            payment = sim.calculate(
                "monthly_ebr_alternative_fuel_payment", f"{year}-{month:02d}"
            )
            if (year, month) == (2023, 1):
                expected = np.where(northern_ireland & eligible, 200, 0)
                np.testing.assert_array_equal(payment, expected)
            else:
                np.testing.assert_array_equal(payment, 0)


@SETTINGS
@given(households)
def test_northern_ireland_receives_the_directions_600(drawn):
    in_2022 = in_northern_ireland(drawn, 2022)
    in_2023 = in_northern_ireland(drawn, 2023)
    expected = np.where(eligible_in_january_2023(drawn), 600, 0)
    sim = simulation(drawn)
    np.testing.assert_array_equal(
        sim.calculate("energy_bills_rebate", 2022)[in_2022], 0
    )
    np.testing.assert_allclose(
        sim.calculate("energy_bills_rebate", 2023)[in_2023],
        expected[in_2023],
        atol=0.01,
    )
    total = sum(sim.calculate("energy_bills_rebate", year) for year in YEARS)
    stayed = in_2022 & in_2023
    np.testing.assert_allclose(total[stayed], expected[stayed], atol=0.01)


@SETTINGS
@given(households)
def test_the_rebate_is_the_sum_of_its_parts(drawn):
    sim = simulation(drawn)
    for year in YEARS:
        parts = [sim.calculate(part, year) for part in PARTS]
        for part in parts:
            assert (part >= 0).all()
        np.testing.assert_allclose(
            sim.calculate("energy_bills_rebate", year), sum(parts), atol=0.01
        )
