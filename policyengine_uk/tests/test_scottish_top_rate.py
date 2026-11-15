"""Scottish top-rate income starts at £125,140 of taxable income (#2130).

Each year's taxable-income bands come independently from its Scottish Rate
Resolution, rather than the model's parameter tree:

* 2024-25: https://www.parliament.scot/chamber-and-committees/votes-and-motions/S6M-12252
* 2025-26: https://www.parliament.scot/chamber-and-committees/votes-and-motions/S6M-16531
* 2026-27: https://www.parliament.scot/chamber-and-committees/votes-and-motions/S6M-20844

The £12,570 personal allowance is withdrawn by £1 for every £2 of adjusted
net income over £100,000 (ITA 2007 s.35), reaching zero at £125,140. It
therefore cannot be subtracted from the £125,140 top-rate limit. The lower
limits, including £62,430 at the advanced rate, are reached with an intact
allowance. These MOCK situations contain employment income only: no survey
data, pension relief, Gift Aid or tax-band classification is involved.
"""

import numpy as np
import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

THRESHOLDS = {
    2024: (0, 2_306, 13_991, 31_092, 62_430, 125_140),
    2025: (0, 2_827, 14_921, 31_092, 62_430, 125_140),
    2026: (0, 3_967, 16_956, 31_092, 62_430, 125_140),
}
RATES = (0.19, 0.20, 0.21, 0.42, 0.45, 0.48)
TOP_LIMIT = 125_140


@pytest.fixture(scope="module")
def template():
    # The examples never modify the tax-benefit system. Reuse it while each
    # clone rebuilds its own small population and calculation caches.
    return Simulation(situation={"people": {"template": {"age": {2026: 45}}}})


def simulate(template, year, wages):
    people = {
        f"p{i}": {
            "age": {year: 45},
            "employment_income": {year: float(wage)},
            "employee_pension_contributions": {year: 0},
            "employer_pension_contributions": {year: 0},
        }
        for i, wage in enumerate(wages)
    }
    simulation = template.clone(clone_tax_benefit_system=False)
    simulation.build_from_situation(
        {
            "people": people,
            "benunits": {f"b_{p}": {"members": [p]} for p in people},
            "households": {
                f"h_{p}": {"members": [p], "region": {year: "SCOTLAND"}} for p in people
            },
        }
    )
    simulation.input_variables = simulation.get_known_variables()
    simulation.calculated_periods = []
    return {
        name: np.asarray(simulation.calculate(name, year), dtype=float)
        for name in ("earned_taxable_income", "earned_income_tax", "income_tax")
    }


def taxable_pay(wage):
    # s.35 rounds a non-whole-pound allowance up to the next whole pound.
    allowance = max(0, np.ceil(12_570 - max(0, wage - 100_000) / 2))
    return max(0, wage - allowance)


def statutory_tax(year, taxable):
    limits = THRESHOLDS[year]
    return sum(
        rate * max(0, min(taxable, upper) - lower)
        for lower, upper, rate in zip(limits, (*limits[1:], float("inf")), RATES)
    )


def assert_statutory_tax(year, wages, values):
    taxable = [taxable_pay(wage) for wage in wages]
    np.testing.assert_allclose(values["earned_taxable_income"], taxable, atol=0.01)
    expected = [statutory_tax(year, amount) for amount in taxable]
    for name in ("earned_income_tax", "income_tax"):
        np.testing.assert_allclose(values[name], expected, rtol=0, atol=0.02)


@pytest.mark.parametrize("year", THRESHOLDS)
def test_scottish_120000_of_pay_has_no_top_rate_tax(template, year):
    values = simulate(template, year, [120_000])
    assert_statutory_tax(year, [120_000], values)
    # All taxable pay is below the top limit; subtracting its statutory tax
    # leaves no tax charge attributable to the 48% band.
    lower_band_tax = statutory_tax(year, taxable_pay(120_000))
    assert values["earned_income_tax"][0] - lower_band_tax == pytest.approx(0, abs=0.01)


@pytest.mark.parametrize("year", THRESHOLDS)
def test_scottish_150000_of_pay_has_24860_taxed_at_48_percent(template, year):
    values = simulate(template, year, [150_000])
    assert_statutory_tax(year, [150_000], values)
    # Once all lower bands are full, the remaining tax is exactly the
    # liability on £150,000 - £125,140 at 48% (allowing float32 rounding).
    lower_band_tax = statutory_tax(year, TOP_LIMIT)
    top_rate_income = (values["earned_income_tax"][0] - lower_band_tax) / 0.48
    assert top_rate_income == pytest.approx(24_860, abs=0.02)


@pytest.mark.parametrize("year", THRESHOLDS)
def test_scottish_band_boundaries_are_continuous(template, year):
    # Lower bands retain the full PA. At the top limit it is fully withdrawn.
    boundaries = [limit + 12_570 for limit in THRESHOLDS[year][:-1]] + [TOP_LIMIT]
    wages = [wage + offset for wage in boundaries for offset in (-1, 0, 1)]
    values = simulate(template, year, wages)
    assert_statutory_tax(year, wages, values)
    tax = values["income_tax"].reshape(-1, 3)
    taxable = values["earned_taxable_income"].reshape(-1, 3)
    for band, (tax_row, taxable_row) in enumerate(zip(tax, taxable)):
        left_rate = RATES[band - 1] if band else 0
        right_rate = RATES[band]
        assert tax_row[1] - tax_row[0] == pytest.approx(
            left_rate * (taxable_row[1] - taxable_row[0]), abs=0.01
        )
        assert tax_row[2] - tax_row[1] == pytest.approx(
            right_rate * (taxable_row[2] - taxable_row[1]), abs=0.01
        )


@settings(max_examples=25, deadline=None, derandomize=True, database=None)
@given(
    year=st.sampled_from(tuple(THRESHOLDS)),
    high_pay=st.integers(TOP_LIMIT, 500_000),
    increase=st.integers(1, 100_000),
    below_top_pay=st.integers(116_761, TOP_LIMIT - 1),
)
@example(year=2024, high_pay=125_140, increase=1, below_top_pay=120_000)
@example(year=2025, high_pay=150_000, increase=1_000, below_top_pay=125_139)
@example(year=2026, high_pay=125_140, increase=1, below_top_pay=120_000)
def test_scottish_tax_is_monotone_and_48_percent_only_above_top_limit(
    template, year, high_pay, increase, below_top_pay
):
    wages = [high_pay, high_pay + increase, below_top_pay, below_top_pay + 1]
    values = simulate(template, year, wages)
    assert_statutory_tax(year, wages, values)
    tax = values["income_tax"]
    taxable = values["earned_taxable_income"]
    assert tax[1] >= tax[0]
    assert tax[1] - tax[0] == pytest.approx(0.48 * increase, abs=0.05)
    assert taxable[0] >= TOP_LIMIT
    assert taxable[3] <= TOP_LIMIT
    # Below £125,140 of taxable income, this interval remains at 45%,
    # including pay of £120,000 that main incorrectly charged at 48%.
    assert tax[3] - tax[2] == pytest.approx(0.45 * (taxable[3] - taxable[2]), abs=0.01)
