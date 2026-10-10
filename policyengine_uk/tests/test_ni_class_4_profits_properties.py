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
5. Carry-forward over many years matches the reference fold, with or
   without a supplied brought-forward balance, whatever order the years are
   calculated in, including beyond the engine's ten-step spiral limit.
6. Each loss is relieved once. With losses entered for only some years, the
   model matches a reference in which a year without an entry makes no new
   loss, though the engine carries the last entry into it. Total relief
   never exceeds the losses entered (relief plus the final carry-forward
   equals them), Class 4 profits are never negative, and a year with no
   loss entered and none brought forward has no relief. Calculating income
   tax's loss relief or the carried-over trading_loss first, or calculating
   on a branch, changes none of this.

test_ni_class_4_properties.py checks s. 15(3) and regulation 100 given these
profits, for arbitrary thresholds and rates. Comparisons allow float32
rounding: the model stores values as float32.
"""

from fractions import Fraction

import numpy as np
import pytest
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st
from policyengine_core.periods import period as period_
from policyengine_core.reforms import Reform

from policyengine_uk import Simulation
from policyengine_uk.utils.supplied_inputs import (
    SUPPLIED_INPUT_VARIABLES,
    supplied_input,
    supplied_input_periods,
)

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

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


def reference_allowance(simulation, year):
    return exact(
        simulation.tax_benefit_system.parameters(
            f"{year}-01-01"
        ).gov.hmrc.income_tax.allowances.trading_allowance
    )


def reference_profits_before_losses(profit, receipts, capital_allowances, allowance):
    """ITTOIA 2005 Part 2 Chapter 2 profits, after capital allowances and
    the trading allowance, before loss relief."""
    if receipts > 0 and receipts >= profit:
        if receipts <= allowance:
            # s. 783AF: the trade's profits are nil.
            return Fraction(0)
        # The better of actual deductions and the allowance (s. 783AI);
        # capital allowances are a deduction (CAA 2001 s. 247) that the
        # allowance replaces, so the two never stack.
        actual_deductions = receipts - profit + capital_allowances
        return max(Fraction(0), receipts - max(actual_deductions, allowance))
    # Receipts unknown: a profit within the allowance is taken to come from
    # receipts within it; a larger one already reflects the better deduction.
    if profit <= allowance:
        return Fraction(0)
    return max(Fraction(0), profit - capital_allowances)


def reference_losses(years, supplied=None):
    """Sch. 2 para. 3: each year's losses (its own and those brought
    forward) are set against its profits; the rest is carried forward to the
    following years without limit (para. 3(4)(b); ITA 2007 s. 84).
    `supplied` maps a year's index to a supplied brought-forward balance."""
    brought_forward = Fraction(0)
    out = []
    for index, (profits, trading_loss) in enumerate(years):
        if supplied and index in supplied:
            brought_forward = supplied[index]
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
            allowance=reference_allowance(sim, period),
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
            v["allowance"],
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
    # Optionally, a brought-forward balance supplied for one year.
    st.one_of(
        st.none(),
        st.tuples(st.integers(0, 15), st.floats(0, 100_000)),
    ),
    st.randoms(use_true_random=False),
)
def test_losses_carry_forward_over_many_years(years, opening_balance, random):
    last_year = 2030
    first_year = last_year - len(years) + 1
    periods = list(range(first_year, last_year + 1))
    person = {
        "age": {first_year: 40},
        "self_employment_income": dict(zip(periods, (profit for profit, _ in years))),
        "trading_loss": dict(zip(periods, (loss for _, loss in years))),
    }
    supplied = None
    if opening_balance is not None:
        index = opening_balance[0] % len(years)
        person["ni_class_4_losses_brought_forward"] = {
            periods[index]: opening_balance[1]
        }
        # Compare against the stored (float32) input.
        supplied = {index: exact(np.float32(opening_balance[1]))}
    sim = Simulation(
        situation={
            "people": {"person": person},
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
                    reference_allowance(sim, period),
                ),
                exact(sim.calculate("trading_loss", period)[0]),
            )
            for period in periods
        ],
        supplied,
    )
    total_losses = sum(loss for _, loss in years) + sum((supplied or {}).values())
    order = periods.copy()
    random.shuffle(order)
    for period in order:
        reference_year = expected[period - first_year]
        brought_forward = float(
            sim.calculate("ni_class_4_losses_brought_forward", period)[0]
        )
        profits = float(sim.calculate("ni_class_4_profits", period)[0])
        tol = tolerance(total_losses)
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


