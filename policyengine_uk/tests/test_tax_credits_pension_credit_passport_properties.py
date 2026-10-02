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
   passport switched off. (This checks the branch against the same rule
   computed outside the formula, so it catches stale or leaked caches; the
   rule itself is checked against the law by the YAML cases.)
2. Consistency: where Pension Credit gives the passport, the simulation's own
   tax credits and Pension Credit equal the passported simulation's. Where it
   does not, they equal the values with the passport switched off.
3. Lifting the income test never lowers a tax credit award.
4. Pension Credit in payment without the passport happens only where the
   passported working tax credit would be larger than the income-tested one
   and would remove Pension Credit; a family with no working tax credit is
   passported whenever it gets Pension Credit.
5. The results do not depend on whether Pension Credit, the income test or
   household net income is requested first, and the branch is removed
   afterwards.
6. In a year with no tax credit awards, the income test is lifted exactly
   when Pension Credit is payable, with no dependency cycle.
7. The targeted childcare tax credit criteria are met only where the gross
   (pre-passport) income is within the £16,190 limit.
"""

import numpy as np
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from policyengine_uk import Microsimulation, Simulation
from policyengine_uk.variables.gov.dwp.tax_credits_applicable_income import (
    PENSION_CREDIT_PASSPORT_BRANCH,
    pension_credit_with_passported_tax_credits,
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
        # Income-related ESA ends at State Pension age.
        "esa_income_reported": (
            draw(st.sampled_from([0, 0, 0, 0, 3_000])) if age < 66 else 0
        ),
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


def no_passport_branch_left(sim):
    """No passport branch remains, at any depth of branching."""
    for name, branch in sim.branches.items():
        if name.startswith(PENSION_CREDIT_PASSPORT_BRANCH):
            return False
        if not no_passport_branch_left(branch):
            return False
    return True


def calculate(sim, year, order=OUTPUTS):
    values = {variable: sim.calculate(variable, year) for variable in order}
    assert no_passport_branch_left(sim)
    return values


SETTINGS = settings(
    max_examples=20,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
FAMILIES = st.lists(families(), min_size=1, max_size=6)

# The YAML cases, run on every invocation: random draws seldom raise CTC or
# hit the third row. Pension Credit earnings are net of SPC Regs Sch VI
# para 5; the CTC family element and the Sch IIA child amount are entered at
# their statutory values (see the YAML file).
_PENSIONER = {
    "age": 70,
    "employment_income": 2_600,
    "weekly_hours": 20,
    "savings_interest_income": 300,
    "working_tax_credit_reported": 1,
}
YAML_FAMILIES = [
    # Guarantee Credit with WTC: passported.
    (
        [{**_PENSIONER, "state_pension": 6_000}],
        [],
        {"pension_credit_earnings": 2_340},
        {"savings": 10_000},
    ),
    # Pension Credit only on the income-tested award: the third row.
    (
        [{**_PENSIONER, "state_pension": 6_600}],
        [],
        {"pension_credit_earnings": 2_340},
        {"savings": 10_000},
    ),
    # Savings Credit alone, with CTC raised by the passport.
    (
        [
            {
                "age": 80,
                "state_pension": 9_000,
                "employment_income": 3_000,
                "savings_interest_income": 500,
                "child_tax_credit_reported": 1,
            },
            {"age": 80, "state_pension": 8_000},
        ],
        [{"age": 10}],
        {
            "pension_credit_earnings": 2_480,
            "child_minimum_guarantee_addition": 0,
            "CTC_family_element": 545,
        },
        {"savings": 10_000},
    ),
    # A mixed-age couple: no Pension Credit, no passport.
    (
        [
            {**_PENSIONER, "state_pension": 6_000},
            {"age": 40},
        ],
        [],
        {},
        {"savings": 10_000},
    ),
]


@SETTINGS
@given(FAMILIES)
@example(YAML_FAMILIES)
def test_passport_matches_an_independent_passported_simulation(drawn):
    sim = Simulation(situation=situation(drawn, ACTIVE_YEAR))
    on = calculate(sim, ACTIVE_YEAR)
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
    # 7. The childcare tax credit criteria test gross income, not the nil
    # income of a passported award.
    gross = sim.calculate("tax_credits_current_year_income", ACTIVE_YEAR)
    limit = sim.tax_benefit_system.parameters(
        ACTIVE_YEAR
    ).gov.dfe.targeted_childcare_entitlement.income_limit.tax_credits
    for criterion in [
        "meets_child_tax_credit_criteria_for_targeted_childcare_entitlement",
        "meets_working_tax_credit_criteria_for_targeted_childcare_entitlement",
    ]:
        met = sim.calculate(criterion, ACTIVE_YEAR)
        assert (gross[met] <= limit).all(), (criterion, drawn)


@SETTINGS
@given(FAMILIES)
@example(YAML_FAMILIES)
def test_results_do_not_depend_on_request_order(drawn):
    forward = calculate(
        Simulation(situation=situation(drawn, ACTIVE_YEAR)), ACTIVE_YEAR
    )
    backward = calculate(
        Simulation(situation=situation(drawn, ACTIVE_YEAR)),
        ACTIVE_YEAR,
        order=list(reversed(OUTPUTS)),
    )
    household_first = calculate(
        Simulation(situation=situation(drawn, ACTIVE_YEAR)),
        ACTIVE_YEAR,
        order=["household_net_income"] + OUTPUTS,
    )
    for variable in OUTPUTS:
        assert np.allclose(forward[variable], backward[variable]), (variable, drawn)
        assert np.allclose(forward[variable], household_first[variable]), (
            variable,
            drawn,
        )


@SETTINGS
@given(FAMILIES)
@example(YAML_FAMILIES)
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
        assert no_passport_branch_left(sim)


def test_passport_in_a_microsimulation_is_unweighted():
    """In a microsimulation the branch's Pension Credit is a plain array.

    A top-level calculate on a microsimulation returns a weighted series;
    reading the branch through its population does not.
    """
    year = ACTIVE_YEAR
    micro = Microsimulation(situation=situation(YAML_FAMILIES, year))
    plain = Simulation(situation=situation(YAML_FAMILIES, year))
    for variable in OUTPUTS:
        assert np.allclose(
            np.asarray(micro.calculate(variable, year)),
            plain.calculate(variable, year),
        ), variable
    result = pension_credit_with_passported_tax_credits(
        micro.populations["benunit"], year, micro.tax_benefit_system.parameters
    )
    assert type(result) is np.ndarray
    assert no_passport_branch_left(micro)


def test_yaml_families_reach_every_case():
    """The pinned examples are not vacuous: they hit each row of the rule."""
    year = ACTIVE_YEAR
    on = calculate(Simulation(situation=situation(YAML_FAMILIES, year)), year)
    off = calculate(
        Simulation(situation=situation(YAML_FAMILIES, year), reform=PASSPORT_OFF),
        year,
    )
    passported = (on["tax_credits_applicable_income"] == 0) & (
        off["tax_credits_applicable_income"] > 0
    )
    assert passported.tolist() == [True, False, True, False]
    # The passport raises WTC (first) and CTC (third).
    assert on["working_tax_credit"][0] > off["working_tax_credit"][0]
    assert on["child_tax_credit"][2] > off["child_tax_credit"][2]
    # The third row: Pension Credit paid without the passport.
    assert on["pension_credit"][1] > 0 and not passported[1]
    # The mixed-age couple gets no Pension Credit.
    assert on["pension_credit"][3] == 0
