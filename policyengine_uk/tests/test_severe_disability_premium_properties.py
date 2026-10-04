"""Property-based tests for the legacy severe disability premium.

HB Regs 2006 Sch 3 para 14 (with IS Regs 1987 Sch 2 para 13, ESA Regs 2008
Sch 4 para 6 and JSA Regs 1996 Sch 1 para 15) pay the premium to a claimant
who receives a qualifying benefit; for a couple, both partners must qualify
unless the other partner is blind. No non-dependant aged 18 or over may
reside with them (ignoring non-dependants who receive a qualifying benefit or
are blind). A single claimant must have no one paid a carer benefit for caring
for them; a couple who both qualify get the double rate when no carer benefit
is paid for either, the single rate when one is paid for only one of them, and
nothing when carers are paid for both.

Invariants, for any generated population of households:

1. Range: the premium is 0, the single rate or the double rate, and the double
   rate goes only to a couple who both qualify.
2. Oracle: the premium equals a separately written implementation of the
   rule, in which the carer condition is the person-to-person matching of
   severe_disability_addition_reference.household_carer_assignments, the
   reference the Pension Credit severe disability addition is tested against
   (the model does not observe who is cared for; both rules read the one
   attribution, is_cared_for_by_carer_benefit_recipient). Carers in other
   benefit units of the household are attributed too, so a non-dependant
   whose presence is ignored can still bar the premium as the claimant's
   carer. The oracle is independent of the model's code but not of its
   assumptions: it shares the carer attribution and the symmetric
   blind-partner rule (either partner may be the claimant), so agreement
   shows the model implements those assumptions, not that they match the
   Regulations.
3. Metamorphic: adding a household member aged 18 or over, in another benefit
   unit, who receives no qualifying benefit and is not blind, removes the
   premium. The oracle also treats a benefit-unit member aged 18 or 19 who is
   not a qualifying young person as a non-dependant (HB Regs regs 3, 19).
4. Metamorphic: paying anyone in the household a carer benefit never
   increases the premium.
5. Metamorphic: giving anyone in the household a qualifying benefit, or making
   them blind, never reduces the premium.
6. Differential: for a family with no children and no one else in the
   household, the premium equals the Pension Credit severe disability
   addition, which has the same qualifying benefits, couple, blind-partner and
   carer rules and rates (SPC Regs 2002 Sch I para 1; reg 6(5)). This keeps
   two encodings of the same rule in step; it is not an independent oracle.
"""

import numpy as np
from hypothesis import HealthCheck, event, example, given, settings
from hypothesis import strategies as st
from severe_disability_addition_reference import household_carer_assignments

from policyengine_uk import Simulation, parameters

YEAR = 2026
WEEKS = 52
SINGLE = 86.05 * WEEKS
DOUBLE = 172.10 * WEEKS
PROPERTY_SETTINGS = settings(
    max_examples=12,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)


def _qualifying_list(year, name):
    return getattr(parameters(str(year)).gov.dwp.disability_premia, name)


def test_northern_ireland_commencements_by_model_year():
    # The model reads the list as at 1 January before 2015 and 30 April from
    # 2015, so AFIP (24 December 2013) first qualifies in 2014 and PIP daily
    # living (20 June 2016) in 2017. The Great Britain list adds both from
    # 8 April 2013, so from 2014.
    ni = "severe_qualifying_benefits_northern_ireland"
    for benefit, last_year_without, first_year_with in (
        ("armed_forces_independence_payment", 2013, 2014),
        ("pip_dl", 2016, 2017),
    ):
        assert benefit not in _qualifying_list(last_year_without, ni)
        assert benefit in _qualifying_list(first_year_with, ni)
    for benefit in ("armed_forces_independence_payment", "pip_dl"):
        gb = "severe_qualifying_benefits"
        assert benefit not in _qualifying_list(2013, gb)
        assert benefit in _qualifying_list(2014, gb)


