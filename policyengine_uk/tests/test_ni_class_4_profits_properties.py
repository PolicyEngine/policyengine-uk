"""Property tests for the profits Class 4 NICs are charged on.

SSCBA 1992 s. 15(1)(b) and Sch. 2 charge Class 4 on the trade profits
chargeable to income tax under ITTOIA 2005 Part 2 Chapter 2, which are after
capital allowances (CAA 2001 s. 247) and the trading allowance (ITTOIA 2005
ss. 783AF and 783AI), less trading losses as Sch. 2 para. 3 allows.

Invariants, for every generated case:

1. Differential: ni_class_4_profits_before_losses, ni_class_4_loss_relief,
   ni_class_4_losses_brought_forward, ni_class_4_losses_carried_forward and
   ni_class_4_profits equal an independent exact-rational reference: the
   better of actual deductions and the allowance where receipts are known,
   and losses set against each year's profits, earliest first, with the
   rest carried forward without limit.
2. Accounting: trading_loss + losses brought forward = loss relief + losses
   carried forward; losses brought forward equal last year's losses carried
   forward; 0 <= loss relief <= profits before losses.
3. Bound: 0 <= ni_class_4 <= the s. 15(3) amount on the reference Class 4
   profits <= the s. 15(3) amount on the unrelieved profit. Where regulation
   100 cannot apply (no Class 1 and, from April 2024, Class 2 irrelevant),
   ni_class_4 equals the s. 15(3) amount.
4. Monotonicity: ni_class_4 is non-decreasing in profit, at fixed expenses
   (or unknown receipts), capital allowances, losses and employment income,
   wherever Class 2 does not change; and non-increasing in capital
   allowances and trading losses.
5. Carry-forward over many years matches the reference fold, whatever order
   the years are calculated in, including beyond the engine's ten-step
   spiral limit.

test_ni_class_4_properties.py checks s. 15(3) and regulation 100 given these
profits, for arbitrary thresholds and rates. Comparisons allow float32
rounding: the model stores values as float32.
"""

from fractions import Fraction

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

ALLOWANCE = 1_000
CASES = 24  # Each case is simulated twice: as drawn, and varied.
PEOPLE = 2 * CASES
PROPERTY_SETTINGS = settings(
    max_examples=30,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)

amount = st.one_of(
    st.floats(min_value=0, max_value=2_500),
    st.floats(min_value=0, max_value=300_000),
    st.sampled_from(
        [0.0, 999.99, 1_000.0, 1_000.01, 6_725.0, 12_570.0, 50_270.0, 50_271.0]
    ),
)
profit = st.one_of(amount, st.floats(min_value=-5_000, max_value=0))
expenses = st.one_of(
    st.sampled_from([0.0, 150.0, 999.0, 1_000.0, 1_001.0]),
    st.floats(min_value=0, max_value=5_000),
)
capital_allowances = st.one_of(
    st.just(0.0), st.sampled_from([150.0, 900.0, 5_000.0]), amount
)
loss = st.one_of(st.just(0.0), amount)
# Receipts: unknown, consistent (profit + expenses), or inconsistently below
# profit, which the model treats as unknown.
receipts_mode = st.sampled_from(["unknown", "consistent", "below_profit"])
year_inputs = st.tuples(
    profit,
    expenses,
    capital_allowances,
    loss,
    receipts_mode,
    st.floats(min_value=0.01, max_value=0.99),  # receipts share if below profit
)
case = st.tuples(
    year_inputs,  # previous year
    year_inputs,  # current year
    st.sampled_from([0.0, 0.0, 8_000.0, 30_000.0, 60_000.0, 200_000.0]),
    st.floats(min_value=0, max_value=30_000),  # variation
)
cases = st.lists(case, min_size=CASES, max_size=CASES)


def exact(x):
    return Fraction(float(x))


