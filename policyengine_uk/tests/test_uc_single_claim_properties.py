"""Property-based tests for a Universal Credit claim by a member of a couple as
a single person (UC Regs 2013 reg. 3(3)).

Where the other member of a couple cannot be a joint claimant, the member
who can claims as a single person, and "regulations 18 (capital limit), 36
(amount of elements) and 22 (deduction of income and work allowance) provide
for the calculation of the award" (reg. 3(3)).

Each generated family is a couple, with up to two children, earnings,
pension income, limited capability for work and work-related activity,
caring, PIP, private or social rent, in or outside London. The same people
are calculated three ways: as a single claim with the second adult flagged
`uc_is_ineligible_partner`, as joint claimants (no flag), and as the
claimant alone with the children ("solo"). Invariants:

1. Standard allowance (reg. 36(3)): the single claimant's amount at the
   claimant's own age, whatever the partner's age.
2. Maximum amount (regs. 36(3), 27(1), 29(1); Sch 4 paras 9(2)(b), 10, 28
   and 29): the single claim's maximum amount equals the solo claimant's.
   The partner adds no standard allowance, LCWRA or carer element and no
   bedroom, is not a non-dependant, and neither their age nor their PIP
   changes the shared accommodation test.
3. Deduction (reg. 22(3)): earned and unearned income, and so the reg. 22(1)
   amount, equal the joint claimants'. That includes the work allowance,
   which joint claimants have where either has limited capability for work.
   No one is self-employed, so the minimum income floor (reg. 62, with
   reg. 90(3)(b) for this case) is not engaged.
4. Capital (reg. 18(2)): the single claim's capital equals the joint
   claimants', and the sum of each member's capital calculated alone, the
   other member's Lifetime ISA included.
5. Benefit cap: in families whose children are all under 16, the
   single-claimant rate applies exactly when there is no child (reg. 80A(2);
   a 16 or 17-year-old is a qualifying young person only in qualifying
   education, which the generator leaves unset). The other member's
   disability benefits, LCWRA, caring, AFCS and contributory ESA lift no cap
   (reg. 83(1)), so both cap exceptions equal the joint claimants' with those
   removed. The model takes any contributory ESA as including the support
   component (reg. 83(1)(a) needs the support component); that proxy is the
   model's, not this change's. The second exception is also met where
   Housing Benefit falls under the pension-age regulations, which the model
   applies to a family with a member over the qualifying age for State
   Pension Credit and no Universal Credit award. Whether there is an award
   can differ between the single claim and the stripped calculation, either
   way round. The single claim has a single claimant's amounts (reg. 36(3))
   and still counts the other member's income, such as contributory ESA
   (reg. 22(3)), so its award can be the lower. It also keeps the work
   allowance the other member's limited capability gives (reg. 22(3)),
   which stripping removes, so its award can be the higher. So each
   calculation's second exception is checked against its own inputs (the
   route as that calculation gives it, or a claimant's AFCS or contributory
   ESA), and the two are compared only for families the pension-age route
   reaches in neither (see off_pension_age_route).
6. Regulation 3(3)(a): with the flag left to its formula, a member of a
   couple under 18 is the ineligible partner exactly when none of the
   generated regulation 8(1) circumstances applies to them (limited
   capability for work and work-related activity, 35 hours of caring, or a
   child under 16 in the family), or they are under 16; the other member
   then claims as a single person.
7. A flag that marks no single claim (a single adult, or both members of a
   couple) leaves every rule Housing Benefit shares (the cap rate, the cap
   exceptions, the shared accommodation test) as it was without the flag.
   Such a flag leaves no one able to claim Universal Credit, so for the
   second cap exception each calculation is again checked against its own
   inputs, and families on the pension-age route in either calculation are
   left out of the comparison (see off_pension_age_route).

Each property also runs on EXAMPLE_FAMILIES, built so that the cases the
properties are about occur, each in a family of its own: an other member
with LCWRA and PIP, with caring, with AFCS, with contributory ESA; a
claimant with LCWRA, with caring, with AFCS; a private renter under 35; a
claimant under 25 with an older partner; an older partner; children under
and over 16; ADM E2017's Tom and Jane. LCWRA and caring are never in the
same person, since reg. 29(4) then gives only the LCWRA element, which the
model does not yet apply. test_examples_reach_the_cases checks that each
case changes the result it should, against the joint claimants or the
claimant alone.

Marriage Allowance is switched off throughout: a transfer moves tax between
the partners, which is not what these invariants are about.
"""

