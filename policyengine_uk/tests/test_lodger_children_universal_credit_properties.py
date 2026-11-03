"""Property-based tests for a boarder's or lodger's children under Universal
Credit's size criteria and housing cost contributions.

UC Regs 2013 Sch 4 para 9(2)(g) leaves out of the renter's non-dependants "a
child or qualifying young person for whom no-one in the renter's extended
benefit unit is responsible". A boarder or lodger who pays the household head
on a commercial basis is not in the renter's extended benefit unit (para
9(2)(d)), and the model makes the claimant and partner of a benefit unit
responsible for its children and qualifying young people. So a child or
qualifying young person in a paying family is not the renter's non-dependant.

Invariant, for any generated household: adding a child or qualifying young
person to a boarder's or lodger's benefit unit, whose claimant pays the
household head, never changes the household head's Universal Credit bedrooms
(LHA_allowed_bedrooms), housing element (uc_housing_costs_element) or
non-dependant deductions (uc_non_dep_deductions).

The generator gives the household head's family one or two working-age
claimants or partners, who claim Universal Credit, and possibly children of
their own. The paying family has a claimant who pays as a boarder or lodger,
possibly a partner, possibly an adult who pays nothing and is neither
claimant nor partner, and possibly a child or qualifying young person
already. A third family, possibly present, pays nothing, so its members are
the household head's non-dependants, and it may hold a child or qualifying
young person of its own. The person added is a child under 16 or a
qualifying young person aged 16 to 19 in non-advanced education.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

PROPERTY_SETTINGS = settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
YEARS = [2025, 2026]
KINDS = ("rent_paid_as_boarder", "rent_paid_as_lodger")
HOST_OUTPUTS = [
    "LHA_allowed_bedrooms",
    "uc_housing_costs_element",
    "uc_non_dep_deductions",
]
NON_ADVANCED = ["LOWER_SECONDARY", "UPPER_SECONDARY", "POST_SECONDARY"]


@st.composite
def adult(draw, claimant_or_partner, ages=(21, 60)):
    return {
        "age": draw(st.integers(*ages)),
        "is_claimant_or_partner": claimant_or_partner,
        "employment_income": draw(st.one_of(st.just(0.0), st.floats(0, 30_000))),
    }


@st.composite
def child_or_qualifying_young_person(draw):
    """A child under 16, or a qualifying young person aged 16 to 19 in
    non-advanced education who meets the entry and terminal date
    conditions."""
    person = {
        "age": draw(st.integers(0, 19)),
        "is_claimant_or_partner": False,
        "is_male": draw(st.booleans()),
        "employment_income": 0.0,
    }
    if person["age"] >= 16:
        person["current_education"] = draw(st.sampled_from(NON_ADVANCED))
        person["age_started_or_accepted_current_education_or_training"] = 16
        person["is_before_universal_credit_qualifying_young_person_terminal_date"] = (
            True
        )
    return person


@st.composite
def paying_unit(draw):
    """A boarder's or lodger's benefit unit whose claimant pays the household
    head."""
    payer = draw(adult(True))
    payer[draw(st.sampled_from(KINDS))] = draw(st.floats(500, 12_000))
    unit = [payer]
    if draw(st.booleans()):
        partner = draw(adult(True))
        if draw(st.booleans()):
            partner[draw(st.sampled_from(KINDS))] = draw(st.floats(500, 12_000))
        unit.append(partner)
    if draw(st.booleans()):
        # An adult who pays nothing and is neither claimant nor partner, such
        # as an adult son: a non-dependant of the household head.
        unit.append(draw(adult(False, ages=(20, 40))))
    if draw(st.booleans()):
        unit.append(draw(child_or_qualifying_young_person()))
    return unit


@st.composite
def non_paying_unit(draw):
    """A family that pays nothing: the household head's non-dependants."""
    unit = [draw(adult(True))]
    if draw(st.booleans()):
        unit.append(draw(child_or_qualifying_young_person()))
    return unit


@st.composite
def households(draw):
    head_unit = [
        draw(adult(True, ages=(25, 60))) for _ in range(draw(st.integers(1, 2)))
    ]
    for _ in range(draw(st.integers(0, 2))):
        head_unit.append(dict(draw(child_or_qualifying_young_person())))
    return dict(
        head_unit=head_unit,
        paying_unit=draw(paying_unit()),
        non_paying_unit=draw(st.one_of(st.none(), non_paying_unit())),
        tenure=draw(st.sampled_from(["RENT_PRIVATELY", "RENT_FROM_COUNCIL"])),
        rent=draw(st.floats(4_000, 30_000)),
        region=draw(st.sampled_from(["LONDON", "NORTH_WEST", "WALES", "SCOTLAND"])),
        added=draw(child_or_qualifying_young_person()),
    )


def situation(h, year, add):
    people, benunits, names = {}, {}, []

    def place(unit_name, unit, prefix, head=False):
        members = []
        for i, attrs in enumerate(unit):
            name = f"{prefix}_{i}"
            people[name] = {key: {year: value} for key, value in attrs.items()}
            people[name]["is_household_head"] = {year: head and i == 0}
            members.append(name)
        benunits[unit_name] = {"members": members}
        names.extend(members)

    place("head_unit", h["head_unit"], "head", head=True)
    benunits["head_unit"]["would_claim_uc"] = {year: True}
    paying = list(h["paying_unit"]) + ([h["added"]] if add else [])
    place("paying_unit", paying, "payer")
    if h["non_paying_unit"] is not None:
        place("non_paying_unit", h["non_paying_unit"], "other")
    return {
        "people": people,
        "benunits": benunits,
        "households": {
            "household": {
                "members": names,
                "tenure_type": {year: h["tenure"]},
                "region": {year: h["region"]},
                "rent": {year: h["rent"]},
            }
        },
    }


@PROPERTY_SETTINGS
@given(households(), st.sampled_from(YEARS))
def test_a_lodgers_child_changes_nothing_in_the_hosts_universal_credit(h, year):
    without = Simulation(situation=situation(h, year, add=False))
    with_child = Simulation(situation=situation(h, year, add=True))
    # The added person is the last member of the paying family.
    added = len(h["head_unit"]) + len(h["paying_unit"])
    assert with_child.calculate(
        "is_child_or_qualifying_young_person_for_universal_credit", year
    )[added]
    for variable in HOST_OUTPUTS:
        np.testing.assert_allclose(
            with_child.calculate(variable, year)[0],
            without.calculate(variable, year)[0],
            atol=0.01,
            err_msg=variable,
        )
