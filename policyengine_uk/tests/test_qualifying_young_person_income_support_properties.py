"""Income Support in a young person's own right and qualifying young person
status.

A person receiving Income Support is not a qualifying young person for
Pension Credit (SPC Regs 2002 reg. 4A(5)), Child Benefit (Child Benefit
(General) Regulations 2006 reg. 8(2)(a)) or Child Tax Credit (CTC Regs 2002
reg. 5(4)(c)). Universal Credit's list (UC Regs 2013 reg. 5(5)) does not
include Income Support, but the Secretary of State leaves a person entitled
to an existing benefit, Income Support among them, out of the Universal
Credit test (SI 2014/1230 regs. 2(1) and 28). Universal Credit reads the
person's own report while Income Support is in payment and not neutralised,
and until the model's legacy closure ends the person's award
(person_legacy_benefits_closed), for a claimant or partner as for any other
member (is_qualifying_young_person_for_universal_credit). No closure
reaches a person in the Universal Credit assertions below: Income Support
and tax credits are in payment in 2016, 2019 and 2024, and the 2025 grid
reports no tax credit.

Pension Credit and Child Tax Credit read is_on_income_support: the benefit
unit's calculated award, for whichever of the claimant and partner receives
it, and the person's own report for any other member while Income Support is
in payment and not neutralised.
Child Benefit reads receives_income_support_in_own_right, the person's own
report on the same terms, because the family's Income Support reads the
Child Benefit test and the calculated award would make a cycle.

Invariants:

1. Over every combination of age, education, training, the other own-right
   benefits and the 16th-birthday fact, for a member who is not the claimant
   or partner: reporting Income Support of their own while it is in payment
   ends the Pension Credit, Child Benefit, Child Tax Credit and Universal
   Credit statuses; without a report each status is what it is when the
   report is left alone; the status under UC Regs reg. 5 alone never
   depends on it; and Pension Credit and Universal Credit agree without it.
2. By default receives_income_support_in_own_right is the person's own
   reported Income Support while Income Support is in payment (to 2025-26)
   and no reform neutralises it, and false otherwise.
3. Under a reform that neutralises income_support, no Pension Credit, Child
   Tax Credit or Child Benefit status depends on reported Income Support.
   Under a reform that replaces income_support's formula with one returning
   zero, no Pension Credit or Child Tax Credit status of a claimant or
   partner depends on it; another member's report and the Child Benefit
   reader still exclude, as their documentation says, because only setting
   gov.dwp.income_support.active to false, neutralising Income Support, or
   setting the report to zero, removes a report.
4. The status under UC Regs reg. 5 alone never depends on reported Income
   Support, in the baseline or under either reform. The Universal Credit
   status ends on a report while Income Support is in payment and the
   person's legacy award remains open, for anyone, until a reform
   neutralises Income Support; a reform that replaces its formula with one
   returning zero leaves the exclusion in place.
5. Setting a young person's reported Income Support to zero never lowers
   their household's Pension Credit.
"""

from itertools import product
from unittest.mock import patch

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.model_api import YEAR as YEAR_PERIOD
from policyengine_uk.model_api import BenUnit, Variable
from policyengine_uk.tax_benefit_system import system
from policyengine_uk.variables.household.demographic.highest_education import (
    EducationType,
)

YEAR = 2025
_PROPERTY_SYSTEM = system.clone()
EDUCATIONS = tuple(item.name for item in EducationType)
SIXTEEN = "is_before_first_september_following_16th_birthday"
INCOME_SUPPORT = "receives_income_support_in_own_right"
REGULATION_5 = "is_qualifying_young_person_under_universal_credit_regulation_5"
EXCLUDING = ("pension_credit", "child_benefit", "child_tax_credit")
# Income Support paid its last awards on 31 March 2026.
IN_PAYMENT = {2016: True, 2019: True, 2024: True, 2025: True, 2026: False}
SETTINGS = settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)


