"""Property tests for a Scottish taxpayer's tax_band (#2350).

tax_band is the highest band in which a person has taxable income. For a
Scottish taxpayer the liability charges income other than savings and
dividends at the Scottish rates (earned_income_tax and property_income_tax,
ITA 2007 s. 11A) and savings and dividends at the rest-of-UK savings and
dividend rates (savings_income_tax and dividend_income_tax, ss. 11D(6) and
13(5)). These tests read the band off that liability: they raise the rates of
one band at a time by RISE and see which bands' rates each person pays.

With the starting rate for savings, the Personal Savings Allowance and the
dividend allowance set to nothing, every pound of taxable income is charged at
a band's rate, and for every Scottish taxpayer:

- a person in a band pays tax at that band's rates on some income and at no
  higher band's rates, and a person with no band pays no tax;
- the Marriage Allowance income conditions hold exactly when the person pays
  nothing at the higher or additional rates (s. 55B(2)(b)).

Under the law in force the nil rates charge some income at 0% where it sits,
so the band can rest on that income alone, but no one pays tax at the higher
or additional rates above their band.

Before #2350 the band compared all taxable income with the Scottish limits.
From 2019-20, when that formula last applied, the band never rises, except
from STARTER to BASIC where savings or dividends sit below the Scottish
starter limit: they are charged at the rest-of-UK basic rates, not at the
starter rate.
"""

from contextlib import contextmanager

import numpy as np
import pytest
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

# Whole-pound limits and allowances, with Scottish schedules of three (2017-18),
# five (2018-19 to 2023-24) and six rates (from 2024-25).
YEARS = list(range(2017, 2027))
PEOPLE = 16
# Raising a band's rates by 100 percentage points raises the tax by the income
# charged at them. Taxable income comes in multiples of 50p (the personal
# allowance taper halves pounds), so SOME separates any income in a band from
# float32 rounding.
RISE = 1.0
SOME = 0.25
BANDS = ["NONE", "STARTER", "BASIC", "INTERMEDIATE", "HIGHER", "ADDITIONAL"]
RANK = {band: rank for rank, band in enumerate(BANDS)}
SCOTTISH = "gov.hmrc.income_tax.rates.scotland.rates[{}].rate"
SAVINGS = "gov.hmrc.income_tax.rates.savings.{}"
DIVIDENDS = "gov.hmrc.income_tax.rates.dividends[{}].rate"
# The rates charged in each band: the Scottish rates on non-savings income,
# the savings rates and the dividend rates. ADDITIONAL covers the Scottish
# advanced and top rates.
BAND_RATES = {
    "STARTER": [SCOTTISH.format(0)],
    "BASIC": [SCOTTISH.format(1), SAVINGS.format("basic"), DIVIDENDS.format(0)],
    "INTERMEDIATE": [SCOTTISH.format(2)],
    "HIGHER": [SCOTTISH.format(3), SAVINGS.format("higher"), DIVIDENDS.format(1)],
    "ADDITIONAL": [
        SCOTTISH.format(4),
        SCOTTISH.format(5),
        SAVINGS.format("additional"),
        DIVIDENDS.format(2),
        DIVIDENDS.format(3),
    ],
}
# The starting rate for savings, the Personal Savings Allowance and the
# dividend allowance.
NIL_RATE_AMOUNTS = [
    "gov.hmrc.income_tax.rates.savings_starter_rate.allowance",
    "gov.hmrc.income_tax.allowances.personal_savings_allowance.basic",
    "gov.hmrc.income_tax.allowances.personal_savings_allowance.higher",
    "gov.hmrc.income_tax.allowances.personal_savings_allowance.additional",
    "gov.hmrc.income_tax.allowances.dividend_allowance",
]
LIABILITY = [
    "earned_income_tax",
    "property_income_tax",
    "savings_income_tax",
    "dividend_income_tax",
]
INCOMES = [
    "employment_income",
    "property_income",
    "savings_interest_income",
    "dividend_income",
    "gift_aid",
]

