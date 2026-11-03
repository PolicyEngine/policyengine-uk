"""Properties of the UC qualifying young person test under SI 2014/1230 reg. 28.

DWP doesn't count a person entitled to an existing benefit (SI 2014/1230
reg. 2(1)) as a UC qualifying young person (reg. 28). The predicate reads the
person's own reports of income-based JSA, income-related ESA, Income Support,
Housing Benefit, Child Tax Credit and Working Tax Credit and, for a claimant
or partner, the couple's joint tax credit award (Tax Credits Act 2002
s.3(3)). It reads a report only in a year the model pays that benefit, and
only if no reform neutralises it; these tests run without a reform, and
test_uc_qualifying_young_person_neutralised_benefits.py covers reforms.
These tests check that:

- any positive own report of an existing benefit the model pays that year
  makes the predicate false;
- with every such report at zero, the predicate equals the UC Regs 2013
  reg. 5 test less the person's reported UC, ESA and JSA awards;
- a claimant's or partner's reports never change a dependant's predicate;
- a parent's Universal Credit never rises when their young person's own
  report turns positive;
- the predicate equals the reg. 5 test less reg. 28's exclusions, exactly.
"""

from unittest.mock import patch

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.tax_benefit_system import system
from policyengine_uk.variables.household.demographic.highest_education import (
    EducationType,
)

EDUCATIONS = tuple(item.name for item in EducationType)
NON_ADVANCED = ("UPPER_SECONDARY", "POST_SECONDARY")
YEARS = (2024, 2025, 2026)
EXISTING_BENEFITS = (
    "jsa_income_reported",
    "esa_income_reported",
    "income_support_reported",
    "housing_benefit_reported",
    "child_tax_credit_reported",
    "working_tax_credit_reported",
)
TAX_CREDITS = ("child_tax_credit_reported", "working_tax_credit_reported")
# The Secretary of State defines ESA and JSA without their income-related and
# income-based forms (UC Regs reg. 2), so reg. 5(5) reaches only these.
REG_5_5_REPORTS = (
    "universal_credit_reported",
    "esa_contrib_reported",
    "jsa_contrib_reported",
)
# The existing benefits the model pays in each year: tax credits until 5 April
# 2025 (gov.dwp.tax_credits.active), Income Support and income-based JSA until
# 31 March 2026 (gov.dwp.income_support.active, gov.dwp.JSA.income.active).
PAYING = {
    2024: set(EXISTING_BENEFITS),
    2025: set(EXISTING_BENEFITS) - set(TAX_CREDITS),
    2026: {"esa_income_reported", "housing_benefit_reported"},
}
SETTINGS = settings(
    max_examples=25,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)

amount = st.floats(0.01, 20_000)


@st.composite
def sometimes(draw):
    """A positive amount one time in three, otherwise zero."""
    return draw(amount) if draw(st.sampled_from((False, False, True))) else 0.0


@st.composite
def member(
    draw,
    ages,
    training,
    educations=EDUCATIONS,
    own_right=(False, True),
    reg_5_5_reports=True,
    one_existing_benefit=False,
):
    """A person who usually reports no UC, ESA or JSA award under reg. 5(5).

    Reg. 5(5) excludes anyone with such a report, so drawing them rarely
    leaves people for reg. 28 to exclude; with reg_5_5_reports false, the
    person reports none. Each existing benefit report is positive one time in
    three; with one_existing_benefit true, the person reports at most one,
    and none one time in three.
    """
    reg_5_5_report = (
        draw(st.sampled_from((None,) * 4 + REG_5_5_REPORTS))
        if reg_5_5_reports
        else None
    )
    return {
        "age": draw(ages),
        "current_education": draw(st.sampled_from(educations)),
        "is_in_approved_training": draw(training),
        "receives_benefits_in_own_right": draw(
            st.sampled_from((False,) * 3 + own_right[1:])
        ),
        **{
            name: draw(amount) if name == reg_5_5_report else 0.0
            for name in REG_5_5_REPORTS
        },
        **existing_benefit_reports(draw, one_existing_benefit),
    }


def existing_benefit_reports(draw, one_existing_benefit):
    if not one_existing_benefit:
        return {name: draw(sometimes()) for name in EXISTING_BENEFITS}
    report = draw(st.sampled_from((None,) * 3 + EXISTING_BENEFITS))
    return {name: draw(amount) if name == report else 0.0 for name in EXISTING_BENEFITS}