class income_support(Variable):
    """A reform's Income Support formula that pays nothing."""

    value_type = float
    entity = BenUnit
    label = "Income Support"
    definition_period = YEAR_PERIOD

    def formula(benunit, period, parameters):
        return benunit.empty_array()


def apply(sim, reform):
    if reform == "zero formula":
        sim.tax_benefit_system.update_variable(income_support)
    elif reform == "neutralised":
        sim.tax_benefit_system.neutralize_variable("income_support")
    return sim


def simulate(households, year=YEAR, reform=None):
    """households: a list of households, each a list of benefit units, each a
    list of people's inputs. Every person gives the same input names."""
    situation = {"people": {}, "benunits": {}, "households": {}}
    people = []
    for h, units in enumerate(households):
        household_members = []
        for b, unit in enumerate(units):
            names = []
            for p, inputs in enumerate(unit):
                name = f"p{h}_{b}_{p}"
                situation["people"][name] = {}
                people.append(inputs)
                names.append(name)
            situation["benunits"][f"b{h}_{b}"] = {"members": names}
            household_members += names
        situation["households"][f"h{h}"] = {"members": household_members}
    with patch(
        "policyengine_uk.simulation.CountryTaxBenefitSystem",
        side_effect=_PROPERTY_SYSTEM.clone,
    ):
        sim = Simulation(situation=situation)
    variables = people[0].keys()
    assert all(p.keys() == variables for p in people)
    for variable in variables:
        sim.set_input(variable, year, [p[variable] for p in people])
    # No family claims Universal Credit, so legacy awards, Child Tax Credit
    # included, continue.
    benunits = len(situation["benunits"])
    sim.set_input("would_claim_uc", year, np.zeros(benunits, dtype=bool))
    sim.input_variables = list(variables) + ["would_claim_uc"]
    sim.reset_calculations()
    return apply(sim, reform)


def status(sim, programme, year=YEAR):
    return sim.calculate(f"is_qualifying_young_person_for_{programme}", year)


def member(age, **inputs):
    return {
        "age": age,
        "current_education": "NOT_IN_EDUCATION",
        "is_in_approved_training": False,
        "receives_benefits_in_own_right": False,
        "age_started_or_accepted_current_education_or_training": 17,
        "is_claimant_or_partner": False,
        "income_support_reported": 0,
        "state_pension": 0,
        "pip_dl_category": "NONE",
        "care_hours": 0,
        "would_claim_carers_allowance": False,
        "child_tax_credit_reported": 0,
        **inputs,
    }


# --- Invariants 1 and 2 ---

BASE = [
    dict(
        current_education=education,
        is_in_approved_training=training,
        receives_benefits_in_own_right=own_right,
        **{SIXTEEN: sixteen},
    )
    for education, training, own_right, sixteen in product(
        EDUCATIONS, (False, True), (False, True), (False, True)
    )
]
GRID = [dict(row, age=age) for age, row in product(range(14, 22), BASE)]


def as_members(rows, **inputs):
    # Each young person sits in the benefit unit of a 70-year-old claimant,
    # so they are not the claimant or partner.
    claimant = member(70, is_claimant_or_partner=True, **{SIXTEEN: False})
    return [[[claimant, member(**{SIXTEEN: False, **row, **inputs})]] for row in rows]


def test_income_support_ends_four_statuses_and_not_regulation_5():
    untouched = simulate(as_members(GRID))
    reporting = simulate(as_members(GRID, income_support_reported=3_000))
    neutralised = simulate(
        as_members(GRID, income_support_reported=3_000), reform="neutralised"
    )
    for programme in EXCLUDING + ("universal_credit",):
        np.testing.assert_array_equal(
            status(neutralised, programme)[1::2],
            status(untouched, programme)[1::2],
            err_msg=programme,
        )
    for programme in EXCLUDING + ("universal_credit",):
        before = status(untouched, programme)[1::2]
        # Not vacuous: there is a status to lose.
        assert before.any(), programme
        assert not status(reporting, programme)[1::2].any(), programme
    universal_credit = status(untouched, "universal_credit")[1::2]
    # Reg. 5 alone doesn't read the report; SI 2014/1230 reg. 28 does.
    np.testing.assert_array_equal(
        reporting.calculate(REGULATION_5, YEAR)[1::2], universal_credit
    )
    np.testing.assert_array_equal(
        status(untouched, "pension_credit")[1::2], universal_credit
    )


