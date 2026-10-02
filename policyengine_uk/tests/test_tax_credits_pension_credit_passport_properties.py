"""State Pension Credit lifts the tax credit income test.

TCA 2002 s.7(2) lifts the income test "for so long as the person, or either
of the persons, is entitled to" a benefit prescribed by SI 2002/2008 reg 4(1),
which includes "state pension credit" (reg 4(1)(d)): the guarantee credit,
the savings credit or both (SPCA 2002 s.1(3)). Working tax credit is Pension
Credit income (SPCA 2002 s.15(1)(b)), so the passport is decided on the
Pension Credit payable with the passported award counted. The model takes
that from a branch in which the income test is lifted.

Properties, for any family:

1. Differential: the passport holds exactly when an independent simulation,
   with the tax credit income test lifted by input, pays Pension Credit.
   Otherwise the applicable income is what it is with the Pension Credit
   passport switched off.
2. Consistency: where Pension Credit gives the passport, the simulation's own
   tax credits and Pension Credit equal the passported simulation's. Where it
   does not, they equal the values with the passport switched off.
3. Lifting the income test never lowers a tax credit award.
4. Pension Credit in payment without the passport happens only where the
   passported working tax credit would be larger than the income-tested one
   and would remove Pension Credit; a family with no working tax credit is
   passported whenever it gets Pension Credit.
5. The results do not depend on whether Pension Credit or the income test is
   requested first, and the branch is removed afterwards.
6. In a year with no tax credit awards, the income test is lifted exactly
   when Pension Credit is payable, with no dependency cycle.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.variables.gov.dwp.tax_credits_applicable_income import (
    PENSION_CREDIT_PASSPORT_BRANCH,
)

ACTIVE_YEAR = 2024  # 2024-25, the last year of tax credit awards
INACTIVE_YEAR = 2025
PASSPORT_OFF = {"gov.dwp.tax_credits.means_test.pension_credit_passport": False}
OUTPUTS = [
    "tax_credits_applicable_income",
    "working_tax_credit",
    "child_tax_credit",
    "pension_credit",
]


@st.composite
def adults(draw, partner):
    age = draw(st.integers(40 if partner else 55, 90))
    earnings = draw(st.sampled_from([0, 0, 2_600, 6_000, 12_000]))
    return {
        "age": age,
        "employment_income": earnings,
        "weekly_hours": draw(st.sampled_from([16, 20, 30])) if earnings else 0,
        "state_pension": (
            draw(st.sampled_from([0, 4_000, 6_000, 9_000, 11_500])) if age >= 66 else 0
        ),
        "private_pension_income": draw(st.sampled_from([0, 0, 1_500, 5_000])),
        "savings_interest_income": draw(st.sampled_from([0, 0, 500])),
        "working_tax_credit_reported": draw(st.sampled_from([0, 1])),
        "child_tax_credit_reported": draw(st.sampled_from([0, 1])),
        "esa_income_reported": draw(st.sampled_from([0, 0, 0, 0, 3_000])),
    }


@st.composite
def families(draw):
    members = [draw(adults(partner=False))]
    if draw(st.booleans()):
        members.append(draw(adults(partner=True)))
    children = [
        {"age": draw(st.integers(0, 15))} for _ in range(draw(st.integers(0, 2)))
    ]
    benunit = {"would_claim_pc": draw(st.sampled_from([True, True, True, False]))}
    household = {"savings": draw(st.sampled_from([0, 5_000, 12_000, 20_000]))}
    return members, children, benunit, household


def situation(families, year, benunit_inputs=None):
    people, benunits, households = {}, {}, {}
    for i, (members, children, benunit, household) in enumerate(families):
        names = []
        for j, inputs in enumerate(members):
            name = f"a{i}_{j}"
            people[name] = {k: {year: v} for k, v in inputs.items()}
            people[name]["is_claimant_or_partner"] = {year: True}
            names.append(name)
        for j, inputs in enumerate(children):
            name = f"c{i}_{j}"
            people[name] = {k: {year: v} for k, v in inputs.items()}
            people[name]["is_claimant_or_partner"] = {year: False}
            names.append(name)
        benunits[f"b{i}"] = {
            "members": names,
            "would_claim_uc": {year: False},
            **{k: {year: v} for k, v in benunit.items()},
            **{k: {year: v} for k, v in (benunit_inputs or {}).items()},
        }
        households[f"h{i}"] = {
            "members": names,
            **{k: {year: v} for k, v in household.items()},
        }
    return {"people": people, "benunits": benunits, "households": households}


def calculate(sim, year, order=OUTPUTS):
    values = {variable: sim.calculate(variable, year) for variable in order}
    assert PENSION_CREDIT_PASSPORT_BRANCH not in sim.branches
    return values


SETTINGS = settings(
    max_examples=20,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
FAMILIES = st.lists(families(), min_size=1, max_size=6)


@SETTINGS
@given(FAMILIES)
def test_passport_matches_an_independent_passported_simulation(drawn):
    on = calculate(Simulation(situation=situation(drawn, ACTIVE_YEAR)), ACTIVE_YEAR)
    off = calculate(
        Simulation(situation=situation(drawn, ACTIVE_YEAR), reform=PASSPORT_OFF),
        ACTIVE_YEAR,
    )
    lifted = calculate(
        Simulation(
            situation=situation(
                drawn,
                ACTIVE_YEAR,
                benunit_inputs={"tax_credits_applicable_income": 0},
            )
        ),
        ACTIVE_YEAR,
    )
    passported = lifted["pension_credit"] > 0
    # 1. Differential.
    expected = np.where(passported, 0, off["tax_credits_applicable_income"])
    assert np.allclose(on["tax_credits_applicable_income"], expected), drawn
    # 2. Consistency.
    for variable in OUTPUTS[1:]:
        expected = np.where(passported, lifted[variable], off[variable])
        assert np.allclose(on[variable], expected, atol=0.01), (variable, drawn)
    # 3. Lifting the test never lowers an award.
    for variable in ["working_tax_credit", "child_tax_credit"]:
        assert (on[variable] >= off[variable] - 0.01).all(), (variable, drawn)
    # 4. Pension Credit without the passport needs a passported WTC award
    # larger than the income-tested one (which then removes Pension Credit),
    # so a family with no WTC is passported whenever it gets Pension Credit.
    unpassported_pc = (on["pension_credit"] > 0) & ~passported
    assert (
        lifted["working_tax_credit"][unpassported_pc]
        > on["working_tax_credit"][unpassported_pc]
    ).all(), drawn


@SETTINGS
@given(FAMILIES)
def test_results_do_not_depend_on_request_order(drawn):
    forward = calculate(
        Simulation(situation=situation(drawn, ACTIVE_YEAR)), ACTIVE_YEAR
    )
    backward = calculate(
        Simulation(situation=situation(drawn, ACTIVE_YEAR)),
        ACTIVE_YEAR,
        order=list(reversed(OUTPUTS)),
    )
    for variable in OUTPUTS:
        assert np.allclose(forward[variable], backward[variable]), (variable, drawn)


@SETTINGS
@given(FAMILIES)
def test_without_awards_pension_credit_alone_decides_the_passport(drawn):
    on = calculate(Simulation(situation=situation(drawn, INACTIVE_YEAR)), INACTIVE_YEAR)
    off = calculate(
        Simulation(situation=situation(drawn, INACTIVE_YEAR), reform=PASSPORT_OFF),
        INACTIVE_YEAR,
    )
    assert (on["working_tax_credit"] == 0).all()
    assert (on["child_tax_credit"] == 0).all()
    assert np.allclose(on["pension_credit"], off["pension_credit"]), drawn
    expected = np.where(
        on["pension_credit"] > 0, 0, off["tax_credits_applicable_income"]
    )
    assert np.allclose(on["tax_credits_applicable_income"], expected), drawn


def test_passport_works_in_traced_and_nested_branch_simulations():
    """The branch runs under tracing and inside another branch.

    The household is the YAML's first case (Guarantee Credit with Working Tax
    Credit). The marginal tax rate calculates household income in its own
    branch, so the passport branch is nested there.
    """
    year = ACTIVE_YEAR
    family = (
        [
            {
                "age": 70,
                "employment_income": 2_600,
                "weekly_hours": 20,
                "state_pension": 6_000,
                "working_tax_credit_reported": 1,
            }
        ],
        [],
        {"pension_credit_earnings": 2_340},
        {},
    )
    for trace in [False, True]:
        sim = Simulation(situation=situation([family], year), trace=trace)
        assert sim.calculate("tax_credits_applicable_income", year)[0] == 0
        assert np.isclose(sim.calculate("working_tax_credit", year)[0], 2_435)
        assert np.isclose(sim.calculate("pension_credit", year)[0], 568.80)
        mtr = sim.calculate("marginal_tax_rate", year)[0]
        assert np.isfinite(mtr)
        assert PENSION_CREDIT_PASSPORT_BRANCH not in sim.branches
        for branch in sim.branches.values():
            assert PENSION_CREDIT_PASSPORT_BRANCH not in branch.branches
