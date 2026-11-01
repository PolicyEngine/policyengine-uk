"""The model refuses a couple income-related ESA only where the couple would
get State Pension Credit without it.

Parliament bars ESA for a claimant who has reached pensionable age, their own
State Pension age (Welfare Reform Act 2007 s.1(3)(c) and s.1(6)), and bars the
income-related allowance where the claimant, or the other member of the
couple, has an entitlement to State Pension Credit (Sch 1 para 6(1)(c) and
(d)). The model's Pension Credit reads the couple's award, so the model reads
the Pension Credit the couple would get with no income-related ESA in the
family, B(0), and refuses the couple's claim where B(0) exceeds nil.

Each example builds a second, separate simulation of the same people with no
income-related ESA reported. Its pension_credit gives B(0) without a branch.
Against it, for every family drawn here:

- where B(0) is nil, whether the couple would claim Pension Credit changes
  neither the couple's income-related ESA (claimant_or_partner_esa_income)
  nor the family's (esa_income);
- where B(0) exceeds nil, the couple would claim it and has an open report,
  the couple's income-related ESA is nil and the family's Pension Credit is
  B(0);
- claiming Pension Credit never raises income-related ESA;
- esa_income_eligible equals the family-by-family reading of the law in
  legacy_award_work_reference (esa_screen), given the model's pensionable age
  (is_SP_age) and B(0);
- nobody who has reached pensionable age is on income-related ESA
  (is_on_income_related_esa), and a family whose every report comes from such
  a member gets none.

A family that gets Pension Credit only with the award, through the higher
earnings disregard the award brings, gets both: no state is consistent there.
The test counts such families and asserts nothing more of them.

The years are 2016, when a man born before 6 December 1953 could be over the
qualifying age for State Pension Credit but under his pensionable age of 65
(Pensions Act 1995 Sch 4 para 1 rule 1), 2018, before the exclusion of
mixed-age couples (SPCA 2002 s.4(1A), from 15 May 2019), and 2026, when only
a mixed-age couple that keeps the SI 2019/37 art 4 saving
(has_mixed_age_couple_pension_credit_saving, drawn) can get Pension Credit.
Adults have earnings, pensions and household savings, so some families pass
Pension Credit's means test and others fail it, and in 2016 and 2018 some
report working tax credit, which HMRC pays without its income test to a
family on the award (TCA 2002 s.7(2)). A member outside the couple claims in their own right: the couple's
Pension Credit leaves their claim alone, and their pensionable age does not.

Each of would_claim_uc, claims_all_entitled_benefits and the mixed-age saving
would otherwise read the ESA report, so the generator enters them, and no one
reports Housing Benefit, whose saving route also reads it. The test asserts
that the two simulations agree on the Pension Credit age conditions. Roles are
given explicitly (is_claimant_or_partner). Each example builds many families
in one simulation, in separate benefit units, with the take-up copies in the
same simulation. Simulations take most of the time here, so each example
builds two and the file builds few.

A differential test runs the drawn families through a reform that calculates
the model's Pension Credit by a formula of its own, so the screen reads
Pension Credit for every couple whose claim passes the other tests, and
requires the same results as the model, which reads it only for a couple
that meets the age conditions and would claim.

Separate tests count the branches the model opens and the variables the
screen reads: a population with no couple that could be on Pension Credit
opens none, a branch never outlives the calculation, the tax credit passport
branch inside it reads the couple's award as nil, and the screen reads no
Pension Credit condition without a couple's claim that passes the other
tests. Others enter Pension Credit, or a part of it, as an input, or reform
it: an entered award, a reform that pays every family and a frozen award each
make the model read the award for every couple, and a parameter reform keeps
the age and take-up conditions.
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, event, example, given, settings
from hypothesis import strategies as st
from policyengine_core.periods import period as period_
from policyengine_core.reforms import Reform
from policyengine_core.simulations import Simulation as CoreSimulation

from policyengine_uk import Simulation
from policyengine_uk.model_api import GBP, YEAR, BenUnit, Variable
from policyengine_uk.tests.legacy_award_work_reference import esa_screen
from policyengine_uk.variables.gov.dwp.esa_income_eligible import (
    NO_INCOME_RELATED_ESA_BRANCH,
    pension_credit_follows_model_formulas,
)
from policyengine_uk.variables.gov.dwp.pension_credit.pension_credit import (
    pension_credit as model_pension_credit,
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


# Each pairing of B(0) and B(e) in 2016, for a man aged 63 and six months, whom
# the model takes to be born on 6 April 1953, with the earnings, pensions and
# awards of esa_income_pension_age.yaml cases 15, 16 and 18; the couple of case
# 19, whose working tax credit decides the pairing; and a member outside the
# couple reporting beside a pensioner on Pension Credit.
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
    a pensioner, and a pensioner reporting the award, who has reached
    pensionable age and so has no claim whatever Pension Credit pays."""
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