def reference_profits_before_losses(profit, receipts, capital_allowances):
    """ITTOIA 2005 Part 2 Chapter 2 profits, after capital allowances and
    the trading allowance, before loss relief."""
    if receipts > 0 and receipts >= profit:
        if receipts <= ALLOWANCE:
            # s. 783AF: the trade's profits are nil.
            return Fraction(0)
        # The better of actual deductions and the allowance (s. 783AI);
        # capital allowances are a deduction (CAA 2001 s. 247) that the
        # allowance replaces, so the two never stack.
        actual_deductions = receipts - profit + capital_allowances
        return max(Fraction(0), receipts - max(actual_deductions, ALLOWANCE))
    # Receipts unknown: a profit within the allowance is taken to come from
    # receipts within it; a larger one already reflects the better deduction.
    if profit <= ALLOWANCE:
        return Fraction(0)
    return max(Fraction(0), profit - capital_allowances)


def reference_losses(years):
    """Sch. 2 para. 3: each year's losses (its own and those brought
    forward) are set against its profits; the rest is carried forward to the
    following years without limit (para. 3(4)(b); ITA 2007 s. 84)."""
    brought_forward = Fraction(0)
    out = []
    for profits, trading_loss in years:
        losses = max(trading_loss, 0) + brought_forward
        relief = min(losses, profits)
        out.append(
            dict(
                brought_forward=brought_forward,
                relief=relief,
                profits=profits - relief,
                carried_forward=losses - relief,
            )
        )
        brought_forward = losses - relief
    return out


def statutory_class_4(profits, class_4):
    """s. 15(3) SSCBA 1992 in exact arithmetic."""
    lpl = exact(class_4.thresholds.lower_profits_limit)
    upl = exact(class_4.thresholds.upper_profits_limit)
    return exact(class_4.rates.main) * min(max(profits - lpl, 0), upl - lpl) + exact(
        class_4.rates.additional
    ) * max(profits - upl, 0)


def tolerance(*amounts):
    # float32 has a 24-bit significand: a few ulps of the largest amount
    # involved, plus a penny.
    return 0.01 + 4e-7 * max(abs(float(a)) for a in amounts)


def receipts_for(profit, expenses, mode, share):
    return np.select(
        [mode == "consistent", mode == "below_profit"],
        [profit + expenses, profit * share],
        0,
    )


@pytest.fixture(scope="module", params=[2023, 2026])
def sim(request):
    year = request.param
    people = {
        f"person_{i}": {
            "age": {year - 1: 40, year: 41},
            **{
                variable: {year - 1: 0, year: 0}
                for variable in [
                    "employment_income",
                    "self_employment_income",
                    "self_employment_gross_receipts",
                    "capital_allowances",
                    "trading_loss",
                ]
            },
        }
        for i in range(PEOPLE)
    }
    sim = Simulation(
        situation={
            "people": people,
            "benunits": {
                f"benunit_{i}": {"members": [f"person_{i}"]} for i in range(PEOPLE)
            },
            "households": {
                f"household_{i}": {"members": [f"person_{i}"]} for i in range(PEOPLE)
            },
        }
    )
    return sim, year


def run(simulation, drawn, vary):
    """Simulate each drawn case twice: as drawn, and with `vary` applied to
    the current year's inputs. Returns stored inputs and model outputs."""
    sim, year = simulation
    previous, current, employment, variation = zip(*drawn)
    previous = [np.array(x) for x in zip(*previous)]
    current = [np.array(x) for x in zip(*current)]
    employment, variation = np.array(employment), np.array(variation)
    varied = vary(*current, variation)

    def both(x, y):
        return np.concatenate([x, y])

    inputs = {
        year - 1: [both(x, x) for x in previous],
        year: [both(x, y) for x, y in zip(current, varied)],
    }
    for period, (profit, expenses, allowances, loss, mode, share) in inputs.items():
        sim.set_input("self_employment_income", period, profit)
        sim.set_input(
            "self_employment_gross_receipts",
            period,
            receipts_for(profit, expenses, mode, share),
        )
        sim.set_input("capital_allowances", period, allowances)
        sim.set_input("trading_loss", period, loss)
        sim.set_input("employment_income", period, both(employment, employment))
    sim.reset_calculations()

    def calculate(variable, period):
        return sim.calculate(variable, period).astype(float)

    return {
        period: dict(
            # Stored (float32) inputs, not the float64 draws.
            profit=calculate("self_employment_income", period),
            receipts=calculate("self_employment_gross_receipts", period),
            capital_allowances=calculate("capital_allowances", period),
            trading_loss=calculate("trading_loss", period),
            **{
                name: calculate(f"ni_class_4_{name}", period)
                for name in [
                    "profits_before_losses",
                    "loss_relief",
                    "losses_brought_forward",
                    "losses_carried_forward",
                    "profits",
                ]
            },
            ni_class_4=calculate("ni_class_4", period),
            ni_class_2=calculate("ni_class_2", period),
            ni_class_1_employee=calculate("ni_class_1_employee", period),
        )
        for period in (year - 1, year)
    }