import numpy as np
import copy

from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

PROPERTY_SETTINGS = settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
# 2021: the old LCWRA amount and work allowances. 2025 and 2026: the fiscal
# years either side of the Universal Credit Act 2025 changes to the LCWRA
# element and the standard allowance.
YEARS = [2021, 2025, 2026]
REGIONS = ["LONDON", "NORTH_EAST", "WALES", "SCOTLAND"]
TENURES = ["RENT_FROM_COUNCIL", "RENT_PRIVATELY"]
rarely = st.integers(0, 4).map(lambda n: n == 0)
employment = st.one_of(st.just(0.0), st.floats(0, 30_000))
pension = st.one_of(st.just(0.0), st.floats(0, 5_000))
pip = st.one_of(st.just(0.0), st.just(0.0), st.floats(1_000, 6_000))
sometimes_paid = st.one_of(st.just(0.0), st.just(0.0), st.floats(500, 5_000))
care = st.sampled_from([0, 0, 0, 35])

# Inputs that describe the other member's own disability, caring and
# benefits, with the value that removes each: what reg. 83(1) and regs. 27
# and 29 ignore for a non-claimant.
PARTNER_OWN = {
    "uc_limited_capability_for_WRA": False,
    "care_hours": 0,
    "pip_dl": 0.0,
    "afcs": 0.0,
    "esa_contrib": 0.0,
}


@st.composite
def adult(draw, ages):
    return dict(
        age=draw(ages),
        employment_income=draw(employment),
        private_pension_income=draw(pension),
        uc_limited_capability_for_WRA=draw(rarely),
        care_hours=draw(care),
        pip_dl=draw(pip),
        afcs=draw(sometimes_paid),
        esa_contrib=draw(sometimes_paid),
    )


@st.composite
def couples(draw):
    return dict(
        claimant=draw(adult(st.integers(18, 64))),
        partner=draw(adult(st.integers(18, 80))),
        children=[draw(st.integers(0, 17)) for _ in range(draw(st.integers(0, 2)))],
        rent=draw(st.one_of(st.just(0.0), st.floats(1_000, 15_000))),
        tenure=draw(st.sampled_from(TENURES)),
        region=draw(st.sampled_from(REGIONS)),
    )


populations = st.lists(couples(), min_size=1, max_size=6)


def adult_inputs(age, **inputs):
    values = dict(
        age=age,
        employment_income=0.0,
        private_pension_income=0.0,
        uc_limited_capability_for_WRA=False,
        care_hours=0,
        pip_dl=0.0,
        afcs=0.0,
        esa_contrib=0.0,
    )
    values.update(inputs)
    return values