# The man of esa_income_pension_age.yaml cases 7 and 8, born 1 March 1953: in
# 2016 he meets the Pension Credit age conditions, under his pensionable age.
# A man aged 40 does not meet them.
MAN_63 = {
    "age": 63,
    "date_of_birth": 19530301,
    "gender": "MALE",
    "is_claimant_or_partner": True,
    "esa_income_reported": 5_000,
}
MAN_40 = dict(MAN_63, age=40, date_of_birth=19760301)
ADULT = {"is_claimant_or_partner": True}


def no_branch_opens_beside(log):
    return log.bar_branches() == []


def test_an_entered_pension_credit_award_bars_the_award_whatever_the_age_and_take_up():
    """Three men in 2016 each have £2,000 of Pension Credit as an input: the
    man aged 63 who would claim Pension Credit, the same man who would not,
    and a man aged 40. Each has an entitlement to that Pension Credit (Sch 1
    para 6(1)(c)), so none gets income-related ESA (esa_income_pension_age.yaml
    case 21)."""
    year = 2016
    sim = Simulation(
        situation=combine(
            household([MAN_63], year, would_claim_pc=True, pension_credit=2_000),
            household([MAN_63], year, would_claim_pc=False, pension_credit=2_000),
            household([MAN_40], year, pension_credit=2_000),
        )
    )
    assert sim.calculate("meets_pension_credit_age_conditions", year).tolist() == [
        True,
        True,
        False,
    ]
    assert sim.calculate("pension_credit", year).tolist() == [2_000] * 3
    assert sim.calculate("esa_income", year).tolist() == [0] * 3
    assert sim.calculate("claimant_or_partner_esa_income", year).tolist() == [0] * 3


class flat_pension_credit(Reform):
    """Pension Credit of £2,000 for every benefit unit."""

    def apply(self):
        class pension_credit(Variable):
            label = "Pension Credit"
            value_type = float
            entity = BenUnit
            definition_period = YEAR
            unit = GBP

            def formula(benunit, period, parameters):
                return benunit.filled_array(2_000)

        self.update_variable(pension_credit)


def test_a_reform_that_pays_pension_credit_to_all_bars_the_award(monkeypatch):
    """Under a reform that pays every benefit unit £2,000 of Pension Credit,
    the man aged 63 who would claim it, the same man who would not and a man
    aged 40 each have an entitlement to it, so none gets income-related ESA,
    and the model reads that Pension Credit for all three."""
    log = BranchLog(monkeypatch)
    year = 2016
    sim = Simulation(
        situation=combine(
            household([MAN_63], year),
            household([MAN_63], year, would_claim_pc=False),
            household([MAN_40], year),
        ),
        reform=flat_pension_credit,
    )
    assert sim.calculate("pension_credit", year).tolist() == [2_000] * 3
    assert sim.calculate("esa_income", year).tolist() == [0] * 3
    assert log.bar_branches()
    assert not pension_credit_follows_model_formulas(
        sim.populations["benunit"], period_(year), sim.tax_benefit_system.parameters
    )


class pension_credit_by_another_formula(Reform):
    """The model's Pension Credit, calculated by a formula of the reform's."""

    def apply(self):
        class pension_credit(Variable):
            label = "Pension Credit"
            value_type = float
            entity = BenUnit
            definition_period = YEAR
            unit = GBP

            def formula(benunit, period, parameters):
                return model_pension_credit.formula(benunit, period, parameters)

        self.update_variable(pension_credit)


OUTPUTS = [
    "esa_income",
    "claimant_or_partner_esa_income",
    "esa_income_eligible",
    "pension_credit",
    "working_tax_credit",
    "household_net_income",
]