@SETTINGS
@given(
    st.lists(
        st.tuples(st.integers(0, 60), st.sampled_from([0, 0, 1, 2_500, 9_000])),
        min_size=1,
        max_size=40,
    ),
    st.sampled_from([2021, 2024, 2025, 2026, 2028]),
)
def test_default_follows_reported_income_support_while_it_is_paid(rows, year):
    # Invariant 2.
    households = [
        [[member(age, income_support_reported=amount)]] for age, amount in rows
    ]
    sim = simulate(households, year)
    expected = [year <= 2025 and amount > 0 for _, amount in rows]
    np.testing.assert_array_equal(sim.calculate(INCOME_SUPPORT, year), expected)
    neutralised = simulate(households, year, reform="neutralised")
    assert not neutralised.calculate(INCOME_SUPPORT, year).any()


# --- Invariants 3 to 5, on generated households ---


@st.composite
def household(draw):
    young = member(
        draw(st.integers(15, 20)),
        current_education=draw(st.sampled_from(EDUCATIONS)),
        is_in_approved_training=draw(st.booleans()),
        income_support_reported=draw(st.sampled_from([0, 3_000])),
        care_hours=draw(st.sampled_from([0, 35])),
    )
    shape = draw(st.sampled_from(["pensioner's unit", "own unit", "parent's unit"]))
    if shape == "parent's unit":
        # A Child Tax Credit claimant and their young person.
        parent = member(
            draw(st.integers(35, 55)),
            is_claimant_or_partner=True,
            child_tax_credit_reported=1,
        )
        return [[parent, young]]
    pensioner = member(
        draw(st.integers(66, 90)),
        is_claimant_or_partner=True,
        state_pension=draw(st.sampled_from([0, 5_000, 9_000])),
        pip_dl_category=draw(st.sampled_from(["NONE", "STANDARD", "ENHANCED"])),
    )
    if shape == "own unit":
        # The young person claims for their own benefit unit, so the model
        # calculates their Income Support.
        return [[pensioner], [dict(young, is_claimant_or_partner=True)]]
    return [[pensioner, young]]


def without_reports(households):
    return [
        [[dict(p, income_support_reported=0) for p in unit] for unit in units]
        for units in households
    ]


def flat(households, key):
    return np.array([p[key] for units in households for unit in units for p in unit])


GENERATED = dict(
    households=st.lists(household(), min_size=1, max_size=8),
    year=st.sampled_from([2016, 2019, 2024]),
)


@SETTINGS
@given(**GENERATED, reform=st.sampled_from(["zero formula", "neutralised"]))
def test_reforms_that_remove_income_support_end_the_exclusions(
    households, year, reform
):
    # Invariants 3 and 4.
    reformed = simulate(households, year, reform)
    unreported = simulate(without_reports(households), year, reform)
    reported = flat(households, "income_support_reported") > 0
    claimant = flat(households, "is_claimant_or_partner")
    # A report counts where it is the reader's evidence: for Child Benefit
    # always, and for Pension Credit and Child Tax Credit for anyone who is
    # not the claimant or partner; and only until a reform neutralises it.
    report_stands = reported & IN_PAYMENT[year] & (reform != "neutralised")
    for programme in ("pension_credit", "child_tax_credit"):
        np.testing.assert_array_equal(
            status(reformed, programme, year),
            status(unreported, programme, year) & ~(report_stands & ~claimant),
            err_msg=programme,
        )
    np.testing.assert_array_equal(
        status(reformed, "child_benefit", year),
        status(unreported, "child_benefit", year) & ~report_stands,
    )
    # Universal Credit reads the person's own report, for a claimant or
    # partner too (SI 2014/1230 reg. 28).
    np.testing.assert_array_equal(
        status(reformed, "universal_credit", year),
        status(unreported, "universal_credit", year) & ~report_stands,
    )
    np.testing.assert_array_equal(
        reformed.calculate(REGULATION_5, year),
        unreported.calculate(REGULATION_5, year),
    )
    assert not reformed.calculate("income_support", year).any()


