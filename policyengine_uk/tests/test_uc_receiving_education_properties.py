"""Universal Credit's condition that a claimant is not receiving education.

The Welfare Reform Act 2012 s. 4(1)(d) makes it a basic condition that a
claimant "is not receiving education". The Universal Credit Regulations 2013
reg. 12 says who receives education, and reg. 14(1) lists exceptions. Reg. 3(2)
lets a couple claim jointly where one member doesn't meet the age condition
or this one, and DWP's Advice for Decision Making E2016 applies it "where one
member of a couple meets all the basic UC conditions". The Universal Credit
(Transitional Provisions) Regulations 2014 reg. 28 takes a person entitled to
an existing benefit out of the definition of a qualifying young person. Only
a person flagged is_in_full_time_education can receive education in the
model, and only has_education_maintenance_funding meets the funding test in
reg. 12(2)(b).

Each drawn case is a year and up to four families, each in a household of its
own: a single adult or a couple, up to two children or young people, and
inputs that reach every limb the model applies (course level, maintenance
funding, student loans and grants, Attendance Allowance, Armed Forces
Independence Payment, DLA and PIP with or without limited capability for work,
foster flags, an ineligible partner, reported Housing Benefit and Working Tax
Credit, a legacy closure claim, earnings, rent and savings). The test
calculates the same people five ways: as drawn; with the eligibility formula
on main before this change (BEFORE, kept verbatim below); with no one flagged;
with the flags of members who are neither claimant nor partner reversed; and
with every student loan and education grant removed.
Invariants:

1. Never raises: each family's Universal Credit is either what it is under
   BEFORE or nil, so setting the input never raises it.
2. Unflagged families don't change: with no one flagged, every output listed
   in OUTPUTS equals its value under BEFORE.
3. Differential: receiving education, the exceptions, the qualifying young
   person status the condition reads, and is_uc_eligible equal a reference
   implementation that reads the drawn inputs. The reference applies regs.
   3(2), 12 and 14 as ADM E2016 reads them, SI 2014/1230 regs. 28 and 60, and
   BEFORE's routes; without the education condition it gives BEFORE's
   eligibility.
4. Exceptions: a claimant who meets a modelled reg. 14 exception, or the SI
   2014/1230 reg. 60 protection, meets the condition, and a family whose
   claimants all meet it gets the Universal Credit it gets under BEFORE.
5. Only the couple counts: reversing the flags of members who are neither
   claimant nor partner (children and qualifying young people) changes no
   family's Universal Credit. A partner who cannot be a joint claimant (reg.
   3(3)) is still a member of the couple, so whether they receive education
   can decide reg. 14(1)(e) for the claimant.
6. One member meets both: every eligible family that makes no closure claim
   has a claimant who meets the minimum age, hasn't reached the qualifying
   age for State Pension Credit and meets the education condition.
7. Maintenance funding comes from the input: removing every student loan and
   education grant changes no one's receiving education and no output in
   OUTPUTS.
8. Reg. 28: a person who reports an existing benefit never counts as a
   qualifying young person for the condition.

A family in a household with other families can lose Universal Credit
because of another family's student: when the household head's family cannot
claim, its non-dependants count in the next claim by a family liable for the
rent. Paragraph 9(2)(f) of Schedule 4 prevents duplicate non-dependant
treatment. The model assigns non-dependants to the household head's eligible
claim first. test_student_head_moves_non_dependant_to_joint_tenant pins it;
the invariants above hold for families with households of their own.
"""

import json

import numpy as np
import pytest
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st
from policyengine_core.reforms import Reform

from policyengine_uk import Simulation
from policyengine_uk.model_api import *

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

