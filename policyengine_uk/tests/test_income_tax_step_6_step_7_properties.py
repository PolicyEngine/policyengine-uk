"""Property tests for Steps 5 to 7 of the Income Tax calculation (ITA 2007 s. 23).

Step 6 deducts the tax reductions from the tax calculated at Step 5, and only so
far as there is Step 5 tax to deduct them from, counting the reductions already
deducted (s. 29(2) and (3)). Step 7 adds the s. 30 charges, here the High Income
Child Benefit Charge and the annual allowance charge, to the tax left.

Invariants, for every drawn case:

1. Bounds: 0 <= Step 6 deduction <= Step 5 tax.
2. Accounting: the Step 6 deduction is the sum of the reductions on the Step 6
   list, limited to the Step 5 tax; income tax is the Step 5 tax less the Step 6
   deduction plus the Step 7 charges.
3. Income tax >= the Step 7 charges, so reductions never offset a charge.
4. Income tax <= the Step 5 tax plus the Step 7 charges.
5. The married couple's allowance reduction is at most the Step 5 tax left
   after other_tax_credits, and the finance-cost reduction at most the tax left
   after both. s. 27(5) deducts the VCT, EIS, SEIS, social investment,
   community investment and maintenance reductions before the married couple's
   allowance; other_tax_credits also holds foreign tax relief, which s. 27(6)
   deducts last. The order changes how the total is split, not the total.
6. Monotonic: more other_tax_credits never raises income tax. The Step 5 tax
   and the charges can change with them, because the property allowance
   election weighs the income tax on each route.
7. Differential, against a simulation of the rules before this fix (main at
   76cfc9e79: max(0, additions - subtractions), with the married couple's
   allowance capped at the Step 5 tax plus the High Income Child Benefit
   Charge): income tax is never lower, since it is never lower on either
   property allowance route and the election takes the cheaper one. Where both
   take the same route, the Step 5 tax, the charges and the finance-cost
   reduction are unchanged, and income tax rises by exactly the part of the
   Step 7 charges the old netting let the excess reductions offset.

The cases run in reusable simulations of single-person households, a third of
them Scottish taxpayers and a third over State Pension age: each case is
simulated twice, as drawn and with more other_tax_credits.
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from policyengine_core.reforms import Reform

from policyengine_uk import Simulation
from policyengine_uk.model_api import GBP, YEAR as YEAR_PERIOD, Person, Variable
from policyengine_uk.model_api import add, max_, min_

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

YEAR = 2026
CASES = 24
PEOPLE = 2 * CASES  # As drawn, then with more other_tax_credits.
SCOTTISH = [i % 3 == 2 for i in range(CASES)]
# The liability built from Steps 5 to 7.
INCOME_TAX = "income_tax"


def amount(maximum, points=()):
    return st.one_of(
        st.just(0.0),
        st.floats(min_value=0, max_value=maximum),
        st.sampled_from([float(p) for p in points] or [0.0]),
    )


case = st.tuples(
    amount(250_000, [12_570, 50_270, 60_000, 80_000, 90_000, 100_000, 125_140]),
    amount(30_000),  # savings interest
    amount(60_000),  # dividends
    amount(40_000, [10_000]),  # property profits, all of them receipts
    amount(25_000, [2_000]),  # property finance costs
    amount(90_000, [27_200, 27_432]),  # other_tax_credits
    amount(11_270, [4_360]),  # married couple's allowance
    amount(120_000, [70_000]),  # employer pension contributions
    st.sampled_from([45.0, 45.0, 70.0]),  # age
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
    "age",
]


class capped_mcad(Variable):
    value_type = float
    entity = Person
    label = "capped Married Couples' Allowance deduction before the fix"
    definition_period = YEAR_PERIOD
    unit = GBP

    def formula(person, period, parameters):
        return min_(
            person("married_couples_allowance_deduction", period),
            add(person, period, ["income_tax_pre_charges", "CB_HITC"]),
        )


def _income_tax_before_the_fix(person, period, parameters):
    p = parameters(period).gov.hmrc.income_tax
    additions = add(person, period, ["income_tax_pre_charges", "income_tax_charges"])
    return max_(0, additions - add(person, period, p.step_6_tax_reductions))


PRE_FIX_INCOME_TAX = type(
    INCOME_TAX,
    (Variable,),
    dict(
        value_type=float,
        entity=Person,
        label="Income Tax before the fix",
        definition_period=YEAR_PERIOD,
        unit=GBP,
        formula=_income_tax_before_the_fix,
    ),
)


class PRE_FIX(Reform):
    def apply(self):
        self.update_variable(capped_mcad)
        self.update_variable(PRE_FIX_INCOME_TAX)


def build(reform=None):
    people = {
        f"person_{i}": {
            **{v: {YEAR: 0} for v in INPUTS},
            "age": {YEAR: 45},
            "property_rental_income": {YEAR: 0},
        }
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
        },
        reform=reform,
    )


@pytest.fixture(scope="module")
def sim():
    return build()


@pytest.fixture(scope="module")
def pre_fix_sim():
    return build(PRE_FIX)


def run(sim, drawn):
    # Reset first: it clears inputs the simulation was not built with, such as
    # Child Benefit, which would otherwise be lost.
    sim.reset_calculations()
    columns = [np.array(column, dtype=float) for column in zip(*drawn)]
    *inputs, child_benefit, extra_credits = columns
    supplied = {}
    for variable, values in zip(INPUTS, inputs):
        extra = extra_credits if variable == "other_tax_credits" else 0
        supplied[variable] = np.concatenate([values, values + extra])
        sim.set_input(variable, YEAR, supplied[variable])
    sim.set_input("property_rental_income", YEAR, supplied["property_income"])
    supplied["child_benefit"] = np.concatenate([child_benefit] * 2)
    sim.set_input("child_benefit", YEAR, supplied["child_benefit"])

    def calc(variable):
        return sim.calculate(variable, YEAR).astype(float)

    # The drawn inputs reach the calculation.
    for variable, values in supplied.items():
        assert np.allclose(calc(variable), values, rtol=1e-6, atol=0.01), variable

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
        uses_property_allowance=sim.calculate("uses_property_allowance", YEAR),
        income_tax=calc(INCOME_TAX),
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


@SETTINGS
@given(cases)
def test_against_the_rules_before_the_fix(sim, pre_fix_sim, drawn):
    new, old = run(sim, drawn), run(pre_fix_sim, drawn)
    tol = tolerance(new["step_5"], new["step_7"], new["other_tax_credits"])
    # The pre-fix simulation reproduces main's formulas.
    assert (
        np.abs(
            old["capped_mcad"]
            - np.minimum(old["mca_deduction"], old["step_5"] + old["hicbc"])
        )
        <= tol
    ).all()
    old_expected = np.maximum(
        0, old["step_5"] + old["step_7"] - old["listed_reductions"]
    )
    assert (np.abs(old["income_tax"] - old_expected) <= tol).all()
    # Never lower, whichever route each election takes.
    assert (new["income_tax"] >= old["income_tax"] - tol).all()
    # On the same route, only the offset charges come back.
    same = new["uses_property_allowance"] == old["uses_property_allowance"]
    for variable in ["step_5", "step_7", "finance_cost_reduction"]:
        assert (np.abs(new[variable] - old[variable])[same] <= tol[same]).all()
    excess = np.maximum(0, old["listed_reductions"] - old["step_5"])
    restored = np.minimum(old["step_7"], excess)
    raised = new["income_tax"] - old["income_tax"]
    assert (np.abs(raised - restored)[same] <= tol[same]).all()


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