# (inputs, qualifies) for each benefit a person may receive.
BENEFITS = {
    "none": ({}, False),
    "aa_lower": ({"aa_category": "LOWER"}, True),
    "aa_higher": ({"aa_category": "HIGHER"}, True),
    "dla_lowest": ({"dla_sc_category": "LOWER"}, False),
    "dla_middle": ({"dla_sc_category": "MIDDLE"}, True),
    "dla_highest": ({"dla_sc_category": "HIGHER"}, True),
    "pip_standard": ({"pip_dl_category": "STANDARD"}, True),
    "pip_enhanced": ({"pip_dl_category": "ENHANCED"}, True),
    "pip_mobility_only": ({"pip_m_category": "ENHANCED"}, False),
    "afip": ({"armed_forces_independence_payment": 1_000.0}, True),
    "afcs_other": ({"afcs_reported": 1_000.0}, False),
}
benefit = st.sampled_from(sorted(BENEFITS))
# Adults aged 20 to 60 and children under 16 are the claimant and partner, and
# their children, under any reading of the benefit unit (18 and 19 year olds
# can be qualifying young persons).
ADULT_AGE = st.integers(20, 60)


@st.composite
def person(draw, age):
    return dict(
        age=draw(age),
        benefit=draw(benefit),
        blind=draw(st.booleans()),
        # Carer benefits are rarer than not, so couples who both qualify with
        # no carer (the double rate) are generated as well.
        carer=draw(st.sampled_from([False, False, False, True])),
    )


@st.composite
def young_person(draw):
    # A 16-19 year old in the benefit unit, who is a qualifying young person
    # only if in non-advanced education and (at 19) started before 19.
    return dict(
        draw(person(st.integers(16, 19))),
        in_education=draw(st.booleans()),
        entry_age=draw(st.sampled_from([17, 19])),
    )


@st.composite
def households(draw):
    young = draw(st.lists(young_person(), max_size=1))
    # With a 16-19 year old present, adults aged 40+ make them the head's
    # presumed child under #1896's claimant and partner inference.
    adult_age = st.integers(40, 60) if young else ADULT_AGE
    adults = draw(st.lists(person(adult_age), min_size=1, max_size=2))
    children = draw(st.lists(person(st.integers(0, 15)), max_size=1))
    others = draw(st.lists(person(st.integers(15, 70)), max_size=2))
    return dict(adults=adults, children=children, young=young, others=others)


def family_members(unit):
    return unit["adults"] + unit["children"] + unit.get("young", [])


def with_family(unit, family):
    a, c = len(unit["adults"]), len(unit["children"])
    return dict(
        unit, adults=family[:a], children=family[a : a + c], young=family[a + c :]
    )


def qualifies(p):
    return BENEFITS[p["benefit"]][1]


def is_qualifying_young_person(p):
    """Child Benefit qualifying young person (SSCBA s.142), as HB reg 19 uses."""
    return (
        16 <= p["age"] < 20
        and p.get("in_education", False)
        and (p["age"] < 19 or p.get("entry_age", 99) < 19)
    )


def person_inputs(p):
    inputs = {"age": {YEAR: p["age"]}, "is_blind": {YEAR: p["blind"]}}
    inputs["receives_carer_benefit"] = {YEAR: p["carer"]}
    if "in_education" in p:
        inputs["is_in_non_advanced_education"] = {YEAR: p["in_education"]}
        inputs["age_started_or_accepted_current_education_or_training"] = {
            YEAR: p["entry_age"]
        }
    for name, value in BENEFITS[p["benefit"]][0].items():
        inputs[name] = {YEAR: value}
    return inputs


def simulate(units, variables=("severe_disability_premium",)):
    """One simulation for many households; returns each primary family's values."""
    people, benunits, hh = {}, {}, {}
    for i, unit in enumerate(units):
        family = []
        for j, p in enumerate(family_members(unit)):
            people[f"h{i}_f{j}"] = person_inputs(p)
            family.append(f"h{i}_f{j}")
        benunits[f"h{i}_family"] = {"members": family}
        members = list(family)
        for j, p in enumerate(unit["others"]):
            people[f"h{i}_o{j}"] = person_inputs(p)
            benunits[f"h{i}_o{j}"] = {"members": [f"h{i}_o{j}"]}
            members.append(f"h{i}_o{j}")
        hh[f"h{i}"] = {"members": members}
    sim = Simulation(
        situation={"people": people, "benunits": benunits, "households": hh}
    )
    ids = list(sim.populations["benunit"].ids)
    rows = [ids.index(f"h{i}_family") for i in range(len(units))]
    return {v: np.asarray(sim.calculate(v, YEAR))[rows] for v in variables}