pounds = st.integers(min_value=0, max_value=60_000)
# Pay at the 2025-26 Scottish and rest-of-UK limits, the taper and the top.
pay = st.one_of(
    st.integers(min_value=0, max_value=160_000),
    st.sampled_from([12_570, 15_397, 27_491, 43_662, 50_270, 75_000, 100_001]),
)
person = st.tuples(
    pay,
    st.one_of(st.just(0), pounds),  # property income
    st.one_of(st.just(0), pounds),  # savings interest
    st.one_of(st.just(0), pounds),  # dividends
    # Gift Aid in multiples of £4 grosses up to whole pounds at 20%.
    st.one_of(
        st.just(0), st.integers(min_value=0, max_value=1_000).map(lambda n: 4 * n)
    ),
)
people = st.lists(person, min_size=PEOPLE, max_size=PEOPLE)
year = st.sampled_from(YEARS)

# The issue's cases, 2025-26: pay and dividends of 40,000 and 5,000, 60,000 and
# 20,000, and 30,000 and 25,000; the same with savings; both limits at once.
ISSUE = [
    (40_000, 0, 0, 5_000, 0),
    (60_000, 0, 0, 20_000, 0),
    (30_000, 0, 0, 25_000, 0),
    (40_000, 0, 5_000, 0, 0),
    (60_000, 0, 20_000, 0, 0),
    (30_000, 0, 25_000, 0, 0),
    (43_662, 0, 0, 6_608, 0),
    (5_000, 0, 1_000, 1_000, 0),
]
ISSUE += [(0, 0, 0, 0, 0)] * (PEOPLE - len(ISSUE))


def situation():
    return {
        "people": {f"person_{i}": {"age": {YEARS[0]: 40}} for i in range(PEOPLE)},
        "benunits": {
            f"benunit_{i}": {"members": [f"person_{i}"]} for i in range(PEOPLE)
        },
        "households": {
            f"household_{i}": {
                "members": [f"person_{i}"],
                "country": {year: "SCOTLAND" for year in YEARS},
            }
            for i in range(PEOPLE)
        },
    }


@pytest.fixture(scope="module")
def sim():
    return Simulation(situation=situation())


def set_people(sim, drawn, period):
    for variable, values in zip(INCOMES, zip(*drawn)):
        sim.set_input(variable, period, np.array(values, dtype=float))
    sim.reset_calculations()


def set_law(sim, period, values):
    """Set parameter values for the year on the simulation's own system."""
    parameters = sim.tax_benefit_system.parameters
    for path, value in values.items():
        parameters.get_child(path).update(period=str(period), value=value)
    sim.tax_benefit_system.reset_parameter_caches()
    sim.reset_calculations()


@contextmanager
def law(sim, period, values):
    parameters = sim.tax_benefit_system.parameters
    before = {path: parameters.get_child(path)(str(period)) for path in values}
    set_law(sim, period, values)
    try:
        yield
    finally:
        set_law(sim, period, before)


def liability(sim, period):
    return sum(sim.calculate(v, period).astype(float) for v in LIABILITY)


def charged(sim, period, bands):
    """The income charged at each band's rates: the rise in tax when only
    that band's rates rise by RISE, divided by RISE."""
    parameters = sim.tax_benefit_system.parameters
    before = liability(sim, period)
    income_at = {}
    for band in bands:
        rates = {
            path: parameters.get_child(path)(str(period)) for path in BAND_RATES[band]
        }
        # A rate with no value that year (a Scottish rate not yet set) stays so.
        raised = {path: rate + RISE for path, rate in rates.items() if rate is not None}
        with law(sim, period, raised):
            income_at[band] = (liability(sim, period) - before) / RISE
    return income_at


def band_of(sim, period):
    return np.asarray(sim.calculate("tax_band", period), dtype=str)


SETTINGS = settings(
    max_examples=8,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)


