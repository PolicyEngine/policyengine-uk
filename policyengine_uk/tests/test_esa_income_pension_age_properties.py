"""Income-related ESA gives way to State Pension Credit only where Pension Credit pays.

Welfare Reform Act 2007 s.1(3)(c) bars ESA for a claimant who has reached
pensionable age, their own State Pension age (s.1(6)). Sch 1 para 6(1)(c) and
(d) bar the income-related allowance where the claimant, or the other member
of the couple, is entitled to State Pension Credit. Pension Credit reads the
couple's award, so the model reads the couple's Pension Credit worked out with
no income-related ESA in the family, B(0), and bars the couple's claim where it
pays.

Each example builds a second, separate simulation of the same people with no
income-related ESA reported. Its pension_credit is B(0), worked out with no
branch. Against it, for every family drawn here:

- where B(0) pays nothing, whether the couple would claim Pension Credit
  changes neither the couple's income-related ESA
  (claimant_or_partner_esa_income) nor the family's (esa_income);
- where B(0) pays, the couple would claim it and has an open report, the
  couple's income-related ESA is nil and the family's Pension Credit is B(0);
- claiming Pension Credit never raises income-related ESA;
- esa_income_eligible equals the family-by-family reading of the law in
  legacy_award_work_reference (esa_screen), given the model's pensionable age
  (is_SP_age) and B(0);
- nobody who has reached pensionable age is on income-related ESA
  (is_on_income_related_esa), and a family whose every report comes from such
  a member gets none.

A family whose Pension Credit pays only with the award, through the higher
earnings disregard the award brings, gets both: no state is consistent there.
The test counts such families and asserts nothing more of them.

The years are 2016, when a man born before 6 December 1953 could be over the
qualifying age for State Pension Credit but under his pensionable age of 65
(Pensions Act 1995 Sch 4 para 1 rule 1), 2018, before the exclusion of
mixed-age couples (SPCA 2002 s.4(1A), from 15 May 2019), and 2026, when only
a mixed-age couple that keeps the SI 2019/37 art 4 saving
(has_mixed_age_couple_pension_credit_saving, drawn) can get Pension Credit.
Adults have earnings, pensions and household savings, so Pension Credit's
means test pays some families and refuses others, and in 2016 and 2018 some
report working tax credit, whose income test the award lifts (TCA 2002
s.7(2)). A member outside the couple claims in their own right: the couple's
Pension Credit does not bar them, and pensionable age does.

Each of would_claim_uc, claims_all_entitled_benefits and the mixed-age saving
would otherwise read the ESA report, so the generator enters them, and no one
reports Housing Benefit, whose saving route also reads it. The test asserts
that the two simulations agree on the Pension Credit age conditions. Roles are
given explicitly (is_claimant_or_partner). Each example builds many families
in one simulation, in separate benefit units, with the take-up copies in the
same simulation. Simulations take most of the time here, so each example
builds two and the file builds few.

Separate tests count the branches the model opens: a population with no couple
that could be on Pension Credit opens none, a branch never outlives the
calculation, and the tax credit passport branch inside it reads the couple's
award as nil.
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, event, example, given, settings
from hypothesis import strategies as st
from policyengine_core.simulations import Simulation as CoreSimulation

from policyengine_uk import Simulation
from policyengine_uk.tests.legacy_award_work_reference import esa_screen
from policyengine_uk.variables.gov.dwp.esa_income_eligible import (
    NO_INCOME_RELATED_ESA_BRANCH,
)

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

YEARS = [2016, 2018, 2026]
# Either side of the State Pension Credit qualifying age and of pensionable
# age in each year drawn, including men aged 62 to 64 in 2016.
AGES = [30, 45, 58, 60, 62, 63, 64, 65, 66, 67, 68, 70, 75, 82]
# 0, 10, 15 and 24 hours a week.
HOURS = [0, 0, 520, 780, 1_248]
# £50, £100 and about £192 a week.
EARNINGS = [0, 0, 2_600, 5_200, 10_000]
# £40, £61 and £200 a week.
PENSIONS = [0, 0, 2_080, 3_172, 10_400]
SAVINGS = [0, 0, 8_000, 14_000, 40_000]


@st.composite
def adults(draw, outside=False, tax_credits=False):
    adult = {
        "age": draw(st.sampled_from(AGES)),
        "months_since_last_birthday": draw(st.sampled_from([0, 3, 8, 11])),
        "gender": draw(st.sampled_from(["MALE", "FEMALE"])),
        "esa_income_reported": draw(st.sampled_from([0, 2_500, 5_000])),
        "esa_includes_support_component": draw(st.booleans()),
        "hours_worked": draw(st.sampled_from(HOURS)),
        "employment_income": draw(st.sampled_from(EARNINGS)),
        "private_pension_income": draw(st.sampled_from(PENSIONS)),
    }
    if outside:
        adult["current_education"] = "NOT_IN_EDUCATION"
    elif tax_credits:
        adult["working_tax_credit_reported"] = draw(st.sampled_from([0, 0, 0, 1]))
    return adult


@st.composite
def families(draw, tax_credits):
    """A claimant, an optional partner, an optional member outside the couple,
    the couple's saving and the household's savings. Members of the couple
    report working tax credit only in a year with tax credits."""
    couple = [draw(adults(tax_credits=tax_credits))]
    if draw(st.booleans()):
        couple.append(draw(adults(tax_credits=tax_credits)))
    others = [draw(adults(outside=True))] if draw(st.integers(0, 3)) == 0 else []
    saving = draw(st.booleans())
    return couple, others, saving, draw(st.sampled_from(SAVINGS))


@st.composite
def examples(draw):
    year = draw(st.sampled_from(YEARS))
    # Tax credits ended on 5 April 2025.
    tax_credits = year < 2025
    units = draw(st.lists(families(tax_credits), min_size=4, max_size=12))
    return units, year


def situation(units, year, would_claim_pc, reports=True):
    """Each family once for each take-up in would_claim_pc. Without reports,
    nobody reports income-related ESA."""
    people, benunits, households = {}, {}, {}
    copies = [(unit, claims) for claims in would_claim_pc for unit in units]
    for i, ((couple, others, saving, savings), claims) in enumerate(copies):
        names = []
        members = [(m, True) for m in couple] + [(m, False) for m in others]
        for j, (inputs, claimant_or_partner) in enumerate(members):
            name = f"p{i}_{j}"
            values = dict(inputs, is_claimant_or_partner=claimant_or_partner)
            if not reports:
                values.pop("esa_income_reported")
            people[name] = {k: {year: v} for k, v in values.items()}
            names.append(name)
        benunits[f"b{i}"] = {
            "members": names,
            "would_claim_uc": {year: False},
            "claims_all_entitled_benefits": {year: False},
            "has_mixed_age_couple_pension_credit_saving": {year: saving},
            "would_claim_pc": {year: claims},
        }
        households[f"h{i}"] = {"members": names, "savings": {year: savings}}
    return {"people": people, "benunits": benunits, "households": households}


def couple_reports(sim, year):
    """Whether the couple has an open report of income-related ESA."""
    open_report = (sim.calculate("esa_income_reported", year) > 0) & ~sim.calculate(
        "esa_income_report_closed", year
    )
    couple = sim.calculate("is_claimant_or_partner", year)
    return sim.populations["benunit"].sum(open_report & couple) > 0


# Each pairing of B(0) and B(e) in 2016, for a man aged 63 born 1 March 1953
# (esa_income_pension_age.yaml cases 15, 16 and 18), the couple of case 19
# whose working tax credit decides it, and a member outside the couple
# reporting beside a pensioner on Pension Credit.
MAN = {
    "age": 63,
    "months_since_last_birthday": 6,
    "gender": "MALE",
    "esa_includes_support_component": True,
    "working_tax_credit_reported": 0,
}
ROWS = [
    (
        [
            dict(
                MAN,
                esa_income_reported=reported,
                employment_income=earnings,
                hours_worked=hours,
                private_pension_income=pension,
            )
        ],
        [],
        False,
        0,
    )
    for reported, earnings, hours, pension in [
        (6_011.20, 2_600, 520, 2_080),
        (4_919.20, 6_006, 780, 3_172),
        (5_491.20, 6_006, 780, 2_600),
    ]
] + [
    (
        [
            {
                "age": 66,
                "months_since_last_birthday": 0,
                "gender": "MALE",
                "esa_income_reported": 0,
                "esa_includes_support_component": False,
                "hours_worked": 1_040,
                "employment_income": 10_000,
                "private_pension_income": 0,
                "working_tax_credit_reported": 1,
            },
            {
                "age": 58,
                "months_since_last_birthday": 0,
                "gender": "FEMALE",
                "esa_income_reported": 3_000,
                "esa_includes_support_component": False,
                "hours_worked": 0,
                "employment_income": 0,
                "private_pension_income": 0,
                "working_tax_credit_reported": 0,
            },
        ],
        [],
        False,
        0,
    ),
    (
        [
            {
                "age": 70,
                "months_since_last_birthday": 0,
                "gender": "FEMALE",
                "esa_income_reported": 0,
                "esa_includes_support_component": False,
                "hours_worked": 0,
                "employment_income": 0,
                "private_pension_income": 0,
                "working_tax_credit_reported": 0,
            }
        ],
        [
            {
                "age": 40,
                "months_since_last_birthday": 0,
                "gender": "MALE",
                "esa_income_reported": 3_000,
                "esa_includes_support_component": False,
                "hours_worked": 0,
                "employment_income": 0,
                "private_pension_income": 0,
                "current_education": "NOT_IN_EDUCATION",
            }
        ],
        False,
        0,
    ),
]


@settings(
    max_examples=4,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
@given(examples())
@example((ROWS, 2016))
def test_couple_esa_follows_pension_credit_worked_out_without_it(drawn):
    units, year = drawn
    n = len(units)
    event(f"year {year}")
    sim = Simulation(situation=situation(units, year, [True, False]))
    oracle = Simulation(situation=situation(units, year, [True], reports=False))
    route = sim.calculate("meets_pension_credit_age_conditions", year)
    # The oracle's Pension Credit reads the same age conditions.
    assert (
        route[:n] == oracle.calculate("meets_pension_credit_age_conditions", year)
    ).all()
    assert (route[:n] == route[n:]).all()
    without_award = oracle.calculate("pension_credit", year)
    pension_credit = sim.calculate("pension_credit", year)
    couple_esa = sim.calculate("claimant_or_partner_esa_income", year)
    esa = sim.calculate("esa_income", year)
    reports = couple_reports(sim, year)
    claims, declines = slice(0, n), slice(n, 2 * n)

    pays = without_award > 0
    barred = pays & reports[claims]
    refused = ~pays
    for label, mask in [
        ("Pension Credit pays without the award", barred),
        ("Pension Credit refuses a couple with a report", refused & reports[claims]),
        (
            "both awards paid",
            (couple_esa[claims] > 0) & (pension_credit[claims] > 0),
        ),
    ]:
        if mask.any():
            event(label)

    # Sch 1 para 6(1)(c) and (d): where Pension Credit pays without the award,
    # the couple's award is nil and the family gets that Pension Credit.
    assert (couple_esa[claims][barred] == 0).all(), units
    assert np.allclose(
        pension_credit[claims][barred], without_award[barred], atol=0.01
    ), units
    # Where it pays nothing, take-up changes no award.
    assert np.allclose(
        couple_esa[claims][refused], couple_esa[declines][refused], atol=0.01
    ), units
    assert np.allclose(esa[claims][refused], esa[declines][refused], atol=0.01), units
    # Claiming Pension Credit never raises income-related ESA.
    assert (esa[claims] <= esa[declines] + 0.01).all(), units

    # The screen, family by family.
    eligible = sim.calculate("esa_income_eligible", year)
    pensionable_age = sim.calculate("is_SP_age", year)
    on_esa = sim.calculate("is_on_income_related_esa", year)
    capital = sim.calculate("esa_income_assessable_capital", year)
    parameters = sim.tax_benefit_system.parameters(year)
    # s.1(3)(c): the award is not payable to anyone over pensionable age.
    assert not (pensionable_age & on_esa).any(), units
    start = 0
    for i, (unit, claimed) in enumerate(
        [(unit, True) for unit in units] + [(unit, False) for unit in units]
    ):
        couple, others, _, _ = unit
        members = [
            dict(member, is_SP_age=pensionable_age[start + j])
            for j, member in enumerate(couple + others)
        ]
        on_pension_credit = claimed and route[i % n] and pays[i % n]
        expected = esa_screen(
            members[: len(couple)],
            members[len(couple) :],
            capital[i],
            parameters,
            on_pension_credit=on_pension_credit,
        )
        assert eligible[i] == expected, (year, claimed, unit)
        reporters = [m["esa_income_reported"] > 0 for m in members]
        if any(reporters) and all(
            m["is_SP_age"] for m, r in zip(members, reporters) if r
        ):
            assert esa[i] == 0, (year, unit)
        start += len(members)


class BranchLog:
    """Records each branch Core creates, with the simulation it branches."""

    def __init__(self, monkeypatch):
        self.created = []
        get_branch = CoreSimulation.get_branch

        def logged(simulation, name="branch", clone_system=False):
            new = name not in simulation.branches and name != simulation.branch_name
            branch = get_branch(simulation, name, clone_system)
            if new:
                self.created.append((simulation, branch))
            return branch

        monkeypatch.setattr(CoreSimulation, "get_branch", logged)

    def bar_branches(self):
        return [
            (parent, branch)
            for parent, branch in self.created
            if branch.branch_name.startswith(NO_INCOME_RELATED_ESA_BRANCH)
        ]


def household(members, year, **benunit):
    names = [f"p{j}" for j in range(len(members))]
    return {
        "people": {
            name: {k: {year: v} for k, v in inputs.items()}
            for name, inputs in zip(names, members)
        },
        "benunits": {
            "b": {
                "members": names,
                "would_claim_uc": {year: False},
                **{k: {year: v} for k, v in benunit.items()},
            }
        },
        "households": {"h": {"members": names}},
    }


def combine(*situations):
    combined = {"people": {}, "benunits": {}, "households": {}}
    for i, part in enumerate(situations):
        for entity, units in part.items():
            for name, unit in units.items():
                unit = dict(unit)
                if "members" in unit:
                    unit["members"] = [f"{m}_{i}" for m in unit["members"]]
                combined[entity][f"{name}_{i}"] = unit
    return combined


def test_no_branch_opens_without_a_couple_that_could_be_on_pension_credit(
    monkeypatch,
):
    """In 2026 no couple here has a claim that passes the other tests and
    meets the Pension Credit age conditions: a working-age claimant reporting
    the award, a couple aged 70 and 60 without the saving (case 4's kind), a
    pensioner without a report, a member outside the couple reporting beside
    a pensioner, and a pensioner reporting the award, whose claim pensionable
    age bars whatever Pension Credit pays."""
    log = BranchLog(monkeypatch)
    year = 2026
    adult = {"is_claimant_or_partner": True}
    sim = Simulation(
        situation=combine(
            household([dict(adult, age=45, esa_income_reported=5_000)], year),
            household(
                [dict(adult, age=70), dict(adult, age=60, esa_income_reported=5_000)],
                year,
            ),
            household([dict(adult, age=75)], year),
            household(
                [
                    dict(adult, age=70),
                    {
                        "age": 40,
                        "is_claimant_or_partner": False,
                        "current_education": "NOT_IN_EDUCATION",
                        "esa_income_reported": 5_000,
                    },
                ],
                year,
            ),
            household([dict(adult, age=75, esa_income_reported=5_000)], year),
        )
    )
    assert sim.calculate("esa_income", year).tolist() == [5_000, 5_000, 0, 5_000, 0]
    assert sim.calculate("meets_pension_credit_age_conditions", year)[-1]
    sim.calculate("household_net_income", year)
    assert log.bar_branches() == []


def test_the_branch_closes_and_its_passport_branch_reads_no_award(monkeypatch):
    """In 2016 the couple of esa_income_pension_age.yaml case 19 meets the
    Pension Credit age conditions with an open report, so the model opens the
    branch, and its working tax credit opens the passport branch inside it
    (pension_credit_with_passported_tax_credits). That branch reads the
    award as nil, set on its parent, and no branch outlives the calculation."""
    log = BranchLog(monkeypatch)
    year = 2016
    sim = Simulation(
        situation=household(
            [
                {
                    "age": 66,
                    "is_claimant_or_partner": True,
                    "employment_income": 10_000,
                    "hours_worked": 1_040,
                    "working_tax_credit_reported": 1,
                },
                {
                    "age": 58,
                    "is_claimant_or_partner": True,
                    "esa_income_reported": 3_000,
                },
            ],
            year,
        )
    )
    assert sim.calculate("esa_income", year).tolist() == [0]
    assert sim.calculate("pension_credit", year) == pytest.approx([370.40], abs=0.01)
    bar_branches = log.bar_branches()
    assert bar_branches
    passports = [
        branch
        for parent, branch in log.created
        if any(parent is bar for _, bar in bar_branches)
        and branch.branch_name.startswith("tax_credits_pension_credit_passport")
    ]
    assert passports
    for passport in passports:
        for variable in ["esa_income", "claimant_or_partner_esa_income"]:
            assert passport.calculate(variable, year).tolist() == [0], variable
    for parent, branch in bar_branches:
        assert all(other is not branch for other in parent.branches.values())
    assert not [
        name for name in sim.branches if name.startswith(NO_INCOME_RELATED_ESA_BRANCH)
    ]
