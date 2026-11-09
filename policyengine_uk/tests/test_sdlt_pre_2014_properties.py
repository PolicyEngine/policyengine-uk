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
