"""Property tests for the 2022 £150 and Council Tax Reduction.

England's Council Tax Rebate went to bands A to D (billing authority guidance,
paragraph 11). Scotland's Cost of Living Award and Wales's Cost of Living
Support Scheme also paid Council Tax Reduction recipients in any band (Local
Government Finance Circular 2/2022, paragraphs 6, 10 and 12; Welsh guide,
conditions A and B). Each nation paid one £150 per dwelling. Northern Ireland
levies domestic rates and had no such payment.

Invariants, each checked over many generated households:

1. No household in Northern Ireland is paid, whatever its band or reduction.
2. Every household in Great Britain gets £150 or nothing.
3. Every household in Great Britain in bands A to D gets £150, whatever its
   reduction.
4. A household in band E or above gets £150 exactly when it lives in Scotland
   or Wales and receives Council Tax Reduction.
5. Nobody is paid in any year but 2022, whatever the reduction.
6. A larger reduction never lowers the payment.
7. Where the model works out the reduction itself, the same rule holds on its
   result, and the payment reaches household net income.
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

YEARS = [2021, 2022, 2023]
BANDS = ["A", "B", "C", "D", "E", "F", "G", "H", "I"]
IN_BAND = BANDS[:4]
COUNTRIES = ["ENGLAND", "SCOTLAND", "WALES", "NORTHERN_IRELAND"]
PAYS_RECIPIENTS = ["SCOTLAND", "WALES"]
HOUSEHOLDS = 16
AMOUNT = 150

reductions = st.one_of(st.just(0.0), st.floats(0.01, 5_000, allow_nan=False))
household = st.tuples(st.sampled_from(BANDS), st.sampled_from(COUNTRIES), reductions)
households = st.lists(household, min_size=HOUSEHOLDS, max_size=HOUSEHOLDS)


def each_year(value):
    return {year: value for year in YEARS}


def people_and_units(count):
    return (
        {f"adult_{i}": {"age": each_year(40)} for i in range(count)},
        {
            f"unit_{i}": {"members": [f"adult_{i}"], "would_claim_uc": each_year(False)}
            for i in range(count)
        },
    )


def simulation(drawn):
    """One household per drawn case, with its reduction given as an input."""
    bands, countries, amounts = zip(*drawn)
    people, benunits = people_and_units(len(drawn))
    return Simulation(
        situation={
            "people": people,
            "benunits": benunits,
            "households": {
                f"household_{i}": {
                    "members": [f"adult_{i}"],
                    "council_tax_band": each_year(bands[i]),
                    "country": each_year(countries[i]),
                    "council_tax_reduction": each_year(amounts[i]),
                }
                for i in range(len(drawn))
            },
        }
    )


def fields(drawn):
    bands, countries, amounts = zip(*drawn)
    return np.array(bands), np.array(countries), np.array(amounts)


SETTINGS = settings(
    max_examples=10,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)


@SETTINGS
@given(households)
def test_northern_ireland_is_never_paid(drawn):
    _, countries, _ = fields(drawn)
    rebate = simulation(drawn).calculate("ebr_council_tax_rebate", 2022)
    np.testing.assert_array_equal(rebate[countries == "NORTHERN_IRELAND"], 0)


@SETTINGS
@given(households)
def test_great_britain_pays_at_most_one_150_per_household(drawn):
    _, countries, _ = fields(drawn)
    rebate = simulation(drawn).calculate("ebr_council_tax_rebate", 2022)
    great_britain = rebate[countries != "NORTHERN_IRELAND"]
    assert np.isin(great_britain, [0, AMOUNT]).all()


@SETTINGS
@given(households)
def test_bands_a_to_d_are_always_paid_in_great_britain(drawn):
    bands, countries, _ = fields(drawn)
    rebate = simulation(drawn).calculate("ebr_council_tax_rebate", 2022)
    in_band = np.isin(bands, IN_BAND) & (countries != "NORTHERN_IRELAND")
    np.testing.assert_array_equal(rebate[in_band], AMOUNT)


@SETTINGS
@given(households)
def test_higher_bands_are_paid_exactly_for_scottish_and_welsh_recipients(drawn):
    bands, countries, amounts = fields(drawn)
    rebate = simulation(drawn).calculate("ebr_council_tax_rebate", 2022)
    higher_band = ~np.isin(bands, IN_BAND)
    expected = np.where(np.isin(countries, PAYS_RECIPIENTS) & (amounts > 0), AMOUNT, 0)
    np.testing.assert_array_equal(rebate[higher_band], expected[higher_band])


@SETTINGS
@given(households)
def test_only_2022_is_paid(drawn):
    sim = simulation(drawn)
    for year in [2021, 2023]:
        np.testing.assert_array_equal(sim.calculate("ebr_council_tax_rebate", year), 0)


@SETTINGS
@given(households, st.floats(0.01, 5_000, allow_nan=False))
def test_a_larger_reduction_never_lowers_the_payment(drawn, increase):
    bands, countries, amounts = fields(drawn)
    larger = [
        (band, country, amount + increase)
        for band, country, amount in zip(bands, countries, amounts)
    ]
    before = simulation(drawn).calculate("ebr_council_tax_rebate", 2022)
    after = simulation(larger).calculate("ebr_council_tax_rebate", 2022)
    assert (after >= before).all()


simulated_household = st.tuples(
    st.sampled_from(BANDS),
    st.sampled_from(COUNTRIES),
    st.integers(0, 40_000),
    st.booleans(),
)
simulated_households = st.lists(
    simulated_household, min_size=HOUSEHOLDS, max_size=HOUSEHOLDS
)


@settings(
    max_examples=10,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(simulated_households)
def test_the_rule_holds_on_a_simulated_reduction(drawn):
    bands, countries, earnings, claims = zip(*drawn)
    bands, countries = np.array(bands), np.array(countries)
    people, benunits = people_and_units(len(drawn))
    for i in range(len(drawn)):
        people[f"adult_{i}"]["employment_income"] = each_year(earnings[i])
        benunits[f"unit_{i}"]["would_claim_council_tax_reduction"] = each_year(
            claims[i]
        )
    sim = Simulation(
        situation={
            "people": people,
            "benunits": benunits,
            "households": {
                f"household_{i}": {
                    "members": [f"adult_{i}"],
                    "council_tax_band": each_year(bands[i]),
                    "country": each_year(countries[i]),
                    "council_tax": each_year(2_400),
                }
                for i in range(len(drawn))
            },
        }
    )
    rebate = sim.calculate("ebr_council_tax_rebate", 2022)
    receives = sim.calculate("council_tax_reduction", 2022) > 0
    in_band = np.isin(bands, IN_BAND)
    expected = np.where(
        countries == "NORTHERN_IRELAND",
        0,
        np.where(in_band | (np.isin(countries, PAYS_RECIPIENTS) & receives), AMOUNT, 0),
    )
    np.testing.assert_array_equal(rebate, expected)
    # The payment reaches net income without a circular dependency.
    assert np.isfinite(sim.calculate("household_net_income", 2022)).all()
    assert (sim.calculate("energy_bills_rebate", 2022) >= rebate).all()