def example_families():
    """Families in which every case the properties cover occurs.

    The order is EXAMPLE_INDEX's.
    """
    return [
        # A claimant under 25, a private renter, with an older other member
        # who has LCWRA, PIP and a private pension.
        dict(
            claimant=adult_inputs(22, employment_income=6_000.0),
            partner=adult_inputs(
                40,
                uc_limited_capability_for_WRA=True,
                pip_dl=4_000.0,
                private_pension_income=1_200.0,
            ),
            children=[],
            rent=9_000.0,
            tenure="RENT_PRIVATELY",
            region="NORTH_EAST",
        ),
        # A claimant with LCWRA, a child under 16, social rent.
        dict(
            claimant=adult_inputs(30, uc_limited_capability_for_WRA=True),
            partner=adult_inputs(30, employment_income=12_000.0),
            children=[4],
            rent=6_000.0,
            tenure="RENT_FROM_COUNCIL",
            region="LONDON",
        ),
        # An other member over State Pension age; children under and over 16.
        dict(
            claimant=adult_inputs(45, employment_income=8_000.0),
            partner=adult_inputs(70, pip_dl=3_000.0),
            children=[10, 16],
            rent=12_000.0,
            tenure="RENT_PRIVATELY",
            region="WALES",
        ),
        # ADM E2017's example: Tom, 19, and Jane, 17, with no regulation 8
        # circumstance.
        dict(
            claimant=adult_inputs(19),
            partner=adult_inputs(17),
            children=[],
            rent=4_000.0,
            tenure="RENT_FROM_COUNCIL",
            region="SCOTLAND",
        ),
        # An other member who cares 35 hours a week, without LCWRA.
        dict(
            claimant=adult_inputs(33),
            partner=adult_inputs(35, care_hours=35),
            children=[],
            rent=5_000.0,
            tenure="RENT_FROM_COUNCIL",
            region="NORTH_EAST",
        ),
        # A claimant who cares 35 hours a week, without LCWRA.
        dict(
            claimant=adult_inputs(28, care_hours=35),
            partner=adult_inputs(28),
            children=[],
            rent=5_000.0,
            tenure="RENT_FROM_COUNCIL",
            region="NORTH_EAST",
        ),
        # An other member with an AFCS payment and nothing else.
        dict(
            claimant=adult_inputs(40),
            partner=adult_inputs(40, afcs=1_000.0),
            children=[],
            rent=0.0,
            tenure="RENT_FROM_COUNCIL",
            region="NORTH_EAST",
        ),
        # An other member with contributory ESA and nothing else.
        dict(
            claimant=adult_inputs(40),
            partner=adult_inputs(40, esa_contrib=2_000.0),
            children=[],
            rent=0.0,
            tenure="RENT_FROM_COUNCIL",
            region="NORTH_EAST",
        ),
        # A claimant with an AFCS payment and nothing else.
        dict(
            claimant=adult_inputs(40, afcs=1_000.0),
            partner=adult_inputs(40),
            children=[],
            rent=0.0,
            tenure="RENT_FROM_COUNCIL",
            region="NORTH_EAST",
        ),
    ]


EXAMPLE_INDEX = dict(
    young_renter=0,
    lcwra_claimant=1,
    older_partner=2,
    tom_and_jane=3,
    carer_partner=4,
    carer_claimant=5,
    afcs_partner=6,
    esa_partner=7,
    afcs_claimant=8,
)
EXAMPLE_FAMILIES = example_families()


def situation(families, year, mode):
    """One simulation holding every family.

    ``mode`` is "single" (the partner flagged), "joint" (no flag), "solo"
    (no partner), "stripped" (joint, with the partner's own disability,
    caring and benefits removed), "both" (both members flagged),
    "single_adult_flagged" (the claimant alone, flagged) or "derived" (the
    flag left to its formula).
    """
    people, benunits, households = {}, {}, {}
    for i, family in enumerate(families):
        names = []
        adults = [("claimant", family["claimant"])]
        if mode not in ("solo", "single_adult_flagged"):
            adults.append(("partner", family["partner"]))
        for role, inputs in adults:
            name = f"{role}{i}"
            person = {k: {year: v} for k, v in inputs.items()}
            person["is_claimant_or_partner"] = {year: True}
            person["would_claim_marriage_allowance"] = {year: False}
            if role == "partner":
                if mode in ("single", "both"):
                    person["uc_is_ineligible_partner"] = {year: True}
                elif mode == "stripped":
                    for variable, removed in PARTNER_OWN.items():
                        person[variable] = {year: removed}
            if role == "claimant" and mode in ("both", "single_adult_flagged"):
                person["uc_is_ineligible_partner"] = {year: True}
            if mode in ("joint", "solo", "stripped"):
                person["uc_is_ineligible_partner"] = {year: False}
            people[name] = person
            names.append(name)
        for k, age in enumerate(family["children"]):
            name = f"child{i}_{k}"
            people[name] = {
                "age": {year: age},
                "is_claimant_or_partner": {year: False},
            }
            names.append(name)
        benunits[f"b{i}"] = {"members": names}
        households[f"h{i}"] = {
            "members": names,
            "rent": {year: family["rent"]},
            "tenure_type": {year: family["tenure"]},
            "region": {year: family["region"]},
        }
    return {"people": people, "benunits": benunits, "households": households}


