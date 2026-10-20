"""Property-based tests for the Pension Credit severe disability addition.

State Pension Credit Regulations 2002 reg 6(4)-(5) and Sch I paras 1-2, as
encoded in severe_disability_minimum_guarantee_addition and the variables it
reads. Households are generated with a pension-age benefit unit and up to two
other benefit units, each single or a couple and possibly with dependants,
each person drawn with a disability benefit (or none), blindness, a carer
benefit and, for 16- to 19-year-olds, non-advanced education. is_claimant_or_partner is
set from the generated roles, as the survey data supply it.

Invariants, for every benefit unit in every generated household:

1. Differential: the number of rates equals that of an independent reference
   implementation written from the law text
   (severe_disability_addition_reference.py).
2. Structural: the addition is 0, 1 or 2 times the weekly rate times 52, and
   2 only for a couple. The qualifying-benefit flag matches the Sch I para
   1(1)(a)(i) list for the drawn benefit categories.
3. Residence, metamorphic: adding another adult resident who is not a para 2
   person removes the addition for every other benefit unit. Adding a resident
   whose presence is ignored and who receives no carer benefit leaves every
   existing unit's addition unchanged if the resident does not qualify (a
   blind person, a qualifying young person or anyone under 18), and never
   lowers it if they do (a qualifying-benefit recipient, to whom a carer in
   the household may then be attributed instead).
4. Carers, metamorphic: giving someone a carer benefit never increases any
   unit's addition.
5. Symmetry: swapping the drawn attributes of a couple's two partners leaves
   their addition unchanged.
6. Shared carer attribution, differential: the claimants and partners that
   is_cared_for_by_carer_benefit_recipient marks in each benefit unit are one
   of the sets the reference's person-to-person matching allows, and the
   number of other members marked (such as disabled children) is the number
   the reference's within-unit matching covers. Structural: only a person
   who is severely disabled for Carer's Allowance is marked, a household has
   no more people cared for than carer benefits, and a household's only
   carer is never marked as caring for themselves.
7. Cross-programme, differential: the legacy severe disability premium (HB
   Regs 2006 Sch 3 para 14) reads the same attribution, and its qualifying
   benefits, couple, blind-partner and carer rules and rates are those of the
   addition. The two residence tests differ only over 16- to 19-year-olds
   (HB reg 3 non-dependants against SPC Sch I para 2(2)(f)), so in a
   household with no one of that age the premium equals the addition for
   every benefit unit, carers in other benefit units included.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from severe_disability_addition_reference import (
    _best_within_unit,
    household_carer_assignments,
    reference_rates,
)

from policyengine_uk import Simulation

YEAR = 2026
WEEKS_IN_YEAR = 52
PROPERTY_SETTINGS = settings(
    max_examples=25,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
# Drawn benefit category -> whether Sch I para 1(1)(a)(i) lists it.
BENEFITS = {
    "none": ({}, False),
    "aa_lower": ({"aa_category": "LOWER"}, True),
    "aa_higher": ({"aa_category": "HIGHER"}, True),
    "dla_care_lowest": ({"dla_sc_category": "LOWER"}, False),
    "dla_care_middle": ({"dla_sc_category": "MIDDLE"}, True),
    "dla_care_highest": ({"dla_sc_category": "HIGHER"}, True),
    "pip_dl_standard": ({"pip_dl_category": "STANDARD"}, True),
    "pip_dl_enhanced": ({"pip_dl_category": "ENHANCED"}, True),
}


@st.composite
def person(draw, min_age, max_age):
    age = draw(st.integers(min_age, max_age))
    return dict(
        age=age,
        benefit=draw(st.sampled_from(sorted(BENEFITS))),
        blind=draw(st.booleans()),
        carer=draw(st.booleans()),
        # Only meaningful at 16 to 19 (reg 4A); started before 19.
        education=16 <= age <= 19 and draw(st.booleans()),
    )


@st.composite
def household(draw):
    focal = dict(
        claimants=[draw(person(66, 95)) for _ in range(draw(st.integers(1, 2)))],
        dependants=draw(st.lists(person(0, 19), max_size=2)),
    )
    others = [
        dict(
            claimants=[draw(person(18, 90)) for _ in range(draw(st.integers(1, 2)))],
            dependants=draw(st.lists(person(0, 19), max_size=1)),
        )
        for _ in range(draw(st.integers(0, 2)))
    ]
    return [focal] + others


def build(households):
    """One Simulation for many households; returns the situation and a map."""
    people, benunits, hh = {}, {}, {}
    layout = []
    for h, units in enumerate(households):
        hh_members, hh_layout = [], []
        for b, unit in enumerate(units):
            names = []
            for role, group in (("cp", unit["claimants"]), ("dep", unit["dependants"])):
                for j, p in enumerate(group):
                    name = f"h{h}b{b}{role}{j}"
                    record = {
                        "age": {YEAR: p["age"]},
                        "is_blind": {YEAR: p["blind"]},
                        "is_claimant_or_partner": {YEAR: role == "cp"},
                        "is_in_non_advanced_education": {YEAR: p["education"]},
                        "age_started_or_accepted_current_education_or_training": {
                            YEAR: min(p["age"], 18)
                        },
                        "care_hours": {YEAR: 35 if p["carer"] else 0},
                        "carers_allowance_reported": {YEAR: 1 if p["carer"] else 0},
                    }
                    for variable, value in BENEFITS[p["benefit"]][0].items():
                        record[variable] = {YEAR: value}
                    people[name] = record
                    names.append((name, role, p))
            benunits[f"h{h}b{b}"] = {"members": [n for n, _, _ in names]}
            hh_members += [n for n, _, _ in names]
            hh_layout.append(names)
        hh[f"h{h}"] = {"members": hh_members, "country": {YEAR: "ENGLAND"}}
        layout.append(hh_layout)
    return {"people": people, "benunits": benunits, "households": hh}, layout


def simulate(households):
    situation, layout = build(households)
    simulation = Simulation(situation=situation)

    def calc(variable):
        return np.asarray(simulation.calculate(variable, YEAR))

    rate = float(
        simulation.tax_benefit_system.parameters(
            str(YEAR)
        ).gov.dwp.pension_credit.guarantee_credit.severe_disability.addition
    )
    return {
        "layout": layout,
        "rates": calc("severe_disability_minimum_guarantee_addition")
        / (rate * WEEKS_IN_YEAR),
        "qualifies": calc("receives_severe_disability_addition_qualifying_benefit"),
        "carer": calc("receives_carer_benefit"),
        "is_couple": calc("is_couple"),
        "cared_for": calc("is_cared_for_by_carer_benefit_recipient"),
        "could_be_cared_for": calc("is_severely_disabled_for_carers_allowance"),
        "addition": calc("severe_disability_minimum_guarantee_addition"),
        "legacy_premium": calc("severe_disability_premium"),
    }


def rates_by_household(result):
    """Split the benefit-unit rates array into one list per household."""
    out, i = [], 0
    for hh_layout in result["layout"]:
        out.append(list(result["rates"][i : i + len(hh_layout)]))
        i += len(hh_layout)
    return out


def reference_household(result, h):
    """The reference's input for household h, from the simulation's inputs."""
    person_index = {}
    k = 0
    for layout in result["layout"]:
        for names in layout:
            for name, _, _ in names:
                person_index[name] = k
                k += 1
    people, benunits = {}, {}
    for b, names in enumerate(result["layout"][h]):
        benunits[b] = {"claimant_or_partner": [], "others": []}
        for name, role, p in names:
            i = person_index[name]
            people[name] = {
                "age": p["age"],
                "qualifying_benefit": BENEFITS[p["benefit"]][1],
                "blind": p["blind"],
                # Reg 4A, from the inputs: 16 to 19, in non-advanced
                # education started before 19, no benefits in own right.
                "qualifying_young_person": 16 <= p["age"] <= 19 and p["education"],
                "receives_carer_benefit": bool(result["carer"][i]),
            }
            key = "claimant_or_partner" if role == "cp" else "others"
            benunits[b][key].append(name)
    return {"people": people, "benunits": benunits}


@PROPERTY_SETTINGS
@given(st.lists(household(), min_size=1, max_size=6))
def test_addition_matches_the_reference_and_is_bounded(households):
    result = simulate(households)
    rates = rates_by_household(result)
    np.testing.assert_allclose(result["rates"], np.round(result["rates"]), atol=1e-9)
    assert np.all(np.isin(np.round(result["rates"]), [0, 1, 2]))
    assert np.all(np.round(result["rates"])[~result["is_couple"].astype(bool)] <= 1)
    # The qualifying-benefit flag follows the para 1(1)(a)(i) list.
    expected_qualifies = [
        BENEFITS[p["benefit"]][1]
        for layout in result["layout"]
        for names in layout
        for _, _, p in names
    ]
    np.testing.assert_array_equal(result["qualifies"], expected_qualifies)
    for h, household_units in enumerate(households):
        reference = reference_household(result, h)
        expected = reference_rates(reference)
        actual = [int(round(x)) for x in rates[h]]
        assert actual == [expected[b] for b in range(len(household_units))], (
            reference,
            actual,
        )


# (resident, whether they receive a para 1(1)(a)(i) qualifying benefit)
IGNORED_RESIDENTS = [
    (
        dict(
            age=50, benefit="pip_dl_standard", blind=False, carer=False, education=False
        ),
        True,
    ),
    (dict(age=50, benefit="aa_lower", blind=False, carer=False, education=False), True),
    (dict(age=50, benefit="none", blind=True, carer=False, education=False), False),
    (dict(age=18, benefit="none", blind=False, carer=False, education=True), False),
    (dict(age=17, benefit="none", blind=False, carer=False, education=False), False),
]
COUNTED_RESIDENT = dict(
    age=30, benefit="none", blind=False, carer=False, education=False
)


@PROPERTY_SETTINGS
@given(household(), st.sampled_from(range(len(IGNORED_RESIDENTS))))
def test_residence_condition_is_metamorphic(original, ignored_index):
    ignored, ignored_qualifies = IGNORED_RESIDENTS[ignored_index]
    with_ignored = original + [dict(claimants=[ignored], dependants=[])]
    with_counted = original + [dict(claimants=[COUNTED_RESIDENT], dependants=[])]
    result = simulate([original, with_ignored, with_counted])
    base, ignored_rates, counted_rates = rates_by_household(result)
    n = len(original)
    if ignored_qualifies:
        assert all(a >= b - 1e-9 for a, b in zip(ignored_rates[:n], base))
    else:
        np.testing.assert_allclose(ignored_rates[:n], base, atol=1e-9)
    np.testing.assert_allclose(counted_rates[:n], 0, atol=1e-9)


@PROPERTY_SETTINGS
@given(household(), st.data())
def test_a_carer_benefit_never_increases_the_addition(original, data):
    candidates = [
        (u, group, j)
        for u, unit in enumerate(original)
        for group in ("claimants", "dependants")
        for j, p in enumerate(unit[group])
        if not p["carer"] and p["age"] >= 16
    ]
    if not candidates:
        return
    u, group, j = data.draw(st.sampled_from(candidates))
    changed = [
        dict(
            claimants=[dict(p) for p in unit["claimants"]],
            dependants=[dict(p) for p in unit["dependants"]],
        )
        for unit in original
    ]
    changed[u][group][j]["carer"] = True
    result = simulate([original, changed])
    before, after = rates_by_household(result)
    assert all(a <= b + 1e-9 for a, b in zip(after, before)), (before, after)


@PROPERTY_SETTINGS
@given(household())
def test_swapping_partners_leaves_a_couples_addition_unchanged(original):
    focal = original[0]
    if len(focal["claimants"]) != 2:
        return
    first, second = focal["claimants"]
    keys = ["benefit", "blind", "carer"]
    swapped_first = {**first, **{k: second[k] for k in keys}}
    swapped_second = {**second, **{k: first[k] for k in keys}}
    swapped = [dict(focal, claimants=[swapped_first, swapped_second])] + original[1:]
    result = simulate([original, swapped])
    before, after = rates_by_household(result)
    assert before[0] == after[0]


@PROPERTY_SETTINGS
@given(st.lists(household(), min_size=1, max_size=6))
def test_shared_carer_attribution_matches_the_reference_matching(households):
    result = simulate(households)
    cared_for = result["cared_for"].astype(bool)
    # Only someone a carer benefit can be paid for is marked.
    assert not np.any(cared_for & ~result["could_be_cared_for"].astype(bool))
    np.testing.assert_array_equal(result["could_be_cared_for"], result["qualifies"])
    k = 0
    for h, layout in enumerate(result["layout"]):
        allowed = household_carer_assignments(reference_household(result, h))
        names = [name for unit in layout for name, _, _ in unit]
        marked = {name for i, name in enumerate(names) if cared_for[k + i]}
        carers = int(result["carer"][k : k + len(names)].sum())
        # Each award is for one person.
        assert len(marked) <= carers, (layout, marked)
        if carers == 1 and len(names) > 0:
            (carer,) = [n for i, n in enumerate(names) if result["carer"][k + i]]
            assert carer not in marked, (layout, marked)
        reference = reference_household(result, h)
        for b, unit in enumerate(layout):
            claimants = {name for name, role, _ in unit if role == "cp"}
            assert frozenset(marked & claimants) in allowed[b], (
                layout,
                marked,
                allowed[b],
            )
            # Other members (such as a disabled child) are cared for only by
            # carers of their own unit, after its claimants and partners.
            others = {name for name, role, _ in unit if role != "cp"}
            unit_carers = sum(
                reference["people"][n]["receives_carer_benefit"]
                for n in claimants | others
            )
            within_cp, left_over = _best_within_unit(
                reference["people"], reference["benunits"][b]
            )
            assert len(marked & others) == unit_carers - left_over - within_cp, (
                layout,
                marked,
            )
        k += len(names)


def no_one_aged_16_to_19(units):
    return not any(
        16 <= p["age"] <= 19
        for unit in units
        for p in unit["claimants"] + unit["dependants"]
    )


@PROPERTY_SETTINGS
@given(st.lists(household().filter(no_one_aged_16_to_19), min_size=1, max_size=6))
def test_legacy_premium_equals_the_addition_without_young_people(households):
    result = simulate(households)
    np.testing.assert_allclose(result["legacy_premium"], result["addition"], atol=0.01)


def test_the_three_qualifying_benefit_lists_agree():
    """The attribution's candidates are the Carer's Allowance list (SSCBA 1992
    s.70(2)); the premium and the addition each count their own qualifying
    claimants and partners among those marked. In the model's variables the
    three lists are the same from 8 April 2013, when PIP and AFIP joined
    s.70(2), which is what makes the two programmes' cared-for counts agree."""
    from policyengine_uk import CountryTaxBenefitSystem

    parameters = CountryTaxBenefitSystem().parameters
    for instant in ("2013-04-08", "2020-01-01", "2026-01-01", "2030-01-01"):
        dwp = parameters(instant).gov.dwp
        carers_allowance = set(dwp.carers_allowance.qualifying_disability_benefits)
        legacy = set(dwp.disability_premia.severe_qualifying_benefits)
        pension_credit = set(
            dwp.pension_credit.guarantee_credit.severe_disability.relevant_benefits
        )
        assert carers_allowance == legacy == pension_credit, instant
