"""Property-based tests for joint tenants who form a single household with
the household head's family (joint_tenant_in_household_head_household) in the
Housing Benefit size criteria (HB Regs 2006 reg 13D(3), (3A), (12); LHA
Guidance Manual para 2.100).

Invariants, for any generated population of households (a head's family,
up to three families sharing the rent, each in the head's household or not,
non-dependant families with any residence value, a lodger, children, foster
children and people who need overnight care):

1. Reference: every family's Housing Benefit bedrooms and additional
   bedrooms equal a count made by the test itself. Members of a single
   household (the head's family and every sharer in its household, once
   there is one) count each other's families and every occupier counted for
   any of them; anyone else counts as before (boarders and lodgers for the
   head, non-dependants for the joint occupiers they reside with). Children's
   rooms come from a brute-force pairing.
2. No-op: the input set to false everywhere gives the same results as the
   default; set to true on a family that does not share the rent (the
   head's, a non-dependant's or a lodger's), it changes nothing.
3. Symmetry: every family in a single household has the same size criteria
   before additional bedrooms (13D(3)), and the same additional bedrooms
   where no foster child is placed in the household (13D(3A)(b) and
   (a)(iv) are the claimant's own).
4. Monotonicity: forming a single household never lowers any family's
   bedrooms, and changes nothing for a family outside it.
5. Exclusive use (13D(2)(b)): where every sharer is in the head's household,
   no joint occupier lacks exclusive use because of the rent sharing; where
   one is not, every joint occupier liable for rent does.
6. Invariance: Universal Credit, the non-dependant deductions, the
   young individual and the Housing Benefit non-dependant test never depend
   on the input (a joint tenant is never a non-dependant, reg 3(2)(d)).
"""

from functools import lru_cache

import numpy as np
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

YEAR = 2026
PROPERTY_SETTINGS = settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
RESIDENCE = [
    "EVERY_JOINT_OCCUPIER",
    "HOUSEHOLD_HEAD_FAMILY",
    "OTHER_JOINT_OCCUPIERS",
]
OVERNIGHT = st.sampled_from([False, False, False, True])
MONEY_TOLERANCE = 0.01

# (age, is_male, is_foster_child, needs overnight care)
child = st.tuples(
    st.integers(0, 15),
    st.booleans(),
    st.sampled_from([False, False, False, True]),
    OVERNIGHT,
)


@st.composite
def family(draw):
    return dict(
        adults=draw(
            st.lists(
                st.tuples(st.integers(18, 85), st.booleans(), OVERNIGHT),
                min_size=1,
                max_size=2,
            )
        ),
        children=draw(st.lists(child, min_size=0, max_size=2)),
    )


@st.composite
def households(draw):
    return dict(
        head=draw(family()),
        sharers=draw(
            st.lists(st.tuples(family(), st.booleans()), min_size=0, max_size=3)
        ),
        non_dependants=draw(
            st.lists(
                st.tuples(family(), st.sampled_from(RESIDENCE)),
                min_size=0,
                max_size=2,
            )
        ),
        lodger=draw(st.booleans()),
        rent=draw(st.floats(2_000, 30_000, allow_nan=False)),
    )


population = st.lists(households(), min_size=1, max_size=4)


