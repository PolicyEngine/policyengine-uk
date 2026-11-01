"""Property-based tests for the dated residential SDLT schedules (issue #2245).

The reference below restates the legislation's own tables, for effective
dates from 15 March 2018:

- Finance Act 2003 s55(1B) Table A (main rates); Sch4ZA para 1(2) (higher
  rates for additional dwellings, the main rates plus 3 points, or 5 from
  31 October 2024 under Finance Act 2025 s50), which para 3(2) applies only
  from £40,000; Sch6ZA paras 1(3) and 4 (first-time buyers' relief: 0% to
  £300,000 and 5% above, on prices up to £500,000); Sch5 para 2(3) Table A
  (lease rent: 1% of net present value above £125,000).
- SDLT (Temporary Relief) Act 2020 s1, from 8 July 2020 to 30 June 2021 (the
  end as amended by Finance Act 2021 s87(2)(a)): 0% to £500,000 on the main
  and lease rent tables, and no first-time buyers' relief (s1(5)).
- s1A of that Act, inserted by Finance Act 2021 s87(3), from 1 July to 30
  September 2021: 0% to £250,000 on the main and lease rent tables.
- SDLT (Temporary Relief) Act 2023 s1, from 23 September 2022 to 31 March
  2025: 0% to £250,000 on the main and lease rent tables, and first-time
  buyers' relief of 0% to £425,000 on prices up to £625,000.

Invariants, for any effective date, price and buyer:

1. Differential: the raw dated parameters give the reference tax for a
   non-first purchase, a first-time buyer, an additional dwelling and a
   lease.
2. Annual sampling: each model year from 2018 to 2040 reads every residential
   SDLT parameter at 30 April of that year.
3. Through stamp_duty_land_tax, in every model year from 2018 to 2040, each
   buyer's tax equals the reference at 30 April, and in every model year
   from 2015 to 2040 it never falls as the price or the lease rent rises.
4. At any effective date, no buyer's tax falls as the price or the lease
   rent rises.
5. Omitted relief: from 8 July 2020 to 30 June 2021, whatever the main and
   first-time buyers' rates, a first-time buyer pays the same tax as a
   non-first buyer. Changing first-time buyers' rates leaves that tax
   unchanged, and changing the main rates moves both buyers' tax equally.
   Model year 2021 shows the same through stamp_duty_land_tax.
"""

from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st
from policyengine_core.parameters import ParameterNode
from policyengine_core.periods import instant

import policyengine_uk
from policyengine_uk import Microsimulation
from policyengine_uk.data import UKSingleYearDataset
from policyengine_uk.system import system

PROPERTY_SETTINGS = settings(
    max_examples=300,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow],
)

STANDARD = ((0, 0), (125_000, 0.02), (250_000, 0.05), (925_000, 0.10))
STANDARD += ((1_500_000, 0.12),)
NIL_500K = ((0, 0), (500_000, 0.05), (925_000, 0.10), (1_500_000, 0.12))
NIL_250K = ((0, 0), (250_000, 0.05), (925_000, 0.10), (1_500_000, 0.12))
FIRST_TIME_BUYER = (300_000, 500_000)
FIRST_TIME_BUYER_2022_25 = (425_000, 625_000)
# First effective date, main rates, first-time buyers' relief (nil band,
# maximum price) or None, higher-rates surcharge, lease rent nil band.
TIMELINE = (
    (date(2018, 3, 15), STANDARD, FIRST_TIME_BUYER, 0.03, 125_000),
    (date(2020, 7, 8), NIL_500K, None, 0.03, 500_000),
    (date(2021, 7, 1), NIL_250K, FIRST_TIME_BUYER, 0.03, 250_000),
    (date(2021, 10, 1), STANDARD, FIRST_TIME_BUYER, 0.03, 125_000),
    (date(2022, 9, 23), NIL_250K, FIRST_TIME_BUYER_2022_25, 0.03, 250_000),
    (date(2024, 10, 31), NIL_250K, FIRST_TIME_BUYER_2022_25, 0.05, 250_000),
    (date(2025, 4, 1), STANDARD, FIRST_TIME_BUYER, 0.05, 125_000),
)
FIRST_DATE = TIMELINE[0][0]
LAST_DATE = date(2035, 12, 31)
HIGHER_RATES_MINIMUM = 40_000
LEASE_RATE = 0.01
BUYERS = ("main", "first", "additional")
PRICE_BOUNDARIES = (40_000, 125_000, 250_000, 300_000, 425_000, 500_000)
PRICE_BOUNDARIES += (625_000, 925_000, 1_500_000)


