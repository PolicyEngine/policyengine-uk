"""Property-based tests: Universal Credit elements turn on the claimants.

UC Regs 2013 reg. 27(1) includes the LCWRA element "in respect of the fact
that a claimant has limited capability for work and work-related activity";
reg. 29(1) includes the carer element "where a claimant has regular and
substantial caring responsibilities for a severely disabled person"; and reg.
22(1)(b)(i) gives no work allowance "where a single claimant does not have,
or neither of joint claimants has, responsibility for a child or qualifying
young person or limited capability for work". A child's or qualifying young
person's disability or caring is not the claimant's. (The benefit cap
exceptions, which read the same circumstances, are tested with the cap.)

Invariants, for any generated population of single claimants and couples
with up to four dependants aged 0 to 19, with or without rent, in England,
Wales and Scotland:

1. A dependant's disability or caring never gives the claimants an LCWRA
   element, a carer element or a work allowance. Flagging every dependant as
   disabled, as having limited capability, as caring 35 hours or more or as
   receiving Carer's Allowance leaves `uc_LCWRA_element`, `uc_carer_element`,
   `is_uc_work_allowance_eligible` and `uc_work_allowance` exactly as they
   are when no dependant is.
2. Differential against DWP's published table. The Advice for Decision
   Making, chapter F6, paragraph F6037 tabulates which of the carer and LCWRA
   amounts an award includes for each combination a single claimant or joint
   claimants can have, for carers of different people. The model includes
   the same number of each element for all sixteen combinations, whatever the
   dependants' circumstances, both in the generated populations and in a
   deterministic run of every combination. Where joint claimants care for
   the same severely disabled person (reg. 29(3)) it includes at most one
   carer element: the table's number, capped at one. The carer element
   amount is written here from the reg. 36 table (£201.68 a month in
   2025-26, £209.34 in 2026-27), as is the 2025-26 LCWRA amount (£423.27),
   not read from the model.
3. Bounds: an award has at most one LCWRA element (reg. 27(4)), at most one
   carer element for each claimant (reg. 29(2)), and at most as many of the
   two elements together as it has claimants (reg. 29(4)). Giving both
   claimants limited capability gives exactly the LCWRA amount that giving it
   to one does, in 2026 too, where the rebalancing modifier sets the amount
   per award.
4. Monotonicity: a claimant coming to have limited capability never lowers
   the two elements' total (the LCWRA element is the larger), and never takes
   a work allowance away.
5. Order does not matter: entering the people of every family in reverse
   leaves the elements and the work allowance unchanged.
Marriage Allowance is switched off throughout, as in the other Universal
Credit property tests.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

PROPERTY_SETTINGS = settings(
    max_examples=15,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
YEARS = [2025, 2026]
TENURES = ["RENT_FROM_COUNCIL", "RENT_PRIVATELY", "OWNED_OUTRIGHT"]
REGIONS = ["LONDON", "NORTH_EAST", "WALES", "SCOTLAND"]
EDUCATION = ["UPPER_SECONDARY", "TERTIARY", "NOT_IN_EDUCATION"]
# Reg. 36 table, a month: carer element and (2025-26) LCWRA element.
CARER_ELEMENT = {2025: 201.68, 2026: 209.34}
LCWRA_ELEMENT_2025 = 423.27
ELEMENT_VARIABLES = [
    "uc_LCWRA_element",
    "uc_carer_element",
    "is_uc_work_allowance_eligible",
    "uc_work_allowance",
]
# What a dependant's disability or caring looks like in the inputs.
DEPENDANT_CIRCUMSTANCES = {
    "is_disabled_for_benefits": st.booleans(),
    "uc_limited_capability_for_WRA": st.booleans(),
    "care_hours": st.sampled_from([0.0, 20.0, 35.0, 60.0]),
    "carers_allowance_reported": st.sampled_from([0.0, 4_000.0]),
}

# DWP Advice for Decision Making, chapter F6, paragraph F6037: the additional
# amounts each claimant qualifies for ("C" carer, "L" LCWRA) and the amounts
# the award then includes, as (LCWRA elements, carer elements). The table
# lists twelve combinations; the other four follow by swapping the claimants
# or are the case where neither qualifies for either.
F6037 = {
    ("C", ""): (0, 1),
    ("L", ""): (1, 0),
    ("CL", ""): (1, 0),
    ("C", "C"): (0, 2),
    ("L", "L"): (1, 0),
    ("", "C"): (0, 1),
    ("C", "L"): (1, 1),
    ("", "L"): (1, 0),
    ("CL", "C"): (1, 1),
    ("CL", "L"): (1, 1),
    ("C", "CL"): (1, 1),
    ("CL", "CL"): (1, 1),
}


def published_elements(first, second=""):
    """(LCWRA elements, carer elements) from the F6037 table."""
    if not first and not second:
        return (0, 0)
    if (first, second) in F6037:
        return F6037[(first, second)]
    return F6037[(second, first)]


def code(claimant):
    return ("C" if claimant["care_hours"] >= 35 else "") + (
        "L" if claimant["uc_limited_capability_for_WRA"] else ""
    )


@st.composite
def dependants(draw, minimum=0, maximum=4):
    members = []
    for _ in range(draw(st.integers(minimum, maximum))):
        age = draw(st.integers(0, 19))
        member = dict(age=age)
        for variable, strategy in DEPENDANT_CIRCUMSTANCES.items():
            member[variable] = draw(strategy)
        if age >= 16:
            # At 18 and 19 only a qualifying young person is a dependant
            # (reg. 5(1)); anyone else that age is an adult whom the
            # calculator treats as a claimant.
            member["current_education"] = (
                draw(st.sampled_from(EDUCATION)) if age < 18 else "UPPER_SECONDARY"
            )
            member["age_started_or_accepted_current_education_or_training"] = draw(
                st.integers(16, min(age, 18))
            )
            if age == 19:
                member[
                    "is_before_universal_credit_qualifying_young_person_terminal_date"
                ] = True
        members.append(member)
    return members


@st.composite
def families(draw):
    claimants = [
        dict(
            age=draw(st.integers(25, 64)),
            care_hours=draw(st.sampled_from([0.0, 20.0, 35.0, 60.0])),
            uc_limited_capability_for_WRA=draw(st.booleans()),
            would_claim_carers_allowance=draw(st.booleans()),
        )
        for _ in range(draw(st.integers(1, 2)))
    ]
    return dict(
        claimants=claimants,
        dependants=draw(dependants()),
        tenure=draw(st.sampled_from(TENURES)),
        rent=draw(st.one_of(st.just(0.0), st.floats(0, 20_000))),
        region=draw(st.sampled_from(REGIONS)),
    )


populations = st.lists(families(), min_size=1, max_size=6)


def situation(
    units,
    year,
    clear=(),
    reverse=False,
    claimant_overrides=None,
    first_claimant_overrides=None,
    same_person=False,
):
    """One simulation holding every family.

    ``clear`` names dependant inputs to reset to their defaults. With
    ``reverse`` the people of each family are entered, and listed in their
    benefit unit and household, in reverse order. ``claimant_overrides``
    replaces inputs of every claimant, ``first_claimant_overrides`` those of
    the first. ``same_person`` says whether the claimants care for the same
    severely disabled person.
    """
    people, benunits, households = {}, {}, {}
    for i, unit in enumerate(units):
        members = []
        for j, claimant in enumerate(unit["claimants"]):
            values = {**claimant, **(claimant_overrides or {})}
            if j == 0:
                values.update(first_claimant_overrides or {})
            person = {k: {year: v} for k, v in values.items()}
            person["is_parent"] = {year: bool(unit["dependants"])}
            members.append((f"p{i}_{j}", person))
        for k, dependant in enumerate(unit["dependants"]):
            person = {
                key: {year: v} for key, v in dependant.items() if key not in clear
            }
            members.append((f"d{i}_{k}", person))
        if reverse:
            members = members[::-1]
        names = []
        for name, person in members:
            person["would_claim_marriage_allowance"] = {year: False}
            people[name] = person
            names.append(name)
        benunits[f"b{i}"] = {
            "members": names,
            "partners_care_for_same_severely_disabled_person": {year: same_person},
        }
        households[f"h{i}"] = {
            "members": names,
            "rent": {year: unit["rent"]},
            "tenure_type": {year: unit["tenure"]},
            "region": {year: unit["region"]},
        }
    return {"people": people, "benunits": benunits, "households": households}


def benunit_values(sim, year, variables):
    return {v: np.asarray(sim.calculate(v, year)) for v in variables}


def assert_same(a, b, units):
    for v in a:
        np.testing.assert_allclose(
            a[v].astype(float), b[v].astype(float), atol=0.01, err_msg=f"{v}: {units}"
        )


@PROPERTY_SETTINGS
@given(units=populations, year=st.sampled_from(YEARS))
def test_dependants_disability_or_caring_never_gives_claimants_an_element(units, year):
    with_circumstances = Simulation(situation=situation(units, year))
    without = Simulation(
        situation=situation(units, year, clear=tuple(DEPENDANT_CIRCUMSTANCES))
    )
    assert_same(
        benunit_values(with_circumstances, year, ELEMENT_VARIABLES),
        benunit_values(without, year, ELEMENT_VARIABLES),
        units,
    )


@PROPERTY_SETTINGS
@given(units=populations, year=st.sampled_from(YEARS))
def test_elements_match_the_published_table_of_combinations(units, year):
    sim = Simulation(situation=situation(units, year, same_person=False))
    lcwra = np.asarray(sim.calculate("uc_LCWRA_element", year))
    carer = np.asarray(sim.calculate("uc_carer_element", year))
    work_allowance = np.asarray(sim.calculate("is_uc_work_allowance_eligible", year))
    responsible = np.asarray(
        sim.map_result(
            np.asarray(
                sim.calculate(
                    "is_child_or_qualifying_young_person_for_universal_credit", year
                )
            ).astype(float),
            "person",
            "benunit",
        )
    )
    for i, unit in enumerate(units):
        lcwra_elements, carer_elements = published_elements(
            *[code(c) for c in unit["claimants"]]
        )
        np.testing.assert_allclose(
            carer[i],
            carer_elements * CARER_ELEMENT[year] * 12,
            atol=0.01,
            err_msg=str(unit),
        )
        assert (lcwra[i] > 0) == (lcwra_elements == 1), unit
        if year == 2025:
            np.testing.assert_allclose(
                lcwra[i],
                lcwra_elements * LCWRA_ELEMENT_2025 * 12,
                atol=0.01,
                err_msg=str(unit),
            )
        # Reg. 22(1)(b)(i): a work allowance needs a claimant with limited
        # capability or responsibility for a child or qualifying young person.
        claimant_limited = any(
            c["uc_limited_capability_for_WRA"] for c in unit["claimants"]
        )
        assert work_allowance[i] == (claimant_limited or responsible[i] > 0), unit


@PROPERTY_SETTINGS
@given(units=populations, year=st.sampled_from(YEARS))
def test_carers_of_the_same_person_have_at_most_one_carer_element(units, year):
    sim = Simulation(situation=situation(units, year, same_person=True))
    carer = np.asarray(sim.calculate("uc_carer_element", year))
    for i, unit in enumerate(units):
        _, carer_elements = published_elements(*[code(c) for c in unit["claimants"]])
        np.testing.assert_allclose(
            carer[i],
            min(carer_elements, 1) * CARER_ELEMENT[year] * 12,
            atol=0.01,
            err_msg=str(unit),
        )


@PROPERTY_SETTINGS
@given(units=populations, year=st.sampled_from(YEARS))
def test_both_claimants_limited_capability_gives_one_lcwra_element(units, year):
    one = Simulation(
        situation=situation(
            units,
            year,
            claimant_overrides=dict(uc_limited_capability_for_WRA=False),
            first_claimant_overrides=dict(uc_limited_capability_for_WRA=True),
        )
    )
    both = Simulation(
        situation=situation(
            units, year, claimant_overrides=dict(uc_limited_capability_for_WRA=True)
        )
    )
    amount_one = np.asarray(one.calculate("uc_LCWRA_element", year))
    amount_both = np.asarray(both.calculate("uc_LCWRA_element", year))
    assert np.all(amount_one > 0), units
    np.testing.assert_allclose(amount_both, amount_one, atol=0.01, err_msg=str(units))


@PROPERTY_SETTINGS
@given(units=populations, year=st.sampled_from(YEARS))
def test_an_award_has_at_most_one_element_for_each_claimant(units, year):
    sim = Simulation(situation=situation(units, year))
    lcwra = np.asarray(sim.calculate("uc_LCWRA_element", year)) > 0
    carer_elements = np.rint(
        np.asarray(sim.calculate("uc_carer_element", year)) / (CARER_ELEMENT[year] * 12)
    )
    claimants = np.array([len(unit["claimants"]) for unit in units])
    assert np.all(carer_elements <= claimants), units
    assert np.all(lcwra.astype(int) + carer_elements <= claimants), units
    if year == 2025:
        amounts = np.asarray(sim.calculate("uc_LCWRA_element", year))
        one_element = LCWRA_ELEMENT_2025 * 12
        assert np.all(
            np.isclose(amounts, 0, atol=0.01)
            | np.isclose(amounts, one_element, atol=0.01)
        ), units


@PROPERTY_SETTINGS
@given(units=populations, year=st.sampled_from(YEARS))
def test_a_claimants_limited_capability_never_lowers_the_elements(units, year):
    variables = ["uc_LCWRA_element", "uc_carer_element", "uc_work_allowance"]
    as_given = benunit_values(
        Simulation(situation=situation(units, year)), year, variables
    )
    all_limited = benunit_values(
        Simulation(
            situation=situation(
                units, year, claimant_overrides=dict(uc_limited_capability_for_WRA=True)
            )
        ),
        year,
        variables,
    )
    total_given = as_given["uc_LCWRA_element"] + as_given["uc_carer_element"]
    total_limited = all_limited["uc_LCWRA_element"] + all_limited["uc_carer_element"]
    assert np.all(total_limited >= total_given - 0.01), units
    assert np.all(
        all_limited["uc_work_allowance"] >= as_given["uc_work_allowance"] - 0.01
    ), units


@PROPERTY_SETTINGS
@given(units=populations, year=st.sampled_from(YEARS))
def test_member_order_does_not_change_the_elements(units, year):
    # The 2026 LCWRA amount is drawn per benefit unit by the rebalancing
    # modifier, and does not depend on the order of the unit's members.
    forward = Simulation(situation=situation(units, year))
    backward = Simulation(situation=situation(units, year, reverse=True))
    assert_same(
        benunit_values(forward, year, ELEMENT_VARIABLES),
        benunit_values(backward, year, ELEMENT_VARIABLES),
        units,
    )


def test_published_table_covers_all_sixteen_combinations():
    # Every combination of two claimants' carer and LCWRA status resolves,
    # and swapping the claimants gives the same award.
    codes = ["", "C", "L", "CL"]
    for first in codes:
        for second in codes:
            assert published_elements(first, second) == published_elements(
                second, first
            )
    assert len(F6037) == 12


def claimant_with(status, age):
    return dict(
        age=age,
        care_hours=35.0 if "C" in status else 0.0,
        uc_limited_capability_for_WRA="L" in status,
    )


def test_model_matches_the_published_table_for_every_combination():
    # A deterministic run of every single and joint combination, for carers
    # of different people and of the same person, in 2025-26.
    year = 2025
    codes = ["", "C", "L", "CL"]
    combinations = [(first,) for first in codes] + [
        (first, second) for first in codes for second in codes
    ]
    for same_person in [False, True]:
        units = [
            dict(
                claimants=[
                    claimant_with(status, 45 - 5 * j) for j, status in enumerate(c)
                ],
                dependants=[],
                tenure="OWNED_OUTRIGHT",
                rent=0.0,
                region="NORTH_EAST",
            )
            for c in combinations
        ]
        sim = Simulation(situation=situation(units, year, same_person=same_person))
        lcwra = np.asarray(sim.calculate("uc_LCWRA_element", year))
        carer = np.asarray(sim.calculate("uc_carer_element", year))
        for i, c in enumerate(combinations):
            lcwra_elements, carer_elements = published_elements(*c)
            if same_person:
                carer_elements = min(carer_elements, 1)
            context = str((c, same_person))
            np.testing.assert_allclose(
                lcwra[i],
                lcwra_elements * LCWRA_ELEMENT_2025 * 12,
                atol=0.01,
                err_msg=context,
            )
            np.testing.assert_allclose(
                carer[i],
                carer_elements * CARER_ELEMENT[year] * 12,
                atol=0.01,
                err_msg=context,
            )