BENUNIT_VARIABLES = [
    "uc_member_of_couple_claims_as_single_person",
    "uc_standard_allowance",
    "uc_maximum_amount",
    "uc_earned_income",
    "uc_unearned_income",
    "uc_income_reduction",
    "uc_assessable_capital",
    "uc_LCWRA_element",
    "uc_carer_element",
    "uc_housing_costs_element",
    "is_uc_eligible",
    "is_uc_work_allowance_eligible",
    "is_benefit_cap_single_claimant_rate",
    "is_benefit_cap_exempt_health_disability",
    "is_benefit_cap_exempt_other",
    "is_lha_shared_accommodation_rate_specified_renter",
    "housing_benefit_pension_age_regulations_apply",
]
PENSION_AGE_ROUTE = "housing_benefit_pension_age_regulations_apply"


def off_pension_age_route(*calculations):
    """The families that no calculation puts on the pension-age route.

    is_benefit_cap_exempt_other also lifts the cap where Housing Benefit falls
    under the pension-age regulations (HB (SPC) Regs 2006 reg. 5; the cap's
    age exception, SI 2014/1230 reg. 60C). The model takes that route for a
    family with a claimant or partner over the qualifying age for State
    Pension Credit and no Universal Credit award. Whether there is an award
    can differ between the calculations, either way round: a single claim has
    a single claimant's amounts (reg. 36(3)) but the joint claimants' income
    and work allowance (reg. 22(3)), and a flag on both members leaves no one
    who can claim. So comparisons of that exception across calculations exclude the
    families the route reaches in any of them. Within each calculation the
    route lifts the cap wherever it applies.
    """
    for values in calculations:
        assert np.all(values["is_benefit_cap_exempt_other"][values[PENSION_AGE_ROUTE]])
    return ~np.logical_or.reduce([values[PENSION_AGE_ROUTE] for values in calculations])


def exempt_other_from_inputs(families, values, members):
    """is_benefit_cap_exempt_other as the inputs give it, with no mask.

    The pension-age route as the same calculation gives it (taken from the
    model; test_benefit_cap_and_ctr_pension_age_properties.py and
    benefit_cap_pension_age.yaml test the route itself), or AFCS or
    contributory ESA of one of ``members`` (reg. 83(1)(a) and (e); the model
    takes any contributory ESA as including the support component). ``members`` are the people whose own benefits
    count: the claimant alone on a single claim, in a stripped calculation
    (the other member's benefits removed) or with no partner, and both
    members of a couple neither of whom is excluded.
    """
    own = np.array(
        [
            any(
                family[member]["afcs"] > 0 or family[member]["esa_contrib"] > 0
                for member in members
            )
            for family in families
        ]
    )
    return values[PENSION_AGE_ROUTE] | own


def calculate(families, year, mode, extra=()):
    sim = Simulation(situation=situation(families, year, mode))
    values = {v: np.asarray(sim.calculate(v, year)) for v in BENUNIT_VARIABLES}
    values["claimant_type"] = np.asarray(
        sim.calculate("uc_standard_allowance_claimant_type", year)
    ).astype(str)
    for v in extra:
        values[v] = np.asarray(sim.calculate(v, year))
    values["parameters"] = sim.tax_benefit_system.parameters(f"{year}-01-01")
    return values