def _law_at(effective_date):
    return [entry for entry in TIMELINE if entry[0] <= effective_date][-1]


def _marginal(bands, amount):
    tax = 0.0
    for (start, rate), (end, _) in zip(bands, bands[1:] + ((np.inf, 0),)):
        tax += rate * max(0.0, min(amount, end) - start)
    return tax


def reference_tax(effective_date, price, buyer):
    _, main, first_time_buyer, surcharge, _ = _law_at(effective_date)
    if buyer == "first" and first_time_buyer is not None:
        nil_band, maximum = first_time_buyer
        if price <= maximum:
            return _marginal(((0, 0), (nil_band, 0.05)), price)
    if buyer == "additional" and price >= HIGHER_RATES_MINIMUM:
        higher = tuple((start, rate + surcharge) for start, rate in main)
        return _marginal(higher, price)
    return _marginal(main, price)


def reference_lease_tax(effective_date, net_present_value):
    nil_band = _law_at(effective_date)[4]
    return LEASE_RATE * max(0.0, net_present_value - nil_band)


def _model_tax(purchase, price, buyer):
    # The schedule sdlt_on_residential_property_transactions applies to each
    # kind of purchase.
    if buyer == "first":
        return np.where(
            price <= purchase.main.first.max,
            purchase.main.first.rate.calc(price),
            purchase.main.subsequent.calc(price),
        )
    if buyer == "additional":
        chargeable = np.where(price < purchase.additional.min, 0, price)
        return purchase.additional.rate.calc(chargeable)
    return purchase.main.subsequent.calc(price)


RAW = ParameterNode(
    "residential",
    directory_path=str(
        Path(policyengine_uk.__file__).parent
        / "parameters/gov/hmrc/stamp_duty/residential"
    ),
)

CHANGE_DATES = [entry[0] for entry in TIMELINE[1:]]
dates = st.one_of(
    st.dates(min_value=FIRST_DATE, max_value=LAST_DATE),
    st.sampled_from(
        [d + timedelta(days=offset) for d in CHANGE_DATES for offset in (-1, 0)]
    ),
)
prices = st.one_of(
    st.integers(0, 300_000_000).map(lambda pence: pence / 100),
    st.sampled_from([b + offset for b in PRICE_BOUNDARIES for offset in (-1, 0, 1)]),
)


@PROPERTY_SETTINGS
@given(effective_date=dates, price_list=st.lists(prices, min_size=1, max_size=8))
def test_dated_parameters_match_the_statutory_tables(effective_date, price_list):
    purchase = RAW(effective_date.isoformat()).purchase
    price = np.array(price_list, dtype=float)
    for buyer in BUYERS:
        expected = [reference_tax(effective_date, p, buyer) for p in price_list]
        np.testing.assert_allclose(
            _model_tax(purchase, price, buyer),
            expected,
            rtol=1e-12,
            atol=1e-6,
            err_msg=f"{buyer} on {effective_date}",
        )


@PROPERTY_SETTINGS
@given(effective_date=dates, value_list=st.lists(prices, min_size=1, max_size=8))
def test_dated_lease_rent_matches_the_statutory_table(effective_date, value_list):
    rent = RAW(effective_date.isoformat()).rent
    expected = [reference_lease_tax(effective_date, v) for v in value_list]
    np.testing.assert_allclose(
        rent.calc(np.array(value_list, dtype=float)), expected, rtol=1e-12, atol=1e-6
    )


@PROPERTY_SETTINGS
@given(effective_date=dates, price_list=st.lists(prices, min_size=2, max_size=8))
def test_tax_never_falls_as_the_price_rises_on_any_date(effective_date, price_list):
    residential = RAW(effective_date.isoformat())
    price = np.sort(np.array(price_list, dtype=float))
    for buyer in BUYERS:
        tax = _model_tax(residential.purchase, price, buyer)
        assert np.all(np.diff(tax) >= -1e-9), (buyer, effective_date, price, tax)
    assert np.all(np.diff(residential.rent.calc(price)) >= -1e-9)


# SDLT (Temporary Relief) Act 2020 s1(5) omits first-time buyers' relief over
# the initial relief period that s1(1), as amended, sets.
INITIAL_RELIEF = (date(2020, 7, 8), date(2021, 6, 30))
rates = st.floats(0, 0.5)