@settings(
    max_examples=2,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
@given(examples())
@example((ROWS, 2016))
def test_reading_pension_credit_for_every_couple_matches_the_model(drawn):
    """Differential: a reform that calculates the model's Pension Credit by a
    formula of its own makes the screen read Pension Credit without the award
    for every couple whose claim passes the other tests. It must give every
    family the same ESA, Pension Credit and income as the model, which reads it
    only for a couple that meets the age conditions and would claim."""
    units, year = drawn
    event(f"year {year}")
    people = situation(units, year, [True, False])
    model = Simulation(situation=people)
    reformed = Simulation(situation=people, reform=pension_credit_by_another_formula)
    parameters = model.tax_benefit_system.parameters
    assert pension_credit_follows_model_formulas(
        model.populations["benunit"], period_(year), parameters
    )
    assert not pension_credit_follows_model_formulas(
        reformed.populations["benunit"], period_(year), parameters
    )
    for variable in OUTPUTS:
        assert np.allclose(
            model.calculate(variable, year),
            reformed.calculate(variable, year),
            atol=0.01,
        ), (variable, units)


def test_a_parameter_reform_keeps_the_age_and_take_up_conditions(monkeypatch):
    """A reform that lifts the exclusion of mixed-age couples in 2026 keeps
    the model's formulas, and meets_pension_credit_age_conditions reads its
    parameters. A couple aged 70 and 60 without the saving then meets the
    age conditions, so the model reads its Pension Credit and refuses the
    younger member's award. With only a working-age claimant, no couple meets
    them, and the model opens no branch, under the reform or without it."""
    log = BranchLog(monkeypatch)
    year = 2026
    reform = {
        "gov.dwp.pension_credit.mixed_age_couples.excluded": {
            f"{year}-01-01.{year}-12-31": False
        }
    }
    working_age = household([dict(ADULT, age=45, esa_income_reported=5_000)], year)
    mixed = household(
        [dict(ADULT, age=70), dict(ADULT, age=60, esa_income_reported=5_000)],
        year,
        has_mixed_age_couple_pension_credit_saving=False,
    )

    alone = Simulation(situation=combine(working_age), reform=reform)
    assert pension_credit_follows_model_formulas(
        alone.populations["benunit"], period_(year), alone.tax_benefit_system.parameters
    )
    assert alone.calculate("esa_income", year).tolist() == [5_000]
    assert no_branch_opens_beside(log)

    baseline = Simulation(situation=combine(working_age, mixed))
    assert baseline.calculate("esa_income", year).tolist() == [5_000, 5_000]
    assert baseline.calculate("pension_credit", year).tolist() == [0, 0]
    assert no_branch_opens_beside(log)

    lifted = Simulation(situation=combine(working_age, mixed), reform=reform)
    assert lifted.calculate("meets_pension_credit_age_conditions", year).tolist() == [
        False,
        True,
    ]
    # The couple's minimum guarantee for 52 weeks in 2026-27: 52 x 363.25.
    assert lifted.calculate("pension_credit", year) == pytest.approx(
        [0, 18_889], abs=0.01
    )
    assert lifted.calculate("esa_income", year).tolist() == [5_000, 0]
    assert log.bar_branches()


def test_a_frozen_pension_credit_bars_the_award_whatever_the_reform_age_conditions():
    """In 2018 a couple aged 70 and 60 meets the Pension Credit age
    conditions, so gets Pension Credit and no income-related ESA. A reform
    that brings the exclusion of mixed-age couples forward to 2018 and freezes
    Pension Credit at the baseline's award (gov.contrib.freeze_pension_credit)
    still pays that award, though the couple no longer meets the reform's age
    conditions, so the couple still gets no income-related ESA."""
    year = 2018
    reform = {
        "gov.dwp.pension_credit.mixed_age_couples.excluded": {
            f"{year}-01-01.{year}-12-31": True
        },
        "gov.contrib.freeze_pension_credit": {f"{year}-01-01.{year}-12-31": True},
    }
    sim = Simulation(
        situation=household(
            [dict(ADULT, age=70), dict(ADULT, age=60, esa_income_reported=5_000)],
            year,
            has_mixed_age_couple_pension_credit_saving=False,
        ),
        reform=reform,
    )
    assert not sim.calculate("meets_pension_credit_age_conditions", year)[0]
    assert sim.baseline.calculate("esa_income", year).tolist() == [0]
    # The couple's minimum guarantee for 52 weeks in 2018-19: 52 x 248.80.
    frozen = sim.baseline.calculate("pension_credit", year)
    assert frozen == pytest.approx([12_937.60], abs=0.01)
    assert sim.calculate("pension_credit", year) == pytest.approx(frozen, abs=0.01)
    assert not pension_credit_follows_model_formulas(
        sim.populations["benunit"], period_(year), sim.tax_benefit_system.parameters
    )
    assert sim.calculate("esa_income", year).tolist() == [0]


def test_each_entered_part_of_pension_credit_drops_the_age_and_take_up_conditions():
    """An input for pension_credit, its entitlement, its eligibility or either
    credit can pay Pension Credit outside the age and take-up conditions, so
    each makes the model read Pension Credit for every couple."""
    year = 2016
    sim = Simulation(situation=household([MAN_40], year))
    parameters = sim.tax_benefit_system.parameters
    assert pension_credit_follows_model_formulas(
        sim.populations["benunit"], period_(year), parameters
    )
    for variable, value in [
        ("pension_credit", 2_000),
        ("pension_credit_entitlement", 2_000),
        ("is_pension_credit_eligible", True),
        ("guarantee_credit", 2_000),
        ("savings_credit", 2_000),
    ]:
        branch = sim.get_branch(f"entered_{variable}")
        try:
            branch.set_input(variable, year, np.array([value]))
            assert not pension_credit_follows_model_formulas(
                branch.populations["benunit"], period_(year), parameters
            ), variable
            # An input for another year leaves this year to the formulas.
            assert pension_credit_follows_model_formulas(
                branch.populations["benunit"], period_(year + 1), parameters
            ), variable
        finally:
            sim.branches.pop(f"entered_{variable}", None)
    assert pension_credit_follows_model_formulas(
        sim.populations["benunit"], period_(year), parameters
    )


class ScreenReads:
    """Records each variable the income-related ESA screen reads in a
    simulation itself. A branch can change the family: the one that works out
    Pension Credit without employment income gives a claimant in paid work no
    earnings, so their claim can pass the work test there."""

    def __init__(self, monkeypatch):
        self.variables = []
        calculate = CoreSimulation.calculate

        def logged(simulation, variable_name, *args, **kwargs):
            stack = simulation.tracer.stack
            if (
                simulation.branch_name == "default"
                and stack
                and stack[-1]["name"] == "esa_income_eligible"
            ):
                self.variables.append(variable_name)
            return calculate(simulation, variable_name, *args, **kwargs)

        monkeypatch.setattr(CoreSimulation, "calculate", logged)


PENSION_CREDIT_CONDITIONS = {"meets_pension_credit_age_conditions", "would_claim_pc"}


def test_the_screen_reads_no_pension_credit_condition_without_a_couple_claim(
    monkeypatch,
):
    """In 2026 no couple here has a claim that passes the age, work and
    capital tests: a pensioner reporting the award, a claimant aged 45 in
    remunerative work, and a member outside the couple aged 40 reporting
    beside a pensioner, whose own claim passes. The screen then reads neither
    the Pension Credit age conditions nor the claim. A claimant aged 45 out of
    work passes, and the screen reads both."""
    reads = ScreenReads(monkeypatch)
    year = 2026
    no_couple_claim = [
        household([dict(ADULT, age=75, esa_income_reported=5_000)], year),
        household(
            [
                dict(
                    ADULT,
                    age=45,
                    esa_income_reported=5_000,
                    employment_income=15_000,
                    hours_worked=1_560,
                )
            ],
            year,
        ),
        household(
            [
                dict(ADULT, age=70),
                {
                    "age": 40,
                    "is_claimant_or_partner": False,
                    "current_education": "NOT_IN_EDUCATION",
                    "esa_income_reported": 5_000,
                },
            ],
            year,
        ),
    ]
    sim = Simulation(situation=combine(*no_couple_claim))
    assert sim.calculate("esa_income_eligible", year).tolist() == [False, False, True]
    assert "esa_income_assessable_capital" in reads.variables
    assert not PENSION_CREDIT_CONDITIONS & set(reads.variables)

    reads.variables.clear()
    out_of_work = household([dict(ADULT, age=45, esa_income_reported=5_000)], year)
    sim = Simulation(situation=combine(*no_couple_claim, out_of_work))
    assert sim.calculate("esa_income_eligible", year).tolist() == [
        False,
        False,
        True,
        True,
    ]
    assert PENSION_CREDIT_CONDITIONS <= set(reads.variables)