def simulate_before_after(units, changed):
    """The premium for the original and changed households, in one simulation."""
    premium = simulate(units + changed)["severe_disability_premium"]
    return premium[: len(units)], premium[len(units) :]


def claimants_and_partners_cared_for(unit):
    """Every allowed set of the family's adults a carer benefit is paid for.

    The household as the shared carer reference reads it: the family's adults
    are its claimant and partner, and each other person is a benefit unit of
    their own, its claimant from age 16. People are listed in simulation
    order.
    """
    family = family_members(unit)
    people, benunits = {}, {}
    benunits["family"] = {"claimant_or_partner": [], "others": []}
    for i, p in enumerate(family):
        role = "claimant_or_partner" if i < len(unit["adults"]) else "others"
        benunits["family"][role].append(("family", i))
        people[("family", i)] = p
    for j, p in enumerate(unit["others"]):
        role = "claimant_or_partner" if p["age"] >= 16 else "others"
        benunits[("other", j)] = {"claimant_or_partner": [], "others": []}
        benunits[("other", j)][role].append(("other", j))
        people[("other", j)] = p
    people = {
        pid: dict(
            age=p["age"],
            qualifying_benefit=qualifies(p),
            receives_carer_benefit=p["carer"],
        )
        for pid, p in people.items()
    }
    allowed = household_carer_assignments({"people": people, "benunits": benunits})
    return [{i for _, i in cared_for} for cared_for in allowed["family"]]


def oracle(unit):
    """The premium from a separately written implementation of the rule.

    Independent of the model's code, but it shares the model's carer
    attribution and symmetric blind-partner assumptions.
    """
    adults = unit["adults"]
    # Non-dependants: other benefit units in the household, and anyone in the
    # benefit unit who is not the claimant, partner, a child or a qualifying
    # young person (HB Regs regs 3(2)(a), 19).
    candidates = unit["others"] + [
        y for y in unit.get("young", []) if not is_qualifying_young_person(y)
    ]
    blocking = [
        o for o in candidates if o["age"] >= 18 and not qualifies(o) and not o["blind"]
    ]
    if blocking:
        return 0.0
    qualifying = [i for i, a in enumerate(adults) if qualifies(a)]
    if len(adults) == 2 and len(qualifying) == 1:
        other = adults[1 - qualifying[0]]
        if not other["blind"]:
            return 0.0
    elif len(adults) == 2 and len(qualifying) == 0:
        return 0.0
    elif len(adults) == 1 and not qualifying:
        return 0.0
    # Which qualifying members a carer benefit is paid for caring for. Where
    # the attribution leaves a choice between partners, the premium must not
    # depend on it.
    premiums = set()
    for cared_for in claimants_and_partners_cared_for(unit):
        cared_for = len(cared_for & set(qualifying))
        if len(adults) == 2 and len(qualifying) == 2:
            premiums.add((2 - cared_for) * SINGLE)
        else:
            premiums.add(SINGLE if cared_for == 0 else 0.0)
    assert len(premiums) == 1, (unit, premiums)
    return premiums.pop()


def _adult(benefit, blind=False, carer=False):
    return dict(age=40, benefit=benefit, blind=blind, carer=carer)


