"""Gift Aid invariants and an independent earned-income tax calculation.

ITA 2007 s.414(2)(a)-(b) treats gifts as net of basic-rate tax and extends
the UK basic/higher limits and the Scottish basic-rate upper and higher
limits. Section 415 defines grossing up; s.58 deducts that gross gift from
adjusted net income, rather than from taxable income:
https://www.legislation.gov.uk/ukpga/2007/3/section/414
https://www.legislation.gov.uk/ukpga/2007/3/section/415
https://www.legislation.gov.uk/ukpga/2007/3/section/58

The differential integrates the model's rate schedules independently to
isolate the effect of extending limits for Gift Aid.
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

YEAR = 2026
CASES = 12
BASE_PEOPLE = 2 * CASES  # The same draws, once in rUK and once in Scotland.
PEOPLE = 3 * BASE_PEOPLE  # Zero, drawn and larger gifts for each person.
INPUTS = (
    "employment_income",
    "savings_interest_income",
    "dividend_income",
    "property_income",
)
PROPERTY_SETTINGS = settings(
    max_examples=30,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow],
)

income = st.one_of(
    st.integers(0, 300_000),
    st.floats(0, 300_000, allow_nan=False, allow_infinity=False, width=32),
    st.sampled_from([0, 12_570, 29_526, 43_662, 50_270, 100_000, 101_000, 150_000]),
)
# Multiples of four net pounds give integer gross gifts, avoiding rounding of
# Personal Allowance's statutory whole-pound taper in the random reference.
gift = st.integers(0, 10_000).map(lambda value: value * 4)
earned_cases = st.lists(st.tuples(income, gift, gift), min_size=CASES, max_size=CASES)
mixed_cases = st.lists(
    st.tuples(income, income, income, income, gift, gift),
    min_size=CASES,
    max_size=CASES,
)
basic_cases = st.lists(
    st.tuples(st.integers(0, 29_526), gift, gift),
    min_size=CASES,
    max_size=CASES,
)


def situation(rows, gifts=None):
    people = {
        f"p{i}": {
            "age": {YEAR: 40},
            **{name: {YEAR: value} for name, value in zip(INPUTS, row)},
        }
        for i, row in enumerate(rows)
    }
    if gifts is not None:
        for i, amount in enumerate(gifts):
            people[f"p{i}"]["gift_aid"] = {YEAR: amount}
    return {
        "people": people,
        "benunits": {f"b{i}": {"members": [f"p{i}"]} for i in range(len(rows))},
        "households": {
            f"h{i}": {
                "members": [f"p{i}"],
                "region": {
                    YEAR: "SCOTLAND" if i % BASE_PEOPLE >= CASES else "NORTH_WEST"
                },
            }
            for i in range(len(rows))
        },
    }


@pytest.fixture(scope="module")
def sim():
    return Simulation(situation=situation([(0, 0, 0, 0)] * PEOPLE, gifts=[0] * PEOPLE))


@pytest.fixture(scope="module")
def omitted_sim():
    return Simulation(situation=situation([(0, 0, 0, 0)] * BASE_PEOPLE))


def run(sim, drawn, *, earned_only=False):
    if earned_only:
        drawn = [(wages, 0, 0, 0, amount, extra) for wages, amount, extra in drawn]
    columns = list(map(np.array, zip(*drawn)))
    for name, values in zip(INPUTS, columns[:4]):
        # Simulation moves wage inputs to the source of its labour-supply
        # formula during initialization. Update that retained input so
        # reset_calculations does not discard the new wage draw.
        input_name = (
            "employment_income_before_lsr" if name == "employment_income" else name
        )
        sim.set_input(input_name, YEAR, np.tile(values, 6))
    amounts, extras = (np.tile(column, 2) for column in columns[-2:])
    intended_gifts = np.concatenate([np.zeros(BASE_PEOPLE), amounts, amounts + extras])
    sim.set_input("gift_aid", YEAR, intended_gifts)
    sim.reset_calculations()
    np.testing.assert_array_equal(sim.calculate("gift_aid", YEAR), intended_gifts)
    for name, values in zip(INPUTS, columns[:4]):
        np.testing.assert_array_equal(sim.calculate(name, YEAR), np.tile(values, 6))
    return {
        name: sim.calculate(name, YEAR).astype(float)
        for name in (
            *INPUTS,
            "gift_aid",
            "gift_aid_grossed_up",
            "personal_allowance",
            "adjusted_net_income",
            "income_tax",
        )
    }


def tolerance(*amounts):
    """A penny plus rounding of the model's float32 monetary values."""
    return 0.01 + 4e-7 * sum(np.abs(amount) for amount in amounts)


