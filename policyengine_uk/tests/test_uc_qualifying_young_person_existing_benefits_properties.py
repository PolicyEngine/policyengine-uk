"""Properties of the UC qualifying young person test under SI 2014/1230 reg. 28.

DWP doesn't count a person entitled to an existing benefit (SI 2014/1230
reg. 2(1)) as a UC qualifying young person (reg. 28). The predicate reads the
person's own reports of income-based JSA, income-related ESA, Income Support,
Housing Benefit, Child Tax Credit and Working Tax Credit and, for a claimant
or partner, the couple's joint tax credit award (Tax Credits Act 2002
s.3(3)). It reads a report only in a year the model pays that benefit and
until the model's legacy closure, or for a claimant or partner the family's
Universal Credit claim, ends the award on it, and only if no reform
neutralises it; these tests run without a reform, and
test_uc_qualifying_young_person_neutralised_benefits.py covers reforms. The
model stops paying a benefit when its year gate closes, and ends a person's
legacy awards when its annual migration proxy closes them: their own Income
Support, income-based JSA and income-related ESA when
person_legacy_benefits_closed holds, the family's tax credits when
legacy_benefits_closed holds, and its Housing Benefit when
legacy_benefits_closed holds and the family doesn't meet the Pension Credit
age conditions. A claim for Universal Credit ends the claimant's and
partner's own awards (SI 2014/1230 reg. 8(2) and (2A); SI 2013/983 art. 4),
and the model ends the family's continuing Housing Benefit award and its
Child Tax Credit, and the claimant's and partner's income-related ESA, when
the family claims (claims_universal_credit). The oracle reads those closure
variables from the model, and each family draws would_claim_uc. These tests
check that:

- any positive own report of an existing benefit whose year gate, legacy
  closure and, for a claimant or partner, claim limb leave it open makes the
  predicate false;
- with every such report at zero, the predicate equals the UC Regs 2013
  reg. 5 test less the person's reported UC, ESA and JSA awards;
- compared with the same family without the claimant's and partner's
  reports, those reports change a dependant's predicate only where the
  proxy closes the family's legacy awards on them, and then only to lift an
  exclusion;
- a person whose legacy awards have closed is never excluded through their
  own income-related ESA report, nor through a Housing Benefit report once
  the family's awards close outside the Pension Credit age conditions;
- a parent's Universal Credit never rises when one existing benefit report
  of their young person turns positive and the young person reports no
  other;
- the predicate equals the reg. 5 test less reg. 28's exclusions, exactly;
- turning would_claim_uc on never changes the predicate of anyone who isn't
  the claimant or partner;
- turning would_claim_uc on never turns a claimant's or partner's predicate
  from true to false.
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
    claimant = dict(
        draw(adult),
        is_claimant_or_partner=True,
        is_parent=True,
        would_claim_uc=draw(st.booleans()),
    )
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
    general strategies. Each slot meets reg. 5 in about three draws in
    five. A partner is otherwise an older adult whose
    own reports reg. 28 must not pass to the claimant, except for the
    couple's tax credit award.
    """
    couple = draw(st.booleans())
    claimant = draw(st.one_of(qualifying, qualifying, adult))
    claimant = dict(
        claimant,
        is_claimant_or_partner=True,
        is_parent=True,
        would_claim_uc=draw(st.booleans()),
    )
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


# Someone who meets reg. 5 unless reg. 28 excludes them and reports each
# existing benefit one time in three, so a report that closes their legacy
# awards often sits beside an income-related ESA or Housing Benefit report.
reporting_qualifying = member(
    st.integers(16, 18),
    st.just(False),
    NON_ADVANCED,
    own_right=(False,),
    reg_5_5_reports=False,
)


@st.composite
def closure_families(draw):
    """A claimant and a second member who meet reg. 5 one time in two, and
    two dependants who always do, each reporting any existing benefit."""
    couple = draw(st.booleans())
    claimant = draw(st.one_of(reporting_qualifying, adult))
    claimant = dict(
        claimant,
        is_claimant_or_partner=True,
        is_parent=True,
        would_claim_uc=draw(st.booleans()),
    )
    second = draw(st.one_of(reporting_qualifying, adult if couple else young_member))
    second = dict(second, is_claimant_or_partner=couple, is_parent=couple)
    dependants = [
        dict(draw(reporting_qualifying), is_claimant_or_partner=False, is_parent=False)
        for _ in range(2)
    ]
    return [claimant, second] + dependants


units_strategy = st.lists(families(), min_size=UNITS, max_size=UNITS)
closure_units_strategy = st.lists(closure_families(), min_size=UNITS, max_size=UNITS)
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
    """Set the inputs on one cached simulation per shape and year. Each
    family claims Universal Credit (would_claim_uc) as its first member's
    draw says, or by default."""
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
    sim.set_input(
        "would_claim_uc",
        year,
        [members[0].get("would_claim_uc", True) for members in units],
    )
    sim.input_variables = list(INPUTS) + ["would_claim_uc"]
    sim.reset_calculations()
    return sim


def flatten(units):
    return [p for members in units for p in members]


def claiming(units, claims):
    """The same families, each with would_claim_uc set to claims."""
    return [
        [dict(members[0], would_claim_uc=claims)] + members[1:] for members in units
    ]


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