@PROPERTY_SETTINGS
@given(st.lists(households(), min_size=1, max_size=10))
@example(
    [
        # Both qualify, no carer: the double rate.
        dict(
            adults=[_adult("pip_standard"), _adult("aa_lower")],
            children=[],
            others=[],
        ),
        # One qualifies, the other is blind: the single rate.
        dict(
            adults=[_adult("dla_middle"), _adult("none", blind=True)],
            children=[],
            others=[],
        ),
        # An 18-year-old in the benefit unit, not in education: a
        # non-dependant, so no premium.
        dict(
            adults=[_adult("pip_standard")],
            children=[],
            young=[dict(_adult("none"), age=18, in_education=False, entry_age=17)],
            others=[],
        ),
        # A 19-year-old qualifying young person: family, so the single rate.
        dict(
            adults=[_adult("pip_standard")],
            children=[],
            young=[dict(_adult("none"), age=19, in_education=True, entry_age=17)],
            others=[],
        ),
        # A non-dependant who receives a qualifying benefit is ignored as a
        # resident (para 14(4)(a)) but, receiving a carer benefit, is the
        # claimant's carer: no premium.
        dict(
            adults=[_adult("pip_standard")],
            children=[],
            others=[_adult("pip_standard", carer=True)],
        ),
        # The same for a couple who both qualify: the single rate.
        dict(
            adults=[_adult("pip_standard"), _adult("aa_lower")],
            children=[],
            others=[_adult("none", blind=True, carer=True)],
        ),
    ]
)
def test_premium_matches_independent_oracle_and_range(units):
    premium = simulate(units)["severe_disability_premium"]
    for unit, value in zip(units, premium):
        event(
            f"{len(unit['adults'])} adult(s), premium "
            f"{'double' if value > SINGLE + 1 else 'single' if value > 1 else 'none'}"
        )
        assert np.isclose(value, oracle(unit), atol=0.01), unit
        assert any(np.isclose(value, x, atol=0.01) for x in (0, SINGLE, DOUBLE))
        if np.isclose(value, DOUBLE, atol=0.01):
            assert len(unit["adults"]) == 2
            assert all(qualifies(a) for a in unit["adults"])


@PROPERTY_SETTINGS
@given(st.lists(households(), min_size=1, max_size=10), ADULT_AGE)
def test_counted_non_dependant_removes_premium(units, age):
    non_dependant = dict(age=age, benefit="none", blind=False, carer=False)
    added = [dict(u, others=u["others"] + [non_dependant]) for u in units]
    premium = simulate(added)["severe_disability_premium"]
    assert np.allclose(premium, 0)


@PROPERTY_SETTINGS
@given(st.lists(households(), min_size=1, max_size=10), st.integers(0, 4))
def test_carer_benefit_never_increases_premium(units, index):
    def pay_carer(unit):
        family = family_members(unit)
        everyone = family + unit["others"]
        i = index % len(everyone)
        paid = [dict(p, carer=p["carer"] or k == i) for k, p in enumerate(everyone)]
        return dict(with_family(unit, paid[: len(family)]), others=paid[len(family) :])

    before, after = simulate_before_after(units, [pay_carer(u) for u in units])
    assert np.all(after <= before + 0.01)


@PROPERTY_SETTINGS
@given(
    st.lists(households(), min_size=1, max_size=10),
    st.integers(0, 4),
    st.sampled_from(["pip_standard", "blind"]),
)
def test_qualifying_benefit_or_blindness_never_reduces_premium(units, index, change):
    def apply(unit):
        family = family_members(unit)
        everyone = family + unit["others"]
        i = index % len(everyone)
        changed = [
            dict(p, **({"blind": True} if change == "blind" else {"benefit": change}))
            if k == i
            else p
            for k, p in enumerate(everyone)
        ]
        return dict(
            with_family(unit, changed[: len(family)]), others=changed[len(family) :]
        )

    before, after = simulate_before_after(units, [apply(u) for u in units])
    assert np.all(after >= before - 0.01)


@PROPERTY_SETTINGS
@given(st.lists(st.lists(person(ADULT_AGE), min_size=1, max_size=2), min_size=1))
def test_matches_pension_credit_severe_disability_addition(families):
    # PolicyEngine/policyengine-uk#1896's Pension Credit addition applies the
    # same couple, blind-partner and carer rules, so every family with no one
    # else in the household is compared, carers and mixed couples included.
    units = [dict(adults=adults, children=[], others=[]) for adults in families]
    values = simulate(
        units,
        ("severe_disability_premium", "severe_disability_minimum_guarantee_addition"),
    )
    assert np.allclose(
        values["severe_disability_premium"],
        values["severe_disability_minimum_guarantee_addition"],
        atol=0.01,
    )