def reference_earned_tax(wages, gross_gift, schedule):
    """Integrate raised bands directly, without using any model tax formula.

    The Scottish starter/basic boundary stays fixed under s.414(2)(b).
    The duplicated UK top rate (an optional reform bracket) has no rate step.
    s.58 lowers ANI for the s.35 Personal Allowance taper, not taxable wages.
    """
    allowance = max(0, np.ceil(12_570 - max(0, wages - gross_gift - 100_000) / 2))
    taxable = max(0, wages - allowance)
    thresholds, rates, eligible_indices = schedule
    raised = [
        threshold + (gross_gift if i in eligible_indices else 0)
        for i, threshold in enumerate(thresholds)
    ]
    tax = 0
    for i, (lower, rate) in enumerate(zip(raised, rates)):
        upper = raised[i + 1] if i + 1 < len(raised) else float("inf")
        tax += rate * max(0, min(taxable, upper) - lower)
    return tax


def schedules(sim):
    rates = sim.tax_benefit_system.parameters(f"{YEAR}-01-01").gov.hmrc.income_tax.rates
    return (
        (rates.uk.thresholds, rates.uk.rates, {1, 2}),
        (
            rates.scotland.rates.thresholds,
            rates.scotland.rates.rates,
            set(range(2, len(rates.scotland.rates.thresholds))),
        ),
    )


@PROPERTY_SETTINGS
@given(earned_cases)
def test_earned_income_matches_independent_raised_limit_reference(sim, drawn):
    result = run(sim, drawn, earned_only=True)
    scales = schedules(sim)
    expected = np.array(
        [
            reference_earned_tax(wages, gross_gift, scales[i % BASE_PEOPLE >= CASES])
            for i, (wages, gross_gift) in enumerate(
                zip(result["employment_income"], result["gift_aid_grossed_up"])
            )
        ]
    )
    assert (
        np.abs(result["income_tax"] - expected)
        <= tolerance(expected, result["income_tax"])
    ).all()


@PROPERTY_SETTINGS
@given(mixed_cases)
def test_relief_is_never_negative_for_mixed_income(sim, drawn):
    result = run(sim, drawn)
    baseline, with_gift, _ = np.split(result["income_tax"], 3)
    assert (baseline - with_gift >= -tolerance(baseline, with_gift)).all()


@PROPERTY_SETTINGS
@given(mixed_cases)
def test_relief_is_non_decreasing_in_gift_for_mixed_income(sim, drawn):
    result = run(sim, drawn)
    _, with_gift, with_more = np.split(result["income_tax"], 3)
    assert (with_more <= with_gift + tolerance(with_gift, with_more)).all()


@PROPERTY_SETTINGS
@given(earned_cases)
def test_earned_relief_is_bounded_by_rate_steps_and_allowance_taper(sim, drawn):
    result = run(sim, drawn, earned_only=True)
    baseline, with_gift, _ = np.split(result["income_tax"], 3)
    allowance_before, allowance_after, _ = np.split(result["personal_allowance"], 3)
    _, gross_gift, _ = np.split(result["gift_aid_grossed_up"], 3)
    scales = schedules(sim)
    # All extended thresholds contribute. At £150,000, the UK 20pp and 5pp
    # steps save £250 on a £1,000 gross gift, so the largest *single* step
    # would incorrectly bound relief at £200. Sum the eligible rate steps.
    cumulative_step, top_rate = [], []
    for i in range(BASE_PEOPLE):
        _, rates, eligible = scales[i >= CASES]
        cumulative_step.append(sum(rates[j] - rates[j - 1] for j in eligible))
        top_rate.append(max(rates))
    limit = gross_gift * np.array(cumulative_step) + (
        allowance_after - allowance_before
    ) * np.array(top_rate)
    # Earned-only cases isolate this bound from jumps in the Personal Savings
    # Allowance when a moved limit changes the model's taxpayer band.
    assert (baseline - with_gift <= limit + tolerance(baseline, with_gift)).all()


@PROPERTY_SETTINGS
@given(basic_cases)
def test_no_relief_within_unextended_basic_band_below_taper(sim, drawn):
    result = run(sim, drawn, earned_only=True)
    baseline, with_gift, with_more = np.split(result["income_tax"], 3)
    # £29,526 = £12,570 PA + £16,956 Scottish basic upper limit in 2026.
    # It is also below rUK's £50,270 basic upper limit and the £100k taper.
    np.testing.assert_array_equal(baseline, with_gift)
    np.testing.assert_array_equal(baseline, with_more)


