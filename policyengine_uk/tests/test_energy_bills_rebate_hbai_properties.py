"""Property tests for the 2022 Energy Bills Rebate in HBAI income.

DWP's HBAI classifies the Energy Bills Support Scheme (£600 in Northern
Ireland) and the £150 Council Tax Rebate as miscellaneous income, not state
support (HBAI quality and methodology report FYE 2023, "Treatment of cost of
living and wider support schemes in the HBAI income estimates for FYE
2023"). The Council Tax Rebate was a one-off: billing authorities made every
payment by 30 September 2022 (Council Tax Rebate 2022-23 billing authority
guidance, paragraph 7).

Invariants, each checked over many generated households in one reusable
simulation:

1. HBAI household net income before the reset to zero rises by exactly the
   household's energy_bills_rebate, in every year, nation and band.
2. The rebate is miscellaneous income: hbai_benefits does not change with it.
3. The Council Tax Rebate is paid once: in 2022 only, at £150, and only in
   bands A to D outside Northern Ireland, which has domestic rates and had no
   Council Tax Rebate.
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.variables.household.income.hbai_household_net_income import (
    HBAI_HOUSEHOLD_NET_INCOME_ADDS,
)

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

YEARS = [2021, 2022, 2023, 2024]
BANDS = ["A", "B", "C", "D", "E", "F", "G", "H", "I"]
COUNTRIES = ["ENGLAND", "SCOTLAND", "WALES", "NORTHERN_IRELAND"]
HOUSEHOLDS = 16

household = st.tuples(
    st.sampled_from(BANDS),
    st.sampled_from(COUNTRIES),
    st.sampled_from([0.0, 6_000.0, 18_000.0, 45_000.0]),  # employment income
    st.booleans(),  # claims Universal Credit
    st.lists(st.booleans(), min_size=12, max_size=12),  # EBSS months eligible
)
households = st.lists(household, min_size=HOUSEHOLDS, max_size=HOUSEHOLDS)


def simulation(drawn, years, without_rebate=False):
    """One household per drawn case, with the same circumstances in each of
    ``years``."""
    bands, countries, pay, claims_uc, months = zip(*drawn)

    def each_year(value):
        return {year: value for year in years}

    people = {
        f"adult_{i}": {"age": each_year(40), "employment_income": each_year(pay[i])}
        for i in range(HOUSEHOLDS)
    }
    benunits = {
        f"unit_{i}": {
            "members": [f"adult_{i}"],
            "would_claim_uc": each_year(claims_uc[i]),
        }
        for i in range(HOUSEHOLDS)
    }
    households = {
        f"household_{i}": {
            "members": [f"adult_{i}"],
            "council_tax_band": each_year(bands[i]),
            "country": each_year(countries[i]),
            "ebr_energy_bills_credit_eligible": {
                f"{year}-{month:02d}": months[i][month - 1]
                for year in years
                for month in range(1, 13)
            },
        }
        for i in range(HOUSEHOLDS)
    }
    if without_rebate:
        for values in households.values():
            values["energy_bills_rebate"] = each_year(0)
    return Simulation(
        situation={"people": people, "benunits": benunits, "households": households}
    )


SETTINGS = settings(
    max_examples=10,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)


@SETTINGS
@given(households, st.sampled_from(YEARS))
def test_hbai_income_rises_by_exactly_the_rebate(drawn, year):
    with_rebate = simulation(drawn, [year])
    without = simulation(drawn, [year], without_rebate=True)
    rebate = with_rebate.calculate("energy_bills_rebate", year)
    gain = with_rebate.calculate(
        "hbai_household_net_income_before_reset_to_zero", year
    ) - without.calculate("hbai_household_net_income_before_reset_to_zero", year)
    np.testing.assert_allclose(gain, rebate, atol=0.01)
    np.testing.assert_allclose(
        with_rebate.calculate("hbai_benefits", year),
        without.calculate("hbai_benefits", year),
        atol=0.01,
    )


@SETTINGS
@given(households)
def test_the_council_tax_rebate_is_paid_once(drawn):
    bands = np.array([band for band, *_ in drawn])
    countries = np.array([country for _, country, *_ in drawn])
    years = range(2015, 2031)
    sim = simulation(drawn, years)
    total = np.zeros(HOUSEHOLDS)
    for year in years:
        rebate = sim.calculate("ebr_council_tax_rebate", year)
        if year == 2022:
            np.testing.assert_array_equal(
                rebate,
                np.where(
                    np.isin(bands, ["A", "B", "C", "D"])
                    & (countries != "NORTHERN_IRELAND"),
                    150,
                    0,
                ),
            )
        else:
            np.testing.assert_array_equal(rebate, 0)
        total += rebate
    assert (total <= 150).all()


def test_the_rebate_is_counted_once_and_not_as_state_support():
    """HBAI adds energy_bills_rebate once, and not its parts as well; it and
    the Warm Home Discount are miscellaneous income, outside hbai_benefits."""
    from policyengine_uk import CountryTaxBenefitSystem

    system = CountryTaxBenefitSystem()
    parts = system.variables["energy_bills_rebate"].adds
    assert set(parts) == {
        "ebr_council_tax_rebate",
        "ebr_energy_bills_credit",
        "ebr_alternative_fuel_payment",
    }
    assert HBAI_HOUSEHOLD_NET_INCOME_ADDS.count("energy_bills_rebate") == 1
    assert not set(parts) & set(HBAI_HOUSEHOLD_NET_INCOME_ADDS)
    state_support = system.variables["hbai_benefits"].adds
    for miscellaneous_income in ["energy_bills_rebate", "warm_home_discount"]:
        assert miscellaneous_income not in state_support