def open_awards(sim, year, claim_limbs=True):
    """For each report, whether the model's legacy closure and, with
    claim_limbs, the family's Universal Credit claim leave the award on it
    open, person by person. The claim ends the claimant's and partner's own
    income-related ESA, Housing Benefit outside the Pension Credit age
    conditions and Child Tax Credit, and nobody else's."""
    own_open = ~sim.calculate("person_legacy_benefits_closed", year)
    family_closed = sim.calculate("legacy_benefits_closed", year, map_to="person")
    pension_age = sim.calculate(
        "meets_pension_credit_age_conditions", year, map_to="person"
    )
    claim_ends = np.zeros_like(own_open)
    if claim_limbs:
        claim_ends = sim.calculate(
            "claims_universal_credit", year, map_to="person"
        ) & sim.calculate("is_claimant_or_partner", year)
    return {
        "income_support_reported": own_open,
        "jsa_income_reported": own_open,
        "esa_income_reported": own_open & ~claim_ends,
        "housing_benefit_reported": pension_age | (~family_closed & ~claim_ends),
        "child_tax_credit_reported": ~family_closed & ~claim_ends,
        "working_tax_credit_reported": ~family_closed,
    }


def reg_28_exclusions(units, year, sim):
    """Who reg. 28 excludes: own reports of benefits the model pays on them
    that year, and, for a claimant or partner, the couple's tax credit
    award."""
    paying = PAYING[year]
    award_open = open_awards(sim, year)
    people = flatten(units)
    own = np.array(
        [
            any(p[n] > 0 and award_open[n][i] for n in paying)
            for i, p in enumerate(people)
        ],
        dtype=bool,
    )
    couple_tax_credits = np.zeros(len(people), dtype=bool)
    start = 0
    for members in units:
        indices = range(start, start + len(members))
        award = any(
            people[j]["is_claimant_or_partner"]
            and people[j][n] > 0
            and award_open[n][j]
            for j in indices
            for n in paying.intersection(TAX_CREDITS)
        )
        for j in indices:
            couple_tax_credits[j] = people[j]["is_claimant_or_partner"] and award
        start += len(members)
    return own | couple_tax_credits


@SETTINGS
@given(units=units_strategy, year=st.sampled_from(YEARS))
def test_any_own_existing_benefit_report_excludes_the_person(units, year):
    sim = simulate(units, year)
    assert not np.any(predicate(sim, year) & reg_28_exclusions(units, year, sim))


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
def test_a_claimants_reports_change_a_dependant_only_by_closing_the_family(units, year):
    sim = simulate(units, year)
    reported = predicate(sim, year)
    family_closed = sim.calculate(
        "legacy_benefits_closed", year, map_to="person"
    ).copy()
    cleared = predicate(
        simulate(
            with_zero(units, EXISTING_BENEFITS, lambda p: p["is_claimant_or_partner"]),
            year,
        ),
        year,
    )
    dependant = np.array([not p["is_claimant_or_partner"] for p in flatten(units)])
    # Where the couple's reports leave the family's legacy awards open, they
    # never change a dependant's predicate.
    kept = dependant & ~family_closed
    assert reported[kept].tolist() == cleared[kept].tolist()
    # Where they close them, they can only lift a dependant's exclusion.
    closed = dependant & family_closed
    assert not np.any(~reported[closed] & cleared[closed])


@SETTINGS
@given(units=closure_units_strategy, year=st.sampled_from((2025, 2026)))
def test_a_closed_legacy_award_never_excludes(units, year):
    # The model ends a person's own income-related ESA once their legacy
    # awards close (person_legacy_benefits_closed, read by
    # esa_income_report_closed), and the family's Housing Benefit once the
    # claimant's and partner's close outside the Pension Credit age
    # conditions (housing_benefit_eligible). Clearing those reports leaves
    # every predicate as it was. Neither report enters legacy_award_is_closed.
    # They reach the closures only through a mixed-age couple's Pension
    # Credit saving, which clearing both reports of a closed family can't
    # create. Tax credits close from 2025 and Income Support and income-based
    # JSA from 2026. The claim limbs stay out: the claim can end an award in
    # a family whose legacy awards stay open.
    sim = simulate(units, year)
    reported = predicate(sim, year)
    award_open = open_awards(sim, year, claim_limbs=False)
    closed = {
        name: ~award_open[name]
        for name in ("esa_income_reported", "housing_benefit_reported")
    }
    cleared_units, index = [], 0
    for members in units:
        cleared_members = []
        for p in members:
            cleared_members.append(
                dict(p, **{name: 0.0 for name in closed if closed[name][index]})
            )
            index += 1
        cleared_units.append(cleared_members)
    cleared = predicate(simulate(cleared_units, year), year)
    assert reported.tolist() == cleared.tolist()


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
    expected = reg_5_test(sim, year) & ~reg_28_exclusions(units, year, sim)
    assert predicate(sim, year).tolist() == expected.tolist()


@SETTINGS
@given(units=units_strategy, year=st.sampled_from(YEARS))
def test_a_claim_changes_no_dependants_predicate(units, year):
    # A claim for Universal Credit ends the claimant's and partner's own
    # awards, not a dependant's (SI 2014/1230 reg. 8(2) and (2A)).
    without_claim = predicate(simulate(claiming(units, False), year), year)
    with_claim = predicate(simulate(claiming(units, True), year), year)
    dependant = np.array([not p["is_claimant_or_partner"] for p in flatten(units)])
    assert with_claim[dependant].tolist() == without_claim[dependant].tolist()


@SETTINGS
@given(units=qualifying_units_strategy, year=st.sampled_from(YEARS))
def test_a_claim_never_excludes_a_claimant_or_partner(units, year):
    # A claim only ends awards, so it can only lift a claimant's or partner's
    # exclusion.
    without_claim = predicate(simulate(claiming(units, False), year), year)
    with_claim = predicate(simulate(claiming(units, True), year), year)
    member_of_couple = np.array([p["is_claimant_or_partner"] for p in flatten(units)])
    assert not np.any(without_claim[member_of_couple] & ~with_claim[member_of_couple])