@PROPERTY_SETTINGS
@given(mixed_cases)
def test_explicit_zero_gift_matches_omitted_input(sim, omitted_sim, drawn):
    result = run(sim, drawn)
    for name in INPUTS:
        input_name = (
            "employment_income_before_lsr" if name == "employment_income" else name
        )
        omitted_sim.set_input(input_name, YEAR, result[name][:BASE_PEOPLE])
    omitted_sim.reset_calculations()
    for variable in (
        "adjusted_net_income",
        "personal_allowance",
        "allowances",
        "unused_personal_allowance",
        "earned_taxable_income",
        "earned_income_tax",
        "savings_income_tax",
        "dividend_income_tax",
        "property_income_tax",
        "income_tax",
        "savings_allowance",
        "tax_band",
        "capital_gains_tax",
    ):
        before = omitted_sim.calculate(variable, YEAR)
        after = sim.calculate(variable, YEAR)[:BASE_PEOPLE]
        assert before.dtype == after.dtype
        assert before.tobytes() == after.tobytes(), variable


def test_zero_gift_preserves_baseline_outputs_bit_for_bit():
    """Freeze intermediate and final outputs, including mixed income.

    Frozen from main at 3381500f4 (after #2352 put savings and dividends
    above property income, and the Scottish personal savings allowance
    moved to the UK bands). The Scottish £150,000 case uses the corrected
    £125,140 top-rate limit from S6M-20844 (#2130), giving £59,634.35:
    https://www.parliament.scot/chamber-and-committees/votes-and-motions/S6M-20844

    Gift Aid's zero-input compatibility also applies to inherited baseline
    choices about property stacking and taxpayer bands.
    Exact float32 expectations catch changes hidden by a tax-level tolerance.
    """
    rows = [
        (30_000, 0, 0, 0),
        (60_000, 0, 0, 0),
        (150_000, 0, 0, 0),
        (30_000, 12_000, 18_000, 9_000),
        (0, 20_000, 10_000, 10_000),
        (101_000, 0, 0, 0),
    ] * 2
    inputs = situation(rows, gifts=[0] * len(rows))
    for i in range(len(rows)):
        inputs["households"][f"h{i}"]["region"][YEAR] = (
            "SCOTLAND" if i >= len(rows) // 2 else "NORTH_WEST"
        )
        inputs["people"][f"p{i}"]["capital_gains"] = {YEAR: 40_000}
    snapshot = Simulation(situation=inputs)
    expected = {
        "adjusted_net_income": [30_000, 60_000, 150_000, 69_000, 40_000, 101_000] * 2,
        "personal_allowance": [12_570, 12_570, 0, 12_570, 12_570, 12_070] * 2,
        "allowances": [12_570, 12_570, 0, 12_570, 12_570, 12_070] * 2,
        "unused_personal_allowance": [0, 0, 0, 0, 0, 0] * 2,
        "earned_taxable_income": [17_430, 47_430, 150_000, 17_430, 0, 88_930] * 2,
        "received_allowances_earned_income": [12_570, 12_570, 0, 12_570, 10_000, 12_070]
        * 2,
        "received_allowances_savings_income": [0, 0, 0, 0, 2570, 0] * 2,
        "received_allowances_dividend_income": [0, 0, 0, 0, 0, 0] * 2,
        "basic_rate_earned_income": [17_430, 37_700, 37_700, 17_430, 0, 37_700] * 2,
        "higher_rate_earned_income": [0, 9730, 87_440, 0, 0, 51_230] * 2,
        "add_rate_earned_income": [0, 0, 24_860, 0, 0, 0] * 2,
        "basic_rate_savings_income": [0, 0, 0, 10_770, 11_430, 0] * 2,
        "higher_rate_savings_income": [0, 0, 0, 730, 0, 0] * 2,
        "add_rate_savings_income": [0, 0, 0, 0, 0, 0] * 2,
        "savings_allowance": [1000, 500, 0, 500, 1000, 500] * 2,
        "earned_income_tax": [
            3486,
            11_432,
            53_703,
            3486,
            0,
            28_032,
            3451.070068359375,
            13182.0498046875,
            59634.3515625,
            3451.070068359375,
            0,
            31407.05078125,
        ],
        "savings_income_tax": [0, 0, 0, 2446, 2286, 0] * 2,
        "dividend_income_tax": [0, 0, 0, 6256.25, 1021.25, 0] * 2,
        "property_income_tax": [0, 0, 0, 1800, 0, 0, 0, 0, 0, 1890, 0, 0],
        "income_tax": [
            3486,
            11_432,
            53_703,
            13988.25,
            3307.25,
            28_032,
            3451.070068359375,
            13182.0498046875,
            59634.3515625,
            14043.3203125,
            3307.25,
            31407.05078125,
        ],
        # The last row's 37,000 of gains is split between the higher band
        # left on top of its 88,930 taxable income and the band above it, at
        # equal rates; float32 rounds the two parts' sum a thousandth low.
        "capital_gains_tax": [
            7663.7998046875,
            8880,
            8880,
            8880,
            8263.7998046875,
            8879.9990234375,
        ]
        * 2,
    }
    for variable, values in expected.items():
        actual = snapshot.calculate(variable, YEAR)
        assert actual.tobytes() == np.array(values, dtype=actual.dtype).tobytes(), (
            variable
        )
    assert snapshot.calculate("tax_band", YEAR).tolist() == [
        "BASIC",
        "HIGHER",
        "ADDITIONAL",
        "HIGHER",
        "BASIC",
        "HIGHER",
        "INTERMEDIATE",
        "HIGHER",
        "ADDITIONAL",
        "HIGHER",
        "INTERMEDIATE",
        "ADDITIONAL",
    ]


