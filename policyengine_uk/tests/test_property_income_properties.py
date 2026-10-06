"""Property tests for landlords' property income (ITTOIA 2005 Part 3 Chapter 3
and Part 6A Chapter 2).

property_income is profit after actual expenses and before the costs of
dwelling-related loans. Those costs are relieved by a tax reduction at the
property basic rate (ss. 274A-274AA), and the property allowance replaces
actual expenses but cannot be had with the reduction (s. 783BL). These tests
check bounds, the reduction's accounting, that the allowance never stacks on
expenses, that the model's choice between the two is never worse than either
alone, and monotonicity, over many generated cases in one reusable
simulation.
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

YEAR = 2027
ALLOWANCE = 1_000
PROPERTY_BASIC_RATE = 0.22
OTHER_EMPLOYMENT_INCOME = [0, 8_000, 13_000, 30_000, 60_000, 110_000, 200_000]
# Every third person is a Scottish taxpayer.
SCOTTISH = [i % 3 == 2 for i in range(7)]
CASES = 21  # Each case is simulated twice: as drawn, and with more costs.
PEOPLE = 2 * CASES

amount = st.one_of(
    st.floats(min_value=0, max_value=2_500),
    st.floats(min_value=0, max_value=60_000),
    st.sampled_from([0.0, 999.99, 1_000.0, 1_000.01, 12_570.0]),
)
case = st.tuples(
    st.one_of(amount, st.floats(min_value=-3_000, max_value=0)),  # profit
    amount,  # expenses
    st.sampled_from([0.0, 0.0, 300.0, 1_500.0]).flatmap(
        lambda base: st.one_of(st.just(base), amount)
    ),  # finance costs
    st.sampled_from([0.0, 0.0, 0.0, 500.0, 4_000.0]),  # brought forward
    # Receipts: unknown, consistent (profit + expenses), or inconsistently
    # below profit, which the model must treat as unknown.
    st.sampled_from(["unknown", "consistent", "consistent", "below_profit"]),
    st.floats(min_value=0.01, max_value=0.99),  # receipts share if below profit
    st.floats(min_value=0, max_value=20_000),  # extra finance costs
)
cases = st.lists(case, min_size=CASES, max_size=CASES)


def person_index(i):
    return i % CASES % len(OTHER_EMPLOYMENT_INCOME)


@pytest.fixture(scope="module")
def sim():
    people = {
        f"person_{i}": {
            "age": {YEAR: 40},
            "employment_income": {YEAR: OTHER_EMPLOYMENT_INCOME[person_index(i)]},
            "property_income": {YEAR: 0},
            "property_rental_income": {YEAR: 0},
            "property_finance_costs": {YEAR: 0},
            "property_finance_costs_brought_forward": {YEAR: 0},
        }
        for i in range(PEOPLE)
    }
    households = {
        f"household_{i}": {
            "members": [f"person_{i}"],
            "region": {YEAR: "SCOTLAND" if SCOTTISH[person_index(i)] else "LONDON"},
        }
        for i in range(PEOPLE)
    }
    return Simulation(
        situation={
            "people": people,
            "benunits": {
                f"benunit_{i}": {"members": [f"person_{i}"]} for i in range(PEOPLE)
            },
            "households": households,
        }
    )


def set_inputs(sim, drawn, uses_allowance=None):
    profit, expenses, costs, brought_forward, mode, share, extra = map(
        np.array, zip(*drawn)
    )
    profit, expenses, brought_forward, mode, share = (
        np.concatenate([x, x]) for x in (profit, expenses, brought_forward, mode, share)
    )
    costs = np.concatenate([costs, costs + extra])
    receipts = np.select(
        [mode == "consistent", mode == "below_profit"],
        [np.maximum(profit, 0) + expenses, np.maximum(profit, 0) * share],
        0,
    )
    sim.set_input("property_income", YEAR, profit)
    sim.set_input("property_rental_income", YEAR, receipts)
    sim.set_input("property_finance_costs", YEAR, costs)
    sim.set_input("property_finance_costs_brought_forward", YEAR, brought_forward)
    sim.reset_calculations()
    if uses_allowance is not None:
        sim.set_input("uses_property_allowance", YEAR, np.full(PEOPLE, uses_allowance))


def run(sim, drawn):
    set_inputs(sim, drawn)

    def calc(variable):
        return sim.calculate(variable, YEAR).astype(float)

    # Compare against the stored (float32) inputs, not the float64 draws.
    profit = calc("property_income")
    receipts = calc("property_rental_income")
    return dict(
        profit=profit,
        receipts=receipts,
        known=(receipts > 0) & (receipts >= profit),
        expenses=calc("property_allowable_expenses"),
        costs=calc("property_finance_costs"),
        brought_forward=calc("property_finance_costs_brought_forward"),
        uses=sim.calculate("uses_property_allowance", YEAR),
        deduction=calc("property_allowance_deduction"),
        deduction_if_used=calc("property_allowance_deduction_if_used"),
        taxable=calc("taxable_property_income"),
        relievable=calc("property_finance_costs_relievable"),
        relieved=calc("property_finance_costs_relieved"),
        relief=calc("property_finance_cost_relief"),
        carried_forward=calc("property_finance_costs_carried_forward"),
        pre_charges=calc("income_tax_pre_charges"),
        adjusted_net_income=calc("adjusted_net_income"),
        allowances=calc("allowances"),
        income_tax=calc("income_tax"),
    )


def income_tax_on_route(sim, drawn, uses_allowance):
    set_inputs(sim, drawn, uses_allowance)
    return sim.calculate("income_tax", YEAR).astype(float)


def tolerance(*values):
    """A penny plus float32 rounding on the amounts involved."""
    return 0.01 + 1e-6 * sum(np.abs(v) for v in values)


SETTINGS = settings(
    max_examples=30,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)


@SETTINGS
@given(cases)
def test_allowance_is_bounded_and_never_stacks_on_expenses(sim, drawn):
    r = run(sim, drawn)
    assert (r["deduction"] >= 0).all()
    assert (r["deduction"] <= ALLOWANCE + tolerance(ALLOWANCE)).all()
    assert (r["deduction"] <= np.maximum(r["profit"], 0) + tolerance(r["profit"])).all()
    # Deducted from receipts: never more than the larger of actual expenses
    # and the allowance.
    known = r["known"] & (r["receipts"] > ALLOWANCE)
    deducted = r["receipts"] - r["taxable"]
    limit = np.maximum(r["expenses"], ALLOWANCE) + tolerance(r["receipts"])
    assert (deducted[known] <= limit[known]).all()
    # Receipts within the allowance are relieved in full unless the person
    # elects out of it.
    full = r["known"] & (r["receipts"] <= ALLOWANCE) & r["uses"]
    assert (r["taxable"][full] <= tolerance(r["receipts"])[full]).all()


@SETTINGS
@given(cases)
def test_taxable_profit_matches_statutory_reference(sim, drawn):
    r = run(sim, drawn)
    profit = np.maximum(r["profit"], 0)
    allowance_route = np.where(
        r["known"],
        np.where(
            r["receipts"] <= ALLOWANCE,
            0,
            np.minimum(profit, r["receipts"] - ALLOWANCE),
        ),
        np.where(r["profit"] <= ALLOWANCE, 0, profit),
    )
    expected = np.where(r["uses"], allowance_route, profit)
    assert (
        np.abs(r["taxable"] - expected) <= tolerance(r["receipts"], r["profit"])
    ).all()


@SETTINGS
@given(cases)
def test_relief_accounting(sim, drawn):
    r = run(sim, drawn)
    expenses_route = ~r["uses"]
    # Relievable: this year's disallowed costs plus the amount brought forward.
    assert (
        np.abs(r["relievable"] - (r["costs"] + r["brought_forward"]))
        <= tolerance(r["costs"], r["brought_forward"])
    ).all()
    # Relieved: the lowest of the relievable amount, the property profits and
    # adjusted total income, on the expenses route only.
    adjusted_total_income = np.maximum(0, r["adjusted_net_income"] - r["allowances"])
    expected_relieved = np.where(
        expenses_route,
        np.maximum(
            0,
            np.minimum(
                r["relievable"],
                np.minimum(r["taxable"], adjusted_total_income),
            ),
        ),
        0,
    )
    assert (
        np.abs(r["relieved"] - expected_relieved)
        <= tolerance(r["relievable"], r["taxable"], adjusted_total_income)
    ).all()
    # The reduction is at most the property basic rate on the costs, and at
    # most the Step 5 tax.
    assert (r["relief"] >= 0).all()
    assert (
        r["relief"]
        <= PROPERTY_BASIC_RATE * r["relievable"] + tolerance(r["relievable"])
    ).all()
    assert (r["relief"] <= r["pre_charges"] + tolerance(r["pre_charges"])).all()
    # What is not relieved is carried forward; on the allowance route this
    # year's costs are replaced by the allowance and only the amount brought
    # forward is carried on.
    expected_carried = np.where(
        expenses_route, r["relievable"] - r["relieved"], r["brought_forward"]
    )
    assert (
        np.abs(r["carried_forward"] - expected_carried)
        <= tolerance(r["relievable"], r["relieved"])
    ).all()


@SETTINGS
@given(cases)
def test_choice_is_never_worse_than_either_route(sim, drawn):
    r = run(sim, drawn)
    with_allowance = income_tax_on_route(sim, drawn, True)
    with_expenses = income_tax_on_route(sim, drawn, False)
    margin = tolerance(r["income_tax"], with_allowance, with_expenses)
    assert (r["income_tax"] <= with_expenses + margin).all()
    # The allowance route exists where the allowance deducts something.
    available = r["deduction_if_used"] > 0
    assert (r["income_tax"][available] <= (with_allowance + margin)[available]).all()


@SETTINGS
@given(cases)
def test_income_tax_is_non_increasing_in_finance_costs(sim, drawn):
    r = run(sim, drawn)
    base, more = r["income_tax"][:CASES], r["income_tax"][CASES:]
    assert (more <= base + tolerance(base)).all()


# Couples: a partner's route can move a person's tax through the Marriage
# Allowance, so each person must choose with the other's route held fixed.
COUPLES = 12
COUPLE_EMPLOYMENT_INCOME = [0, 9_000, 11_000, 20_000, 30_000, 45_000, 60_000]
couple_member = st.tuples(
    st.sampled_from(COUPLE_EMPLOYMENT_INCOME),
    st.one_of(amount, st.floats(min_value=-1_000, max_value=0)),  # profit
    amount,  # expenses
    st.sampled_from([0.0, 300.0, 850.0, 1_500.0, 6_000.0]),  # finance costs
    st.sampled_from(["unknown", "consistent", "consistent"]),
)
# A close call: the allowance's value over actual expenses (1,000 - expenses)
# within 150 of the finance costs it would give up.
close_call = st.tuples(
    st.sampled_from([20_000, 30_000, 45_000]),
    st.floats(min_value=1_500, max_value=20_000),  # profit
    st.floats(min_value=0, max_value=950),  # expenses
    st.floats(min_value=-150, max_value=150),  # finance costs less the gap
).map(lambda m: (m[0], m[1], m[2], max(1_000 - m[2] + m[3], 1.0), "consistent"))
# A partner within the personal allowance with receipts within the property
# allowance and finance costs, whose route moves their unused allowance.
transferor = st.tuples(
    st.floats(min_value=8_000, max_value=12_500),  # employment income
    st.floats(min_value=50, max_value=1_000),  # profit = receipts
    st.floats(min_value=50, max_value=3_000),  # finance costs
).map(lambda m: (m[0], m[1], 0.0, m[2], "consistent"))
couples = st.lists(
    st.one_of(
        st.tuples(couple_member, couple_member),
        st.tuples(close_call, transferor),
    ),
    min_size=COUPLES,
    max_size=COUPLES,
)


@pytest.fixture(scope="module")
def couple_sim():
    people, benunits, households = {}, {}, {}
    for c in range(COUPLES):
        members = []
        for k in range(2):
            name = f"person_{c}_{k}"
            members.append(name)
            people[name] = {
                "age": {YEAR: 40},
                "employment_income": {YEAR: 0},
                "property_income": {YEAR: 0},
                "property_rental_income": {YEAR: 0},
                "property_finance_costs": {YEAR: 0},
            }
        benunits[f"benunit_{c}"] = {"members": members, "is_married": {YEAR: True}}
        households[f"household_{c}"] = {"members": members}
    return Simulation(
        situation={"people": people, "benunits": benunits, "households": households}
    )


def set_couple_inputs(sim, drawn, uses_allowance=None):
    members = [member for couple in drawn for member in couple]
    employment, profit, expenses, costs, mode = map(np.array, zip(*members))
    receipts = np.where(mode == "consistent", np.maximum(profit, 0) + expenses, 0)
    # The simulation moves employment_income to employment_income_before_lsr
    # when it is built, so that is the input to set.
    sim.set_input("employment_income_before_lsr", YEAR, employment.astype(float))
    sim.set_input("property_income", YEAR, profit)
    sim.set_input("property_rental_income", YEAR, receipts)
    sim.set_input("property_finance_costs", YEAR, costs)
    sim.reset_calculations()
    if uses_allowance is not None:
        sim.set_input("uses_property_allowance", YEAR, uses_allowance)


@SETTINGS
@given(couples)
def test_no_one_lowers_their_tax_by_switching_route_alone(couple_sim, drawn):
    set_couple_inputs(couple_sim, drawn)
    routes = couple_sim.calculate("uses_property_allowance", YEAR)
    income_tax = couple_sim.calculate("income_tax", YEAR).astype(float)
    profit = couple_sim.calculate("property_income", YEAR).astype(float)
    choosing = (
        (couple_sim.calculate("property_allowance_deduction_if_used", YEAR) > 0)
        & (couple_sim.calculate("property_finance_costs_relievable", YEAR) > 0)
        & (profit > 0)
    )
    position = np.arange(2 * COUPLES) % 2
    for k in range(2):
        switching = choosing & (position == k)
        if not switching.any():
            continue
        set_couple_inputs(couple_sim, drawn, routes ^ switching)
        switched_tax = couple_sim.calculate("income_tax", YEAR).astype(float)
        margin = tolerance(income_tax, switched_tax)
        assert (switched_tax[switching] >= (income_tax - margin)[switching]).all()
