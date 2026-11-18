"""Ordinary residential SDLT before 4 December 2014 (issue 2838).

The independent upper-bound tables below come from HMRC's archived rates:
https://www.gov.uk/government/publications/rates-and-allowances-stamp-duty-land-tax
FA 2003 s55(1)-(2) charges one percentage of the whole consideration.
SDLT Act 2015 s2(2) changes that basis on 4 December 2014. These tests execute
the production formula with raw dated parameters because an annual simulation
cannot represent an individual transaction's December effective date.
The 2010-12 first-time-buyer, disadvantaged-area and contract reliefs are outside
these ordinary-purchase oracles. No private dataset or historical tax total is used.
"""

from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from policyengine_core.parameters import ParameterNode

import policyengine_uk
from policyengine_uk.variables.gov.hmrc.sdlt_on_residential_property_transactions import (
    sdlt_on_residential_property_transactions,
)

# Dates and ordinary bands are literals from the corresponding HMRC tables.
# Each pair is an inclusive upper price limit and the whole-price percentage.
HISTORY = (
    (
        date(2003, 12, 1),
        ((60_000, 0), (250_000, 0.01), (500_000, 0.03), (np.inf, 0.04)),
    ),
    (
        date(2005, 3, 17),
        ((120_000, 0), (250_000, 0.01), (500_000, 0.03), (np.inf, 0.04)),
    ),
    (
        date(2006, 3, 23),
        ((125_000, 0), (250_000, 0.01), (500_000, 0.03), (np.inf, 0.04)),
    ),
    (
        date(2008, 9, 3),
        ((175_000, 0), (250_000, 0.01), (500_000, 0.03), (np.inf, 0.04)),
    ),
    (
        date(2010, 1, 1),
        ((125_000, 0), (250_000, 0.01), (500_000, 0.03), (np.inf, 0.04)),
    ),
    (
        date(2011, 4, 6),
        (
            (125_000, 0),
            (250_000, 0.01),
            (500_000, 0.03),
            (1_000_000, 0.04),
            (np.inf, 0.05),
        ),
    ),
    (
        date(2012, 3, 22),
        (
            (125_000, 0),
            (250_000, 0.01),
            (500_000, 0.03),
            (1_000_000, 0.04),
            (2_000_000, 0.05),
            (np.inf, 0.07),
        ),
    ),
)
MARGINAL_START = date(2014, 12, 4)
FIRST_DATE = HISTORY[0][0]
LAST_DATE = MARGINAL_START - timedelta(days=1)
UPPER_LIMITS = [
    60_000,
    120_000,
    125_000,
    175_000,
    250_000,
    500_000,
    1_000_000,
    2_000_000,
]
BOUNDARIES = [0.0, 0.01, 2_500_000.0] + [
    bound + offset for bound in UPPER_LIMITS for offset in (-0.01, 0, 0.01)
]
CHANGE_DAYS = sorted(
    {day + timedelta(days=offset) for day, _ in HISTORY for offset in (-1, 0)}
    | {LAST_DATE, MARGINAL_START}
)


@pytest.fixture(scope="module")
def raw_residential():
    return ParameterNode(
        "residential",
        directory_path=str(
            Path(policyengine_uk.__file__).parent
            / "parameters/gov/hmrc/stamp_duty/residential"
        ),
    )


def reference_tax(effective_date, price):
    if effective_date < FIRST_DATE:
        return 0.0
    if effective_date >= MARGINAL_START:
        return (
            0.02 * min(max(price - 125_000, 0), 125_000)
            + 0.05 * min(max(price - 250_000, 0), 675_000)
            + 0.10 * min(max(price - 925_000, 0), 575_000)
            + 0.12 * max(price - 1_500_000, 0)
        )
    bands = [bands for start, bands in HISTORY if start <= effective_date][-1]
    return next(price * rate for upper, rate in bands if price <= upper)


class PurchaseHouseholds:
    """Only the three public inputs used by the production purchase formula."""

    def __init__(self, prices, buyer):
        zero = np.zeros_like(prices)
        self.inputs = {
            "main_residential_property_purchased": zero
            if buyer == "additional"
            else prices,
            "additional_residential_property_purchased": prices
            if buyer == "additional"
            else zero,
            "main_residential_property_purchased_is_first_home": np.full(
                prices.shape, buyer == "first", dtype=bool
            ),
        }
        self.shape = prices.shape

    def __call__(self, variable, period):
        return self.inputs[variable]

    def empty_array(self):
        return np.zeros(self.shape)


def actual_formula(raw, effective_date, prices, buyer="main"):
    residential = raw(effective_date.isoformat())
    stamp_duty = SimpleNamespace(residential=residential)
    parameters = SimpleNamespace(
        gov=SimpleNamespace(hmrc=SimpleNamespace(stamp_duty=stamp_duty))
    )
    return sdlt_on_residential_property_transactions.formula(
        PurchaseHouseholds(prices, buyer), None, lambda _: parameters
    )


