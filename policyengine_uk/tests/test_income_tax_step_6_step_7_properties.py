"""Property tests for Steps 5 to 7 of the Income Tax calculation (ITA 2007 s. 23).

Step 6 deducts the tax reductions from the tax calculated at Step 5, and only so
far as there is Step 5 tax to deduct them from, counting the reductions already
deducted (s. 29(2) and (3)). Step 7 adds the s. 30 charges, here the High Income
Child Benefit Charge and the annual allowance charge, to the tax left.

Invariants, for every drawn case:

1. Bounds: 0 <= Step 6 deduction <= Step 5 tax.
2. Accounting: the Step 6 deduction is the sum of the reductions (the married
   couple's allowance, other_tax_credits and the finance-cost reduction),
   limited to the Step 5 tax; income tax is the Step 5 tax less the Step 6
   deduction plus the Step 7 charges.
3. Income tax >= the Step 7 charges, so reductions never offset a charge.
4. Income tax <= the Step 5 tax plus the Step 7 charges.
5. The married couple's allowance reduction is at most the Step 5 tax left
   after other_tax_credits (s. 27(5) deducts those reductions before it), and
   the finance-cost reduction at most the tax left after both.
6. Monotonic: more other_tax_credits never raises income tax.
7. Differential: against the formula on main before this fix (76cfc9e79),
   income tax is never lower, and rises by exactly the part of the Step 7
   charges the old netting let the excess reductions offset.

The cases run in one reusable simulation of single-person households: each
case is simulated twice, as drawn and with more other_tax_credits.
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

YEAR = 2026
CASES = 24
PEOPLE = 2 * CASES  # As drawn, then with more other_tax_credits.
# Every third case is a Scottish taxpayer.
SCOTTISH = [i % 3 == 2 for i in range(CASES)]


def amount(maximum, points=()):
    return st.one_of(
        st.just(0.0),
        st.floats(min_value=0, max_value=maximum),
        st.sampled_from([float(p) for p in points] or [0.0]),
    )


case = st.tuples(
    amount(250_000, [12_570, 50_270, 60_000, 80_000, 100_000, 125_140]),  # pay
    amount(30_000),  # savings interest
    amount(60_000),  # dividends
    amount(40_000),  # property profits
    amount(25_000),  # property finance costs
    amount(90_000, [27_432]),  # other_tax_credits
    amount(11_270, [4_360]),  # married couple's allowance
    amount(120_000, [70_000]),  # employer pension contributions
    st.sampled_from([0.0, 0.0, 1_406.6, 2_337.4]),  # Child Benefit
    st.floats(min_value=0, max_value=40_000),  # extra other_tax_credits
)
cases = st.lists(case, min_size=CASES, max_size=CASES)

INPUTS = [
    "employment_income",
    "savings_interest_income",
    "dividend_income",
    "property_income",
    "property_finance_costs",
    "other_tax_credits",
    "married_couples_allowance",
    "employer_pension_contributions",
]


@pytest.fixture(scope="module")
def sim():
    people = {
        f"person_{i}": {"age": {YEAR: 45}, **{v: {YEAR: 0} for v in INPUTS}}
        for i in range(PEOPLE)
    }
    return Simulation(
        situation={
            "people": people,
            "benunits": {
                f"benunit_{i}": {"members": [f"person_{i}"]} for i in range(PEOPLE)
            },
            "households": {
                f"household_{i}": {
                    "members": [f"person_{i}"],
                    "region": {YEAR: "SCOTLAND" if SCOTTISH[i % CASES] else "LONDON"},
                }
                for i in range(PEOPLE)
            },
        }
    )


def run(sim, drawn):
    columns = [np.array(column, dtype=float) for column in zip(*drawn)]
    *inputs, child_benefit, extra_credits = columns
    for variable, values in zip(INPUTS, inputs):
        if variable == "other_tax_credits":
            values = np.concatenate([values, values + extra_credits])
        else:
            values = np.concatenate([values, values])
        sim.set_input(variable, YEAR, values)
    sim.set_input("child_benefit", YEAR, np.concatenate([child_benefit] * 2))
    sim.reset_calculations()

    def calc(variable):
        return sim.calculate(variable, YEAR).astype(float)

    income_tax = sim.tax_benefit_system.parameters(YEAR).gov.hmrc.income_tax
    property_basic_rate = income_tax.rates.property.basic
    return dict(
        listed_reductions=sum(calc(v) for v in income_tax.step_6_tax_reductions),
        listed_charges=sum(calc(v) for v in income_tax.step_7_additional_tax),
        step_5=calc("income_tax_pre_charges"),
        step_6=calc("income_tax_reductions"),
        step_7=calc("income_tax_charges"),
        hicbc=calc("CB_HITC"),
        annual_allowance_charge=calc("personal_pension_contributions_tax"),
        other_tax_credits=calc("other_tax_credits"),
        mca_deduction=calc("married_couples_allowance_deduction"),
        capped_mcad=calc("capped_mcad"),
        finance_cost_reduction=calc("property_finance_cost_relief"),
        finance_cost_reduction_uncapped=property_basic_rate
        * calc("property_finance_costs_relieved"),
        income_tax=calc("income_tax"),
    )


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
def test_step_6_deduction_is_the_reductions_limited_to_the_step_5_tax(sim, drawn):
    r = run(sim, drawn)
    tol = tolerance(r["step_5"], r["other_tax_credits"])
    assert (r["step_5"] >= 0).all()
    assert (r["step_6"] >= 0).all()
    assert (r["step_6"] <= r["step_5"] + tol).all()
    limited = np.minimum(r["listed_reductions"], r["step_5"])
    assert (np.abs(r["step_6"] - limited) <= tol).all()


@SETTINGS
@given(cases)
def test_income_tax_is_step_5_less_step_6_plus_step_7(sim, drawn):
    r = run(sim, drawn)
    charges = r["listed_charges"]
    tol = tolerance(r["step_5"], charges)
    assert (np.abs(r["step_7"] - charges) <= tol).all()
    # Both modelled s. 30 charges are on the Step 7 list.
    assert (charges >= r["hicbc"] + r["annual_allowance_charge"] - tol).all()
    expected = r["step_5"] - r["step_6"] + charges
    assert (np.abs(r["income_tax"] - expected) <= tol).all()
    # Reductions never offset a Step 7 charge, and never add tax.
    assert (r["income_tax"] >= charges - tol).all()
    assert (r["income_tax"] <= r["step_5"] + charges + tol).all()


@SETTINGS
@given(cases)
def test_each_reduction_is_limited_to_the_tax_left_before_it(sim, drawn):
    r = run(sim, drawn)
    tol = tolerance(r["step_5"], r["other_tax_credits"])
    left_after_credits = np.maximum(0, r["step_5"] - r["other_tax_credits"])
    assert (r["capped_mcad"] >= 0).all()
    assert (
        np.abs(r["capped_mcad"] - np.minimum(r["mca_deduction"], left_after_credits))
        <= tol
    ).all()
    left_after_mca = np.maximum(0, left_after_credits - r["capped_mcad"])
    assert (r["finance_cost_reduction"] <= left_after_mca + tol).all()
    assert (
        r["finance_cost_reduction"] <= r["finance_cost_reduction_uncapped"] + tol
    ).all()


@SETTINGS
@given(cases)
def test_more_other_tax_credits_never_raise_income_tax(sim, drawn):
    r = run(sim, drawn)
    drawn_tax, with_more = r["income_tax"][:CASES], r["income_tax"][CASES:]
    assert (with_more <= drawn_tax + tolerance(drawn_tax)).all()
    # The other inputs are the same, so the Step 5 tax and charges are too.
    assert np.allclose(r["step_5"][:CASES], r["step_5"][CASES:])
    assert np.allclose(r["step_7"][:CASES], r["step_7"][CASES:])


def income_tax_before_the_fix(r):
    """income_tax on main at 76cfc9e79: max(0, additions - subtractions), with
    the married couple's allowance capped at the Step 5 tax plus the High Income
    Child Benefit Charge, and the finance-cost reduction at the Step 5 tax left
    after the other reductions."""
    capped_mcad = np.minimum(r["mca_deduction"], r["step_5"] + r["hicbc"])
    finance_cost_reduction = np.minimum(
        r["finance_cost_reduction_uncapped"],
        np.maximum(0, r["step_5"] - capped_mcad - r["other_tax_credits"]),
    )
    additions = r["step_5"] + r["hicbc"] + r["annual_allowance_charge"]
    subtractions = capped_mcad + r["other_tax_credits"] + finance_cost_reduction
    return np.maximum(0, additions - subtractions), subtractions


@SETTINGS
@given(cases)
def test_the_fix_restores_exactly_the_charges_the_old_netting_offset(sim, drawn):
    r = run(sim, drawn)
    old, old_reductions = income_tax_before_the_fix(r)
    charges = r["hicbc"] + r["annual_allowance_charge"]
    excess = np.maximum(0, old_reductions - r["step_5"])
    tol = tolerance(r["step_5"], charges, r["other_tax_credits"])
    assert (r["income_tax"] >= old - tol).all()
    assert (np.abs((r["income_tax"] - old) - np.minimum(charges, excess)) <= tol).all()
    # The finance-cost reduction was already limited correctly.
    finance_cost_old = np.minimum(
        r["finance_cost_reduction_uncapped"],
        np.maximum(
            0,
            r["step_5"]
            - np.minimum(r["mca_deduction"], r["step_5"] + r["hicbc"])
            - r["other_tax_credits"],
        ),
    )
    assert (np.abs(r["finance_cost_reduction"] - finance_cost_old) <= tol).all()


def test_the_step_lists_are_disjoint_and_hold_the_modelled_provisions():
    from policyengine_uk import CountryTaxBenefitSystem

    system = CountryTaxBenefitSystem()
    p = system.parameters(YEAR).gov.hmrc.income_tax
    step_5 = list(p.step_5_tax_components)
    step_6 = list(p.step_6_tax_reductions)
    step_7 = list(p.step_7_additional_tax)
    assert set(step_5) == {
        "earned_income_tax",
        "savings_income_tax",
        "dividend_income_tax",
        "property_income_tax",
    }
    assert {
        "capped_mcad",
        "other_tax_credits",
        "property_finance_cost_relief",
    } <= set(step_6)
    assert {"CB_HITC", "personal_pension_contributions_tax"} <= set(step_7)
    every = step_5 + step_6 + step_7
    assert len(every) == len(set(every))
    assert all(variable in system.variables for variable in every)