def _change_rates_over_initial_relief(scale, new_rates):
    # The relief tables leave some brackets empty; change the others in order.
    start, stop = (instant(day) for day in INITIAL_RELIEF)
    on_start = INITIAL_RELIEF[0].isoformat()
    brackets = [b for b in scale.brackets if b.rate(on_start) is not None]
    for bracket, rate in zip(brackets, new_rates):
        bracket.rate.update(start=start, stop=stop, value=rate)


@PROPERTY_SETTINGS
@example(
    effective_date=date(2021, 4, 30),
    price_list=[0.01, 1, 300_000],
    main_rates=[0.07] * 4,
    first_time_buyer_rates=[0.11, 0.30],
)
@given(
    effective_date=st.dates(*INITIAL_RELIEF),
    price_list=st.lists(prices, min_size=1, max_size=8),
    main_rates=st.lists(rates, min_size=4, max_size=4),
    first_time_buyer_rates=st.lists(rates, min_size=2, max_size=2),
)
def test_omitted_relief_ignores_buyer_status_under_any_rates(
    effective_date, price_list, main_rates, first_time_buyer_rates
):
    residential = RAW.clone()
    main = residential.purchase.main
    _change_rates_over_initial_relief(main.subsequent, main_rates)
    _change_rates_over_initial_relief(main.first.rate, first_time_buyer_rates)
    purchase = residential(effective_date.isoformat()).purchase
    assert list(purchase.main.subsequent.rates) == main_rates
    assert list(purchase.main.first.rate.rates) == first_time_buyer_rates
    price = np.array(price_list, dtype=float)
    np.testing.assert_array_equal(
        _model_tax(purchase, price, "first"),
        _model_tax(purchase, price, "main"),
        err_msg=f"{effective_date}, main {main_rates}, first {first_time_buyer_rates}",
    )


def _scale(scale):
    return scale.thresholds, scale.rates


def _read(residential):
    purchase = residential.purchase
    return (
        _scale(purchase.main.subsequent),
        _scale(purchase.main.first.rate),
        purchase.main.first.max,
        _scale(purchase.additional.rate),
        purchase.additional.min,
        _scale(residential.rent),
    )


@pytest.mark.parametrize("year", range(FIRST_DATE.year, 2041))
def test_each_model_year_reads_30_april(year):
    annual = system.parameters(year).gov.hmrc.stamp_duty.residential
    assert _read(annual) == _read(RAW(f"{year}-04-30"))


GRID = np.unique(
    np.concatenate(
        [
            np.arange(0, 2_000_001, 50_000),
            [b + offset for b in PRICE_BOUNDARIES for offset in (-1, 0, 1)],
            [2_500_000],
        ]
    )
).astype(float)
GROUPS = BUYERS + ("lease",)


def _london_dataset(households):
    ids = np.arange(1, households + 1)
    return UKSingleYearDataset(
        person=pd.DataFrame(
            {
                "person_id": ids,
                "person_benunit_id": ids,
                "person_household_id": ids,
                "age": 40,
            }
        ),
        benunit=pd.DataFrame({"benunit_id": ids}),
        household=pd.DataFrame(
            {
                "household_id": ids,
                "household_weight": 1.0,
                "region": "LONDON",
                "tenure_type": "OWNED_OUTRIGHT",
                "council_tax": 0.0,
                "rent": 0.0,
            }
        ),
        fiscal_year=2025,
    )


@pytest.fixture(scope="module")
def grid_simulation():
    # One household per price and group: a non-first purchase, a first-time
    # buyer, an additional dwelling and a lease, all in London.
    return Microsimulation(dataset=_london_dataset(len(GRID) * len(GROUPS)))


def _grid_inputs():
    zero = np.zeros_like(GRID)
    return {
        "main_residential_property_purchased": np.concatenate([GRID, GRID, zero, zero]),
        "main_residential_property_purchased_is_first_home": np.repeat(
            [False, True, False, False], len(GRID)
        ),
        "additional_residential_property_purchased": np.concatenate(
            [zero, zero, GRID, zero]
        ),
        "cumulative_residential_rent": np.concatenate([zero, zero, zero, zero]),
        "rent": np.concatenate([zero, zero, zero, GRID]),
    }