def build(population, flags="as_drawn"):
    """One simulation for the whole population, with each family's role and
    whether it sits in a single household.

    ``flags`` is "as_drawn" (each sharer's drawn value), "unset" (input
    absent), "false" (false everywhere) or "inert" (drawn values on sharers,
    and true on every family that does not share the rent)."""
    people, benunits, homes, roles, single = {}, {}, {}, [], []
    for h, house in enumerate(population):
        members = []
        any_joins = any(joins for _, joins in house["sharers"])

        def add_family(name, fam, role, joins, extra):
            ids = []
            for i, (age, male, overnight) in enumerate(fam["adults"]):
                pid = f"{name}_adult_{i}"
                people[pid] = {
                    "age": {YEAR: age},
                    "is_male": {YEAR: male},
                    "is_claimant_or_partner": {YEAR: True},
                    "is_household_head": {YEAR: False},
                    "meets_lha_overnight_care_condition": {YEAR: overnight},
                }
                ids.append(pid)
            for i, (age, male, foster, overnight) in enumerate(fam["children"]):
                pid = f"{name}_child_{i}"
                people[pid] = {
                    "age": {YEAR: age},
                    "is_male": {YEAR: male},
                    "is_claimant_or_partner": {YEAR: False},
                    "is_household_head": {YEAR: False},
                    "is_looked_after_by_local_authority": {YEAR: foster},
                    "meets_lha_overnight_care_condition": {YEAR: overnight},
                }
                ids.append(pid)
            flag = {
                "as_drawn": joins if role == "sharer" else None,
                "unset": None,
                "false": False,
                "inert": joins if role == "sharer" else True,
            }[flags]
            if flag is not None:
                extra = {
                    **extra,
                    "joint_tenant_in_household_head_household": {YEAR: flag},
                }
            benunits[name] = {"members": ids, **extra}
            members.extend(ids)
            roles.append(role)
            in_single = flags in ("as_drawn", "inert") and (
                (role == "head" and any_joins) or (role == "sharer" and joins)
            )
            single.append(in_single)
            return ids

        head_ids = add_family(f"h{h}_head", house["head"], "head", False, {})
        people[head_ids[0]]["is_household_head"] = {YEAR: True}
        for f, (sharer, joins) in enumerate(house["sharers"]):
            add_family(
                f"h{h}_s{f}",
                sharer,
                "sharer",
                joins,
                {"liable_for_share_of_household_rent": {YEAR: True}},
            )
        for f, (non_dep, residence) in enumerate(house["non_dependants"]):
            add_family(
                f"h{h}_n{f}",
                non_dep,
                "non_dependant",
                False,
                {"non_dependant_normally_resides_with": {YEAR: residence}},
            )
        if house["lodger"]:
            ids = add_family(
                f"h{h}_l",
                dict(adults=[(40, True, False)], children=[]),
                "lodger",
                False,
                {},
            )
            people[ids[0]]["rent_paid_as_lodger"] = {YEAR: 4_000}
        homes[f"h{h}"] = {
            "members": members,
            "rent": {YEAR: house["rent"]},
            "tenure_type": {YEAR: "RENT_PRIVATELY"},
            "brma": {YEAR: "MAIDSTONE"},
        }
    situation = {"people": people, "benunits": benunits, "households": homes}
    return Simulation(situation=situation), np.array(roles), np.array(single)


def calc(sim, variable):
    return np.asarray(sim.calculate(variable, YEAR), dtype=float)


def assert_same(left, right, variable):
    """The variable's values agree in both simulations: money to the penny,
    and enums exactly."""
    a = np.asarray(left.calculate(variable, YEAR))
    b = np.asarray(right.calculate(variable, YEAR))
    if a.dtype.kind in "biuf":
        np.testing.assert_allclose(a, b, atol=MONEY_TOLERANCE, err_msg=variable)
    else:
        np.testing.assert_array_equal(a, b, err_msg=variable)


def benunit_household(sim):
    person_benunit = sim.populations["benunit"].members_entity_id
    person_household = sim.populations["household"].members_entity_id
    out = np.zeros(sim.populations["benunit"].count, dtype=int)
    out[person_benunit] = person_household
    return out


@lru_cache(maxsize=None)
def fewest_rooms(children):
    """Brute force: the fewest rooms holding ``children`` (a sorted tuple of
    (age, is_male)) two to a room, where two may share if they are of the
    same sex or both under 10."""
    if not children:
        return 0
    first, rest = children[0], children[1:]
    best = 1 + fewest_rooms(rest)
    for i, other in enumerate(rest):
        if first[1] == other[1] or (first[0] < 10 and other[0] < 10):
            best = min(best, 1 + fewest_rooms(rest[:i] + rest[i + 1 :]))
    return best