def reference(values, i):
    years = [values[period] for period in sorted(values)]
    profits = [
        reference_profits_before_losses(
            exact(v["profit"][i]),
            exact(v["receipts"][i]),
            exact(v["capital_allowances"][i]),
        )
        for v in years
    ]
    losses = reference_losses(
        [(p, exact(v["trading_loss"][i])) for p, v in zip(profits, years)]
    )
    return [dict(profits_before_losses=p, **l) for p, l in zip(profits, losses)]


def unchanged(profit, expenses, allowances, loss, mode, share, variation):
    return profit, expenses, allowances, loss, mode, share


@PROPERTY_SETTINGS
@given(cases)
def test_class_4_profits_match_statutory_reference(sim, drawn):
    values = run(sim, drawn, unchanged)
    for i in range(PEOPLE):
        expected = reference(values, i)
        for period, reference_year in zip(sorted(values), expected):
            model = values[period]
            for name, expected_value in reference_year.items():
                model_name = {
                    "brought_forward": "losses_brought_forward",
                    "relief": "loss_relief",
                    "carried_forward": "losses_carried_forward",
                }.get(name, name)
                actual = model[model_name][i]
                tol = tolerance(actual, expected_value, model["profit"][i])
                assert abs(actual - float(expected_value)) <= tol, (
                    period,
                    i,
                    model_name,
                    actual,
                    float(expected_value),
                )
            # Accounting identities.
            tol = tolerance(
                model["trading_loss"][i],
                model["losses_brought_forward"][i],
                model["profits_before_losses"][i],
            )
            assert (
                abs(
                    max(model["trading_loss"][i], 0)
                    + model["losses_brought_forward"][i]
                    - model["loss_relief"][i]
                    - model["losses_carried_forward"][i]
                )
                <= tol
            )
            assert -tol <= model["loss_relief"][i]
            assert model["loss_relief"][i] <= model["profits_before_losses"][i] + tol
        previous, current = (values[period] for period in sorted(values))
        assert current["losses_brought_forward"][i] == pytest.approx(
            previous["losses_carried_forward"][i], abs=0.01, rel=1e-6
        )


@PROPERTY_SETTINGS
@given(cases)
def test_class_4_never_exceeds_uncapped_statutory_amount(sim, drawn):
    values = run(sim, drawn, unchanged)
    simulation, year = sim
    current = values[year]
    class_4 = simulation.tax_benefit_system.parameters(
        f"{year}-01-01"
    ).gov.hmrc.national_insurance.class_4
    for i in range(PEOPLE):
        profits = reference(values, i)[-1]["profits"]
        uncapped = statutory_class_4(profits, class_4)
        unrelieved = statutory_class_4(max(exact(current["profit"][i]), 0), class_4)
        model = current["ni_class_4"][i]
        tol = tolerance(model, uncapped, current["profit"][i])
        assert uncapped <= unrelieved
        assert -tol <= model <= float(uncapped) + tol, (i, model, float(uncapped))
        regulation_100_cannot_apply = current["ni_class_1_employee"][i] == 0 and (
            year >= 2024 or current["ni_class_2"][i] == 0
        )
        if regulation_100_cannot_apply:
            assert abs(model - float(uncapped)) <= tol, (i, model, float(uncapped))