@pytest.mark.parametrize("effective_date", CHANGE_DAYS, ids=str)
@pytest.mark.parametrize("buyer", ["main", "additional"])
def test_each_operative_day_and_eve_runs_the_production_formula(
    raw_residential, effective_date, buyer
):
    prices = np.array(BOUNDARIES, dtype=float)
    expected = [reference_tax(effective_date, price) for price in prices]
    np.testing.assert_allclose(
        actual_formula(raw_residential, effective_date, prices, buyer),
        expected,
        rtol=1e-12,
        atol=1e-8,
    )


@settings(max_examples=300, deadline=None, derandomize=True)
@given(
    effective_date=st.dates(FIRST_DATE, LAST_DATE),
    prices=st.lists(st.integers(0, 500_000_000), min_size=1, max_size=8),
)
def test_ordinary_whole_price_tax_matches_independent_upper_bound_tables(
    raw_residential, effective_date, prices
):
    amounts = np.array(prices, dtype=float) / 100
    expected = [reference_tax(effective_date, price) for price in amounts]
    for buyer in ["main", "additional"]:
        np.testing.assert_allclose(
            actual_formula(raw_residential, effective_date, amounts, buyer),
            expected,
            rtol=1e-12,
            atol=1e-8,
        )


def test_2014_first_purchase_flag_does_not_read_the_2017_relief(raw_residential):
    amounts = np.array([0, 125_000, 200_000, 300_000, 1_000_000], dtype=float)
    np.testing.assert_allclose(
        actual_formula(raw_residential, date(2014, 1, 1), amounts, "first"),
        [0, 0, 2_000, 9_000, 40_000],
        rtol=0,
        atol=1e-8,
    )


def test_2014_regime_can_be_reformed_to_charge_slices(raw_residential):
    raw = raw_residential.clone()
    raw.purchase_charged_on_whole_price.update(period="2014", value=False)
    np.testing.assert_allclose(
        actual_formula(raw, date(2014, 1, 1), np.array([300_000.0])),
        [2_750],
        rtol=0,
        atol=1e-8,
    )


def test_positive_reformed_first_threshold_does_not_charge_prices_below_it(
    raw_residential,
):
    raw = raw_residential.clone()
    scale = raw.purchase.main.subsequent
    scale.brackets[0].threshold.update(period="2014", value=10_000)
    scale.brackets[0].rate.update(period="2014", value=0.005)
    np.testing.assert_allclose(
        actual_formula(raw, date(2014, 1, 1), np.array([0.0, 5_000, 10_000, 20_000])),
        [0, 0, 0, 100],
        rtol=0,
        atol=1e-8,
    )


# Ordinary Scottish jurisdiction: Scotland Act 2012 s29; SI 2015/637 art2;
# SSI 2015/108 art2. Older-contract exceptions and transition credits are
# outside these snapshots. Country remains a proxy for the land's location.
@pytest.fixture(scope="module")
def raw_scottish_transaction_parameters():
    root = Path(policyengine_uk.__file__).parent / "parameters/gov"
    return (
        ParameterNode("stamp_duty", directory_path=str(root / "hmrc/stamp_duty")),
        ParameterNode("lbtt", directory_path=str(root / "revenue_scotland/lbtt")),
    )


class JurisdictionHouseholds:
    """Use the production Country enum and require the anchored YEAR period."""

    def __init__(self, expected_period, allow_country=True):
        from policyengine_uk.variables.household.demographic.country import Country

        self.country = Country.encode(
            np.array(["SCOTLAND", "ENGLAND", "NORTHERN_IRELAND", "WALES", "UNKNOWN"])
        )
        self.expected_period = expected_period
        self.allow_country = allow_country

    def __call__(self, variable, period):
        assert self.allow_country, "Inactive LBTT must return before reading country"
        assert variable == "country"
        assert period == self.expected_period
        return self.country

    def filled_array(self, value):
        return np.full(self.country.shape, value, dtype=bool)


def raw_jurisdiction_inputs(raw_parameters, effective_date, abolish=False):
    from policyengine_core.periods import Instant, Period, YEAR

    stamp_duty, lbtt = raw_parameters
    if abolish:
        stamp_duty = stamp_duty.clone()
        stamp_duty.abolish.update(period="2014", value=True)
    # Call the liability formula directly with a real YEAR anchored on the
    # legal date. An annual simulation separately samples Jan/Apr law; this
    # unit snapshot does not introduce a transaction-date API.
    anchored = Period(
        (
            YEAR,
            Instant((effective_date.year, effective_date.month, effective_date.day)),
            1,
        )
    )
    parameters = SimpleNamespace(
        gov=SimpleNamespace(
            hmrc=SimpleNamespace(stamp_duty=stamp_duty(effective_date.isoformat())),
            revenue_scotland=SimpleNamespace(lbtt=lbtt(effective_date.isoformat())),
        )
    )

    def at_period(period):
        assert period == anchored
        return parameters

    return anchored, parameters, at_period