young_member = member(st.integers(15, 20), st.booleans())
# Claimants and partners aged 16 to 19 can be qualifying young people.
adult = member(st.one_of(st.integers(16, 19), st.integers(20, 70)), st.just(False))
# Someone who meets reg. 5 unless reg. 28 excludes them: 16 to 18, on a
# non-advanced course, not flagged as receiving benefits in their own right
# and reporting no UC, ESA or JSA award under reg. 5(5). A 19-year-old needs
# the entry and terminal-date inputs (reg. 5(1)(b) and (2)), which these
# draws don't set. They report at most one existing benefit, so reg. 28
# often leaves them in the test.
qualifying = member(
    st.integers(16, 18),
    st.just(False),
    NON_ADVANCED,
    own_right=(False,),
    reg_5_5_reports=False,
    one_existing_benefit=True,
)
INPUTS = (
    (
        "age",
        "current_education",
        "is_in_approved_training",
        "receives_benefits_in_own_right",
        "is_claimant_or_partner",
        "is_parent",
    )
    + REG_5_5_REPORTS
    + EXISTING_BENEFITS
)


UNITS = 4


@st.composite
def families(draw):
    """A claimant, then a partner or a dependant, then two dependants."""
    couple = draw(st.booleans())
    claimant = dict(draw(adult), is_claimant_or_partner=True, is_parent=True)
    second = draw(adult if couple else young_member)
    second = dict(second, is_claimant_or_partner=couple, is_parent=couple)
    dependants = [
        dict(draw(young_member), is_claimant_or_partner=False, is_parent=False)
        for _ in range(2)
    ]
    return [claimant, second] + dependants


@st.composite
def qualifying_families(draw):
    """Families where reg. 28 alone decides most members' status.

    Each slot is drawn from qualifying, which meets reg. 5, or from the
    general strategies. Over 10,000 derandomised draws for 2025, the
    claimant met reg. 5 in 59% of draws, the partner or dependant in 62%,
    and the dependants in 65% and 69%. A partner is otherwise an older adult whose
    own reports reg. 28 must not pass to the claimant, except for the
    couple's tax credit award.
    """
    couple = draw(st.booleans())
    claimant = draw(st.one_of(qualifying, qualifying, adult))
    claimant = dict(claimant, is_claimant_or_partner=True, is_parent=True)
    second = draw(st.one_of(qualifying, qualifying, adult if couple else young_member))
    second = dict(second, is_claimant_or_partner=couple, is_parent=couple)
    dependants = [
        dict(
            draw(st.one_of(qualifying, qualifying, young_member)),
            is_claimant_or_partner=False,
            is_parent=False,
        )
        for _ in range(2)
    ]
    return [claimant, second] + dependants


units_strategy = st.lists(families(), min_size=UNITS, max_size=UNITS)
qualifying_units_strategy = st.lists(
    qualifying_families(), min_size=UNITS, max_size=UNITS
)
_CACHE = {}


@pytest.fixture(autouse=True, scope="module")
def _release_simulations():
    """Drop the cloned system and cached simulations when the module ends."""
    yield
    _CACHE.clear()


def simulate(units, year):
    """Set the inputs on one cached simulation per shape and year."""
    shape = (tuple(len(members) for members in units), year)
    if shape not in _CACHE:
        situation = {"people": {}, "benunits": {}, "households": {}}
        for i, members in enumerate(units):
            names = [f"p{i}_{j}" for j in range(len(members))]
            for name in names:
                situation["people"][name] = {}
            situation["benunits"][f"b{i}"] = {"members": names}
            situation["households"][f"h{i}"] = {"members": names}
        if "system" not in _CACHE:
            _CACHE["system"] = system.clone()
        with patch(
            "policyengine_uk.simulation.CountryTaxBenefitSystem",
            side_effect=_CACHE["system"].clone,
        ):
            _CACHE[shape] = Simulation(situation=situation)
    sim = _CACHE[shape]
    people = flatten(units)
    for variable in INPUTS:
        sim.set_input(variable, year, [p[variable] for p in people])
    sim.input_variables = list(INPUTS)
    sim.reset_calculations()
    return sim


def flatten(units):
    return [p for members in units for p in members]


def with_zero(units, names, who):
    return [
        [dict(p, **{n: 0.0 for n in names}) if who(p) else p for p in members]
        for members in units
    ]


def predicate(sim, year):
    return sim.calculate("is_qualifying_young_person_for_universal_credit", year).copy()