def more_profit(profit, expenses, allowances, loss, mode, share, variation):
    # Expenses stay fixed, so known receipts rise with profit.
    return profit + variation, expenses, allowances, loss, mode, share


def more_capital_allowances(profit, expenses, allowances, loss, mode, share, variation):
    return profit, expenses, allowances + variation, loss, mode, share


def more_trading_loss(profit, expenses, allowances, loss, mode, share, variation):
    return profit, expenses, allowances, loss + variation, mode, share


@PROPERTY_SETTINGS
@given(cases)
def test_class_4_is_non_decreasing_in_profit(sim, drawn):
    values = run(sim, drawn, more_profit)
    current = values[sim[1]]
    for i in range(CASES):
        j = i + CASES
        assert current["profit"][j] >= current["profit"][i]
        assert current["profits"][j] >= current["profits"][i] - tolerance(
            current["profits"][j]
        )
        if current["ni_class_2"][j] == current["ni_class_2"][i]:
            tol = tolerance(current["profit"][j], current["ni_class_4"][j])
            assert current["ni_class_4"][j] >= current["ni_class_4"][i] - tol, (
                i,
                current["profit"][i],
                current["profit"][j],
                current["ni_class_4"][i],
                current["ni_class_4"][j],
            )


@PROPERTY_SETTINGS
@given(cases, st.sampled_from([more_capital_allowances, more_trading_loss]))
def test_class_4_is_non_increasing_in_reliefs(sim, drawn, vary):
    values = run(sim, drawn, vary)
    current = values[sim[1]]
    for i in range(CASES):
        j = i + CASES
        tol = tolerance(current["profit"][i], current["ni_class_4"][i])
        assert current["profits"][j] <= current["profits"][i] + tol
        assert current["ni_class_4"][j] <= current["ni_class_4"][i] + tol, (
            vary.__name__,
            i,
            current["ni_class_4"][i],
            current["ni_class_4"][j],
        )


@settings(
    max_examples=15,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
@given(
    st.lists(
        st.tuples(
            st.one_of(st.just(0.0), st.floats(0, 80_000)),  # profit
            st.one_of(st.just(0.0), st.just(0.0), st.floats(0, 150_000)),  # loss
        ),
        min_size=2,
        max_size=16,
    ),
    st.randoms(use_true_random=False),
)
def test_losses_carry_forward_over_many_years(years, random):
    last_year = 2030
    first_year = last_year - len(years) + 1
    periods = list(range(first_year, last_year + 1))
    sim = Simulation(
        situation={
            "people": {
                "person": {
                    "age": {first_year: 40},
                    "self_employment_income": dict(
                        zip(periods, (profit for profit, _ in years))
                    ),
                    "trading_loss": dict(zip(periods, (loss for _, loss in years))),
                }
            },
            "benunits": {"benunit": {"members": ["person"]}},
            "households": {"household": {"members": ["person"]}},
        }
    )
    expected = reference_losses(
        [
            (
                reference_profits_before_losses(
                    exact(sim.calculate("self_employment_income", period)[0]),
                    Fraction(0),
                    Fraction(0),
                ),
                exact(sim.calculate("trading_loss", period)[0]),
            )
            for period in periods
        ]
    )
    order = periods.copy()
    random.shuffle(order)
    for period in order:
        reference_year = expected[period - first_year]
        brought_forward = float(
            sim.calculate("ni_class_4_losses_brought_forward", period)[0]
        )
        profits = float(sim.calculate("ni_class_4_profits", period)[0])
        tol = tolerance(reference_year["brought_forward"], sum(l for _, l in years))
        assert abs(brought_forward - float(reference_year["brought_forward"])) <= tol, (
            period,
            brought_forward,
            float(reference_year["brought_forward"]),
        )
        assert abs(profits - float(reference_year["profits"])) <= tol, (
            period,
            profits,
            float(reference_year["profits"]),
        )