@SETTINGS
@given(**GENERATED)
def test_universal_credit_and_pension_credit_with_and_without_the_report(
    households, year
):
    # Invariants 4 and 5 in the baseline.
    reported = simulate(households, year)
    unreported = simulate(without_reports(households), year)
    report_stands = (flat(households, "income_support_reported") > 0) & IN_PAYMENT[year]
    np.testing.assert_array_equal(
        status(reported, "universal_credit", year),
        status(unreported, "universal_credit", year) & ~report_stands,
    )
    np.testing.assert_array_equal(
        reported.calculate(REGULATION_5, year),
        unreported.calculate(REGULATION_5, year),
    )
    gained = unreported.calculate("pension_credit", year, map_to="household")
    kept = reported.calculate("pension_credit", year, map_to="household")
    assert (gained >= kept - 0.01).all(), (gained, kept)


# --- The review's household: a pensioner and a student-carer ---


def pensioner_and_student_carer():
    # 2019: a pensioner aged 70 on PIP daily living with £5,000 of State
    # Pension, and an unrelated 18-year-old in their own benefit unit: an
    # orphan in full-time non-advanced education with an existing Income
    # Support claim (IS Regs 1987 reg. 13(2)(c)), caring for the pensioner 35
    # hours a week without Carer's Allowance.
    pensioner = member(
        70,
        is_claimant_or_partner=True,
        state_pension=5_000,
        pip_dl_category="STANDARD",
    )
    student = member(
        18,
        is_claimant_or_partner=True,
        current_education="UPPER_SECONDARY",
        income_support_reported=3_000,
        care_hours=35,
    )
    return [[[pensioner], [student]]]


def test_a_reform_paying_no_income_support_restores_the_severe_disability_addition():
    # With the student's Income Support in payment, reg. 4A(5) excludes them,
    # the pensioner does not live alone, and Pension Credit is the standard
    # minimum guarantee 167.25 x 52 = 8,697 less the State Pension: 3,697.
    # A reform that pays no Income Support leaves the student a qualifying
    # young person, disregarded under Schedule I para. 2(2)(f), so the
    # pensioner gets the severe disability addition 65.85 x 52 = 3,424.20 as
    # well: 7,121.20. Household net income: State Pension 5,000 + PIP 58.70 x
    # 52 = 3,052.40 + Pension Credit 7,121.20 + winter fuel payment 200, less
    # TV licence 154.50: 15,219.10, before the cost-of-living payments.
    year = 2019
    for reform in ("zero formula", "neutralised"):
        sim = simulate(pensioner_and_student_carer(), year, reform)
        np.testing.assert_array_equal(status(sim, "pension_credit", year), [0, 1])
        np.testing.assert_allclose(
            sim.calculate("severe_disability_minimum_guarantee_addition", year),
            [3_424.20, 0],
            atol=0.01,
        )
        np.testing.assert_allclose(
            sim.calculate("pension_credit", year), [7_121.20, 0], atol=0.01
        )
        np.testing.assert_allclose(
            sim.calculate("household_net_income", year)
            - sim.calculate("cost_of_living_support_payment", year),
            [15_219.10],
            atol=0.01,
        )
    # Child Benefit reads the report: of these two reforms, only neutralising
    # Income Support ends its exclusion.
    zero = simulate(pensioner_and_student_carer(), year, "zero formula")
    assert zero.calculate(INCOME_SUPPORT, year)[1]
    assert not status(zero, "child_benefit", year)[1]
    neutralised = simulate(pensioner_and_student_carer(), year, "neutralised")
    assert status(neutralised, "child_benefit", year)[1]