@pytest.mark.parametrize("year", range(2015, 2041))
def test_stamp_duty_by_model_year(grid_simulation, year):
    # Each year's inputs are the same grid, set directly rather than uprated.
    for variable, values in _grid_inputs().items():
        grid_simulation.set_input(variable, year, values)
    tax = np.array(grid_simulation.calculate("stamp_duty_land_tax", year), dtype=float)
    groups = dict(zip(GROUPS, np.split(tax, len(GROUPS))))
    for group, values in groups.items():
        assert np.all(np.diff(values) >= -1e-6), (group, year, values)
    sampled = date(year, 4, 30)
    if sampled < FIRST_DATE:
        return
    for buyer in BUYERS:
        expected = [reference_tax(sampled, p, buyer) for p in GRID]
        np.testing.assert_allclose(
            groups[buyer], expected, rtol=1e-6, atol=0.01, err_msg=f"{buyer} {year}"
        )
    expected = [reference_lease_tax(sampled, v) for v in GRID]
    np.testing.assert_allclose(groups["lease"], expected, rtol=1e-6, atol=0.01)


# Model year 2021 samples 30 April 2021, inside the initial relief period.
OMITTED_RELIEF_YEAR = 2021
MAIN_RATES = "gov.hmrc.stamp_duty.residential.purchase.main.subsequent"
FIRST_TIME_BUYER_RATES = "gov.hmrc.stamp_duty.residential.purchase.main.first.rate"
# New rates for the brackets that carry one in model year 2021, by index.
FIRST_TIME_BUYER_REFORM = {FIRST_TIME_BUYER_RATES: {0: 0.11, 1: 0.30}}
MAIN_REFORM = {MAIN_RATES: {0: 0.07, 2: 0.09, 3: 0.15, 4: 0.20}}
RATE_REFORMS = {
    "first-time buyers' rates": FIRST_TIME_BUYER_REFORM,
    "main rates": MAIN_REFORM,
    "both": {**FIRST_TIME_BUYER_REFORM, **MAIN_REFORM},
}
BUYER_PRICES = np.unique(np.concatenate([[0.01, 1], GRID]))


@pytest.fixture(scope="module")
def buyer_simulation():
    # A non-first purchase and a first-time buyer at each price, in London.
    simulation = Microsimulation(dataset=_london_dataset(2 * len(BUYER_PRICES)))
    zero = np.zeros(2 * len(BUYER_PRICES))
    inputs = {
        "main_residential_property_purchased": np.tile(BUYER_PRICES, 2),
        "main_residential_property_purchased_is_first_home": np.repeat(
            [False, True], len(BUYER_PRICES)
        ),
        "additional_residential_property_purchased": zero,
        "cumulative_residential_rent": zero,
        "rent": zero,
    }
    for variable, values in inputs.items():
        simulation.set_input(variable, OMITTED_RELIEF_YEAR, values)
    return simulation


def _buyer_tax(simulation):
    tax = simulation.calculate("stamp_duty_land_tax", OMITTED_RELIEF_YEAR)
    return np.split(np.array(tax, dtype=float), 2)


def _set_rates(simulation, leaf_rates):
    for leaf, rate in leaf_rates:
        leaf.update(period=str(OMITTED_RELIEF_YEAR), value=rate)
    simulation.tax_benefit_system.reset_parameter_caches()
    simulation.reset_calculations()


@pytest.mark.parametrize("reform", RATE_REFORMS)
def test_model_year_2021_omits_relief_under_rate_reforms(buyer_simulation, reform):
    parameters = buyer_simulation.tax_benefit_system.parameters
    changes = [
        (parameters.get_child(f"{scale}[{index}].rate"), rate)
        for scale, new_rates in RATE_REFORMS[reform].items()
        for index, rate in new_rates.items()
    ]
    baseline = [(leaf, leaf(str(OMITTED_RELIEF_YEAR))) for leaf, _ in changes]
    base_main, base_first = _buyer_tax(buyer_simulation)
    _set_rates(buyer_simulation, changes)
    try:
        assert all(leaf(str(OMITTED_RELIEF_YEAR)) == rate for leaf, rate in changes)
        main, first = _buyer_tax(buyer_simulation)
    finally:
        _set_rates(buyer_simulation, baseline)
    # Buyer status leaves the tax unchanged, with and without the reform.
    np.testing.assert_array_equal(base_first, base_main)
    np.testing.assert_array_equal(first, main)
    if MAIN_RATES in RATE_REFORMS[reform]:
        # Main-rate changes move both buyers' tax, and equally.
        assert np.any(main != base_main)
        np.testing.assert_array_equal(first - base_first, main - base_main)
    else:
        # First-time buyers' rates leave their tax unchanged.
        np.testing.assert_array_equal(first, base_first)