def reg_5_test(sim, year):
    """UC Regs 2013 reg. 5 less the person's reported UC, ESA and JSA awards."""

    def get(name):
        return sim.calculate(name, year)

    routes = get("is_before_first_september_following_16th_birthday") | (
        get(
            "meets_qualifying_young_person_education_or_training_condition_for_universal_credit"
        )
        & get("meets_qualifying_young_person_entry_condition_for_universal_credit")
        & get(
            "meets_qualifying_young_person_terminal_date_condition_for_universal_credit"
        )
    )
    excluded = get("receives_benefits_in_own_right")
    for name in REG_5_5_REPORTS:
        excluded = excluded | (get(name) > 0)
    return (
        get("meets_qualifying_young_person_age_condition_for_universal_credit")
        & routes
        & ~excluded
    )


def reg_28_exclusions(units, year):
    """Who reg. 28 excludes: own reports of benefits the model pays that year,
    and, for a claimant or partner, the couple's tax credit award."""
    paying = PAYING[year]
    own = np.array([any(p[n] > 0 for n in paying) for p in flatten(units)], dtype=bool)
    couple_tax_credits = np.array(
        [
            p["is_claimant_or_partner"]
            and any(
                q["is_claimant_or_partner"] and q[n] > 0
                for q in members
                for n in paying.intersection(TAX_CREDITS)
            )
            for members in units
            for p in members
        ],
        dtype=bool,
    )
    return own | couple_tax_credits


@SETTINGS
@given(units=units_strategy, year=st.sampled_from(YEARS))
def test_any_own_existing_benefit_report_excludes_the_person(units, year):
    sim = simulate(units, year)
    assert not np.any(predicate(sim, year) & reg_28_exclusions(units, year))


@SETTINGS
@given(units=units_strategy, year=st.sampled_from(YEARS))
def test_zero_existing_benefit_reports_leave_the_reg_5_test(units, year):
    zeroed = with_zero(units, EXISTING_BENEFITS, lambda p: True)
    sim = simulate(zeroed, year)
    assert predicate(sim, year).tolist() == reg_5_test(sim, year).tolist()
    assert (
        reg_5_test(sim, year).tolist()
        == sim.calculate(
            "is_qualifying_young_person_under_universal_credit_regulation_5", year
        ).tolist()
    )
    # With reports present, reg. 28 only removes people from the test.
    sim = simulate(units, year)
    assert not np.any(predicate(sim, year) & ~reg_5_test(sim, year))


@SETTINGS
@given(units=units_strategy, year=st.sampled_from(YEARS))
def test_a_claimants_reports_never_change_a_dependants_predicate(units, year):
    reported = predicate(simulate(units, year), year)
    cleared = predicate(
        simulate(
            with_zero(units, EXISTING_BENEFITS, lambda p: p["is_claimant_or_partner"]),
            year,
        ),
        year,
    )
    dependant = np.array([not p["is_claimant_or_partner"] for p in flatten(units)])
    assert reported[dependant].tolist() == cleared[dependant].tolist()


@SETTINGS
@given(
    parent_age=st.integers(25, 60),
    young_age=st.integers(16, 19),
    education=st.sampled_from(EDUCATIONS),
    benefit=st.sampled_from(EXISTING_BENEFITS),
    report=st.floats(0.01, 20_000),
    year=st.sampled_from(YEARS),
)
def test_a_young_persons_report_never_raises_the_parents_award(
    parent_age, young_age, education, benefit, report, year
):
    def family(young_report):
        zeros = {n: 0.0 for n in REG_5_5_REPORTS + EXISTING_BENEFITS}
        parent = dict(
            zeros,
            age=parent_age,
            current_education="NOT_IN_EDUCATION",
            is_in_approved_training=False,
            receives_benefits_in_own_right=False,
            is_claimant_or_partner=True,
            is_parent=True,
        )
        young = dict(
            zeros,
            age=young_age,
            current_education=education,
            is_in_approved_training=False,
            receives_benefits_in_own_right=False,
            is_claimant_or_partner=False,
            is_parent=False,
        )
        young[benefit] = young_report
        return [[parent, young]]

    without = simulate(family(0.0), year).calculate("universal_credit", year)[0]
    with_report = simulate(family(report), year).calculate("universal_credit", year)[0]
    assert with_report <= without + 1e-6


@SETTINGS
@given(units=qualifying_units_strategy, year=st.sampled_from(YEARS))
def test_the_predicate_is_reg_5_less_reg_28(units, year):
    sim = simulate(units, year)
    expected = reg_5_test(sim, year) & ~reg_28_exclusions(units, year)
    assert predicate(sim, year).tolist() == expected.tolist()
