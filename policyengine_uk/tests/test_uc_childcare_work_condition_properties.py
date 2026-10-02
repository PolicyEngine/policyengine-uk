"""Property-based tests for the Universal Credit childcare work condition.

Universal Credit Regulations 2013 reg. 32(1): the condition is met if (a) the
claimant is in paid work or has an offer of paid work due to start before the
end of the next assessment period, and (b) for a couple, the other member is
in paid work or is unable to provide childcare because they (i) have limited
capability for work, (ii) have regular and substantial caring
responsibilities for a severely disabled person, or (iii) are temporarily
absent from the claimant's household. Reg. 32(2)(b) treats a claimant
receiving statutory sick, maternity or paternity pay or maternity allowance
as in paid work. Each joint claimant is a claimant (WRA 2012 s. 40).

Invariants, for any generated population of single claimants and couples,
each with a dependant child or young person:

1. Differential: the condition equals a reference transcribed from reg. 32 in
   its pairwise form, (a)(A) and (b)(B), or (a)(B) and (b)(A).
2. Monotonic: giving any member an exception, a listed payment, paid work or
   an offer of paid work never removes the condition.
3. A couple who are both in paid work always meet the condition.
4. Without a member meeting limb (a), no exception meets the condition.
5. Swapping the two members of a couple does not change the result.
6. A dependant's work, payments and circumstances never change the result.
7. The childcare element is zero whenever the condition fails, and never
   negative.

Every member's is_claimant_or_partner is set from its generated role, as the
FRS supplies it, and every attribute is set for every member: setting an
input for anyone makes it an input for everyone.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

YEAR = 2025
PROPERTY_SETTINGS = settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
# Reg. 32(2)(b) payments the model has variables for.
PAYMENTS = [
    None,
    "statutory_sick_pay",
    "statutory_maternity_pay",
    "statutory_paternity_pay",
    "maternity_allowance_reported",
]
CARE_HOURS = [0, 20, 34, 35, 50]
# Attributes that can only add a route to the condition.
WIDENING = ["works", "payment", "offer", "lcw", "carer", "absent"]


@st.composite
def members(draw):
    # Each member has a small set of routes, so that members with exactly one
    # route (an offer only, an exception only) are common.
    routes = draw(st.sets(st.sampled_from(WIDENING), max_size=3))
    payments = PAYMENTS[1:] if "payment" in routes else [None]
    carer_hours = [
        h for h in CARE_HOURS if (h >= MIN_CARE_HOURS) == ("carer" in routes)
    ]
    return dict(
        works="works" in routes,
        payment=draw(st.sampled_from(payments)),
        offer="offer" in routes,
        lcw="lcw" in routes,
        care_hours=draw(st.sampled_from(carer_hours)),
        absent="absent" in routes,
    )


@st.composite
def families(draw):
    adults = draw(st.lists(members(), min_size=1, max_size=2))
    return dict(
        adults=adults,
        dependant=draw(members()),
        dependant_age=draw(st.sampled_from([3, 17, 18])),
        childcare=draw(st.sampled_from([0.0, 2_000.0, 20_000.0])),
    )


def person_inputs(member, age, claimant_or_partner):
    inputs = {
        "age": age,
        "is_claimant_or_partner": claimant_or_partner,
        "employment_income": 12_000.0 if member["works"] else 0.0,
        "hours_worked": 0.0,
        "uc_has_offer_of_paid_work": member["offer"],
        "uc_limited_capability_for_WRA": member["lcw"],
        "care_hours": float(member["care_hours"]),
        "uc_is_temporarily_absent_from_claimant_household": member["absent"],
    }
    for payment in PAYMENTS[1:]:
        inputs[payment] = 1_000.0 if member["payment"] == payment else 0.0
    return {name: {YEAR: value} for name, value in inputs.items()}


def situation(units, with_dependants=True):
    people, benunits, households = {}, {}, {}
    for i, unit in enumerate(units):
        names = []
        for j, adult in enumerate(unit["adults"]):
            name = f"p{i}_{j}"
            people[name] = person_inputs(adult, 30 + j, True)
            names.append(name)
        if with_dependants:
            name = f"p{i}_dependant"
            people[name] = person_inputs(
                unit["dependant"], unit["dependant_age"], False
            )
            people[name]["childcare_expenses"] = {YEAR: unit["childcare"]}
            if unit["dependant_age"] >= 16:
                people[name]["current_education"] = {YEAR: "UPPER_SECONDARY"}
            names.append(name)
        benunits[f"b{i}"] = {"members": names}
        households[f"h{i}"] = {"members": names}
    return {"people": people, "benunits": benunits, "households": households}


def calculate(units, with_dependants=True):
    sim = Simulation(situation=situation(units, with_dependants))
    return {
        variable: np.asarray(sim.calculate(variable, YEAR))
        for variable in ["uc_childcare_work_condition", "uc_childcare_element"]
    }


def min_care_hours():
    sim = Simulation(situation={"people": {"p": {"age": {YEAR: 30}}}})
    return sim.tax_benefit_system.parameters(YEAR).gov.dwp.carers_allowance.min_hours


MIN_CARE_HOURS = min_care_hours()


def meets_claimant_limb(member):
    # Reg. 32(1)(a) with reg. 32(2)(b).
    return member["works"] or member["payment"] is not None or member["offer"]


def meets_other_member_limb(member):
    # Reg. 32(1)(b); joint claimants also have reg. 32(2)(b).
    unable = member["lcw"] or member["care_hours"] >= MIN_CARE_HOURS or member["absent"]
    return member["works"] or member["payment"] is not None or unable


def reference(unit):
    adults = unit["adults"]
    if len(adults) == 1:
        return meets_claimant_limb(adults[0])
    first, second = adults
    return (meets_claimant_limb(first) and meets_other_member_limb(second)) or (
        meets_claimant_limb(second) and meets_other_member_limb(first)
    )


def with_member(unit, index, **changes):
    adults = [dict(adult) for adult in unit["adults"]]
    adults[index].update(changes)
    return dict(unit, adults=adults)


WIDEN = {
    "works": dict(works=True),
    "payment": dict(payment="statutory_sick_pay"),
    "offer": dict(offer=True),
    "lcw": dict(lcw=True),
    "carer": dict(care_hours=50),
    "absent": dict(absent=True),
}


@PROPERTY_SETTINGS
@given(st.lists(families(), min_size=1, max_size=30))
def test_condition_matches_the_regulation_32_reference(units):
    values = calculate(units)
    for i, unit in enumerate(units):
        assert bool(values["uc_childcare_work_condition"][i]) == reference(unit), unit


def route_sets():
    return [
        {route for k, route in enumerate(WIDENING) if mask >> k & 1}
        for mask in range(2 ** len(WIDENING))
    ]


def member_with(routes, payment, care_hours):
    return dict(
        works="works" in routes,
        payment=payment if "payment" in routes else None,
        offer="offer" in routes,
        lcw="lcw" in routes,
        care_hours=care_hours if "carer" in routes else 0,
        absent="absent" in routes,
    )


def test_condition_matches_the_reference_for_every_combination_of_routes():
    # Exhaustive: every single claimant's set of routes with every listed
    # payment, and every pair of route sets for a couple, the payment and the
    # caring hours cycling across pairs.
    sets = route_sets()
    singles = [
        dict(adults=[member_with(routes, payment, MIN_CARE_HOURS)])
        for routes in sets
        for payment in PAYMENTS[1:]
    ]
    couples = [
        dict(
            adults=[
                member_with(first, PAYMENTS[1 + (i + j) % 4], MIN_CARE_HOURS),
                member_with(second, PAYMENTS[1 + (i + 2 * j) % 4], 50),
            ]
        )
        for i, first in enumerate(sets)
        for j, second in enumerate(sets)
    ]
    units = singles + couples
    met = calculate(units, with_dependants=False)["uc_childcare_work_condition"]
    expected = np.array([reference(unit) for unit in units])
    mismatches = [unit for unit, m, e in zip(units, met, expected) if m != e]
    assert not mismatches, mismatches[:5]


@PROPERTY_SETTINGS
@given(
    st.lists(
        st.tuples(families(), st.integers(0, 1), st.sampled_from(WIDENING)),
        min_size=1,
        max_size=30,
    )
)
def test_adding_an_exception_or_work_never_removes_the_condition(cases):
    units = [unit for unit, _, _ in cases]
    widened = [
        with_member(unit, index % len(unit["adults"]), **WIDEN[route])
        for unit, index, route in cases
    ]
    before = calculate(units)["uc_childcare_work_condition"]
    after = calculate(widened)["uc_childcare_work_condition"]
    assert not np.any(before & ~after), [
        case for case, b, a in zip(cases, before, after) if b and not a
    ]


@PROPERTY_SETTINGS
@given(st.lists(families(), min_size=1, max_size=30))
def test_a_couple_both_in_paid_work_always_meets_the_condition(units):
    couples = [
        dict(unit, adults=[dict(adult, works=True) for adult in unit["adults"]])
        for unit in units
        if len(unit["adults"]) == 2
    ]
    if couples:
        assert calculate(couples)["uc_childcare_work_condition"].all()


@PROPERTY_SETTINGS
@given(st.lists(families(), min_size=1, max_size=30))
def test_no_exception_meets_the_condition_without_limb_a(units):
    idle = [
        dict(
            unit,
            adults=[
                dict(adult, works=False, payment=None, offer=False)
                for adult in unit["adults"]
            ],
        )
        for unit in units
    ]
    assert not calculate(idle)["uc_childcare_work_condition"].any()


@PROPERTY_SETTINGS
@given(st.lists(families(), min_size=1, max_size=30))
def test_swapping_the_members_of_a_couple_does_not_change_the_result(units):
    couples = [unit for unit in units if len(unit["adults"]) == 2]
    if not couples:
        return
    swapped = [dict(unit, adults=unit["adults"][::-1]) for unit in couples]
    np.testing.assert_array_equal(
        calculate(couples)["uc_childcare_work_condition"],
        calculate(swapped)["uc_childcare_work_condition"],
    )


@PROPERTY_SETTINGS
@given(st.lists(families(), min_size=1, max_size=30))
def test_dependants_do_not_affect_the_condition(units):
    np.testing.assert_array_equal(
        calculate(units)["uc_childcare_work_condition"],
        calculate(units, with_dependants=False)["uc_childcare_work_condition"],
    )


@PROPERTY_SETTINGS
@given(st.lists(families(), min_size=1, max_size=30))
def test_childcare_element_needs_the_work_condition(units):
    values = calculate(units)
    element = values["uc_childcare_element"]
    assert np.all(element >= 0)
    assert np.all(element[~values["uc_childcare_work_condition"]] == 0)