def test_losses_carry_forward_beyond_the_spiral_limit():
    # A £720,000 loss in 2016 against £50,000 of profit a year: 2016-2029
    # use £700,000, so £20,000 is brought into 2030 and 2030's Class 4
    # profits are £30,000. A formula recursing on the previous year would
    # be cut off by the engine's spiral guard after ten years, dropping the
    # loss and leaving £50,000.
    years = range(2016, 2031)
    sim = Simulation(
        situation={
            "people": {
                "person": {
                    "age": {2016: 40},
                    "self_employment_income": {year: 50_000 for year in years},
                    "trading_loss": {
                        year: 720_000 if year == 2016 else 0 for year in years
                    },
                }
            },
            "benunits": {"benunit": {"members": ["person"]}},
            "households": {"household": {"members": ["person"]}},
        }
    )
    assert sim.calculate("ni_class_4_losses_brought_forward", 2030)[0] == 20_000
    assert sim.calculate("ni_class_4_profits", 2030)[0] == 30_000


def single_person(person):
    return Simulation(
        situation={
            "people": {"person": person},
            "benunits": {"benunit": {"members": ["person"]}},
            "households": {"household": {"members": ["person"]}},
        }
    )


def test_pre_allowance_profits_exhaust_the_loss_in_the_historical_reference():
    sim = single_person(
        {
            "self_employment_income": {2015: 500, 2016: 500},
            "trading_loss": {2015: 1_000, 2016: 0},
        }
    )
    periods = (2015, 2016)
    profits = [
        reference_profits_before_losses(
            Fraction(500),
            Fraction(0),
            Fraction(0),
            reference_allowance(sim, period),
        )
        for period in periods
    ]
    assert profits == [500, 500]
    expected = reference_losses(zip(profits, (Fraction(1_000), Fraction(0))))
    assert [year["relief"] for year in expected] == [500, 500]
    assert [year["carried_forward"] for year in expected] == [500, 0]
    for period, reference_year in zip(periods, expected):
        assert sim.calculate("ni_class_4_profits_before_losses", period)[0] == 500
        for name, reference_name in [
            ("losses_brought_forward", "brought_forward"),
            ("loss_relief", "relief"),
            ("losses_carried_forward", "carried_forward"),
            ("profits", "profits"),
        ]:
            assert sim.calculate(f"ni_class_4_{name}", period)[0] == float(
                reference_year[reference_name]
            )