def reference_bedrooms(house, flags="as_drawn"):
    """The size criteria (bedrooms, additional bedrooms) of each family in
    the household, in build order, counted independently of the model."""
    sharers = house["sharers"]
    joins = [j and flags in ("as_drawn", "inert") for _, j in sharers]
    families = [("head", house["head"], None)]
    families += [("sharer", fam, None) for fam, _ in sharers]
    families += [("non_dependant", fam, r) for fam, r in house["non_dependants"]]
    if house["lodger"]:
        families.append(("lodger", dict(adults=[(40, True, False)], children=[]), None))
    single = [False] * len(families)
    if any(joins):
        single[0] = True
        for s, j in enumerate(joins):
            single[1 + s] = j
    has_sharer = bool(sharers)

    def residence_families(residence):
        """Indices of the joint occupiers a non-dependant resides with."""
        head = {0}
        sharer_indices = set(range(1, 1 + len(sharers)))
        if residence == "EVERY_JOINT_OCCUPIER":
            return head | sharer_indices
        if residence == "HOUSEHOLD_HEAD_FAMILY":
            return head
        return sharer_indices if has_sharer else head

    def counted_for(index):
        """Indices of the other families whose members occupy family
        ``index``'s dwelling in its size criteria."""
        role = families[index][0]
        if role not in ("head", "sharer"):
            return set()
        group = (
            {i for i in range(len(families)) if single[i]} if single[index] else {index}
        )
        others = {i for i in group if i != index}
        for i, (other_role, _, residence) in enumerate(families):
            if other_role == "lodger" and 0 in group:
                others.add(i)
            if other_role == "non_dependant" and residence_families(residence) & group:
                others.add(i)
        return others

    out = []
    for index, (role, fam, _) in enumerate(families):
        # The claimant or couple.
        rooms = 1
        children = [(a, m) for a, m, foster, _ in fam["children"] if not foster]
        # 13D(3A)(a)(i), (ii), (iv): the family's own members, including a
        # foster child placed with it.
        overnight = any(o for _, _, o in fam["adults"]) or any(
            o for *_, o in fam["children"]
        )
        carer = any(foster for _, _, foster, _ in fam["children"])
        for i in counted_for(index):
            other = families[i][1]
            # 13D(3)(a), (b): a couple, or a single adult, has one bedroom.
            rooms += 1
            children += [(a, m) for a, m, foster, _ in other["children"] if not foster]
            # (a)(iii): another occupier, not a child placed with them.
            overnight |= any(o for _, _, o in other["adults"]) or any(
                o for _, _, foster, o in other["children"] if not foster
            )
        rooms += fewest_rooms(tuple(sorted(children)))
        additional = int(overnight) + int(carer)
        out.append((rooms + additional, additional))
    return out


@PROPERTY_SETTINGS
@given(population)
def test_bedrooms_match_a_reference_count(population):
    sim, roles, _ = build(population)
    bedrooms = calc(sim, "housing_benefit_LHA_allowed_bedrooms")
    additional = calc(sim, "housing_benefit_LHA_additional_bedrooms")
    expected = [pair for house in population for pair in reference_bedrooms(house)]
    np.testing.assert_array_equal(bedrooms, [b for b, _ in expected])
    np.testing.assert_array_equal(additional, [a for _, a in expected])


@PROPERTY_SETTINGS
@given(population)
def test_the_default_and_a_flag_off_the_rent_sharers_are_no_ops(population):
    unset, _, _ = build(population, flags="unset")
    false, _, _ = build(population, flags="false")
    drawn, _, _ = build(population, flags="as_drawn")
    inert, _, _ = build(population, flags="inert")
    for variable in [
        "housing_benefit_LHA_allowed_bedrooms",
        "housing_benefit_LHA_additional_bedrooms",
        "housing_benefit_LHA_category",
        "housing_benefit_shares_accommodation",
        "housing_benefit_non_dep_deductions",
        "council_tax_reduction_non_dep_deductions",
        "LHA_allowed_bedrooms",
        "housing_benefit",
    ]:
        assert_same(false, unset, variable)
        assert_same(inert, drawn, variable)