def single_amount(families, year, parameters):
    p = parameters.gov.dwp.universal_credit.standard_allowance
    threshold = p.claimant_type.age_threshold
    return np.array(
        [
            12
            * (
                p.amount.SINGLE_OLD
                if family["claimant"]["age"] >= threshold
                else p.amount.SINGLE_YOUNG
            )
            for family in families
        ]
    )


@PROPERTY_SETTINGS
@given(families=populations, year=st.sampled_from(YEARS))
@example(families=example_families(), year=2026)
def test_single_standard_allowance_at_the_claimants_own_age(families, year):
    single = calculate(families, year, "single")
    assert np.all(single["uc_member_of_couple_claims_as_single_person"]), families
    assert np.all(np.char.startswith(single["claimant_type"], "SINGLE")), families
    np.testing.assert_allclose(
        single["uc_standard_allowance"],
        single_amount(families, year, single["parameters"]),
        atol=0.01,
        err_msg=str(families),
    )


@PROPERTY_SETTINGS
@given(families=populations, year=st.sampled_from(YEARS))
@example(families=example_families(), year=2026)
@example(families=example_families(), year=2021)
def test_maximum_amount_is_the_solo_claimants(families, year):
    single = calculate(families, year, "single")
    solo = calculate(families, year, "solo")
    # Capital is nil, so both are eligible exactly when the claimant is.
    np.testing.assert_array_equal(single["is_uc_eligible"], solo["is_uc_eligible"])
    for variable in [
        "uc_maximum_amount",
        "uc_standard_allowance",
        "uc_LCWRA_element",
        "uc_carer_element",
        "uc_housing_costs_element",
        "is_lha_shared_accommodation_rate_specified_renter",
    ]:
        np.testing.assert_allclose(
            single[variable],
            solo[variable],
            atol=0.01,
            err_msg=f"{variable}: {families}",
        )


@PROPERTY_SETTINGS
@given(families=populations, year=st.sampled_from(YEARS))
@example(families=example_families(), year=2026)
def test_deduction_is_the_joint_claimants(families, year):
    single = calculate(families, year, "single")
    joint = calculate(families, year, "joint")
    for variable in [
        "uc_earned_income",
        "uc_unearned_income",
        "is_uc_work_allowance_eligible",
    ]:
        np.testing.assert_allclose(
            single[variable],
            joint[variable],
            atol=0.01,
            err_msg=f"{variable}: {families}",
        )
    rate = single["parameters"].gov.dwp.universal_credit.means_test.reduction_rate
    reg_22_amount = rate * joint["uc_earned_income"] + joint["uc_unearned_income"]
    eligible = single["is_uc_eligible"].astype(bool)
    np.testing.assert_allclose(
        single["uc_income_reduction"][eligible],
        np.minimum(single["uc_maximum_amount"], reg_22_amount)[eligible],
        atol=0.01,
        err_msg=str(families),
    )


@PROPERTY_SETTINGS
@given(
    families=populations,
    year=st.sampled_from([2021, 2026]),
    balances=st.lists(st.floats(0, 30_000), min_size=18, max_size=18),
)
@example(
    families=example_families(),
    year=2026,
    balances=[8_000.0, 16_000.0, 0.0, 30_000.0, 2_000.0, 0.0] + [5_000.0] * 12,
)
def test_capital_includes_the_other_members(families, year, balances):
    families = copy.deepcopy(families)
    for i, family in enumerate(families):
        family["claimant"]["lifetime_isa_balance"] = balances[2 * i]
        family["partner"]["lifetime_isa_balance"] = balances[2 * i + 1]
    single = calculate(families, year, "single")
    joint = calculate(families, year, "joint")
    claimant_alone = calculate(families, year, "solo")
    partner_alone = calculate(
        [dict(family, claimant=family["partner"]) for family in families],
        year,
        "solo",
    )
    np.testing.assert_allclose(
        single["uc_assessable_capital"],
        joint["uc_assessable_capital"],
        atol=0.01,
        err_msg=str(families),
    )
    # Differential: the other member's capital is the same amount it is when
    # they are calculated alone, so leaving it out in both the single and
    # joint calculations would fail here.
    np.testing.assert_allclose(
        single["uc_assessable_capital"],
        claimant_alone["uc_assessable_capital"]
        + partner_alone["uc_assessable_capital"],
        atol=0.01,
        err_msg=str(families),
    )


