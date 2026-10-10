"""Property-based tests for pension contributions relief and the annual
allowance charge (issue #2237).

Relief runs to the annual limit in FA 2004 s. 190 (the greater of relevant UK
earnings and the basic amount), not to the annual allowance. The annual
allowance charge (s. 227) then taxes the pension input amount above the
allowance, plus any unused allowance brought forward (s. 228A), as the top
slice of reduced net income at the non-savings rates (s. 227(4A)), or the
Scottish rates with the starter band at the Scottish basic rate (s. 227(4AA)).

Invariants, for any generated population of single adults:

1. Relief bounds: relief is the lesser of the contributions and the s. 190
   limit for anyone under 75, and nil at 75 or over.
2. The excess is taxed once: raising contributions, up to relevant earnings,
   never raises income tax by more than it raises the charge. So income tax
   before the charge never rises with contributions.
3. No double taxation: for someone whose income is all non-savings income,
   contributing more than the allowance, up to relevant earnings, never costs
   more income tax than contributing up to the allowance.
4. Charge bounds: nil exactly when the chargeable amount is nil, and between
   the lowest and highest rate charged times the chargeable amount.
5. Differential: the charge equals an independent band-by-band sum of the
   chargeable amount stacked on reduced net income.
6. Carry-forward: unused allowance reduces the chargeable amount one for one
   until it is nil, and never raises the charge.

Invariant 3 is restricted to non-savings income. With dividends on top, the
relief comes off non-savings income and lets dividends fall to lower dividend
rates, while s. 227(4A) charges the excess at the non-savings rates, so income
tax can rise (intended: that is what the statute does). It also stops where
contributions use up income after allowances: relief beyond that is worth
nothing, while the charge still falls on the whole input amount (also
intended).
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

PROPERTY_SETTINGS = settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
# 2020: £40,000 allowance, £4,000 tapered minimum. 2024: £60,000 allowance.
# 2026: Scottish starter band present; 2027: property income rates.
YEARS = [2020, 2024, 2026, 2027]
REGIONS = ["LONDON", "NORTH_EAST", "WALES", "SCOTLAND"]
TOLERANCE = 0.01

person_strategy = st.fixed_dictionaries(
    {
        "age": st.integers(18, 80),
        "employment_income": st.integers(0, 400_000),
        "self_employment_income": st.integers(-20_000, 200_000),
        "employer_pension_contributions": st.integers(0, 80_000),
        "contribution_share": st.floats(0, 1.2),
        "savings_interest_income": st.integers(0, 30_000),
        "dividend_income": st.integers(0, 80_000),
        "unused_pension_annual_allowance": st.integers(0, 120_000),
        "region": st.sampled_from(REGIONS),
    }
)
population_strategy = st.lists(person_strategy, min_size=4, max_size=12)


def _situation(people, year, overrides=None):
    overrides = overrides or {}
    situation = {"people": {}, "benunits": {}, "households": {}}
    for i, person in enumerate(people):
        name = f"p{i}"
        values = {**person, **overrides.get(i, {})}
        situation["people"][name] = {
            key: {year: values[key]}
            for key in [
                "age",
                "employment_income",
                "self_employment_income",
                "employer_pension_contributions",
                "personal_pension_contributions",
                "savings_interest_income",
                "dividend_income",
                "unused_pension_annual_allowance",
            ]
        }
        situation["benunits"][f"b{i}"] = {"members": [name]}
        situation["households"][f"h{i}"] = {
            "members": [name],
            "region": {year: values["region"]},
        }
    return situation


def _relevant_earnings(person):
    return person["employment_income"] + max(0, person["self_employment_income"])


def _with_contributions(people, contributions):
    return [
        {**person, "personal_pension_contributions": float(c)}
        for person, c in zip(people, contributions)
    ]


def _calc(people, year, variables):
    sim = Simulation(situation=_situation(people, year))
    return {v: np.array(sim.calculate(v, year), dtype=float) for v in variables}


def _base_contributions(people):
    return [p["contribution_share"] * max(_relevant_earnings(p), 3_600) for p in people]


@PROPERTY_SETTINGS
@given(population_strategy, st.sampled_from(YEARS))
def test_relief_is_the_section_190_limit(people, year):
    people = _with_contributions(people, _base_contributions(people))
    out = _calc(people, year, ["pension_contributions_relief"])
    basic_amount = 3_600
    for i, person in enumerate(people):
        limit = max(_relevant_earnings(person), basic_amount)
        expected = (
            min(person["personal_pension_contributions"], limit)
            if person["age"] < 75
            else 0
        )
        assert abs(out["pension_contributions_relief"][i] - expected) < TOLERANCE


@PROPERTY_SETTINGS
@given(population_strategy, st.sampled_from(YEARS), st.floats(0, 1))
def test_extra_contributions_never_raise_tax_by_more_than_the_charge(
    people, year, step
):
    # Two contribution levels, both within relevant earnings.
    earnings = np.array([max(_relevant_earnings(p), 3_600) for p in people])
    low = np.array([min(p["contribution_share"], 1) for p in people]) * earnings
    high = low + step * (earnings - low)
    variables = ["income_tax", "personal_pension_contributions_tax"]
    before = _calc(_with_contributions(people, low), year, variables)
    after = _calc(_with_contributions(people, high), year, variables)
    tax_rise = after["income_tax"] - before["income_tax"]
    charge_rise = (
        after["personal_pension_contributions_tax"]
        - before["personal_pension_contributions_tax"]
    )
    assert np.all(tax_rise <= charge_rise + TOLERANCE)


@PROPERTY_SETTINGS
@given(population_strategy, st.sampled_from(YEARS), st.floats(0, 1))
def test_contributions_above_the_allowance_are_not_taxed_twice(people, year, step):
    # Non-savings income only, under 75, no carry-forward: contributions of
    # exactly the allowance (net of employer contributions) against any
    # amount from there up to relevant earnings.
    people = [
        {
            **p,
            "age": min(p["age"], 74),
            "savings_interest_income": 0,
            "dividend_income": 0,
            "unused_pension_annual_allowance": 0,
        }
        for p in people
    ]
    zero_sim = Simulation(
        situation=_situation(_with_contributions(people, [0] * len(people)), year)
    )
    allowance = np.array(
        zero_sim.calculate("pension_annual_allowance", year), dtype=float
    )
    # Income after allowances with no contributions. Relief beyond it is worth
    # nothing, but the charge still falls on the input amount, so the
    # comparison stops there as well as at relevant earnings.
    taxable_income = np.maximum(
        0,
        np.array(zero_sim.calculate("adjusted_net_income", year), dtype=float)
        - np.array(zero_sim.calculate("allowances", year), dtype=float),
    )
    earnings = np.array([_relevant_earnings(p) for p in people], dtype=float)
    upper = np.minimum(earnings, taxable_income)
    employer = np.array([p["employer_pension_contributions"] for p in people])
    at_allowance = np.clip(allowance - employer, 0, earnings)
    above = at_allowance + step * np.maximum(0, upper - at_allowance)
    tax_at = _calc(_with_contributions(people, at_allowance), year, ["income_tax"])
    tax_above = _calc(_with_contributions(people, above), year, ["income_tax"])
    assert np.all(tax_above["income_tax"] <= tax_at["income_tax"] + TOLERANCE)


def _reference_charge(chargeable, reduced_net_income, thresholds, rates):
    """Band-by-band sum of the chargeable amount stacked on income."""
    bottom = reduced_net_income
    top = reduced_net_income + chargeable
    upper = list(thresholds[1:]) + [np.inf]
    charge = 0.0
    for lower, upper_limit, rate in zip(thresholds, upper, rates):
        charge += rate * max(0.0, min(top, upper_limit) - max(bottom, lower))
    return charge


@PROPERTY_SETTINGS
@given(population_strategy, st.sampled_from(YEARS))
def test_charge_matches_band_by_band_reference(people, year):
    people = _with_contributions(people, _base_contributions(people))
    sim = Simulation(situation=_situation(people, year))
    chargeable = np.array(
        sim.calculate("pension_annual_allowance_chargeable_amount", year), dtype=float
    )
    charge = np.array(
        sim.calculate("personal_pension_contributions_tax", year), dtype=float
    )
    reduced_net_income = np.maximum(
        0,
        np.array(sim.calculate("adjusted_net_income", year), dtype=float)
        - np.array(sim.calculate("allowances", year), dtype=float),
    )
    scottish = np.array(sim.calculate("pays_scottish_income_tax", year))
    rates = sim.tax_benefit_system.parameters(year).gov.hmrc.income_tax.rates
    uk_thresholds, uk_rates = list(rates.uk.thresholds), list(rates.uk.rates)
    sco_thresholds = list(rates.scotland.rates.thresholds)
    sco_rates = list(rates.scotland.rates.rates)
    if year >= 2018:
        # s. 227(4AA): the starter band is charged at the Scottish basic rate.
        sco_rates[0] = sco_rates[1]
    for i in range(len(people)):
        thresholds, band_rates = (
            (sco_thresholds, sco_rates) if scottish[i] else (uk_thresholds, uk_rates)
        )
        expected = _reference_charge(
            chargeable[i], reduced_net_income[i], thresholds, band_rates
        )
        assert abs(charge[i] - expected) < TOLERANCE
        # Bounds: nil exactly when nothing is chargeable, and between the
        # lowest and highest rate charged.
        assert (charge[i] == 0) == (chargeable[i] == 0)
        assert charge[i] >= min(band_rates) * chargeable[i] - TOLERANCE
        assert charge[i] <= max(band_rates) * chargeable[i] + TOLERANCE


@PROPERTY_SETTINGS
@given(population_strategy, st.sampled_from(YEARS), st.integers(0, 150_000))
def test_unused_allowance_reduces_chargeable_amount_one_for_one(people, year, extra):
    people = _with_contributions(people, _base_contributions(people))
    variables = [
        "pension_annual_allowance_chargeable_amount",
        "personal_pension_contributions_tax",
    ]
    before = _calc(people, year, variables)
    more_unused = [
        {
            **p,
            "unused_pension_annual_allowance": p["unused_pension_annual_allowance"]
            + extra,
        }
        for p in people
    ]
    after = _calc(more_unused, year, variables)
    chargeable_before = before["pension_annual_allowance_chargeable_amount"]
    expected = np.maximum(0, chargeable_before - extra)
    assert np.allclose(
        after["pension_annual_allowance_chargeable_amount"], expected, atol=TOLERANCE
    )
    assert np.all(
        after["personal_pension_contributions_tax"]
        <= before["personal_pension_contributions_tax"] + TOLERANCE
    )