@PROPERTY_SETTINGS
@given(population)
def test_a_single_household_has_the_same_size_criteria(population):
    assume(any(any(j for _, j in house["sharers"]) for house in population))
    sim, _, single = build(population)
    household = benunit_household(sim)
    bedrooms = calc(sim, "housing_benefit_LHA_allowed_bedrooms")
    additional = calc(sim, "housing_benefit_LHA_additional_bedrooms")
    no_foster_child = [
        not any(
            foster
            for fam in [house["head"]]
            + [f for f, _ in house["sharers"]]
            + [f for f, _ in house["non_dependants"]]
            for _, _, foster, _ in fam["children"]
        )
        for house in population
    ]
    for h in np.unique(household[single]):
        members = single & (household == h)
        before_additional = (bedrooms - additional)[members]
        assert np.all(before_additional == before_additional[0])
        if no_foster_child[h]:
            assert np.all(bedrooms[members] == bedrooms[members][0])


@PROPERTY_SETTINGS
@given(population)
def test_a_single_household_never_lowers_bedrooms(population):
    joined, _, single = build(population)
    apart, _, _ = build(population, flags="false")
    for variable in [
        "housing_benefit_LHA_allowed_bedrooms",
        "housing_benefit_LHA_additional_bedrooms",
    ]:
        with_single = calc(joined, variable)
        without = calc(apart, variable)
        assert np.all(with_single >= without)
        np.testing.assert_array_equal(with_single[~single], without[~single])


@PROPERTY_SETTINGS
@given(population)
def test_exclusive_use_follows_the_household(population):
    sim, roles, single = build(population)
    household = benunit_household(sim)
    shares = calc(sim, "housing_benefit_shares_accommodation").astype(bool)
    liable = calc(sim, "benunit_is_rent_liable").astype(bool)
    joint_occupier = (roles == "head") | (roles == "sharer")
    separate_sharer = (roles == "sharer") & ~single
    for h in range(len(population)):
        in_household = household == h
        families = joint_occupier & in_household
        if not np.any((roles == "sharer") & in_household):
            continue
        if np.any(separate_sharer & in_household):
            # A joint tenant outside someone's household shares their rooms.
            assert np.all(shares[families & liable])
        else:
            # Every joint occupier is in the head's household.
            assert not np.any(shares[families])


@PROPERTY_SETTINGS
@given(population)
def test_universal_credit_deductions_and_non_dependants_do_not_depend_on_the_input(
    population,
):
    joined, _, _ = build(population)
    apart, _, _ = build(population, flags="false")
    for variable in [
        "LHA_allowed_bedrooms",
        "LHA_additional_bedrooms",
        "uc_non_dep_deductions",
        "lha_renter_has_non_dependant",
        "housing_benefit_non_dep_deductions",
        "council_tax_reduction_non_dep_deductions",
        "housing_benefit_claimant_has_non_dependant",
        "is_housing_benefit_young_individual",
    ]:
        assert_same(joined, apart, variable)


def test_the_input_has_no_effect_without_a_household_head():
    """A single household needs the household head's family, so where no one
    is the household head the input changes nothing, even on a family that
    shares the rent and with a lodger present."""

    def situation(joins):
        people = {
            name: {
                "age": {YEAR: age},
                "is_household_head": {YEAR: False},
                **extra,
            }
            for name, age, extra in [
                ("older", 60, {}),
                ("sharer", 40, {}),
                ("lodger", 35, {"rent_paid_as_lodger": {YEAR: 4_000}}),
            ]
        }
        benunits = {
            "older_family": {"members": ["older"]},
            "sharer_family": {
                "members": ["sharer"],
                "liable_for_share_of_household_rent": {YEAR: True},
                "joint_tenant_in_household_head_household": {YEAR: joins},
            },
            "lodger_family": {"members": ["lodger"]},
        }
        households = {
            "home": {
                "members": list(people),
                "rent": {YEAR: 15_600},
                "tenure_type": {YEAR: "RENT_PRIVATELY"},
                "brma": {YEAR: "MAIDSTONE"},
            }
        }
        return Simulation(
            situation={"people": people, "benunits": benunits, "households": households}
        )

    joined, apart = situation(True), situation(False)
    for variable in [
        "housing_benefit_LHA_allowed_bedrooms",
        "housing_benefit_LHA_additional_bedrooms",
        "housing_benefit_LHA_category",
        "housing_benefit_shares_accommodation",
    ]:
        assert_same(joined, apart, variable)