@PROPERTY_SETTINGS
@given(families=populations, year=st.sampled_from(YEARS))
@example(families=example_families(), year=2026)
def test_benefit_cap_rate_and_exceptions(families, year):
    single = calculate(families, year, "single")
    stripped = calculate(families, year, "stripped")
    # Reg. 80A(2): the single-claimant limit unless responsible for a child
    # or qualifying young person. A 16 or 17-year-old is a qualifying young
    # person only in qualifying education, which the generator leaves
    # unset, so the oracle is read only for families without one.
    no_children = np.array([not family["children"] for family in families])
    under_16_only = np.array(
        [all(age < 16 for age in family["children"]) for family in families]
    )
    np.testing.assert_array_equal(
        single["is_benefit_cap_single_claimant_rate"][under_16_only],
        no_children[under_16_only],
    )
    np.testing.assert_array_equal(
        single["is_benefit_cap_exempt_health_disability"],
        stripped["is_benefit_cap_exempt_health_disability"],
        err_msg=f"is_benefit_cap_exempt_health_disability: {families}",
    )
    for values in [single, stripped]:
        np.testing.assert_array_equal(
            values["is_benefit_cap_exempt_other"],
            exempt_other_from_inputs(families, values, ["claimant"]),
            err_msg=f"is_benefit_cap_exempt_other: {families}",
        )
    off_route = off_pension_age_route(single, stripped)
    np.testing.assert_array_equal(
        single["is_benefit_cap_exempt_other"][off_route],
        stripped["is_benefit_cap_exempt_other"][off_route],
        err_msg=f"is_benefit_cap_exempt_other: {families}",
    )


@PROPERTY_SETTINGS
@given(
    families=populations,
    year=st.sampled_from(YEARS),
    partner_ages=st.lists(st.integers(15, 20), min_size=6, max_size=6),
)
@example(
    families=example_families(),
    year=2026,
    partner_ages=[17, 17, 16, 17, 17, 16, 17, 17, 16],
)
def test_a_partner_under_18_outside_regulation_8_cannot_claim_jointly(
    families, year, partner_ages
):
    families = copy.deepcopy(families)
    for family, age in zip(families, partner_ages):
        family["partner"]["age"] = age
    sim = Simulation(situation=situation(families, year, "derived"))
    claims_as_single = np.asarray(
        sim.calculate("uc_member_of_couple_claims_as_single_person", year)
    )
    names = list(situation(families, year, "derived")["people"])
    ineligible = dict(
        zip(names, np.asarray(sim.calculate("uc_is_ineligible_partner", year)))
    )
    for i, family in enumerate(families):
        partner = family["partner"]
        # Reg. 8(1)(a), (c) and (d), as generated: limited capability for work
        # (the LCWRA flag), 35 hours of caring, responsibility for a child
        # (under 16, WRA 2012 s. 40). Reg. 3(3)(a): under 18 and outside
        # reg. 8; the model also takes anyone under 16.
        regulation_8 = (
            partner["uc_limited_capability_for_WRA"]
            or partner["care_hours"] >= 35
            or any(age < 16 for age in family["children"])
        )
        expected = partner["age"] < 16 or (partner["age"] < 18 and not regulation_8)
        assert ineligible[f"partner{i}"] == expected, family
        # The claimant is 18 to 64, so never excluded, and can claim.
        assert not ineligible[f"claimant{i}"], family
        assert claims_as_single[i] == expected, family