@pytest.mark.parametrize("ani,net_gift", [(50_000, 0), (49_000, 800)])
def test_explicit_adjusted_net_income_preserves_tax_base(ani, net_gift):
    """An input ANI already includes the s.58 gross Gift Aid adjustment.

    Reconstruct net income once when ANI is supplied directly. Zero Gift Aid
    must retain the longstanding ability to supply this intermediate input.
    """
    supplied_inputs = situation([(0, 0, 0, 0)], gifts=[net_gift])
    supplied_inputs["people"]["p0"]["adjusted_net_income"] = {YEAR: ani}
    supplied = Simulation(situation=supplied_inputs)
    raw = Simulation(situation=situation([(50_000, 0, 0, 0)], gifts=[net_gift]))
    for variable in (
        "net_income",
        "adjusted_net_income",
        "personal_allowance",
        "earned_taxable_income",
        "income_tax",
    ):
        before = raw.calculate(variable, YEAR)
        after = supplied.calculate(variable, YEAR)
        assert before.dtype == after.dtype
        assert before.tobytes() == after.tobytes(), variable
    assert supplied.calculate("net_income", YEAR)[0] == 50_000
    assert supplied.calculate("earned_taxable_income", YEAR)[0] == 37_430
    assert supplied.calculate("income_tax", YEAR)[0] == 7_486


# The helper on its own, against each scale shape a caller passes it. Raising
# a threshold must equal recomputing the scale with that threshold raised;
# thresholds outside the range must not move, which a zero rate step (the
# model's extra UK bracket repeats 45%) would not reveal.
HELPER_SCALES = {
    "UK, with an extra bracket at a distinct rate": (
        [0, 37_700, 125_140, 10_000_000],
        [0.20, 0.40, 0.45, 0.50],
        None,
    ),
    "Scotland, three rates (before 2018-19)": (
        [0, 31_500, 150_000],
        [0.20, 0.40, 0.45],
        "scottish",
    ),
    "Scotland, six rates": (
        [0, 3_967, 16_956, 31_092, 62_430, 125_140],
        [0.19, 0.20, 0.21, 0.42, 0.45, 0.48],
        "scottish",
    ),
}


def _scale(thresholds, rates):
    from policyengine_core.taxscales import MarginalRateTaxScale

    scale = MarginalRateTaxScale()
    for threshold, rate in zip(thresholds, rates):
        scale.add_bracket(threshold, rate)
    return scale


@pytest.mark.parametrize("name", list(HELPER_SCALES))
@settings(max_examples=200, deadline=None, derandomize=True)
@given(
    income=st.floats(0, 12_000_000, allow_nan=False, allow_infinity=False),
    gross_gift=st.floats(0, 2_000_000, allow_nan=False, allow_infinity=False),
)
def test_helper_equals_the_scale_with_its_limits_raised(name, income, gross_gift):
    from policyengine_uk.utils.income_tax import (
        calc_income_tax_with_gift_aid,
        first_extended_scottish_threshold,
    )

    thresholds, rates, kind = HELPER_SCALES[name]
    scale = _scale(thresholds, rates)
    if kind == "scottish":
        first = first_extended_scottish_threshold(scale)
        last = len(scale.thresholds)
        # Three rates: raise the basic rate limit and above. Six: keep the
        # starter limit and raise the basic rate's upper limit and above.
        assert first == (1 if len(thresholds) == 3 else 2)
        tax = calc_income_tax_with_gift_aid(
            scale, np.array([income]), np.array([gross_gift]), first, last
        )
    else:
        # UK default: the basic and higher rate limits only.
        first, last = 1, 3
        tax = calc_income_tax_with_gift_aid(
            scale, np.array([income]), np.array([gross_gift])
        )
    raised = [
        threshold + gross_gift if first <= index < last else threshold
        for index, threshold in enumerate(thresholds)
    ]
    expected = _scale(raised, rates).calc(np.array([income]))
    assert tax[0] == pytest.approx(expected[0], rel=1e-9, abs=1e-6)