@settings(
    max_examples=20,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
@given(
    st.lists(
        st.tuples(
            st.one_of(st.just(0.0), st.floats(0, 80_000)),  # profit
            st.one_of(st.just(0.0), st.floats(0, 150_000)),  # loss
            st.booleans(),  # whether the loss is entered for the year
        ),
        min_size=2,
        max_size=12,
    ),
    st.randoms(use_true_random=False),
)
def test_a_loss_entered_for_some_years_is_relieved_once(years, random):
    last_year = 2030
    first_year = last_year - len(years) + 1
    periods = list(range(first_year, last_year + 1))
    entered = {
        period: loss
        for period, (_, loss, is_entered) in zip(periods, years)
        if is_entered
    }
    person = {
        "age": {first_year: 40},
        "self_employment_income": dict(
            zip(periods, (profit for profit, _, _ in years))
        ),
    }
    if entered:
        person["trading_loss"] = entered
    sim = single_person(person)
    # Fill the engine's caches first, in random order: trading_loss carried
    # into the years without an entry, and income tax's loss relief, which
    # reads it there. Neither may count as a new loss for Class 4.
    for period in random.sample(periods, random.randint(0, len(periods))):
        sim.calculate(random.choice(["trading_loss", "loss_relief"]), period)

    # Independent reference: the stored (float32) inputs, a loss only in the
    # years it is entered for, and the year-by-year fold.
    stored_losses = {
        period: exact(np.float32(loss)) for period, loss in entered.items()
    }
    expected = reference_losses(
        [
            (
                reference_profits_before_losses(
                    exact(np.float32(profit)),
                    Fraction(0),
                    Fraction(0),
                    reference_allowance(sim, period),
                ),
                stored_losses.get(period, Fraction(0)),
            )
            for period, (profit, _, _) in zip(periods, years)
        ]
    )
    names = [
        "losses_brought_forward",
        "loss_relief",
        "losses_carried_forward",
        "profits_before_losses",
        "profits",
    ]
    queries = [(period, name) for period in periods for name in names]
    random.shuffle(queries)
    model = {period: {} for period in periods}
    for period, name in queries:
        model[period][name] = float(sim.calculate(f"ni_class_4_{name}", period)[0])

    total_entered = float(sum(stored_losses.values()))
    tol = tolerance(total_entered, *(profit for profit, _, _ in years))
    for period in periods:
        reference_year = expected[period - first_year]
        values = model[period]
        for name, reference_name in [
            ("losses_brought_forward", "brought_forward"),
            ("loss_relief", "relief"),
            ("losses_carried_forward", "carried_forward"),
            ("profits", "profits"),
        ]:
            assert abs(values[name] - float(reference_year[reference_name])) <= tol, (
                period,
                name,
                values[name],
                float(reference_year[reference_name]),
            )
        # Class 4 profits are never negative, nor above profits before losses.
        assert 0 <= values["profits"] <= values["profits_before_losses"] + tol
        assert values["loss_relief"] >= 0
        # No relief without a loss entered for the year or brought forward.
        if stored_losses.get(period, 0) == 0 and values["losses_brought_forward"] == 0:
            assert values["loss_relief"] == 0, (period, values)
    # Conservation: each loss entered is relieved at most once, and what is
    # not relieved is still being carried forward at the end.
    total_relief = sum(model[period]["loss_relief"] for period in periods)
    assert total_relief <= total_entered + tol
    assert (
        abs(total_relief + model[last_year]["losses_carried_forward"] - total_entered)
        <= tol
    )


def test_class_4_counts_only_supplied_losses_on_branches():
    # A £10,000 loss entered for 2025 only, with £40,000 of profit in 2026
    # and 2027. A branch made before any calculation adds a £5,000 loss in
    # 2026. Each simulation counts only the losses supplied to it.
    sim = single_person(
        {
            "age": {2025: 40},
            "self_employment_income": {2026: 40_000, 2027: 40_000},
            "trading_loss": {2025: 10_000},
        }
    )
    branch = sim.get_branch("extra_2026_loss")
    branch.set_input("trading_loss", 2026, np.array([5_000.0]))
    # The engine carries the 2025 loss into 2027, but it is not a new loss.
    assert sim.calculate("trading_loss", 2027)[0] == 10_000
    assert sim.calculate("ni_class_4_profits", 2026)[0] == 30_000
    assert sim.calculate("ni_class_4_profits", 2027)[0] == 40_000
    # On the branch, 2026 relieves its own 5,000 and the 10,000 from 2025.
    assert branch.calculate("ni_class_4_trading_loss", 2026)[0] == 5_000
    assert branch.calculate("ni_class_4_profits", 2026)[0] == 25_000
    assert branch.calculate("ni_class_4_profits", 2027)[0] == 40_000
    # The branch's input does not reach the simulation it was made from.
    assert sim.calculate("ni_class_4_trading_loss", 2026)[0] == 0


def test_class_4_counts_only_supplied_losses_on_plain_clones():
    sim = single_person(
        {
            "age": {2025: 40},
            "self_employment_income": {2026: 40_000, 2027: 40_000},
            "trading_loss": {2025: 10_000},
        }
    )
    clone = sim.clone()
    clone.set_input("trading_loss", 2026, np.array([5_000.0]))
    # Warm the original's carry-over cache after the clone records its input.
    # A shared provenance set would count this cached 10,000 as a new loss.
    assert sim.calculate("trading_loss", 2026)[0] == 10_000
    observed = (
        float(sim.calculate("ni_class_4_profits", 2026)[0]),
        round(float(sim.calculate("ni_class_4", 2026)[0]), 2),
    )
    assert observed == (30_000, 1_045.80)
    assert clone.calculate("ni_class_4_profits", 2026)[0] == 25_000
    for simulation in (sim, clone):
        assert simulation.calculate("ni_class_4_profits", 2027)[0] == 40_000
    assert clone._user_input_keys is not sim._user_input_keys
    assert clone._user_input_contexts is not sim._user_input_contexts


@pytest.mark.parametrize("on_branch", [False, True])
def test_class_4_does_not_count_a_deleted_loss_after_recalculation(on_branch):
    original = single_person(
        {
            "age": {2025: 40},
            "self_employment_income": {2026: 40_000, 2027: 40_000},
            "trading_loss": {2025: 10_000},
        }
    )
    sim = original.get_branch("deleted_loss") if on_branch else original
    sim.set_input("trading_loss", 2026, np.array([5_000.0]))
    sim.delete_arrays("trading_loss", 2026)
    # Deletion leaves the earlier loss available for engine carry-over, but
    # that replacement cache must not retain the deleted input's provenance.
    assert sim.calculate("trading_loss", 2026)[0] == 10_000
    observed = (
        float(sim.calculate("ni_class_4_profits", 2026)[0]),
        round(float(sim.calculate("ni_class_4", 2026)[0]), 2),
    )
    assert observed == (30_000, 1_045.80)
    assert sim.calculate("ni_class_4_profits", 2027)[0] == 40_000
    if on_branch:
        assert original.calculate("ni_class_4_profits", 2026)[0] == 30_000


def test_supplied_input_helpers_ignore_missing_stored_arrays():
    sim = single_person({"trading_loss": {2025: 10_000, 2026: 5_000}})
    population = sim.get_variable_population("trading_loss")
    population.get_holder("trading_loss").delete_arrays(period_(2026))
    # Core forgets the deleted input's record (policyengine-core#561). Put it
    # back, as a population rebuild would leave it (policyengine-core#605):
    # neither helper may identify the missing stored value as an effective
    # input.
    sim._user_input_keys.add(("trading_loss", "default", period_(2026)))
    assert supplied_input(population, "trading_loss", period_(2026)) is None
    assert supplied_input_periods(population, "trading_loss") == [period_(2025)]


@pytest.mark.parametrize("on_branch", [False, True])
@pytest.mark.parametrize("deleted_loss", [5_000.0, 10_000.0])
def test_class_4_does_not_count_a_loss_deleted_from_its_holder(on_branch, deleted_loss):
    original = single_person(
        {
            "age": {2025: 40},
            "self_employment_income": {2026: 40_000, 2027: 40_000},
            "trading_loss": {2025: 10_000},
        }
    )
    sim = original.get_branch("deleted_loss") if on_branch else original
    sim.set_input("trading_loss", 2026, np.array([deleted_loss]))
    # The engine carries the 2025 loss into the emptied 2026. Before
    # policyengine-core 3.32.27, Holder.delete_arrays kept core's record of
    # the deleted input (policyengine-core#559), and that 10,000 would count
    # as a second loss (profits of 20,000 and contributions of 445.80), also
    # when the deleted loss was 10,000 too.
    sim.get_holder("trading_loss").delete_arrays(period_(2026), sim.branch_name)
    assert sim.calculate("trading_loss", 2026)[0] == 10_000
    population = sim.get_variable_population("trading_loss")
    assert supplied_input(population, "trading_loss", period_(2026)) is None
    assert supplied_input_periods(population, "trading_loss") == [period_(2025)]
    observed = (
        float(sim.calculate("ni_class_4_profits", 2026)[0]),
        round(float(sim.calculate("ni_class_4", 2026)[0]), 2),
    )
    assert observed == (30_000, 1_045.80)
    assert sim.calculate("ni_class_4_profits", 2027)[0] == 40_000
    if on_branch:
        assert original.calculate("ni_class_4_profits", 2026)[0] == 30_000


def test_class_4_does_not_count_a_loss_a_rebuild_drops():
    def situation(losses):
        person = {
            "age": {2025: 40},
            "self_employment_income": {2026: 40_000},
            "trading_loss": losses,
        }
        return {
            "people": {"person": person},
            "benunits": {"benunit": {"members": ["person"]}},
            "households": {"household": {"members": ["person"]}},
        }

    sim = Simulation(situation=situation({2025: 10_000, 2026: 5_000}))
    # Rebuilding the populations replaces every holder but keeps core's
    # record of the 2026 loss (policyengine-core#605). The engine carries the
    # 2025 loss into 2026; with the stale record that 10,000 would count as a
    # second loss (profits of 20,000 and contributions of 445.80).
    sim.build_from_situation(situation({2025: 10_000}))
    assert sim.calculate("trading_loss", 2026)[0] == 10_000
    population = sim.get_variable_population("trading_loss")
    assert supplied_input(population, "trading_loss", period_(2026)) is None
    assert supplied_input_periods(population, "trading_loss") == [period_(2025)]
    observed = (
        float(sim.calculate("ni_class_4_profits", 2026)[0]),
        round(float(sim.calculate("ni_class_4", 2026)[0]), 2),
    )
    assert observed == (30_000, 1_045.80)


LIFECYCLE_YEARS = (2024, 2025, 2026)
lifecycle_loss = st.integers(min_value=0, max_value=3).map(lambda k: 1_000.0 * k)
LIFECYCLE_STEPS = 6
# Each step names the simulation it acts on, modulo the number made so far
# (at most one more than the steps), so an original keeps changing after it
# has been cloned.
lifecycle_step = st.tuples(
    st.integers(min_value=0, max_value=LIFECYCLE_STEPS),
    st.one_of(
        st.tuples(st.just("set"), st.sampled_from(LIFECYCLE_YEARS), lifecycle_loss),
        st.tuples(
            st.sampled_from(
                ["delete", "delete_from_holder", "calculate", "calculate_profits"]
            ),
            st.sampled_from(LIFECYCLE_YEARS),
        ),
        st.tuples(st.just("clone")),
        st.tuples(st.just("rebuild"), st.frozensets(st.sampled_from(LIFECYCLE_YEARS))),
    ),
)


def lifecycle_situation(losses):
    person = {
        "age": {2024: 40},
        "self_employment_income": {year: 20_000 for year in LIFECYCLE_YEARS},
        "trading_loss": losses,
    }
    return {
        "people": {"person": person},
        "benunits": {"benunit": {"members": ["person"]}},
        "households": {"household": {"members": ["person"]}},
    }


_lifecycle_templates = []


def lifecycle_simulation(losses):
    # Rebuild a clone of one template, as the State Pension age properties do,
    # so each example also starts from a population rebuild.
    if not _lifecycle_templates:
        _lifecycle_templates.append(
            Simulation(situation=lifecycle_situation({2025: 2_000.0}))
        )
    sim = _lifecycle_templates[0].clone(clone_tax_benefit_system=False)
    sim.build_from_situation(lifecycle_situation(losses))
    return sim


def assert_supplied_losses(sim, expected):
    population = sim.get_variable_population("trading_loss")
    for year in LIFECYCLE_YEARS:
        value = supplied_input(population, "trading_loss", period_(year))
        assert (None if value is None else value.tolist()) == (
            [expected[year]] if year in expected else None
        )
    assert supplied_input_periods(population, "trading_loss") == [
        period_(year) for year in sorted(expected)
    ]


@PROPERTY_SETTINGS
@given(
    st.dictionaries(st.sampled_from(LIFECYCLE_YEARS), lifecycle_loss),
    st.lists(lifecycle_step, max_size=LIFECYCLE_STEPS),
)
# The rebuild leaves the template's 2025 record behind, and building the
# dataset calculates 2025 (policyengine-core#605).
@example(initial={2024: 0.0}, steps=[])
# With one record between a simulation and its clone, the input set on one
# passes off the other's calculated 2025 as supplied (policyengine-core#559).
@example(initial={2024: 0.0}, steps=[(0, ("clone",)), (0, ("set", 2025, 0.0))])
def test_only_losses_set_and_kept_count_as_supplied(initial, steps):
    # A loss counts as supplied exactly while the last value set for it, by
    # set_input or a rebuild, has not been deleted or dropped by a rebuild,
    # whatever the engine has carried over or calculated meanwhile. A clone
    # starts with its original's supplied losses, and what either does
    # afterwards does not reach the other.
    sim = lifecycle_simulation(initial)
    simulations = [(sim, dict(initial))]
    assert_supplied_losses(sim, initial)
    for which, step in steps:
        sim, expected = simulations[which % len(simulations)]
        kind = step[0]
        if kind == "set":
            sim.set_input("trading_loss", step[1], np.array([step[2]]))
            expected[step[1]] = step[2]
        elif kind == "delete":
            sim.delete_arrays("trading_loss", step[1])
            expected.pop(step[1], None)
        elif kind == "delete_from_holder":
            sim.get_holder("trading_loss").delete_arrays(period_(step[1]))
            expected.pop(step[1], None)
        elif kind == "calculate":
            sim.calculate("trading_loss", step[1])
        elif kind == "calculate_profits":
            sim.calculate("ni_class_4_profits", step[1])
        elif kind == "clone":
            simulations.append(
                (sim.clone(clone_tax_benefit_system=False), dict(expected))
            )
        elif kind == "rebuild":
            kept = {year: expected[year] for year in step[1] if year in expected}
            sim.build_from_situation(lifecycle_situation(kept))
            expected.clear()
            expected.update(kept)
        for simulation, supplied in simulations:
            assert_supplied_losses(simulation, supplied)


def test_supplied_input_helpers_refuse_an_unregistered_variable():
    sim = single_person({"employment_income": {2026: 20_000}})
    population = sim.get_variable_population("employment_income")
    # Simulation.calculate keeps input records in step with storage only for
    # SUPPLIED_INPUT_VARIABLES, so the helpers answer for no other variable.
    assert "employment_income" not in SUPPLIED_INPUT_VARIABLES
    with pytest.raises(ValueError, match="SUPPLIED_INPUT_VARIABLES"):
        supplied_input(population, "employment_income", period_(2026))
    with pytest.raises(ValueError, match="SUPPLIED_INPUT_VARIABLES"):
        supplied_input_periods(population, "employment_income")


class neutralize_trading_loss(Reform):
    def apply(self):
        self.neutralize_variable("trading_loss")


def test_class_4_respects_a_neutralized_supplied_loss():
    sim = single_person(
        {
            "self_employment_income": {2026: 40_000, 2027: 40_000},
            "trading_loss": {2025: 10_000},
        }
    )
    assert sim.calculate("ni_class_4_profits", 2026)[0] == 30_000
    sim.apply_reform(neutralize_trading_loss)
    # The reform leaves the raw input in storage, but it is no longer an
    # effective loss. Read the current variable, not the holder's old one.
    assert sim.calculate("trading_loss", 2025)[0] == 0
    assert sim.calculate("ni_class_4_trading_loss", 2025)[0] == 0
    for year in (2026, 2027):
        assert sim.calculate("ni_class_4_loss_relief", year)[0] == 0
        assert sim.calculate("ni_class_4_profits", year)[0] == 40_000