@PROPERTY_SETTINGS
@given(families=populations, year=st.sampled_from(YEARS))
@example(families=example_families(), year=2026)
def test_a_flag_marking_no_single_claim_leaves_shared_rules_alone(families, year):
    shared = [
        "is_benefit_cap_single_claimant_rate",
        "is_benefit_cap_exempt_health_disability",
        "is_benefit_cap_exempt_other",
        "is_lha_shared_accommodation_rate_specified_renter",
    ]
    both = calculate(families, year, "both")
    joint = calculate(families, year, "joint")
    alone_flagged = calculate(families, year, "single_adult_flagged")
    solo = calculate(families, year, "solo")
    assert not np.any(both["uc_member_of_couple_claims_as_single_person"]), families
    assert not np.any(both["is_uc_eligible"]), families
    assert not np.any(alone_flagged["is_uc_eligible"]), families
    couple = ["claimant", "partner"]
    for values, members in [
        (both, couple),
        (joint, couple),
        (alone_flagged, ["claimant"]),
        (solo, ["claimant"]),
    ]:
        np.testing.assert_array_equal(
            values["is_benefit_cap_exempt_other"],
            exempt_other_from_inputs(families, values, members),
            err_msg=f"is_benefit_cap_exempt_other: {families}",
        )
    for flagged, unflagged in [(both, joint), (alone_flagged, solo)]:
        off_route = off_pension_age_route(flagged, unflagged)
        for variable in shared:
            compared = (
                off_route
                if variable == "is_benefit_cap_exempt_other"
                else np.ones_like(off_route)
            )
            np.testing.assert_array_equal(
                flagged[variable][compared],
                unflagged[variable][compared],
                err_msg=f"{variable}: {families}",
            )


def test_examples_reach_the_cases():
    """The example families exercise each rule: the single claim changes it."""
    year = 2026
    single = calculate(EXAMPLE_FAMILIES, year, "single")
    joint = calculate(EXAMPLE_FAMILIES, year, "joint")
    i = EXAMPLE_INDEX
    # Reg. 36(3): the claimant under 25 with a partner of 40.
    assert single["claimant_type"][i["young_renter"]] == "SINGLE_YOUNG"
    assert joint["claimant_type"][i["young_renter"]] == "COUPLE_OLD"
    # Reg. 27(1): the other member's LCWRA gives nothing; the claimant's does.
    family = i["young_renter"]
    assert single["uc_LCWRA_element"][family] == 0 < joint["uc_LCWRA_element"][family]
    assert single["uc_LCWRA_element"][i["lcwra_claimant"]] > 0
    # Reg. 29(1): the same for caring (no LCWRA in either carer, reg. 29(4)).
    family = i["carer_partner"]
    assert single["uc_carer_element"][family] == 0 < joint["uc_carer_element"][family]
    assert single["uc_carer_element"][i["carer_claimant"]] > 0
    # Reg. 83(1): the other member's LCWRA and PIP, AFCS or ESA lift the
    # joint claimants' cap only; the claimant's AFCS lifts it.
    family = i["young_renter"]
    assert not single["is_benefit_cap_exempt_health_disability"][family]
    assert joint["is_benefit_cap_exempt_health_disability"][family]
    for family in [i["afcs_partner"], i["esa_partner"]]:
        assert not single["is_benefit_cap_exempt_other"][family]
        assert joint["is_benefit_cap_exempt_other"][family]
        assert not single["is_benefit_cap_exempt_health_disability"][family]
        assert joint["is_benefit_cap_exempt_health_disability"][family]
    assert single["is_benefit_cap_exempt_other"][i["afcs_claimant"]]
    # Reg. 80A(2) and Sch 4 para 28(2): single rate and shared accommodation.
    family = i["young_renter"]
    assert single["is_benefit_cap_single_claimant_rate"][family]
    assert not joint["is_benefit_cap_single_claimant_rate"][family]
    assert single["is_lha_shared_accommodation_rate_specified_renter"][family]
    assert not joint["is_lha_shared_accommodation_rate_specified_renter"][family]
    # Reg. 22(3): the other member's LCW gives the work allowance either way.
    assert single["is_uc_work_allowance_eligible"][family]