@SETTINGS
@given(people, year)
@example(ISSUE, 2025)
def test_band_is_the_highest_rate_charged_without_nil_rates(sim, drawn, period):
    set_people(sim, drawn, period)
    with law(sim, period, {path: 0 for path in NIL_RATE_AMOUNTS}):
        band = band_of(sim, period)
        meets = np.asarray(
            sim.calculate("meets_marriage_allowance_income_conditions", period)
        )
        income_at = charged(sim, period, BAND_RATES)
    for i, b in enumerate(band):
        case = f"{drawn[i]} in {period}: {b}, {[income_at[x][i] for x in income_at]}"
        if b == "NONE":
            assert all(abs(income_at[x][i]) < SOME for x in income_at), case
            continue
        assert income_at[b][i] > SOME, case
        for above in BANDS[RANK[b] + 1 :]:
            assert abs(income_at[above][i]) < SOME, case
    above_intermediate = (income_at["HIGHER"] > SOME) | (income_at["ADDITIONAL"] > SOME)
    np.testing.assert_array_equal(meets, ~above_intermediate, err_msg=str(drawn))


@SETTINGS
@given(people, year)
@example(ISSUE, 2025)
def test_no_one_pays_higher_rates_above_their_band(sim, drawn, period):
    set_people(sim, drawn, period)
    band = band_of(sim, period)
    tax = liability(sim, period)
    # The Marriage Allowance and counts by marginal rate turn on these.
    income_at = charged(sim, period, ["HIGHER", "ADDITIONAL"])
    for i, b in enumerate(band):
        case = f"{drawn[i]} in {period}: {b}, {[income_at[x][i] for x in income_at]}"
        if b == "NONE":
            assert abs(tax[i]) < SOME, case
        for above in income_at:
            if RANK[above] > RANK[b]:
                assert abs(income_at[above][i]) < SOME, case


def band_before_2350(sim, period):
    """tax_band's Scottish formula from 2019-20 before #2350: all taxable
    income against the Scottish limits, the next band from each limit on."""
    scale = sim.tax_benefit_system.parameters(
        str(period)
    ).gov.hmrc.income_tax.rates.scotland.rates
    income = sim.calculate("net_income", period) - sim.calculate("allowances", period)
    gift = sim.calculate("gift_aid_grossed_up", period)
    return np.select(
        [
            income < threshold + (gift if index >= 2 else 0)
            for index, threshold in enumerate(scale.thresholds[:5])
        ],
        BANDS[:5],
        default="ADDITIONAL",
    )


@SETTINGS
@given(people, st.sampled_from(YEARS[2:]))
@example(ISSUE, 2025)
def test_band_never_rises_except_from_starter_to_basic(sim, drawn, period):
    set_people(sim, drawn, period)
    band = band_of(sim, period)
    before = band_before_2350(sim, period)
    taxable = sim.calculate("net_income", period) - sim.calculate("allowances", period)
    non_savings = sim.calculate("non_savings_income_after_allowances", period)
    starter_limit = sim.tax_benefit_system.parameters(
        str(period)
    ).gov.hmrc.income_tax.rates.scotland.rates.thresholds[1]
    for i in range(PEOPLE):
        if RANK[band[i]] <= RANK[before[i]]:
            continue
        # Savings or dividends below the starter limit are basic, not starter.
        case = f"{drawn[i]} in {period}: {before[i]} to {band[i]}"
        assert (before[i], band[i]) == ("STARTER", "BASIC"), case
        assert non_savings[i] < taxable[i] < starter_limit, case


def test_savings_allowance_does_not_read_the_band():
    # ITA 2007 s. 12B(8) sets the Personal Savings Allowance on the
    # rest-of-UK bands for everyone, so savings_allowance (#2347) never reads
    # tax_band: forcing the band changes nothing.
    sim = Simulation(situation=situation())
    set_people(sim, ISSUE, 2025)
    allowance = sim.calculate("savings_allowance", 2025)
    np.testing.assert_array_equal(allowance[:6], [1_000, 500, 500, 1_000, 500, 500])
    for band in BANDS:
        sim.set_input("tax_band", 2025, np.array([band] * PEOPLE))
        sim.reset_calculations()
        np.testing.assert_array_equal(
            sim.calculate("savings_allowance", 2025), allowance
        )
