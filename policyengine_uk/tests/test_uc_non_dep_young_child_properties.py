"""Property-based tests for the Universal Credit housing cost contribution
exemption for a non-dependant responsible for a child under 5 (UC Regs 2013
Sch 4 para 16(2)(i)).

Responsibility follows UC reg 4 with benefit-unit membership standing for
"normally lives with": a family's claimant and partner are responsible for
its children, except a child looked after by a local authority (reg 4(6)(a)).
Invariants, for any generated population of households:

1. Oracle: each person's contribution and each family's total equal an
   independent calculation from the generated structure: who is a
   non-dependant (a member of a family not liable for rent, or a member of
   the renter's own family who is neither claimant, partner nor a qualifying
   young person), aged 21 or over, and whether any modelled exemption applies.
2. Monotonicity: the exemption only removes contributions. No person's or
   family's contribution is higher than with the exemption switched off
   (an age limit of 0), and raising the age limit never raises one.
3. Locality: the only people whose contribution the exemption changes are
   the claimant or partner of a family with a child under the limit whom the
   family is responsible for, and each of them goes from a full contribution
   to none.
4. No-op: in a population with no child under 5, the contributions equal
   those with the exemption switched off.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

# Situation inputs without a period key are set for 2025, so the properties
# are checked in 2025, when the contribution was £93.02 a month.
YEAR = 2025
UC_CONTRIBUTION = 93.02 * 12
AGE_LIMIT = (
    "gov.dwp.universal_credit.elements.housing.non_dep_deduction.young_child_age_limit"
)
PROPERTY_SETTINGS = settings(
    max_examples=15,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)


@st.composite
def child(draw):
    return dict(
        age=draw(st.integers(0, 15)),
        looked_after=draw(st.sampled_from([False, False, False, True])),
    )


@st.composite
def family(draw, role):
    # Adults stay below State Pension Credit age, so the Pension Credit limb
    # (para 16(2)(b)) never applies and the oracle needs no Pension Credit.
    adult_age = st.integers(40, 64) if role == "head" else st.integers(18, 39)
    return dict(
        role=role,
        adults=[
            dict(age=age, pip=draw(st.sampled_from([False, False, True])))
            for age in draw(st.lists(adult_age, min_size=1, max_size=2))
        ],
        # Members aged 16 or over who are neither claimant, partner nor a
        # qualifying young person: non-dependants within the family.
        extras=draw(st.lists(st.integers(16, 39), min_size=0, max_size=1)),
        children=draw(st.lists(child(), min_size=0, max_size=2)),
    )


@st.composite
def household(draw):
    head = draw(family("head"))
    others = [
        draw(family(draw(st.sampled_from(["non_dependant", "sharer"]))))
        for _ in range(draw(st.integers(0, 2)))
    ]
    return dict(
        families=[head] + others,
        rent=draw(st.floats(3_000, 20_000, allow_nan=False)),
        tenure=draw(st.sampled_from(["RENT_FROM_COUNCIL", "RENT_PRIVATELY"])),
    )


population = st.lists(household(), min_size=1, max_size=4)


def build(population, minimum_child_age=0):
    """One situation for the whole population, and a record per person and
    per family for the oracle. Children are aged at least minimum_child_age."""
    people, benunits, homes = {}, {}, {}
    person_rows, family_rows = [], []
    for h, house in enumerate(population):
        members = []
        for f, fam in enumerate(house["families"]):
            name = f"h{h}_f{f}"
            ids = []
            family_index = len(family_rows)
            children = [
                dict(c, age=max(c["age"], minimum_child_age)) for c in fam["children"]
            ]
            for i, adult in enumerate(fam["adults"]):
                pid = f"{name}_adult_{i}"
                people[pid] = {
                    "age": adult["age"],
                    "is_claimant_or_partner": True,
                    "is_household_head": f == 0 and i == 0,
                    "pip_dl": 3_000.0 if adult["pip"] else 0.0,
                }
                ids.append(pid)
                person_rows.append(
                    dict(family=family_index, kind="adult", age=adult["age"])
                )
            for i, age in enumerate(fam["extras"]):
                pid = f"{name}_extra_{i}"
                people[pid] = {
                    "age": age,
                    "is_claimant_or_partner": False,
                    "is_household_head": False,
                    "is_qualifying_young_person_for_universal_credit": False,
                }
                ids.append(pid)
                person_rows.append(dict(family=family_index, kind="extra", age=age))
            for i, c in enumerate(children):
                pid = f"{name}_child_{i}"
                people[pid] = {
                    "age": c["age"],
                    "is_claimant_or_partner": False,
                    "is_household_head": False,
                    "is_looked_after_by_local_authority": c["looked_after"],
                }
                ids.append(pid)
                person_rows.append(
                    dict(family=family_index, kind="child", age=c["age"])
                )
            benunit = {"members": ids}
            if fam["role"] == "sharer":
                benunit["liable_for_share_of_household_rent"] = True
            benunits[name] = benunit
            members.extend(ids)
            family_rows.append(
                dict(
                    household=h,
                    role=fam["role"],
                    renter_pip=any(a["pip"] for a in fam["adults"]),
                    adult_pip=[a["pip"] for a in fam["adults"]],
                    child_ages=[c["age"] for c in children if not c["looked_after"]],
                )
            )
        homes[f"h{h}"] = {
            "members": members,
            "rent": house["rent"],
            "tenure_type": house["tenure"],
            "brma": "MAIDSTONE",
        }
    situation = {"people": people, "benunits": benunits, "households": homes}
    return situation, person_rows, family_rows


def calc(sim, variable):
    return np.asarray(sim.calculate(variable, YEAR), dtype=float)


def simulate(situation, age_limit=None):
    reform = None
    if age_limit is not None:
        reform = {AGE_LIMIT: {"2013-01-01.2100-12-31": age_limit}}
    return Simulation(situation=situation, reform=reform)


def responsible_for_young_child(row, family_rows, age_limit):
    ages = family_rows[row["family"]]["child_ages"]
    return row["kind"] == "adult" and any(age < age_limit for age in ages)


def oracle(person_rows, family_rows, age_limit=5):
    """Each person's contribution and each family's total."""
    individual = np.zeros(len(person_rows))
    totals = np.zeros(len(family_rows))
    adult_index = {}
    for p, row in enumerate(person_rows):
        fam = family_rows[row["family"]]
        if row["kind"] == "adult":
            i = adult_index.get(row["family"], 0)
            adult_index[row["family"]] = i + 1
            pip = fam["adult_pip"][i]
        else:
            pip = False
        # Sch 4 para 9: members of a family not liable for rent, and members
        # of any family who are neither claimant, partner nor a qualifying
        # young person (children under 16 are never non-dependants of
        # their own family).
        other_family = fam["role"] == "non_dependant"
        own_family = row["kind"] == "extra"
        if not (other_family or own_family):
            continue
        exempt = (
            row["age"] < 21
            or pip
            or responsible_for_young_child(row, family_rows, age_limit)
        )
        if not exempt:
            individual[p] = UC_CONTRIBUTION
        # The head's family bears other families' non-dependants; each family
        # bears its own (para 9(2)(f)); none if the bearer's renter is exempt
        # under para 15.
        head = [
            i
            for i, f in enumerate(family_rows)
            if f["household"] == fam["household"] and f["role"] == "head"
        ][0]
        bearer = head if other_family else row["family"]
        if not family_rows[bearer]["renter_pip"]:
            totals[bearer] += individual[p]
    return individual, totals


@PROPERTY_SETTINGS
@given(population)
def test_contributions_match_the_oracle(population):
    situation, person_rows, family_rows = build(population)
    sim = simulate(situation)
    individual, totals = oracle(person_rows, family_rows)
    # 1. Oracle.
    assert np.allclose(
        calc(sim, "uc_individual_non_dep_deduction"), individual, atol=0.01
    )
    assert np.allclose(calc(sim, "uc_non_dep_deductions"), totals, atol=0.01)
    expected_responsible = np.array(
        [responsible_for_young_child(row, family_rows, 5) for row in person_rows]
    )
    assert np.array_equal(
        calc(sim, "is_responsible_for_child_under_5_for_universal_credit") > 0,
        expected_responsible,
    )


@PROPERTY_SETTINGS
@given(population)
def test_the_exemption_only_removes_contributions(population):
    situation, person_rows, family_rows = build(population)
    with_exemption = simulate(situation)
    without = simulate(situation, age_limit=0)
    wider = simulate(situation, age_limit=16)
    for variable in ["uc_individual_non_dep_deduction", "uc_non_dep_deductions"]:
        on, off, wide = (calc(s, variable) for s in (with_exemption, without, wider))
        # 2. Monotonicity in the exemption and in its age limit.
        assert np.all(on <= off + 0.01), variable
        assert np.all(wide <= on + 0.01), variable
    # 3. Locality: only a responsible claimant or partner changes, and from a
    # full contribution to none.
    on = calc(with_exemption, "uc_individual_non_dep_deduction")
    off = calc(without, "uc_individual_non_dep_deduction")
    changed = ~np.isclose(on, off, atol=0.01)
    responsible = (
        calc(with_exemption, "is_responsible_for_child_under_5_for_universal_credit")
        > 0
    )
    assert np.all(responsible[changed])
    assert np.allclose(off[changed], UC_CONTRIBUTION, atol=0.01)
    assert np.allclose(on[changed], 0, atol=0.01)
    # Without the exemption the oracle with an age limit of 0 holds too.
    individual, totals = oracle(person_rows, family_rows, age_limit=0)
    assert np.allclose(off, individual, atol=0.01)
    assert np.allclose(calc(without, "uc_non_dep_deductions"), totals, atol=0.01)


@PROPERTY_SETTINGS
@given(population)
def test_no_op_without_a_child_under_5(population):
    situation, *_ = build(population, minimum_child_age=5)
    with_exemption = simulate(situation)
    without = simulate(situation, age_limit=0)
    # 4. No-op.
    assert not np.any(
        calc(with_exemption, "is_responsible_for_child_under_5_for_universal_credit")
    )
    for variable in ["uc_individual_non_dep_deduction", "uc_non_dep_deductions"]:
        assert np.allclose(
            calc(with_exemption, variable), calc(without, variable), atol=0.01
        ), variable
