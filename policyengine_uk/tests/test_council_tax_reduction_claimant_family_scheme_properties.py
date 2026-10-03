"""Property-based tests: each family that claims Council Tax Reduction is
assessed under its own scheme and its own non-dependant exemption.

Where the household's rent is shared, every family liable for it claims, and
each claim follows the applicant's own circumstances. "Pensioner" is defined
per person and partner (SI 2012/2885 reg 3(1); SI 2012/2886 Sch para 3(2);
SI 2013/3029 reg 3(1); SSI 2021/249 reg 3; SSI 2012/319 reg 12). No
non-dependant deduction is made "if the applicant or his partner" is blind or
gets a listed disability benefit (SI 2012/2885 Sch 1 para 8(6); SI 2012/2886
Sch para 30(6); SI 2013/3029 Sch 1 para 3(6) and Sch 6 para 5(6); SSI
2021/249 reg 90(6); SSI 2012/319 reg 48(6)).

Invariants, for any generated population of households with a flagged head,
up to two sharer families and at most one non-dependant family. Every adult
here is 20 or over and the head is a claimant, so each family's applicant and
partner are its claimant and partner (the YAML cases cover a head who is
not):

1. Own members: a family is a pensioner exactly when its claimant or partner
   has reached State Pension age. It is exempt from non-dependant deductions
   exactly when its claimant or partner is blind or gets Attendance
   Allowance, the care component of Disability Living Allowance, the daily
   living component of Personal Independence Payment or Armed Forces
   Independence Payment.
2. As if alone: each family's pensioner status, exemption and whether its
   scheme is simulated are what they would be if it lived alone.
3. Scheme: a family's scheme is simulated exactly when it lives in Scotland
   or Wales, is a pensioner, or lives in a council whose working-age scheme
   is modelled. In England only a pensioner family is paid by the national
   pensioner scheme, and only a working-age family by a council's scheme.
4. Others do not matter: changing the ages and disability benefits of every
   other family that claims leaves a family's pensioner status, exemption,
   scheme and simulated award unchanged. Its council_tax_benefit is unchanged
   too, unless it falls back to a reported reduction and whether a simulated
   claim in its household pays something changes (property 5's
   reconciliation).
5. Fallback: a claiming family gets its simulated reduction where its scheme
   is simulated, and otherwise its reported one. Beside a simulated claim
   that pays something, a jointly liable claimant's reported reduction is
   limited to its share of the council tax; otherwise it is kept as reported. A
   family that cannot claim gets its reported reduction only where no claim
   in its household is simulated.
6. Bounds: a family that cannot claim gets no simulated reduction; a
   household whose simulated claims pay something never gets more than its
   council tax.
7. The exemption is the applicant's own: in a council's working-age scheme,
   giving one claiming family an exempting benefit removes the non-dependant
   deductions from its own reduction and leaves every other claim's
   deductions and award unchanged.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

YEAR = 2026
PROPERTY_SETTINGS = settings(
    max_examples=20,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
SCHEMES = [
    ("ENGLAND", "MAIDSTONE"),
    ("ENGLAND", "MERTON"),
    ("ENGLAND", "KINGSTON_UPON_THAMES"),
    ("ENGLAND", "NEWHAM"),
    ("ENGLAND", "WESTMINSTER"),
    ("ENGLAND", "OXFORD"),
    ("SCOTLAND", "CITY_OF_EDINBURGH"),
    ("WALES", "CARDIFF"),
]
MODELLED_WORKING_AGE_SCHEMES = {
    "MERTON",
    "KINGSTON_UPON_THAMES",
    "NEWHAM",
    "WESTMINSTER",
    "OXFORD",
}
LOCAL_SCHEMES = [
    "merton_council_tax_reduction",
    "kingston_upon_thames_council_tax_reduction",
    "newham_council_tax_reduction",
    "westminster_council_tax_reduction",
    "oxford_council_tax_reduction",
]
# Inputs that exempt the applicant from non-dependant deductions, as an
# annual amount (or a flag for blindness).
DISABILITY = {
    "attendance_allowance": 5_000,
    "dla_sc": 3_500,
    "pip_dl": 4_000,
    "armed_forces_independence_payment": 9_000,
    "is_blind": True,
}
# Ages of 20 or more are never presumed to be a child of the family, so
# changing them never changes who is a claimant or partner. The sampled values
# sit on both sides of State Pension age.
adult_age = st.one_of(
    st.sampled_from([20, 30, 45, 64, 65, 66, 67, 70, 85]), st.integers(20, 100)
)
disability = st.sampled_from([None, *DISABILITY])
money = st.floats(0, 40_000, allow_nan=False, allow_infinity=False)
reported = st.one_of(st.just(0.0), st.floats(0, 3_000, allow_nan=False))


@st.composite
def adults(draw, most):
    n = draw(st.integers(1, most))
    return dict(
        ages=draw(st.lists(adult_age, min_size=n, max_size=n)),
        disabilities=draw(st.lists(disability, min_size=n, max_size=n)),
        earnings=draw(st.lists(money, min_size=n, max_size=n)),
    )


@st.composite
def family(draw, role):
    # A non-dependant here is one adult with no children.
    alone = role == "non_dependant"
    return dict(
        role=role,
        child_age=None if alone else draw(st.one_of(st.none(), st.integers(0, 15))),
        reported=draw(reported),
        **draw(adults(1 if alone else 2)),
    )


@st.composite
def households(draw):
    families = [draw(family("head"))]
    families += [draw(family("sharer")) for _ in range(draw(st.integers(0, 2)))]
    if draw(st.booleans()):
        families.append(draw(family("non_dependant")))
    claimants = sum(f["role"] != "non_dependant" for f in families)
    return dict(
        families=families,
        scheme=draw(st.sampled_from(SCHEMES)),
        council_tax=draw(st.floats(0, 4_000, allow_nan=False)),
        rent=draw(money),
        savings=draw(st.floats(0, 20_000, allow_nan=False)),
        target=draw(st.integers(0, claimants - 1)),
        # Replacement circumstances for the other families that claim.
        other_ages=draw(st.lists(adult_age, min_size=6, max_size=6)),
        other_disabilities=draw(st.lists(disability, min_size=6, max_size=6)),
    )


population = st.lists(households(), min_size=1, max_size=6)


def person(age, disability_input, earnings):
    attributes = {"age": age, "employment_income": earnings}
    if disability_input is not None:
        attributes[disability_input] = DISABILITY[disability_input]
    return attributes


def build(population, alone=False, perturb_others=False):
    """One situation for the whole population, plus per-family facts.

    alone: put every family in a household of its own, as its head.
    perturb_others: give every family that claims, other than each
    household's target, the household's replacement ages and disabilities.
    """
    people, benunits, homes = {}, {}, {}
    facts = dict(country=[], local_authority=[], role=[], target=[], house=[])
    for h, house in enumerate(population):
        country, local_authority = house["scheme"]
        home = dict(
            country=country,
            local_authority=local_authority,
            council_tax=house["council_tax"],
            rent=house["rent"],
            tenure_type="RENT_PRIVATELY",
            savings=house["savings"],
        )
        members, replacement = [], 0
        for f, fam in enumerate(house["families"]):
            ids = []
            claims = fam["role"] != "non_dependant"
            is_target = claims and f == house["target"]
            for i, age in enumerate(fam["ages"]):
                pid = f"h{h}_f{f}_adult_{i}"
                disability_input = fam["disabilities"][i]
                if perturb_others and claims and not is_target:
                    age = house["other_ages"][replacement]
                    disability_input = house["other_disabilities"][replacement]
                    replacement += 1
                people[pid] = person(age, disability_input, fam["earnings"][i])
                if i == 0:
                    people[pid]["council_tax_benefit_reported"] = fam["reported"]
                people[pid]["is_household_head"] = (
                    alone or fam["role"] == "head"
                ) and i == 0
                ids.append(pid)
            if fam["child_age"] is not None:
                pid = f"h{h}_f{f}_child"
                people[pid] = {"age": fam["child_age"], "is_household_head": False}
                ids.append(pid)
            benunits[f"h{h}_f{f}"] = {
                "members": ids,
                "liable_for_share_of_household_rent": fam["role"] == "sharer"
                and not alone,
                "claims_all_entitled_benefits": True,
                "would_claim_uc": True,
            }
            if alone:
                homes[f"h{h}_f{f}"] = {"members": ids, **home}
            members.extend(ids)
            facts["country"].append(country)
            facts["local_authority"].append(local_authority)
            facts["role"].append(fam["role"])
            facts["target"].append(is_target)
            facts["house"].append(h)
        if not alone:
            homes[f"h{h}"] = {"members": members, **home}
    situation = {
        group: {
            name: {
                key: value if key == "members" else {YEAR: value}
                for key, value in entity.items()
            }
            for name, entity in entities.items()
        }
        for group, entities in (
            ("people", people),
            ("benunits", benunits),
            ("households", homes),
        )
    }
    return situation, {k: np.array(v) for k, v in facts.items()}


def calc(simulation, variable, map_to=None):
    return np.asarray(simulation.calculate(variable, YEAR, map_to=map_to))


def any_in_benunit(simulation, person_values):
    return simulation.map_result(person_values.astype(float), "person", "benunit") > 0


FLAGS = [
    "council_tax_reduction_pensioner",
    "council_tax_reduction_applicant_has_non_dep_exemption",
    "council_tax_reduction_scheme_supported",
]


@PROPERTY_SETTINGS
@given(population)
def test_scheme_follows_own_family(population):
    situation, facts = build(population)
    sim = Simulation(situation=situation)
    pensioner = calc(sim, "council_tax_reduction_pensioner")
    exempt = calc(sim, "council_tax_reduction_applicant_has_non_dep_exemption")
    supported = calc(sim, "council_tax_reduction_scheme_supported")
    claimant = calc(sim, "council_tax_reduction_claimant_benunit")

    # 1. Own members.
    claimant_or_partner = calc(sim, "is_claimant_or_partner")
    assert np.array_equal(
        pensioner,
        any_in_benunit(sim, claimant_or_partner & calc(sim, "is_SP_age")),
    )
    exempting = calc(sim, "is_blind").astype(bool)
    for variable in DISABILITY:
        if variable != "is_blind":
            exempting |= calc(sim, variable) > 0
    assert np.array_equal(exempt, any_in_benunit(sim, claimant_or_partner & exempting))

    # 2. As if alone.
    alone_situation, alone_facts = build(population, alone=True)
    alone = Simulation(situation=alone_situation)
    assert np.array_equal(alone_facts["role"], facts["role"])
    for variable in FLAGS:
        assert np.array_equal(calc(sim, variable), calc(alone, variable)), variable

    # 3. Scheme.
    england = facts["country"] == "ENGLAND"
    modelled = np.isin(facts["local_authority"], list(MODELLED_WORKING_AGE_SCHEMES))
    assert np.array_equal(supported, ~england | pensioner | modelled)
    simulated = calc(sim, "simulated_council_tax_reduction_benunit")
    local = sum(calc(sim, variable) for variable in LOCAL_SCHEMES)
    national = simulated - local
    assert not np.any((national > 0.005) & england & ~pensioner)
    assert not np.any((local > 0.005) & pensioner)
    assert not np.any((local > 0.005) & ~england)

    # 5. Fallback.
    benefit = calc(sim, "council_tax_benefit")
    reported_amount = calc(sim, "council_tax_benefit_reported", map_to="benunit")
    share = calc(sim, "council_tax_reduction_joint_liability_share")
    # Index households directly: map_to splits a household value among members.
    house = facts["house"]
    bill = calc(sim, "council_tax")[house]
    simulates = calc(sim, "council_tax_reduction_household_has_simulated_claim")
    household_simulates = simulates[house].astype(bool)
    paid = np.bincount(house, weights=(claimant & supported) * simulated)
    household_pays = paid[house] > 0
    expected = np.where(
        claimant,
        np.where(
            supported,
            simulated,
            np.where(
                household_pays & (share < 1),
                np.minimum(reported_amount, bill * share),
                reported_amount,
            ),
        ),
        np.where(household_simulates, 0, reported_amount),
    )
    np.testing.assert_allclose(benefit, expected, atol=0.01)
    simulated_claims = np.bincount(house, weights=claimant & supported)
    assert np.array_equal(simulates.astype(bool), simulated_claims > 0)

    # 6. Bounds.
    assert np.all(simulated[~claimant] == 0)
    household_reduction = calc(sim, "council_tax_reduction")
    over = household_reduction > calc(sim, "council_tax") + 0.01
    assert not np.any(over & (paid > 0))


@PROPERTY_SETTINGS
@given(population)
def test_other_families_do_not_change_a_claim(population):
    situation, facts = build(population)
    perturbed_situation, _ = build(population, perturb_others=True)
    before = Simulation(situation=situation)
    after = Simulation(situation=perturbed_situation)
    target = facts["target"]
    # 4. Others do not matter.
    for variable in FLAGS + LOCAL_SCHEMES:
        assert np.array_equal(
            calc(before, variable)[target], calc(after, variable)[target]
        ), variable
    for variable in (
        "council_tax_reduction_joint_liability_share",
        "simulated_council_tax_reduction_benunit",
    ):
        np.testing.assert_allclose(
            calc(before, variable)[target],
            calc(after, variable)[target],
            atol=1e-6,
            err_msg=variable,
        )
    # A reported fallback is reconciled against the household's paid
    # simulated claims (property 5); compare it wherever that is the same.
    house = facts["house"]
    supported = calc(before, "council_tax_reduction_scheme_supported").astype(bool)

    def household_pays(sim_):
        claims = calc(sim_, "council_tax_reduction_claimant_benunit").astype(bool)
        supported_ = calc(sim_, "council_tax_reduction_scheme_supported").astype(bool)
        simulated = calc(sim_, "simulated_council_tax_reduction_benunit")
        paid = np.bincount(house, weights=(claims & supported_) * simulated)
        return paid[house] > 0

    same_reconciliation = household_pays(before) == household_pays(after)
    compare = target & (supported | same_reconciliation)
    np.testing.assert_allclose(
        calc(before, "council_tax_benefit")[compare],
        calc(after, "council_tax_benefit")[compare],
        atol=1e-6,
        err_msg="council_tax_benefit",
    )


@st.composite
def shared_council_homes(draw):
    """A working-age head and sharer under one council's scheme, with a
    non-dependant in remunerative work, and an exempting benefit for one of
    the two claimants."""
    return dict(
        local_authority=draw(st.sampled_from(sorted(MODELLED_WORKING_AGE_SCHEMES))),
        ages=draw(st.lists(st.integers(20, 60), min_size=2, max_size=2)),
        non_dependant_age=draw(st.integers(20, 60)),
        non_dependant_earnings=draw(st.floats(10_000, 60_000, allow_nan=False)),
        council_tax=draw(st.floats(1_000, 4_000, allow_nan=False)),
        exempt_family=draw(st.sampled_from([0, 1])),
        disability=draw(st.sampled_from(sorted(DISABILITY))),
    )


def council_situation(homes, with_disability):
    people, benunits, households = {}, {}, {}
    for h, home in enumerate(homes):
        ids = []
        for f, age in enumerate(home["ages"]):
            pid = f"h{h}_claimant_{f}"
            disability_input = (
                home["disability"]
                if with_disability and f == home["exempt_family"]
                else None
            )
            people[pid] = person(age, disability_input, 0)
            people[pid]["is_household_head"] = f == 0
            benunits[f"h{h}_f{f}"] = {
                "members": [pid],
                "liable_for_share_of_household_rent": f == 1,
                "claims_all_entitled_benefits": True,
                "would_claim_uc": False,
            }
            ids.append(pid)
        pid = f"h{h}_non_dependant"
        people[pid] = person(
            home["non_dependant_age"], None, home["non_dependant_earnings"]
        )
        people[pid].update(is_household_head=False, weekly_hours=37.5)
        benunits[f"h{h}_f2"] = {"members": [pid], "would_claim_uc": False}
        ids.append(pid)
        households[f"h{h}"] = dict(
            members=ids,
            country="ENGLAND",
            local_authority=home["local_authority"],
            council_tax=home["council_tax"],
            rent=12_000,
            tenure_type="RENT_PRIVATELY",
            savings=0,
        )
    return {
        group: {
            name: {
                key: value if key == "members" else {YEAR: value}
                for key, value in entity.items()
            }
            for name, entity in entities.items()
        }
        for group, entities in (
            ("people", people),
            ("benunits", benunits),
            ("households", households),
        )
    }


@PROPERTY_SETTINGS
@given(st.lists(shared_council_homes(), min_size=1, max_size=6))
def test_exemption_is_the_applicants_own(homes):
    without = Simulation(situation=council_situation(homes, with_disability=False))
    with_ = Simulation(situation=council_situation(homes, with_disability=True))
    # Benefit units run head, sharer, non-dependant in each household.
    family = np.tile([0, 1, 2], len(homes))
    exempt_family = np.repeat([home["exempt_family"] for home in homes], 3)
    exempted = family == exempt_family
    other = (family < 2) & ~exempted
    variables = [v + "_non_dep_deductions" for v in LOCAL_SCHEMES]

    def total(sim_, names):
        return sum(calc(sim_, name) for name in names)

    before_deductions = total(without, variables)
    after_deductions = total(with_, variables)
    # 7. The non-dependant is deducted from both claims without the benefit,
    # so the test is not vacuous.
    assert np.all(before_deductions[family < 2] > 0)
    flag = "council_tax_reduction_applicant_has_non_dep_exemption"
    assert not np.any(calc(without, flag)[family < 2])
    assert np.array_equal(calc(with_, flag)[family < 2], exempted[family < 2])
    assert np.all(after_deductions[exempted] == 0)
    np.testing.assert_allclose(
        after_deductions[other], before_deductions[other], atol=1e-6
    )
    for name in LOCAL_SCHEMES + ["council_tax_benefit"]:
        np.testing.assert_allclose(
            calc(with_, name)[other], calc(without, name)[other], atol=1e-6
        )
