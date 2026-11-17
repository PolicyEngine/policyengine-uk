"""Property-based test of a commercial lodger's children and the household
head's Universal Credit extended benefit unit.

Under UC Regs 2013 Sch 4 para 9(2)(g), DWP leaves out of the renter's
non-dependants "a child or qualifying young person for whom no-one in the
renter's extended benefit unit is responsible". DWP also leaves out a person
liable to pay on a commercial basis for their occupation (para 9(2)(d)), and
the model treats that payer's partner as liable too. So when a claimant or
partner of a benefit unit pays the household head as a boarder or lodger,
nobody in the head's extended benefit unit has responsibility for the unit's
children and qualifying young people.

Invariant, for any generated household whose head claims Universal Credit,
with one or two commercial lodger units (each with possibly a partner, an
adult who pays nothing and a child of their own), possibly a non-paying
family with a child, and the head's own partner and children:

1. Adding a child under 16, or a qualifying young person aged 16 to 18 in
   non-advanced education, to the first lodger unit leaves the head's
   Universal Credit bedrooms (LHA_allowed_bedrooms), housing element
   (uc_housing_costs_element) and non-dependant deductions
   (uc_non_dep_deductions) unchanged, and the model never counts the added
   person as the head's Universal Credit non-dependant.

The generator keeps everyone in the lodger units under State Pension age, so
no lodger family receives Pension Credit.
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
HOST_OUTPUTS = [
    "LHA_allowed_bedrooms",
    "uc_housing_costs_element",
    "uc_non_dep_deductions",
]
money = st.floats(0, 30_000, allow_nan=False, allow_infinity=False)


@st.composite
def young_person(draw, min_age=0, max_age=18):
    """A child under 16, or a qualifying young person aged 16 to 18 in
    non-advanced education."""
    age = draw(st.integers(min_age, max_age))
    person = dict(age=age, is_claimant_or_partner=False)
    if age >= 16:
        person["current_education"] = "UPPER_SECONDARY"
    return person


@st.composite
def adult(draw, claimant_or_partner, pays=False):
    person = dict(
        age=draw(st.integers(21, 60)),
        is_claimant_or_partner=claimant_or_partner,
        employment_income=draw(money),
    )
    if pays:
        kind = draw(st.sampled_from(["rent_paid_as_boarder", "rent_paid_as_lodger"]))
        person[kind] = draw(st.floats(1_000, 12_000))
    return person


@st.composite
def lodger_unit(draw):
    """A benefit unit whose claimant pays the household head, with possibly a
    partner (paying or not), an adult who is neither claimant nor partner and
    pays nothing, and a child of their own."""
    unit = [draw(adult(True, pays=True))]
    if draw(st.booleans()):
        unit.append(draw(adult(True, pays=draw(st.booleans()))))
    if draw(st.booleans()):
        unit.append(draw(adult(False)))
    if draw(st.booleans()):
        unit.append(draw(young_person()))
    return unit


@st.composite
def households(draw):
    head_age = draw(st.one_of(st.integers(18, 34), st.integers(35, 60)))
    head_unit = [dict(age=head_age, employment_income=draw(money))]
    if draw(st.booleans()):
        head_unit.append(dict(age=draw(st.integers(18, 60)), employment_income=0.0))
    head_unit += [draw(young_person()) for _ in range(draw(st.integers(0, 2)))]
    others = [draw(lodger_unit()) for _ in range(draw(st.integers(1, 2)))]
    if draw(st.booleans()):
        family = [draw(adult(True))]
        if draw(st.booleans()):
            family.append(draw(young_person()))
        others.append(family)
    return dict(
        head_unit=head_unit,
        others=others,
        added=draw(st.one_of(young_person(0, 15), young_person(16, 18))),
        region=draw(st.sampled_from(["LONDON", "NORTH_WEST", "SCOTLAND", "WALES"])),
        tenure=draw(st.sampled_from(["RENT_PRIVATELY", "RENT_FROM_COUNCIL"])),
        rent=draw(st.floats(6_000, 30_000)),
    )


def situation(h, year, with_added):
    people, benunits, names = {}, {}, []

    def add(name, attrs, head=False):
        person = {
            "age": {year: attrs["age"]},
            "is_household_head": {year: head},
            "is_claimant_or_partner": {year: attrs.get("is_claimant_or_partner", True)},
        }
        for key, value in attrs.items():
            if key not in ("age", "is_claimant_or_partner"):
                person[key] = {year: value}
        people[name] = person
        names.append(name)
        return name

    head_members = []
    for i, attrs in enumerate(h["head_unit"]):
        head_members.append(add(f"head_{i}", attrs, head=i == 0))
    benunits["head_unit"] = {
        "members": head_members,
        "would_claim_uc": {year: True},
    }
    for j, unit in enumerate(h["others"]):
        members = [add(f"other_{j}_{k}", attrs) for k, attrs in enumerate(unit)]
        if with_added and j == 0:
            members.append(add("added", h["added"]))
        benunits[f"other_{j}"] = {"members": members}
    return {
        "people": people,
        "benunits": benunits,
        "households": {
            "household": {
                "members": names,
                "rent": {year: h["rent"]},
                "tenure_type": {year: h["tenure"]},
                "region": {year: h["region"]},
            }
        },
    }


def calculate(h, year, with_added):
    sim = Simulation(situation=situation(h, year, with_added))
    values = {v: np.asarray(sim.calculate(v, year), dtype=float) for v in HOST_OUTPUTS}
    values["is_uc_non_dependant_of_household_head"] = np.asarray(
        sim.calculate("is_uc_non_dependant_of_household_head", year)
    )
    return values


@PROPERTY_SETTINGS
@given(households(), st.sampled_from(YEARS))
def test_a_commercial_lodgers_child_changes_nothing_for_the_heads_universal_credit(
    h, year
):
    without = calculate(h, year, with_added=False)
    with_child = calculate(h, year, with_added=True)
    # The head's benefit unit comes first.
    for v in HOST_OUTPUTS:
        np.testing.assert_allclose(
            with_child[v][0], without[v][0], atol=0.01, err_msg=v
        )
    # The added person comes after the members of the first lodger unit.
    added = len(h["head_unit"]) + len(h["others"][0])
    assert not with_child["is_uc_non_dependant_of_household_head"][added]