@pytest.mark.parametrize(
    "effective_date,sdlt_in_scotland,lbtt_in_effect",
    [
        (date(2003, 11, 30), False, False),
        (date(2003, 12, 1), True, False),
        (date(2015, 3, 31), True, False),
        (date(2015, 4, 1), False, True),
    ],
    ids=["sdlt-commencement-eve", "sdlt-commencement", "switch-eve", "switch-day"],
)
def test_raw_scottish_dates_run_both_production_liability_gates(
    raw_scottish_transaction_parameters,
    effective_date,
    sdlt_in_scotland,
    lbtt_in_effect,
):
    from policyengine_uk.variables.gov.hmrc.sdlt_liable import sdlt_liable
    from policyengine_uk.variables.gov.revenue_scotland.lbtt_liable import lbtt_liable

    anchored, parameters, at_period = raw_jurisdiction_inputs(
        raw_scottish_transaction_parameters, effective_date
    )
    assert bool(parameters.gov.hmrc.stamp_duty.applies_in_scotland) is sdlt_in_scotland
    assert bool(parameters.gov.revenue_scotland.lbtt.in_effect) is lbtt_in_effect
    households = JurisdictionHouseholds(anchored)
    np.testing.assert_array_equal(
        sdlt_liable.formula(households, anchored, at_period),
        [sdlt_in_scotland, True, True, True, False],
    )
    np.testing.assert_array_equal(
        lbtt_liable.formula(households, anchored, at_period),
        [lbtt_in_effect, False, False, False, False],
    )


def test_inactive_raw_lbtt_does_not_read_country(raw_scottish_transaction_parameters):
    from policyengine_uk.variables.gov.revenue_scotland.lbtt_liable import lbtt_liable

    anchored, _, at_period = raw_jurisdiction_inputs(
        raw_scottish_transaction_parameters, date(2014, 1, 1)
    )
    np.testing.assert_array_equal(
        lbtt_liable.formula(
            JurisdictionHouseholds(anchored, allow_country=False), anchored, at_period
        ),
        [False, False, False, False, False],
    )


def test_raw_sdlt_abolition_includes_historical_scotland(
    raw_scottish_transaction_parameters,
):
    from policyengine_uk.variables.gov.hmrc.sdlt_liable import sdlt_liable

    anchored, _, at_period = raw_jurisdiction_inputs(
        raw_scottish_transaction_parameters, date(2014, 1, 1), abolish=True
    )
    np.testing.assert_array_equal(
        sdlt_liable.formula(JurisdictionHouseholds(anchored), anchored, at_period),
        [False, False, False, False, False],
    )


def scottish_purchase_world(year, regions):
    situation = {"people": {}, "benunits": {}, "households": {}}
    for index, region in enumerate(regions):
        person = f"person{index}"
        situation["people"][person] = {"age": {year: 40}}
        situation["benunits"][f"benunit{index}"] = {"members": [person]}
        situation["households"][f"household{index}"] = {
            "members": [person],
            "region": {year: region},
            "main_residential_property_purchased": {year: 300_000},
            "main_residential_property_purchased_is_first_home": {year: False},
        }
    return situation


@pytest.mark.parametrize(
    "year,expected_sdlt,expected_lbtt",
    [(2014, 9_000, 0), (2015, 0, 4_600), (2026, 0, 4_600)],
)
def test_scottish_final_transaction_taxes_use_the_ordinary_annual_snapshot(
    year, expected_sdlt, expected_lbtt
):
    from policyengine_uk import Simulation

    # FA 2003 s55 Table A: £300,000 * 3% = £9,000 in January 2014.
    # SSI 2015/126 Table A: £105,000 * 2% + £50,000 * 5% = £4,600.
    # Annual 2015 samples 30 April, after the ordinary 1 April switch.
    simulation = Simulation(situation=scottish_purchase_world(year, ["SCOTLAND"]))
    sdlt = simulation.calculate("stamp_duty_land_tax", year)
    lbtt = simulation.calculate("land_and_buildings_transaction_tax", year)
    np.testing.assert_allclose(sdlt, [expected_sdlt], rtol=0, atol=0.01)
    np.testing.assert_allclose(lbtt, [expected_lbtt], rtol=0, atol=0.01)
    np.testing.assert_allclose(
        sdlt + lbtt, [expected_sdlt + expected_lbtt], rtol=0, atol=0.01
    )
    np.testing.assert_array_equal(
        simulation.calculate("sdlt_liable", year), [year == 2014]
    )
    np.testing.assert_array_equal(
        simulation.calculate("lbtt_liable", year), [year >= 2015]
    )


def test_2014_final_taxes_preserve_mixed_country_and_unknown_controls():
    from policyengine_uk import Simulation

    regions = ["SCOTLAND", "LONDON", "NORTHERN_IRELAND", "WALES", "UNKNOWN"]
    simulation = Simulation(situation=scottish_purchase_world(2014, regions))
    np.testing.assert_allclose(
        simulation.calculate("stamp_duty_land_tax", 2014),
        [9_000, 9_000, 9_000, 9_000, 0],
        rtol=0,
        atol=0.01,
    )
    np.testing.assert_array_equal(
        simulation.calculate("land_and_buildings_transaction_tax", 2014),
        [0, 0, 0, 0, 0],
    )