PROPERTY_SETTINGS = settings(
    max_examples=15,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
# 2019: before the mixed-age couple exclusion of 15 May 2019 (parameters are
# read at 30 April). 2021, 2024 and 2026 span the reg. 14(1)(b) versions.
YEARS = [2019, 2021, 2024, 2026]
REGIONS = ["NORTH_EAST", "LONDON", "SCOTLAND", "NORTHERN_IRELAND"]
EDUCATION = ["TERTIARY", "POST_SECONDARY", "NOT_IN_EDUCATION"]
# SI 2014/1230 reg. 2(1), as reported receipt.
EXISTING_BENEFITS = [
    "jsa_income_reported",
    "esa_income_reported",
    "income_support_reported",
    "housing_benefit_reported",
    "child_tax_credit_reported",
    "working_tax_credit_reported",
]
TAX_CREDITS = ["child_tax_credit_reported", "working_tax_credit_reported"]
# Compare eligibility, maximum entitlement, income reduction and Universal
# Credit awards.
OUTPUTS = [
    "universal_credit",
    "is_uc_eligible",
    "uc_maximum_amount",
    "uc_income_reduction",
]
rarely = st.integers(0, 4).map(lambda n: n == 0)
sometimes = st.integers(0, 2).map(lambda n: n == 0)


class is_uc_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "Eligible for Universal Credit (before the education condition)"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        # main at 2da212abc, without its comments.
        capital = benunit("uc_assessable_capital", period)
        limit = parameters(period).gov.dwp.universal_credit.means_test.capital.limit
        claimant = benunit.members("is_uc_single_or_joint_claimant", period)
        meets_minimum_age = benunit.members("meets_uc_minimum_age_condition", period)
        pension_age = benunit.members(
            "has_attained_state_pension_credit_qualifying_age", period
        )
        has_qualifying_claimant = benunit.any(
            claimant & meets_minimum_age & ~pension_age
        )
        pension_credit_route = benunit("meets_pension_credit_age_conditions", period)
        closure_claim = benunit("claims_uc_at_legacy_closure", period)
        on_working_tax_credit = (
            add(benunit, period, ["working_tax_credit_reported"]) > 0
        )
        reg_60a = on_working_tax_credit & benunit.any(claimant & meets_minimum_age)
        route = (has_qualifying_claimant & ~pension_credit_route) | (
            closure_claim & (has_qualifying_claimant | reg_60a)
        )
        return route & (capital <= limit)


class before_education_condition(Reform):
    def apply(self):
        self.update_variable(is_uc_eligible)


@st.composite
def adult(draw, ages):
    full_time = draw(sometimes)
    return dict(
        age=draw(ages),
        is_in_full_time_education=full_time,
        current_education=draw(st.sampled_from(EDUCATION)),
        in_HE=draw(rarely),
        has_education_maintenance_funding=draw(rarely),
        student_loans=draw(st.sampled_from([0, 0, 0, 3_000])),
        education_grants=draw(st.sampled_from([0, 0, 0, 1_500])),
        aa_category=draw(st.sampled_from(["NONE", "NONE", "NONE", "LOWER"])),
        armed_forces_independence_payment=draw(st.sampled_from([0, 0, 0, 8_000])),
        dla_sc_category=draw(st.sampled_from(["NONE", "NONE", "NONE", "MIDDLE"])),
        pip_dl_category=draw(st.sampled_from(["NONE", "NONE", "STANDARD"])),
        uc_limited_capability_for_work=draw(rarely),
        uc_is_responsible_foster_parent_of_child_under_one=draw(rarely),
        uc_is_foster_parent_or_new_friend_or_family_carer=draw(rarely),
        housing_benefit_reported=draw(st.sampled_from([0, 0, 0, 0, 6_000])),
        working_tax_credit_reported=draw(st.sampled_from([0, 0, 0, 0, 1_000])),
        employment_income=draw(st.sampled_from([0, 0, 4_000, 15_000])),
        is_claimant_or_partner=True,
    )


@st.composite
def young_person(draw):
    return dict(
        age=draw(st.sampled_from([2, 10, 16, 17, 18])),
        is_in_full_time_education=draw(st.booleans()),
        current_education=draw(st.sampled_from(EDUCATION)),
        has_education_maintenance_funding=draw(rarely),
        is_claimant_or_partner=False,
    )


@st.composite
def family(draw):
    ages = st.sampled_from([16, 17, 18, 19, 22, 30, 45, 61, 70, 80])
    people = [draw(adult(ages))]
    if draw(st.booleans()):
        partner = draw(adult(ages))
        partner["uc_is_ineligible_partner"] = draw(rarely)
        people.append(partner)
    people += draw(st.lists(young_person(), max_size=2))
    if len(people) > 1 and any(not p["is_claimant_or_partner"] for p in people):
        for person in people:
            if person["is_claimant_or_partner"]:
                person["is_parent"] = True
    tenure = draw(st.sampled_from(["RENT_FROM_COUNCIL", "OWNED_OUTRIGHT"]))
    return dict(
        people=people,
        benunit=dict(claims_uc_at_legacy_closure=draw(rarely)),
        household=dict(
            region=draw(st.sampled_from(REGIONS)),
            tenure_type=tenure,
            rent=0 if tenure == "OWNED_OUTRIGHT" else 6_000,
            savings=draw(st.sampled_from([0, 0, 20_000])),
        ),
    )


@st.composite
def cases(draw):
    return dict(
        year=draw(st.sampled_from(YEARS)),
        families=draw(st.lists(family(), min_size=1, max_size=4)),
    )


def situation(case, variants):
    """Each family in a household of its own, once for each variant. A variant
    is None for the drawn inputs, or a function that takes a person's index
    and inputs and returns the inputs to use."""
    year = case["year"]
    people, benunits, households = {}, {}, {}
    for v, change in enumerate(variants):
        index = 0
        for f, fam in enumerate(case["families"]):
            members = []
            for person in fam["people"]:
                name = f"p{v}_{index}"
                values = dict(person)
                if change is not None:
                    values = change(index, values)
                people[name] = {k: {year: x} for k, x in values.items()}
                members.append(name)
                index += 1
            benunits[f"b{v}_{f}"] = {
                "members": members,
                **{k: {year: x} for k, x in fam["benunit"].items()},
            }
            households[f"h{v}_{f}"] = {
                "members": members,
                **{k: {year: x} for k, x in fam["household"].items()},
            }
    return {"people": people, "benunits": benunits, "households": households}


def all_flags(case):
    return [
        p["is_in_full_time_education"] for f in case["families"] for p in f["people"]
    ]


VARIABLES = OUTPUTS + [
    "is_uc_single_or_joint_claimant",
    "is_uc_assessed_claimant",
    "meets_uc_minimum_age_condition",
    "meets_pension_credit_age_conditions",
    "uc_assessable_capital",
    "is_qualifying_young_person_for_universal_credit",
    "is_qualifying_young_person_for_uc_education",
    "is_responsible_for_child_or_qualifying_young_person_for_universal_credit",
    "has_attained_state_pension_credit_qualifying_age",
    "is_mixed_age_couple",
    "uc_limited_capability_for_work",
    "attendance_allowance",
    "dla",
    "pip",
    "uc_receiving_education",
    "uc_is_excepted_from_education_condition",
    "meets_uc_education_condition",
]


def run(case, variants=(None,), before=False):
    """One simulation of every variant; returns one result per variant."""
    simulation = Simulation(situation=situation(case, variants))
    if before:
        simulation.apply_reform(before_education_condition)
    year = case["year"]
    values = {name: simulation.calculate(name, year) for name in VARIABLES}
    limit = simulation.tax_benefit_system.parameters(
        f"{year}-01-01"
    ).gov.dwp.universal_credit.means_test.capital.limit
    sizes = {
        "person": sum(len(f["people"]) for f in case["families"]),
        "benunit": len(case["families"]),
        "household": len(case["families"]),
    }
    results = []
    for v in range(len(variants)):
        result = {"capital_limit": limit}
        for name, array in values.items():
            entity = simulation.tax_benefit_system.variables[name].entity.key
            size = sizes[entity]
            result[name] = array[v * size : (v + 1) * size]
        results.append(result)
    return results


def reference(case, result):
    """Regs. 3(2), 12 and 14, SI 2014/1230 regs. 28 and 60 and ADM E2016 from
    the drawn inputs.

    Returns, per person, receiving education, excepted and qualifying young
    person for the condition, and per family, eligibility with the education
    condition and without it. Reads from the model only the roles (who is a
    claimant), the age conditions, qualifying young person status before reg.
    28, the Pension Credit route, capital, responsibility for a child, limited
    capability for work and the disability benefit amounts, which other rules
    settle.
    """
    receiving, excepted, qyp_for_education = [], [], []
    eligible, eligible_before = [], []
    index = 0
    for f, fam in enumerate(case["families"]):
        start = index
        members = range(start, start + len(fam["people"]))
        person_of = dict(zip(members, fam["people"]))
        couple = [i for i in members if result["is_uc_assessed_claimant"][i]]
        couple_tax_credits = any(
            person_of[j].get(name, 0) > 0 for j in couple for name in TAX_CREDITS
        )
        qyp, recv = {}, {}
        for i, person in person_of.items():
            existing_benefit = any(
                person.get(name, 0) > 0 for name in EXISTING_BENEFITS
            ) or (i in couple and couple_tax_credits)
            qyp[i] = (
                bool(result["is_qualifying_young_person_for_universal_credit"][i])
                and not existing_benefit
            )
            advanced = person["current_education"] == "TERTIARY" or person.get(
                "in_HE", False
            )
            maintenance = person.get("has_education_maintenance_funding", False)
            recv[i] = person["is_in_full_time_education"] and (
                advanced or maintenance or qyp[i]
            )
        foster = {
            i: person.get("uc_is_responsible_foster_parent_of_child_under_one", False)
            or person.get("uc_is_foster_parent_or_new_friend_or_family_carer", False)
            for i, person in person_of.items()
        }
        exc = {}
        for i, person in person_of.items():
            in_couple_role = i in couple
            partner = [j for j in couple if j != i]
            disability_benefit = (
                result["attendance_allowance"][i] > 0
                or person.get("armed_forces_independence_payment", 0) > 0
                or result["dla"][i] > 0
                or result["pip"][i] > 0
            )
            limb_b = bool(disability_benefit) and bool(
                result["uc_limited_capability_for_work"][i]
            )
            limb_c = in_couple_role and bool(
                result[
                    "is_responsible_for_child_or_qualifying_young_person_for_universal_credit"
                ][f]
            )
            limb_d = in_couple_role and len(couple) == 1 and foster[i]
            limb_e = (
                in_couple_role
                and len(couple) == 2
                and all(recv[j] for j in couple)
                and any(foster[j] for j in partner)
            )
            limb_f = (
                in_couple_role
                and bool(result["has_attained_state_pension_credit_qualifying_age"][i])
                and bool(result["is_mixed_age_couple"][f])
            )
            reg_60 = (
                in_couple_role
                and fam["benunit"]["claims_uc_at_legacy_closure"]
                and not qyp[i]
            )
            exc[i] = limb_b or limb_c or limb_d or limb_e or limb_f or reg_60
        claimants = [i for i in members if result["is_uc_single_or_joint_claimant"][i]]
        minimum_age = {
            i: bool(result["meets_uc_minimum_age_condition"][i]) for i in claimants
        }
        pension_age = {
            i: bool(result["has_attained_state_pension_credit_qualifying_age"][i])
            for i in claimants
        }
        on_working_tax_credit = any(
            person.get("working_tax_credit_reported", 0) > 0 for person in fam["people"]
        )
        pension_credit_route = bool(result["meets_pension_credit_age_conditions"][f])
        closure = fam["benunit"]["claims_uc_at_legacy_closure"]
        capital_ok = result["uc_assessable_capital"][f] <= result["capital_limit"]

        def eligibility(meets):
            # ADM E2016: one claimant meets the age and education conditions.
            qualifying = any(
                minimum_age[i] and not pension_age[i] and meets[i] for i in claimants
            )
            reg_60a = on_working_tax_credit and any(
                minimum_age[i] and meets[i] for i in claimants
            )
            route = (qualifying and not pension_credit_route) or (
                closure and (qualifying or reg_60a)
            )
            return bool(route and capital_ok)

        eligible.append(eligibility({i: not recv[i] or exc[i] for i in claimants}))
        eligible_before.append(eligibility({i: True for i in claimants}))
        receiving += [recv[i] for i in members]
        excepted += [exc[i] for i in members]
        qyp_for_education += [qyp[i] for i in members]
        index += len(fam["people"])
    return (
        np.array(receiving),
        np.array(excepted),
        np.array(qyp_for_education),
        np.array(eligible),
        np.array(eligible_before),
    )


def person(age, **inputs):
    values = dict(
        age=age,
        is_in_full_time_education=False,
        current_education="NOT_IN_EDUCATION",
        is_claimant_or_partner=True,
    )
    values.update(inputs)
    return values


def student(age, **inputs):
    return person(
        age, is_in_full_time_education=True, current_education="TERTIARY", **inputs
    )


def household(region="NORTH_EAST", **inputs):
    values = dict(region=region, tenure_type="OWNED_OUTRIGHT", rent=0, savings=0)
    values.update(inputs)
    return values


def single_family(people, closure=False, **household_inputs):
    return dict(
        people=people,
        benunit=dict(claims_uc_at_legacy_closure=closure),
        household=household(**household_inputs),
    )


EXAMPLES = [
    # Issue 2346: a 19-year-old on a full-time degree, alone.
    dict(
        year=2026,
        families=[
            single_family(
                [student(19, employment_income=4_571)],
                region="SOUTH_WEST",
                tenure_type="RENT_FROM_COUNCIL",
                rent=6_000,
            )
        ],
    ),
    # A mixed-age couple who are both students (reg. 14(1)(f) excepts the
    # older member, and no member meets both conditions), and a student
    # couple with a foster parent (reg. 14(1)(e)(ii)).
    dict(
        year=2026,
        families=[
            single_family([student(70), student(61)]),
            single_family(
                [
                    student(30),
                    student(30, uc_is_foster_parent_or_new_friend_or_family_carer=True),
                ],
                region="NORTHERN_IRELAND",
            ),
        ],
    ),
    # The other mixed-age couples: the older member alone studies (eligible),
    # and the younger member alone studies (no member meets both).
    dict(
        year=2026,
        families=[
            single_family([student(70), person(61)]),
            single_family([person(70), student(61)]),
        ],
    ),
    # SI 2014/1230 reg. 28: an 18-year-old on a non-advanced full-time course
    # who reports Housing Benefit, without and with a closure claim.
    dict(
        year=2026,
        families=[
            single_family(
                [
                    person(
                        18,
                        is_in_full_time_education=True,
                        current_education="POST_SECONDARY",
                        housing_benefit_reported=6_000,
                    )
                ],
                tenure_type="RENT_FROM_COUNCIL",
                rent=6_000,
            ),
            single_family(
                [
                    person(
                        18,
                        is_in_full_time_education=True,
                        current_education="POST_SECONDARY",
                        has_education_maintenance_funding=True,
                        housing_benefit_reported=6_000,
                    )
                ],
                closure=True,
                tenure_type="RENT_FROM_COUNCIL",
                rent=6_000,
            ),
        ],
    ),
]


def check(case):
    context = json.dumps(case)
    flags = all_flags(case)
    # Members who are neither claimant nor partner: is_claimant_or_partner is
    # supplied, and a benefit unit has at most two adults.
    couple = [
        p["is_claimant_or_partner"] for f in case["families"] for p in f["people"]
    ]

    def unflagged(i, values):
        return {**values, "is_in_full_time_education": False}

    def others_reversed(i, values):
        if couple[i]:
            return values
        return {**values, "is_in_full_time_education": not flags[i]}

    def no_loans_or_grants(i, values):
        return {**values, "student_loans": 0, "education_grants": 0}

    drawn, no_flags, reversed_others, no_loans = run(
        case, variants=[None, unflagged, others_reversed, no_loans_or_grants]
    )
    (before,) = run(case, before=True)
    claimant = drawn["is_uc_single_or_joint_claimant"]
    np.testing.assert_array_equal(drawn["is_uc_assessed_claimant"], couple, context)

    uc = drawn["universal_credit"]
    uc_before = before["universal_credit"]
    # 1. Never raises: either BEFORE's amount or nil.
    unchanged = np.isclose(uc, uc_before, atol=0.005)
    assert np.all(unchanged | (uc == 0)), context
    assert np.all(uc <= uc_before + 0.005), context
    # 2. Unflagged families don't change.
    for name in OUTPUTS:
        np.testing.assert_allclose(
            no_flags[name].astype(float),
            before[name].astype(float),
            atol=0.005,
            err_msg=f"{name}: {context}",
        )
    # 3. Differential against the reference implementation.
    receiving, excepted, qyp, eligible, eligible_before = reference(case, drawn)
    np.testing.assert_array_equal(drawn["uc_receiving_education"], receiving, context)
    np.testing.assert_array_equal(
        drawn["uc_is_excepted_from_education_condition"], excepted, context
    )
    np.testing.assert_array_equal(
        drawn["is_qualifying_young_person_for_uc_education"], qyp, context
    )
    np.testing.assert_array_equal(drawn["is_uc_eligible"], eligible, context)
    np.testing.assert_array_equal(before["is_uc_eligible"], eligible_before, context)
    # 4. Exceptions keep the claimant in, and a family whose claimants all
    # meet the condition keeps BEFORE's award.
    meets = drawn["meets_uc_education_condition"]
    assert np.all(meets[excepted]), context
    index = 0
    for f, fam in enumerate(case["families"]):
        members = range(index, index + len(fam["people"]))
        if all(meets[i] for i in members if claimant[i]):
            assert np.isclose(uc[f], uc_before[f], atol=0.005), context
        index += len(fam["people"])
    # 5. Only the couple counts.
    np.testing.assert_allclose(
        reversed_others["universal_credit"], uc, atol=0.005, err_msg=context
    )
    np.testing.assert_array_equal(
        reversed_others["is_uc_eligible"], drawn["is_uc_eligible"], context
    )
    # 6. One member meets both conditions on the ordinary route.
    index = 0
    for f, fam in enumerate(case["families"]):
        members = range(index, index + len(fam["people"]))
        if (
            drawn["is_uc_eligible"][f]
            and not fam["benunit"]["claims_uc_at_legacy_closure"]
        ):
            assert any(
                claimant[i]
                and drawn["meets_uc_minimum_age_condition"][i]
                and not drawn["has_attained_state_pension_credit_qualifying_age"][i]
                and meets[i]
                for i in members
            ), context
        index += len(fam["people"])
    # 7. Student loans and education grants don't decide receiving education.
    np.testing.assert_array_equal(
        no_loans["uc_receiving_education"], drawn["uc_receiving_education"], context
    )
    for name in OUTPUTS:
        np.testing.assert_allclose(
            no_loans[name].astype(float),
            drawn[name].astype(float),
            atol=0.005,
            err_msg=f"{name}: {context}",
        )
    # 8. Reg. 28: no one who reports an existing benefit counts as a
    # qualifying young person for the condition.
    reports = np.array(
        [
            any(p.get(name, 0) > 0 for name in EXISTING_BENEFITS)
            for fam in case["families"]
            for p in fam["people"]
        ]
    )
    assert not np.any(drawn["is_qualifying_young_person_for_uc_education"][reports])


@PROPERTY_SETTINGS
@example(EXAMPLES[0])
@example(EXAMPLES[1])
@example(EXAMPLES[2])
@example(EXAMPLES[3])
@given(cases())
def test_education_condition_invariants(case):
    check(case)


def test_examples_reach_the_cases():
    """The examples exclude the issue's student, apply the couple rule both
    ways and send the young Housing Benefit claimant down the ordinary route,
    so the invariants run on each outcome."""
    (issue,) = run(EXAMPLES[0])
    assert not issue["is_uc_eligible"][0]
    assert issue["universal_credit"][0] == 0
    assert run(EXAMPLES[0], before=True)[0]["universal_credit"][0] > 0
    (couples,) = run(EXAMPLES[1])
    np.testing.assert_array_equal(couples["is_uc_eligible"], [False, True])
    np.testing.assert_array_equal(
        couples["uc_is_excepted_from_education_condition"],
        [True, False, True, False],
    )
    (mixed_age,) = run(EXAMPLES[2])
    np.testing.assert_array_equal(mixed_age["is_uc_eligible"], [True, False])
    (young,) = run(EXAMPLES[3])
    np.testing.assert_array_equal(
        young["is_qualifying_young_person_for_universal_credit"], [True, True]
    )
    np.testing.assert_array_equal(
        young["is_qualifying_young_person_for_uc_education"], [False, False]
    )
    np.testing.assert_array_equal(young["uc_receiving_education"], [False, True])
    np.testing.assert_array_equal(
        young["uc_is_excepted_from_education_condition"], [False, True]
    )
    np.testing.assert_array_equal(young["is_uc_eligible"], [True, True])
    assert np.all(young["universal_credit"] > 0)


def test_student_head_moves_non_dependant_to_joint_tenant():
    """A family with no one flagged loses Universal Credit when the household
    head's family is a full-time student's.

    The head's family cannot claim, so the model counts the non-dependant in
    the joint tenant's claim instead. Paragraph 9(2)(f) of Schedule 4 to the
    UC Regs 2013 prevents duplicate non-dependant treatment, and the model
    assigns non-dependants to the household head's eligible claim first. The
    joint tenant's claim then has the housing cost contribution of £96.55 a
    month in 2026 (Sch 4 para 14(1), as SI 2026/148 art. 32(3) sets it): 12 x
    £96.55 = £1,158.60. Two copies of the household, the head unflagged and
    then flagged.
    """
    year = 2026
    people, benunits, households = {}, {}, {}
    for copy, head_full_time in enumerate([False, True]):
        head, tenant, other = (f"{role}{copy}" for role in ("head", "tenant", "nd"))
        people[head] = {
            "age": {year: 30},
            "current_education": {year: "TERTIARY"},
            "is_in_full_time_education": {year: head_full_time},
        }
        people[tenant] = {"age": {year: 30}}
        people[other] = {"age": {year: 30}, "employment_income": {year: 20_000}}
        benunits[f"b_{head}"] = {"members": [head]}
        benunits[f"b_{tenant}"] = {
            "members": [tenant],
            "liable_for_share_of_household_rent": {year: True},
        }
        benunits[f"b_{other}"] = {"members": [other]}
        households[f"h{copy}"] = {
            "members": [head, tenant, other],
            "region": {year: "NORTH_EAST"},
            "tenure_type": {year: "RENT_FROM_COUNCIL"},
            "rent": {year: 12_000},
        }
    simulation = Simulation(
        situation={"people": people, "benunits": benunits, "households": households}
    )
    np.testing.assert_array_equal(
        simulation.calculate("uc_non_dependants_counted", year),
        [True, False, False, False, True, False],
    )
    universal_credit = simulation.calculate("universal_credit", year)
    assert np.isclose(universal_credit[1] - universal_credit[4], 12 * 96.55, atol=0.01)
