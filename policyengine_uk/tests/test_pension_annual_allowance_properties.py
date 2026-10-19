"""Property-based tests for pension contributions relief and the annual
allowance charge (issue #2237).

Relief runs to the annual limit in FA 2004 s. 190 (relevant UK earnings,
raised to the basic amount where lower, the increase only through relief at
source, s. 191(7)), not to the annual allowance. The model takes personal
pension contributions as relief at source and employee contributions as a net
pay arrangement. The annual allowance charge (s. 227) then taxes the pension
input amount above the allowance, plus any unused allowance brought forward
(s. 228A), as the top slice of reduced net income at the non-savings rates
(s. 227(4A)), with the rate limits raised by qualifying relief-at-source contributions
(ss. 192(4)/(4A), 227(4C)) and grossed-up Gift Aid, or at the Scottish rates with the
starter band at the Scottish basic rate (s. 227(4AA)).

Invariants, for any generated population of single adults with contributions
split between relief at source and net pay:

1. Relief bounds: relief is the lesser of the contributions and the s. 190
   limit (the basic-amount increase capped at relief-at-source contributions)
   for anyone under 75, and nil at 75 or over.
2. The excess is taxed once: raising contributions, up to relevant earnings,
   never raises income tax by more than it raises the charge. So income tax
   before the charge never rises with contributions.
3. With non-savings income only and stable eligibility for any RAS band
   extension, contributions above the allowance up to relevant earnings never
   cost more income tax than contributing up to the allowance.
4. Charge bounds: nil exactly when the chargeable amount is nil, and between
   the lowest and highest rate charged times the chargeable amount.
5. Differential: the charge equals an independent band-by-band sum of the
   chargeable amount stacked on reduced net income.
6. Carry-forward: unused allowance reduces the chargeable amount one for one
   until it is nil, and never raises the charge.
7. With stable RAS extension eligibility, Gift Aid never raises income tax,
   including when contributions exceed relevant earnings or the allowance.
   Its s. 58 adjusted-net-income deduction does not reduce reduced net income.

Invariant 3 requires the s.192 condition to hold at both contribution levels
when there are RAS contributions. The excess can enter higher bands while
ordinary income remains below higher rate, and s.227(5) excludes that excess
from the condition. Total tax can then rise without double taxation. Gift Aid
can also remove ordinary higher-rate liability and thus RAS band extension,
so invariant 7 compares only cases with the same eligibility at each gift.

Invariant 3 is also restricted to non-savings income. With dividends on top, the
relief comes off non-savings income and lets dividends fall to lower dividend
rates, while s. 227(4A) charges the excess at the non-savings rates, so income
tax can rise (intended: that is what the statute does). It also stops where
contributions use up income after allowances: relief beyond that is worth
nothing, while the charge still falls on the whole input amount (also
intended). And it is restricted to taxpayers outside Scotland. The model gives
relief at source as a deduction, which relieves a Scottish starter-rate slice
at 19%, while the charge on that slice is at the Scottish basic rate
(s. 227(4AA)), so income tax can rise by up to 1% of the starter band
(a model deviation: relief at source pays 20%; see the YAML example).
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, example, given, settings
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
# Simulated values are float32: allow a relative error on large amounts.
RELATIVE_TOLERANCE = 1e-6


def _close(actual, expected):
    return abs(actual - expected) <= max(TOLERANCE, RELATIVE_TOLERANCE * abs(expected))


person_strategy = st.fixed_dictionaries(
    {
        "age": st.integers(18, 80),
        "employment_income": st.integers(0, 400_000),
        "self_employment_income": st.integers(-20_000, 200_000),
        "employer_pension_contributions": st.integers(0, 80_000),
        "contribution_share": st.floats(0, 1.2),
        # Share of contributions paid through a net pay arrangement.
        "net_pay_share": st.sampled_from([0.0, 0.5, 1.0]),
        "gift_aid": st.integers(0, 5_000),
        "savings_interest_income": st.integers(0, 30_000),
        "dividend_income": st.integers(0, 80_000),
        "unused_pension_annual_allowance": st.integers(0, 120_000),
        "region": st.sampled_from(REGIONS),
    }
)
population_strategy = st.lists(person_strategy, min_size=4, max_size=12)


@st.composite
def reference_population_strategy(draw):
    people = [
        {**person, "property_income": draw(st.integers(0, 80_000))}
        for person in draw(population_strategy)
    ]
    # Unrestricted draws rarely combine a positive RAS charge with ordinary
    # income below higher rate. Include generated people on either side of
    # that condition in every population, with enough excess to cross a limit
    # whose extension changes the charge.
    for income in [
        draw(st.integers(38_000, 45_000)),
        draw(st.integers(60_000, 70_000)),
    ]:
        people.append(
            {
                "age": draw(st.integers(18, 74)),
                "employment_income": income,
                "self_employment_income": 0,
                "employer_pension_contributions": draw(st.integers(60_000, 80_000)),
                "contribution_share": draw(st.floats(0.5, 0.75)),
                "net_pay_share": 0.0,
                "gift_aid": draw(st.integers(0, 2_000)),
                "savings_interest_income": 0,
                "dividend_income": 0,
                "property_income": 0,
                "unused_pension_annual_allowance": 0,
                "region": "LONDON",
            }
        )
    return people


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
                "employee_pension_contributions_reported",
                "gift_aid",
                "savings_interest_income",
                "dividend_income",
                "unused_pension_annual_allowance",
            ]
        }
        situation["people"][name]["property_income"] = {
            year: values.get("property_income", 0)
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
        {
            **person,
            "personal_pension_contributions": float(c) * (1 - person["net_pay_share"]),
            "employee_pension_contributions_reported": float(c)
            * person["net_pay_share"],
        }
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
        earnings = _relevant_earnings(person)
        relief_at_source = person["personal_pension_contributions"]
        total = relief_at_source + person["employee_pension_contributions_reported"]
        limit = earnings + min(max(0, basic_amount - earnings), relief_at_source)
        expected = min(total, limit) if person["age"] < 75 else 0
        relief = out["pension_contributions_relief"][i]
        assert _close(relief, expected)
        assert relief <= max(earnings, basic_amount) + max(
            TOLERANCE, RELATIVE_TOLERANCE * max(earnings, basic_amount)
        )


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
    slack = TOLERANCE + RELATIVE_TOLERANCE * np.maximum(
        abs(before["income_tax"]), abs(after["income_tax"])
    )
    assert np.all(tax_rise <= charge_rise + slack)


@PROPERTY_SETTINGS
@example(
    people=[
        {
            "age": 45,
            "employment_income": 150_000,
            "self_employment_income": 0,
            "employer_pension_contributions": 0,
            "contribution_share": 0.0,
            "net_pay_share": net_pay_share,
            "gift_aid": 0,
            "savings_interest_income": 0,
            "dividend_income": 0,
            "unused_pension_annual_allowance": 0,
            "region": "LONDON",
        }
        for net_pay_share in (0.0, 0.0, 1.0, 1.0)
    ],
    year=2024,
    step=1.0,
)
@example(
    people=[
        {
            "age": 54,
            "employment_income": 362_880,
            "self_employment_income": 5_249,
            "employer_pension_contributions": 60_817,
            "contribution_share": 1.0294618785360077,
            "net_pay_share": 1.0,
            "gift_aid": 2_629,
            "savings_interest_income": 64,
            "dividend_income": 8_818,
            "unused_pension_annual_allowance": 96_126,
            "region": "LONDON",
        }
    ],
    year=2020,
    step=0.5420285667238235,
)
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
            "property_income": 0,
            "unused_pension_annual_allowance": 0,
            "region": "NORTH_EAST" if p["region"] == "SCOTLAND" else p["region"],
        }
        for p in people
    ]
    zero_sim = Simulation(
        situation=_situation(_with_contributions(people, [0] * len(people)), year)
    )
    allowance = np.array(
        zero_sim.calculate("pension_annual_allowance", year), dtype=float
    )
    income_tax = zero_sim.tax_benefit_system.parameters(year).gov.hmrc.income_tax
    # Contributions can restore the full personal allowance as ANI falls.
    # Retain the other allowances from zero contributions, but reserve the
    # year's full PA so relief remains valuable throughout the comparison.
    # Beyond that income, the charge still falls on the full input amount.
    restored_allowances = (
        np.array(zero_sim.calculate("allowances", year), dtype=float)
        - np.array(zero_sim.calculate("personal_allowance", year), dtype=float)
        + float(income_tax.allowances.personal_allowance.amount)
    )
    taxable_income = np.maximum(
        0,
        np.array(zero_sim.calculate("net_income", year), dtype=float)
        - restored_allowances,
    )
    earnings = np.array([_relevant_earnings(p) for p in people], dtype=float)
    upper = np.minimum(earnings, taxable_income)
    employer = np.array([p["employer_pension_contributions"] for p in people])
    at_allowance = np.clip(allowance - employer, 0, earnings)
    above = at_allowance + step * np.maximum(0, upper - at_allowance)
    variables = [
        "income_tax",
        "net_income",
        "allowances",
        "personal_pension_contributions",
        "pension_contributions_relief",
        "gift_aid_grossed_up",
    ]
    tax_at = _calc(_with_contributions(people, at_allowance), year, variables)
    tax_above = _calc(_with_contributions(people, above), year, variables)
    basic_limit = float(income_tax.rates.uk.thresholds[1])

    def qualifies_for_ras_extension(out):
        ras = np.minimum(
            out["personal_pension_contributions"], out["pension_contributions_relief"]
        )
        ordinary_income = np.maximum(
            0, out["net_income"] - np.maximum(0, out["allowances"] - ras)
        )
        return ordinary_income > basic_limit + out["gift_aid_grossed_up"]

    net_pay_only = np.array([p["net_pay_share"] == 1 for p in people])
    applicable = net_pay_only | (
        qualifies_for_ras_extension(tax_at) & qualifies_for_ras_extension(tax_above)
    )
    slack = TOLERANCE + RELATIVE_TOLERANCE * np.maximum(
        abs(tax_at["income_tax"]), abs(tax_above["income_tax"])
    )
    assert np.all(
        tax_above["income_tax"][applicable]
        <= (tax_at["income_tax"] + slack)[applicable]
    )


def _reference_charge(chargeable, reduced_net_income, thresholds, rates, extension):
    """Band-by-band sum with rate limits raised by the eligible extension."""
    bottom = reduced_net_income
    top = reduced_net_income + chargeable
    lowers = [thresholds[0]] + [t + extension for t in thresholds[1:]]
    uppers = lowers[1:] + [np.inf]
    charge = 0.0
    for lower, upper_limit, rate in zip(lowers, uppers, rates):
        charge += rate * max(0.0, min(top, upper_limit) - max(bottom, lower))
    return charge


def _reference_ras_extension_eligibility(
    reduced_net_income,
    savings,
    dividends,
    gross_gift,
    scottish,
    income_tax,
    year,
    property_income=0,
):
    """Find an ordinary income slice taxed above basic, apart from s.192.

    Section 192(4) names the higher and additional rates, excluding dividend
    rates, savings rates from 2017 and rUK property rates from 2027. Scottish
    property still bears Scottish rates and can meet s.192(4A). The annual
    allowance excess never enters these ordinary income slices (s.227(5)).
    """
    non_savings = max(0, reduced_net_income - savings - dividends)
    savings_top = max(0, reduced_net_income - dividends)
    if scottish:
        scale = income_tax.rates.scotland.rates
        # These generated years all have the starter band before basic.
        basic_rate = float(scale.rates[1] if year >= 2018 else scale.rates[0])
        slices = [(0, non_savings)]
    else:
        scale = income_tax.rates.uk
        basic_rate = float(scale.rates[0])
        ordinary_rates_top = max(
            0, non_savings - (property_income if year >= 2027 else 0)
        )
        slices = [(0, ordinary_rates_top)]
        if year < 2017:
            psa = income_tax.allowances.personal_savings_allowance
            if reduced_net_income > scale.thresholds[2] + gross_gift:
                savings_allowance = float(psa.additional)
            elif reduced_net_income > scale.thresholds[1] + gross_gift:
                savings_allowance = float(psa.higher)
            else:
                savings_allowance = float(psa.basic)
            starting_rate_savings = max(
                0, income_tax.rates.savings_starter_rate.allowance - non_savings
            )
            nil_savings = min(
                savings_top - non_savings, starting_rate_savings + savings_allowance
            )
            slices.append((non_savings + nil_savings, savings_top))
    for index, (threshold, rate) in enumerate(zip(scale.thresholds, scale.rates)):
        if rate <= basic_rate:
            continue
        lower = threshold + gross_gift
        upper = (
            scale.thresholds[index + 1] + gross_gift
            if index + 1 < len(scale.thresholds)
            else np.inf
        )
        for bottom, top in slices:
            if min(top, upper) > max(bottom, lower):
                return True
    return False


@PROPERTY_SETTINGS
@given(reference_population_strategy(), st.sampled_from(YEARS))
def test_charge_matches_band_by_band_reference(people, year):
    people = _with_contributions(people, _base_contributions(people))
    sim = Simulation(situation=_situation(people, year))
    chargeable = np.array(
        sim.calculate("pension_annual_allowance_chargeable_amount", year), dtype=float
    )
    charge = np.array(
        sim.calculate("personal_pension_contributions_tax", year), dtype=float
    )
    get = lambda v: np.array(sim.calculate(v, year), dtype=float)  # noqa: E731
    # FA 2004 s. 227(4B)-(4C), ITA 2007 ss. 23 and 58: reduced net income
    # starts before the gross Gift Aid adjustment to adjusted net income.
    # RAS stays in this base; s.192 conditions its rate-limit extension
    # on ordinary higher-rate liability apart from s.192 itself.
    relief_at_source = np.minimum(
        get("personal_pension_contributions"), get("pension_contributions_relief")
    )
    gross_gift = get("gift_aid_grossed_up")
    reduced_net_income = np.maximum(
        0,
        get("net_income") - np.maximum(0, get("allowances") - relief_at_source),
    )
    scottish = np.array(sim.calculate("pays_scottish_income_tax", year))
    rates = sim.tax_benefit_system.parameters(year).gov.hmrc.income_tax.rates
    uk_thresholds, uk_rates = list(rates.uk.thresholds), list(rates.uk.rates)
    sco_thresholds = list(rates.scotland.rates.thresholds)
    sco_rates = list(rates.scotland.rates.rates)
    if year >= 2018:
        # s. 227(4AA): the starter band is charged at the Scottish basic rate.
        sco_rates[0] = sco_rates[1]
    gate_coverage = {False: False, True: False}
    for i in range(len(people)):
        thresholds, band_rates = (
            (sco_thresholds, sco_rates) if scottish[i] else (uk_thresholds, uk_rates)
        )
        qualifies = _reference_ras_extension_eligibility(
            reduced_net_income[i],
            get("taxable_savings_interest_income")[i],
            get("taxable_dividend_income")[i],
            gross_gift[i],
            bool(scottish[i]),
            sim.tax_benefit_system.parameters(year).gov.hmrc.income_tax,
            year,
            get("taxable_property_income")[i],
        )
        extension = gross_gift[i] + (relief_at_source[i] if qualifies else 0)
        expected = _reference_charge(
            chargeable[i], reduced_net_income[i], thresholds, band_rates, extension
        )
        assert _close(charge[i], expected)
        alternative_extension = gross_gift[i] + (
            0 if qualifies else relief_at_source[i]
        )
        alternative_charge = _reference_charge(
            chargeable[i],
            reduced_net_income[i],
            thresholds,
            band_rates,
            alternative_extension,
        )
        gate_coverage[qualifies] |= not _close(expected, alternative_charge)
        # Bounds: nil exactly when nothing is chargeable, and between the
        # lowest and highest rate charged.
        assert (charge[i] == 0) == (chargeable[i] == 0)
        slack = max(TOLERANCE, RELATIVE_TOLERANCE * max(band_rates) * chargeable[i])
        assert charge[i] >= min(band_rates) * chargeable[i] - slack
        assert charge[i] <= max(band_rates) * chargeable[i] + slack

    # Both eligibility outcomes must actually affect a generated charge;
    # positive contributions alone would leave this property vacuous.
    assert all(gate_coverage.values())

    # FA 2004 ss. 227ZA and 228A: no charge within the available allowance,
    # including unused allowance from the previous three years.
    available = get("pension_annual_allowance") + np.maximum(
        0, get("unused_pension_annual_allowance")
    )
    within_allowance = get("pension_contributions_for_annual_allowance") <= available
    assert np.all(charge >= 0)
    assert np.all(charge[within_allowance] == 0)


@PROPERTY_SETTINGS
@given(population_strategy, st.sampled_from(YEARS))
def test_gift_aid_never_increases_tax_with_stable_ras_eligibility(people, year):
    people = _with_contributions(people, _base_contributions(people))
    # Compare the same pension/input amounts with zero, drawn, and larger
    # gifts, across UK and Scottish rates and mixed income sources.
    zero_gift = [{**p, "gift_aid": 0} for p in people]
    larger_gift = [{**p, "gift_aid": p["gift_aid"] + 4_000} for p in people]
    combined = zero_gift + people + larger_gift
    sim = Simulation(situation=_situation(combined, year))
    get = lambda v: np.array(sim.calculate(v, year), dtype=float)  # noqa: E731
    ras = np.minimum(
        get("personal_pension_contributions"), get("pension_contributions_relief")
    )
    reduced_net_income = np.maximum(
        0, get("net_income") - np.maximum(0, get("allowances") - ras)
    )
    p = sim.tax_benefit_system.parameters(year).gov.hmrc.income_tax
    qualifies = np.array(
        [
            _reference_ras_extension_eligibility(
                rni, savings, dividends, gift, scottish, p, year
            )
            for rni, savings, dividends, gift, scottish in zip(
                reduced_net_income,
                get("taxable_savings_interest_income"),
                get("taxable_dividend_income"),
                get("gift_aid_grossed_up"),
                sim.calculate("pays_scottish_income_tax", year),
            )
        ]
    )
    no_gift_gate, gift_gate, more_gift_gate = np.split(qualifies, 3)
    stable_gate = (no_gift_gate == gift_gate) & (gift_gate == more_gift_gate)
    before, with_gift, with_more = np.split(get("income_tax"), 3)
    slack = TOLERANCE + RELATIVE_TOLERANCE * np.maximum(abs(before), abs(with_gift))
    assert np.all(with_gift[stable_gate] <= (before + slack)[stable_gate])
    assert np.all(with_more[stable_gate] <= (with_gift + slack)[stable_gate])


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
        after["pension_annual_allowance_chargeable_amount"],
        expected,
        atol=TOLERANCE,
        rtol=RELATIVE_TOLERANCE,
    )
    slack = TOLERANCE + RELATIVE_TOLERANCE * np.maximum(
        abs(before["personal_pension_contributions_tax"]),
        abs(after["personal_pension_contributions_tax"]),
    )
    assert np.all(
        after["personal_pension_contributions_tax"]
        <= before["personal_pension_contributions_tax"] + slack
    )


def test_scottish_basic_band_is_not_lifted_when_the_starter_band_is_removed():
    """A reform that removes the Scottish starter band (null threshold, basic
    band from zero) leaves the lowest band at the basic rate: the charge is
    not lifted to the intermediate rate."""
    from policyengine_uk.utils.scenario import Scenario

    def remove_starter_band(simulation):
        system = simulation.tax_benefit_system
        system.reset_parameters()
        brackets = system.parameters.gov.hmrc.income_tax.rates.scotland.rates.brackets
        brackets[0].threshold.update(period="year:2026-01-01:1", value=None)
        brackets[1].threshold.update(period="year:2026-01-01:1", value=0)
        system.process_parameters()

    situation = {
        "people": {
            "p": {
                "age": {2026: 45},
                "employment_income": {2026: 12_570},
                "employer_pension_contributions": {2026: 70_000},
            }
        },
        "benunits": {"b": {"members": ["p"]}},
        "households": {"h": {"members": ["p"], "region": {2026: "SCOTLAND"}}},
    }
    sim = Simulation(
        situation=situation,
        scenario=Scenario(
            simulation_modifier=remove_starter_band, applied_before_data_load=True
        ),
    )
    rates = sim.tax_benefit_system.parameters(2026).gov.hmrc.income_tax.rates
    assert float(rates.scotland.rates.rates[0]) == 0.2
    # Reduced net income 0; chargeable amount 10_000, all in the basic band.
    charge = float(sim.calculate("personal_pension_contributions_tax", 2026)[0])
    assert abs(charge - 10_000 * 0.2) < TOLERANCE


def _charge_situation(year, region, **inputs):
    return {
        "people": {
            "p": {
                "age": {year: 45},
                **{key: {year: value} for key, value in inputs.items()},
            }
        },
        "benunits": {"b": {"members": ["p"]}},
        "households": {"h": {"members": ["p"], "region": {year: region}}},
    }


def test_mixed_methods_below_higher_rate_have_unextended_charge_lower_bound():
    """Either relief allocation leaves ordinary income below higher rate.

    With £50,000 earnings, at least £30,000 of £40,000 net pay must receive
    relief if all £20,000 RAS does. RNI is therefore at most £7,430. A net-pay
    allocation of £40,000 instead leaves RNI nil. Neither can meet s.192(4).
    The £70,000 excess therefore costs at least £37,700 × 20% + £32,300 × 40%.
    This does not presume a statutory ordering of net-pay and RAS relief.
    """
    sim = Simulation(
        situation=_charge_situation(
            2024,
            "LONDON",
            employment_income=50_000,
            employee_pension_contributions_reported=40_000,
            personal_pension_contributions=20_000,
            employer_pension_contributions=70_000,
        )
    )
    assert float(sim.calculate("pension_contributions_relief", 2024)[0]) == 50_000
    assert (
        float(sim.calculate("pension_annual_allowance_chargeable_amount", 2024)[0])
        == 70_000
    )
    charge = float(sim.calculate("personal_pension_contributions_tax", 2024)[0])
    assert charge >= 20_460 - TOLERANCE


@pytest.fixture
def scottish_advanced_rate_charge_simulation():
    return Simulation(
        situation=_charge_situation(
            2026,
            "SCOTLAND",
            employment_income=112_000,
            employer_pension_contributions=70_000,
        )
    )


def test_scottish_charge_uses_top_limit_parameter(
    scottish_advanced_rate_charge_simulation,
):
    """The charge follows the configured top-rate parameter."""
    sim = scottish_advanced_rate_charge_simulation
    scale = sim.tax_benefit_system.parameters(
        2026
    ).gov.hmrc.income_tax.rates.scotland.rates
    top_limit = float(scale.thresholds[-1])
    advanced_rate, top_rate = map(float, scale.rates[-2:])
    # PA £6,570; RNI £105,430; chargeable amount £10,000.
    advanced_amount = min(10_000, max(0, top_limit - 105_430))
    expected = advanced_amount * advanced_rate + (10_000 - advanced_amount) * top_rate
    charge = float(sim.calculate("personal_pension_contributions_tax", 2026)[0])
    assert charge == pytest.approx(expected, abs=TOLERANCE)


def test_scottish_charge_below_statutory_top_limit_is_all_advanced_rate(
    scottish_advanced_rate_charge_simulation,
):
    """S6M-20844: £105,430 RNI plus £10,000 excess remains below £125,140.

    https://www.parliament.scot/chamber-and-committees/votes-and-motions/S6M-20844
    """
    sim = scottish_advanced_rate_charge_simulation
    assert float(sim.calculate("personal_allowance", 2026)[0]) == 6_570
    charge = float(sim.calculate("personal_pension_contributions_tax", 2026)[0])
    assert charge == pytest.approx(4_500, abs=TOLERANCE)
