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
2. Oracle: the premium equals an independent statement of the rule in which
   the carer condition is a brute-force assignment of each carer award to a
   benefit-unit member other than its recipient (the model does not observe
   who is cared for, so it takes the assignment that covers the most
   qualifying members).
3. Metamorphic: adding a household member aged 18 or over, in another benefit
   unit, who receives no qualifying benefit and is not blind, removes the
   premium.
4. Metamorphic: paying anyone in the benefit unit a carer benefit never
   increases the premium.
5. Metamorphic: giving anyone in the household a qualifying benefit, or making
   them blind, never reduces the premium.
6. Differential: for a family with no children and no one else in the
   household, the premium equals the Pension Credit severe disability
   addition, which has the same qualifying benefits, couple, blind-partner and
   carer rules and rates (SPC Regs 2002 Sch I para 1; reg 6(5)). This keeps
   two encodings of the same rule in step; it is not an independent oracle.
"""

from itertools import product

import numpy as np
from hypothesis import HealthCheck, event, example, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

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
def households(draw):
    adults = draw(st.lists(person(ADULT_AGE), min_size=1, max_size=2))
    children = draw(st.lists(person(st.integers(0, 15)), max_size=1))
    others = draw(st.lists(person(st.integers(15, 70)), max_size=2))
    return dict(adults=adults, children=children, others=others)


def qualifies(p):
    return BENEFITS[p["benefit"]][1]


def person_inputs(p):
    inputs = {"age": {YEAR: p["age"]}, "is_blind": {YEAR: p["blind"]}}
    inputs["receives_carer_benefit"] = {YEAR: p["carer"]}
    for name, value in BENEFITS[p["benefit"]][0].items():
        inputs[name] = {YEAR: value}
    return inputs


def simulate(units, variables=("severe_disability_premium",)):
    """One simulation for many households; returns each primary family's values."""
    people, benunits, hh = {}, {}, {}
    for i, unit in enumerate(units):
        family = []
        for j, p in enumerate(unit["adults"] + unit["children"]):
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


def oracle(unit):
    """The premium by the statutory rule, written independently of the model."""
    adults, family = unit["adults"], unit["adults"] + unit["children"]
    blocking = [
        o
        for o in unit["others"]
        if o["age"] >= 18 and not qualifies(o) and not o["blind"]
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
    # Assign each carer award to one family member other than its recipient,
    # and count the most qualifying members that can be covered.
    carers = [i for i, p in enumerate(family) if p["carer"]]
    cared_for = 0
    for assignment in product(range(len(family)), repeat=len(carers)):
        if any(c == target for c, target in zip(carers, assignment)):
            continue
        cared_for = max(cared_for, len(set(assignment) & set(qualifying)))
    if len(adults) == 2 and len(qualifying) == 2:
        return (2 - cared_for) * SINGLE
    return SINGLE if cared_for == 0 else 0.0


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
    ]
)
def test_premium_matches_statutory_oracle_and_range(units):
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
@given(st.lists(households(), min_size=1, max_size=10), st.integers(0, 2))
def test_carer_benefit_never_increases_premium(units, index):
    def pay_carer(unit):
        family = unit["adults"] + unit["children"]
        i = index % len(family)
        family = [dict(p, carer=p["carer"] or k == i) for k, p in enumerate(family)]
        n = len(unit["adults"])
        return dict(unit, adults=family[:n], children=family[n:])

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
        everyone = unit["adults"] + unit["children"] + unit["others"]
        i = index % len(everyone)
        changed = [
            dict(p, **({"blind": True} if change == "blind" else {"benefit": change}))
            if k == i
            else p
            for k, p in enumerate(everyone)
        ]
        a, c = len(unit["adults"]), len(unit["children"])
        return dict(
            unit,
            adults=changed[:a],
            children=changed[a : a + c],
            others=changed[a + c :],
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
