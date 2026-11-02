"""Universal Credit carer-element awards as a carer benefit.

HB Regs 2006 Sch 3 para 14(2)(a)(iii) and (b) (with the IS, JSA, ESA,
pension-age Housing Benefit and council tax reduction schedules) and SPC Regs
2002 Sch I para 1(1) and (4) withhold the severe disability premium and the
Pension Credit severe disability addition where someone "has an award of
universal credit which includes the carer element in respect of caring for"
the claimant or partner. Scotland's working-age council tax reduction (SSI
2021/249 Sch 1 paras 5 and 6(1)(c), from 1 April 2022) pays the carer premium
to an applicant or partner with such an award.

The model reads the award from its conditions and an upper bound on it
(has_uc_award_with_carer_element, uc_award_upper_bound) for the severe
disability carer test, since the award itself reads Pension Credit, unless the
simulation stores the award. Scotland's carer premium reads the positive award
(receives_uc_carer_element), or from 1 April 2022 to 31 March 2025, when the
model counts a nil award as one with a value of zero, the award's conditions.
Each example simulates the households as drawn, and again with
has_uc_award_with_carer_element supplied as false for everyone, which leaves
receives_carer_benefit as the attribution's only source of carers.
carer_premium gives the Scottish premium's counterpart without the limb.

Invariants, on generated households under baseline law:

1. No change without a carer element: where no one has
   has_uc_award_with_carer_element or receives_uc_carer_element, the
   attribution, the severe disability premiums and the addition equal their
   values without the limb, and the Scottish premium equals carer_premium,
   exactly.
2. Never raises: no carer element raises the severe disability premium (the
   shared, council tax reduction and pension-age premiums) or the Pension
   Credit addition.
3. Never lowers, and only in Scotland: council_tax_reduction_carer_premium
   never falls below carer_premium, and differs from it only for a Scottish
   working-age family.
4. Bounds: the Scottish premium comes to a whole number of weekly amounts, at most
   the number of claimants and partners, and at most one where partners care
   for the same person; a person with both an allowance and a carer element
   counts once.
5. A nil bound leaves a nil award: uc_award_upper_bound >=
   universal_credit_pre_benefit_cap >= universal_credit for awards the
   model's formulas calculate, so receives_uc_carer_element implies
   has_uc_award_with_carer_element. That implication also holds where the
   simulation stores the award, which can exceed the bound.
6. Attribution: the attribution makes no one their own carer, everyone it
   counts as cared for meets Carer's Allowance's severe disability test, and
   no household has more people cared for than carers (carer benefit
   recipients and carer element holders).
7. No cycle: every reader calculates on one simulation, whichever the test
   requests first, and also where the simulation stores the award.
8. The bound reads neither the award nor Pension Credit: its trace reaches
   none of the award's steps, the non-dependant deduction or the attribution.
9. Endpoint parity: uc_award_upper_bound equals, exactly, the larger of two
   awards the model's own formulas calculate, one with non-dependant
   deductions supplied as nil and one with the housing costs element supplied
   as nil, at the rows test_upper_bound_matches_real_award_endpoints draws.
10. Every component: the bound reads each element of uc_maximum_amount in its
    order, and every input of the award's steps apart from the non-dependant
    deduction, the Tax-Free Childcare choice and the claim.

A reform that makes is_uc_eligible read Pension Credit would cycle through the
attribution, which reads eligibility; these tests do not cover reforms.
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

YEAR = 2026
WEEKS = 52
CARER_PREMIUM = 48.15
PROPERTY_SETTINGS = settings(
    max_examples=5,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)

SEVERE_READERS = (
    "severe_disability_premium",
    "severe_disability_premium_before_non_dependant_test",
    "council_tax_reduction_severe_disability_premium",
    "pension_age_severe_disability_premium",
    "severe_disability_minimum_guarantee_addition",
)
CARER_READERS = (
    "carer_premium",
    "council_tax_reduction_carer_premium",
    "council_tax_reduction_premiums",
)
BENUNIT_READERS = SEVERE_READERS + CARER_READERS
PERSON_READERS = (
    "is_cared_for_by_carer_benefit_recipient",
    "has_uc_award_with_carer_element",
    "receives_uc_carer_element",
)
# Every reader of the attribution or the carer element award, and the
# programmes that read them, for the cycle check.
ALL_READERS = BENUNIT_READERS + (
    "is_cared_for_by_carer_benefit_recipient",
    "has_uc_award_with_carer_element",
    "receives_uc_carer_element",
    "uc_award_upper_bound",
    "universal_credit",
    "pension_credit",
    "housing_benefit",
    "income_support",
    "council_tax_reduction",
    "household_net_income",
)


DISABILITY = {
    "none": {},
    "pip_standard": {"pip_dl_category": "STANDARD"},
    "aa_higher": {"aa_category": "HIGHER"},
    "dla_middle": {"dla_sc_category": "MIDDLE"},
}


@st.composite
def adult(draw, age):
    return dict(
        age=draw(age),
        disability=draw(st.sampled_from(["none", "none", "pip_standard", "aa_higher"])),
        blind=draw(st.sampled_from([False, False, True])),
        # Draw the qualifying hours with or without a Carer's Allowance claim:
        # DWP includes the Universal Credit carer element without a claim and
        # above the allowance's earnings limit (UC Regs 2013 reg 30(1)(a)(i)
        # and (2)).
        care_hours=draw(st.sampled_from([0, 35, 35])),
        would_claim_carers_allowance=draw(st.booleans()),
        earnings=draw(st.sampled_from([0, 0, 8_000, 25_000])),
    )


@st.composite
def benefit_unit(draw):
    # Working-age or pension-age adults, partners within ten years of each
    # other, so no adult reads as the other's child.
    eldest = draw(st.integers(20, 80))
    ages = st.integers(max(18, eldest - 10), eldest)
    adults = [draw(adult(st.just(eldest)))]
    adults += draw(st.lists(adult(ages), max_size=1))
    children = draw(
        st.lists(
            st.fixed_dictionaries(
                dict(
                    age=st.integers(0, 15),
                    disability=st.sampled_from(["none", "dla_middle"]),
                )
            ),
            max_size=1,
        )
    )
    return dict(adults=adults, children=children)


@st.composite
def households(draw):
    # DWP includes housing costs for renters and deducts an amount for each
    # non-dependant in another benefit unit. The upper bound leaves that
    # deduction out.
    tenure, rent = draw(
        st.sampled_from(
            [
                ("OWNED_OUTRIGHT", 0),
                ("RENT_PRIVATELY", 6_000),
                ("RENT_PRIVATELY", 12_000),
                ("RENT_FROM_COUNCIL", 6_000),
            ]
        )
    )
    return dict(
        country=draw(st.sampled_from(["ENGLAND", "SCOTLAND", "WALES"])),
        tenure=tenure,
        rent=rent,
        units=draw(st.lists(benefit_unit(), min_size=1, max_size=3)),
    )


def situation(population, without_limb=()):
    """One situation; households in without_limb have no carer element award."""
    people, benunits, hh = {}, {}, {}
    for h, household in enumerate(population):
        members = []
        for u, unit in enumerate(household["units"]):
            unit_members = []
            for a, p in enumerate(unit["adults"]):
                name = f"h{h}_u{u}_a{a}"
                people[name] = {
                    "age": {YEAR: p["age"]},
                    "is_blind": {YEAR: p["blind"]},
                    "care_hours": {YEAR: p["care_hours"]},
                    "would_claim_carers_allowance": {
                        YEAR: p["would_claim_carers_allowance"]
                    },
                    "employment_income": {YEAR: p["earnings"]},
                    "is_claimant_or_partner": {YEAR: True},
                    **{k: {YEAR: v} for k, v in DISABILITY[p["disability"]].items()},
                }
                if h in without_limb:
                    people[name]["has_uc_award_with_carer_element"] = {YEAR: False}
                unit_members.append(name)
            for c, p in enumerate(unit["children"]):
                name = f"h{h}_u{u}_c{c}"
                people[name] = {
                    "age": {YEAR: p["age"]},
                    "is_claimant_or_partner": {YEAR: False},
                    **{k: {YEAR: v} for k, v in DISABILITY[p["disability"]].items()},
                }
                unit_members.append(name)
            benunits[f"h{h}_u{u}"] = {"members": unit_members}
            members += unit_members
        hh[f"h{h}"] = {"members": members, "country": {YEAR: household["country"]}}
        if "tenure" in household:
            hh[f"h{h}"]["tenure_type"] = {YEAR: household["tenure"]}
            hh[f"h{h}"]["rent"] = {YEAR: household["rent"]}
    return {"people": people, "benunits": benunits, "households": hh}


def with_and_without_limb(population, variables):
    """Each variable for the households as drawn, and without the limb.

    Without the limb, a second simulation supplies
    has_uc_award_with_carer_element as false for everyone: a variable supplied
    for some people takes its default, not its formula, for the rest.
    """
    sim = Simulation(situation=situation(population))
    sim_without = Simulation(
        situation=situation(population, without_limb=range(len(population)))
    )
    return sim, {
        v: (
            np.asarray(sim.calculate(v, YEAR)),
            np.asarray(sim_without.calculate(v, YEAR)),
        )
        for v in variables
    }


def household_index(sim, entity):
    """The household each benefit unit or person belongs to, by position."""
    population = sim.populations[entity]
    names = population.ids
    return np.array([int(str(name).split("_")[0][1:]) for name in names])


def single(age=40, **inputs):
    return dict(
        dict(
            age=age,
            disability="none",
            blind=False,
            care_hours=0,
            would_claim_carers_allowance=False,
            earnings=0,
        ),
        **inputs,
    )


EXAMPLES = [
    # A blind carer's Universal Credit carer element, in another benefit
    # unit, bars the disabled person's premium.
    dict(
        country="ENGLAND",
        units=[
            dict(adults=[single(50, disability="pip_standard")], children=[]),
            dict(adults=[single(40, blind=True, care_hours=35)], children=[]),
        ],
    ),
    # The same carer earning enough to taper the award to nil.
    dict(
        country="ENGLAND",
        units=[
            dict(adults=[single(50, disability="pip_standard")], children=[]),
            dict(
                adults=[single(40, blind=True, care_hours=35, earnings=25_000)],
                children=[],
            ),
        ],
    ),
    # The Scottish carer of the issue, aged 40 with 35 hours and no claim.
    dict(country="SCOTLAND", units=[dict(adults=[single(care_hours=35)], children=[])]),
    # A Scottish couple, one claiming the allowance, both caring.
    dict(
        country="SCOTLAND",
        units=[
            dict(
                adults=[
                    single(45, care_hours=35),
                    single(40, care_hours=35, would_claim_carers_allowance=True),
                ],
                children=[dict(age=6, disability="dla_middle")],
            )
        ],
    ),
    # A pensioner whose son, on a qualifying benefit, cares for her.
    dict(
        country="WALES",
        units=[
            dict(adults=[single(75, disability="aa_higher")], children=[]),
            dict(
                adults=[single(40, disability="pip_standard", care_hours=35)],
                children=[],
            ),
        ],
    ),
]


def test_issue_households_read_the_carer_element_award():
    # In #2120 the blind carer's award includes the carer element, 209.34 x
    # 12, so the disabled person has no severe disability premium (86.05 x 52
    # without it). In #2124 the Scottish carer's applicable amount includes
    # the carer premium, (95.55 + 48.15) x 52, not 95.55 x 52.
    sim = Simulation(situation=situation(EXAMPLES[:1] + EXAMPLES[2:3]))
    severe = sim.calculate("severe_disability_premium", YEAR)
    carer_element = sim.calculate("uc_carer_element", YEAR)
    applicable = sim.calculate("council_tax_reduction_applicable_amount", YEAR)
    # Benefit units: the disabled person, the blind carer, the Scottish carer.
    assert carer_element == pytest.approx([0, 209.34 * 12, 209.34 * 12])
    assert severe[0] == 0
    assert applicable[2] == pytest.approx((95.55 + 48.15) * WEEKS)


@PROPERTY_SETTINGS
@given(st.lists(households(), min_size=1, max_size=4))
@example(EXAMPLES)
def test_the_carer_element_limb_moves_only_its_readers_and_only_one_way(population):
    variables = SEVERE_READERS + (
        "carer_premium",
        "council_tax_reduction_carer_premium",
        "council_tax_reduction_pensioner",
        "partners_care_for_same_severely_disabled_person",
        "is_cared_for_by_carer_benefit_recipient",
        "is_severely_disabled_for_carers_allowance",
        "has_uc_award_with_carer_element",
        "receives_uc_carer_element",
        "receives_carer_benefit",
        "is_claimant_or_partner",
        "uc_award_upper_bound",
        "universal_credit_pre_benefit_cap",
        "universal_credit",
    )
    sim, values = with_and_without_limb(population, variables)
    drawn = {v: pair[0] for v, pair in values.items()}
    without = {v: pair[1] for v, pair in values.items()}
    n_benunits = len(drawn["carer_premium"])
    benunit_household = household_index(sim, "benunit")
    person_household = household_index(sim, "person")

    # 5. A nil bound leaves a nil award, exactly, so the carer test misses no
    # award.
    bound = drawn["uc_award_upper_bound"]
    award = drawn["universal_credit_pre_benefit_cap"]
    assert (bound >= award).all()
    assert (award >= drawn["universal_credit"]).all()
    has_award = drawn["has_uc_award_with_carer_element"]
    positive_award = drawn["receives_uc_carer_element"]
    assert not (positive_award & ~has_award).any()

    # 1. No change without a carer element, household by household.
    touched = list(set(person_household[has_award | positive_award]))
    untouched_units = ~np.isin(benunit_household, touched)
    untouched_people = ~np.isin(person_household, touched)
    for v in SEVERE_READERS:
        assert (drawn[v][untouched_units] == without[v][untouched_units]).all(), v
    cared_for = drawn["is_cared_for_by_carer_benefit_recipient"]
    cared_for_without = without["is_cared_for_by_carer_benefit_recipient"]
    assert (cared_for[untouched_people] == cared_for_without[untouched_people]).all()
    ctr = drawn["council_tax_reduction_carer_premium"]
    shared = drawn["carer_premium"]
    assert (ctr[untouched_units] == shared[untouched_units]).all()

    # 2. A carer element never raises the severe disability premium or the
    # addition, and never removes anyone from the cared-for set.
    for v in SEVERE_READERS:
        assert (drawn[v] <= without[v]).all(), v
    assert not (cared_for_without & ~cared_for).any()

    # 3. The Scottish premium never lowers the carer premium and moves it
    # only in Scotland at working age.
    assert (ctr >= shared).all()
    countries = sim.calculate("country", YEAR)
    if hasattr(countries, "decode_to_str"):
        countries = countries.decode_to_str()
    country = dict(zip(sim.populations["household"].ids, np.asarray(countries)))
    scottish = np.array([country[f"h{h}"] == "SCOTLAND" for h in benunit_household])
    scottish_working_age = scottish & ~drawn["council_tax_reduction_pensioner"]
    assert (ctr[~scottish_working_age] == shared[~scottish_working_age]).all()

    # 4. Whole weekly amounts, at most one per claimant or partner, one where
    # partners care for the same person.
    weekly = ctr / (CARER_PREMIUM * WEEKS)
    assert np.allclose(weekly, np.round(weekly))
    benunit_position = {
        name: i for i, name in enumerate(sim.populations["benunit"].ids)
    }
    person_benunit = [
        benunit_position[name.rsplit("_", 1)[0]]
        for name in sim.populations["person"].ids
    ]
    claimants = np.bincount(
        person_benunit, weights=drawn["is_claimant_or_partner"], minlength=n_benunits
    )
    assert (np.round(weekly) <= claimants).all()
    same_person = drawn["partners_care_for_same_severely_disabled_person"]
    assert (np.round(weekly[same_person]) <= 1).all()

    # 6. Everyone cared for meets Carer's Allowance's severe disability test; no
    # household has more people cared for than carers, and the attribution
    # never counts a lone carer as cared for.
    assert not (cared_for & ~drawn["is_severely_disabled_for_carers_allowance"]).any()
    carer = drawn["receives_carer_benefit"] | has_award
    for h in np.unique(person_household):
        in_h = person_household == h
        assert cared_for[in_h].sum() <= carer[in_h].sum()
        if carer[in_h].sum() == 1:
            assert not (cared_for & carer)[in_h].any()


READER_ORDERS = st.permutations(ALL_READERS)


@settings(
    max_examples=3,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
@given(st.lists(households(), min_size=1, max_size=3), READER_ORDERS)
@example(EXAMPLES, ALL_READERS)
@example(EXAMPLES, tuple(reversed(ALL_READERS)))
def test_every_reader_calculates_on_one_simulation_in_any_order(population, order):
    # A CycleError, or the recursion it guards, would fail this test.
    sim = Simulation(situation=situation(population))
    for variable in order:
        values = np.asarray(sim.calculate(variable, YEAR))
        assert np.isfinite(values.astype(float)).all(), variable


def stored_award_situation(stored=True):
    """The issue's blind carer on £20,000, which tapers the award the model
    works out to nil, with neither family claiming; the situation supplies
    the award instead: nil for the disabled person's family, £100 for the carer's."""
    sim_situation = situation(
        [
            dict(
                country="ENGLAND",
                units=[
                    dict(adults=[single(50, disability="pip_standard")], children=[]),
                    dict(
                        adults=[single(40, blind=True, care_hours=35, earnings=20_000)],
                        children=[],
                    ),
                ],
            )
        ]
    )
    for unit, award in (("h0_u0", 0), ("h0_u1", 100)):
        sim_situation["benunits"][unit]["claims_universal_credit"] = {YEAR: False}
        if stored:
            sim_situation["benunits"][unit]["universal_credit"] = {YEAR: award}
    return sim_situation


@pytest.mark.parametrize("order", [ALL_READERS, tuple(reversed(ALL_READERS))])
def test_a_stored_award_is_the_award_and_reads_no_cycle(order):
    # A stored award reads no other variable, so the carer test reads it: the
    # carer's £100 award includes the carer element and bars the disabled
    # person's premium, 86.05 x 52 = 4,474.60 without it. Every reader then
    # calculates on the one simulation (invariants 5 and 7).
    sim = Simulation(situation=stored_award_situation())
    for variable in order:
        values = np.asarray(sim.calculate(variable, YEAR))
        assert np.isfinite(values.astype(float)).all(), variable
    has_award = sim.calculate("has_uc_award_with_carer_element", YEAR)
    receives = sim.calculate("receives_uc_carer_element", YEAR)
    assert receives.tolist() == [False, True]
    assert has_award.tolist() == [False, True]
    assert sim.calculate("is_cared_for_by_carer_benefit_recipient", YEAR).tolist() == [
        True,
        False,
    ]
    assert sim.calculate("severe_disability_premium", YEAR).tolist() == [0, 0]
    # Without the stored award neither family claims, so no one has an award.
    unstored = Simulation(situation=stored_award_situation(stored=False))
    assert not unstored.calculate("has_uc_award_with_carer_element", YEAR).any()
    assert unstored.calculate("severe_disability_premium", YEAR)[0] == pytest.approx(
        86.05 * WEEKS
    )


def test_a_reform_that_abolishes_universal_credit_leaves_no_carer_element_award():
    # A neutralized award reads no other variable and comes to nil, so no one
    # has an award, and the issue's blind carer does not bar the premium.
    from policyengine_core.reforms import Reform

    class AbolishUniversalCredit(Reform):
        def apply(self):
            self.neutralize_variable("universal_credit")

    sim = Simulation(situation=situation(EXAMPLES[:1]), reform=AbolishUniversalCredit)
    assert not sim.calculate("has_uc_award_with_carer_element", YEAR).any()
    assert sim.calculate("severe_disability_premium", YEAR)[0] == pytest.approx(
        86.05 * WEEKS
    )


def require(condition, message):
    # Raise RuntimeError when a premise fails, so xfail accepts only the
    # premium assertion.
    if not condition:
        raise RuntimeError(message)


def non_dependant_situation():
    """A carer (40) who rents jointly with the disabled person (50) she cares
    for, each liable for half of £12,000, and a blind non-dependant (30)
    earning £20,000. The carer earns £27,000."""
    people = {
        "carer": {
            "age": {YEAR: 40},
            "care_hours": {YEAR: 35},
            "would_claim_carers_allowance": {YEAR: False},
            "employment_income": {YEAR: 27_000},
            "is_household_head": {YEAR: True},
        },
        "disabled": {"age": {YEAR: 50}, "pip_dl_category": {YEAR: "STANDARD"}},
        "non_dependant": {
            "age": {YEAR: 30},
            "is_blind": {YEAR: True},
            "employment_income": {YEAR: 20_000},
        },
    }
    benunits = {
        "carer_unit": {"members": ["carer"], "share_of_household_rent": {YEAR: 0.5}},
        "disabled_unit": {
            "members": ["disabled"],
            "would_claim_uc": {YEAR: False},
            "liable_for_share_of_household_rent": {YEAR: True},
            "share_of_household_rent": {YEAR: 0.5},
            "severe_disability_premium_joint_occupier_exclusion_applies": {YEAR: True},
        },
        "non_dependant_unit": {
            "members": ["non_dependant"],
            "would_claim_uc": {YEAR: False},
        },
    }
    household = {
        "members": ["carer", "disabled", "non_dependant"],
        "country": {YEAR: "ENGLAND"},
        "tenure_type": {YEAR: "RENT_PRIVATELY"},
        "rent": {YEAR: 12_000},
    }
    return {"people": people, "benunits": benunits, "households": {"h": household}}


def tax_free_childcare_situation():
    """A blind carer (35) earning £60,000 with a child (3) in £12,000 of
    childcare, and the disabled person (60) she cares for in another family
    of the household."""
    people = {
        "carer": {
            "age": {YEAR: 35},
            "is_blind": {YEAR: True},
            "care_hours": {YEAR: 35},
            "would_claim_carers_allowance": {YEAR: False},
            "employment_income": {YEAR: 60_000},
        },
        "child": {"age": {YEAR: 3}, "childcare_expenses": {YEAR: 12_000}},
        "disabled": {"age": {YEAR: 60}, "pip_dl_category": {YEAR: "STANDARD"}},
    }
    benunits = {
        "carer_unit": {"members": ["carer", "child"]},
        "disabled_unit": {"members": ["disabled"], "would_claim_uc": {YEAR: False}},
    }
    household = {
        "members": ["carer", "child", "disabled"],
        "country": {YEAR: "ENGLAND"},
    }
    return {"people": people, "benunits": benunits, "households": {"h": household}}


@pytest.mark.xfail(
    raises=AssertionError,
    strict=True,
    reason=(
        "#2795: the carer test reads the bound, which leaves out the "
        "non-dependant deduction that takes this award to nil."
    ),
)
def test_a_non_dependant_deduction_that_takes_the_award_to_nil_leaves_no_award():
    # DWP's deduction for the non-dependant (UC Regs 2013 Sch 4 paras 13 and
    # 16; blindness brings no exemption, and para 15 does not exempt the
    # carer as a renter) takes the carer's award to nil, so she has no award
    # (Welfare Reform Act 2012 s.5(1)(b); reg 17). DWP does not count the
    # disabled person, a joint tenant, as her non-dependant (para 9(2)(d)),
    # the council does not count her as his (HB Regs 2006 reg 3(2)(d)), and a
    # blind non-dependant does not bar the premium (Sch 3 para 14(4)). So he
    # keeps the premium in law.
    sim = Simulation(situation=non_dependant_situation())
    award = sim.calculate("universal_credit_pre_benefit_cap", YEAR)
    bound = sim.calculate("uc_award_upper_bound", YEAR)
    deductions = sim.calculate("uc_non_dep_deductions", YEAR)
    require(award[0] == 0 and bound[0] > 0, "the carer's award is not nil")
    require(deductions[0] > bound[0], "the deduction does not take it to nil")
    severe = sim.calculate("severe_disability_premium", YEAR)
    assert severe[1] == pytest.approx(86.05 * WEEKS)


@pytest.mark.xfail(
    raises=AssertionError,
    strict=True,
    reason=(
        "#2795: the carer test cannot read whether a family takes "
        "Tax-Free Childcare instead, which reads the award."
    ),
)
def test_a_family_that_takes_tax_free_childcare_instead_has_no_award():
    # The family gets more from the Tax-Free Childcare top-up than from the
    # award, so it takes no award (forgoes_universal_credit_for_tax_free_
    # childcare). No one then has an award in respect of caring for the
    # disabled person, so he keeps the premium in law.
    sim = Simulation(situation=tax_free_childcare_situation())
    forgoes = sim.calculate("forgoes_universal_credit_for_tax_free_childcare", YEAR)
    award = sim.calculate("universal_credit_pre_benefit_cap", YEAR)
    bound = sim.calculate("uc_award_upper_bound", YEAR)
    require(forgoes[0] and award[0] == 0 and bound[0] > 0, "the family claims")
    severe = sim.calculate("severe_disability_premium", YEAR)
    assert severe[1] == pytest.approx(86.05 * WEEKS)


def small_housing_situation():
    """A blind carer (35) earning £25,000, whom DWP has determined to have
    limited capability for work, rents from the council at £600 a year; the
    disabled person (60) she cares for lives in another family of the
    household."""
    people = {
        "carer": {
            "age": {YEAR: 35},
            "is_blind": {YEAR: True},
            "care_hours": {YEAR: 35},
            "would_claim_carers_allowance": {YEAR: False},
            "employment_income": {YEAR: 25_000},
            "uc_limited_capability_for_work": {YEAR: True},
            "is_household_head": {YEAR: True},
        },
        "disabled": {"age": {YEAR: 60}, "pip_dl_category": {YEAR: "STANDARD"}},
    }
    benunits = {
        "carer_unit": {"members": ["carer"]},
        "disabled_unit": {"members": ["disabled"], "would_claim_uc": {YEAR: False}},
    }
    household = {
        "members": ["carer", "disabled"],
        "country": {YEAR: "ENGLAND"},
        "tenure_type": {YEAR: "RENT_FROM_COUNCIL"},
        "rent": {YEAR: 600},
    }
    return {"people": people, "benunits": benunits, "households": {"h": household}}


@pytest.mark.xfail(
    raises=AssertionError,
    strict=True,
    reason=(
        "#2795: the bound's calculation without housing costs takes the "
        "higher work allowance and stays positive when this award comes to nil."
    ),
)
def test_small_housing_costs_with_a_work_allowance_leave_no_award():
    # DWP has determined that the carer has limited capability for work, so
    # her award has a work allowance (UC Regs 2013 reg 22(1)(b)), and she
    # gets the carer element with it: DWP gives the LCWRA element in its
    # place only for limited capability for work and work-related activity
    # (reg 29(4)), and ignores the allowance's earnings limit and the missing
    # claim (reg 30(1)(a)(i) and (2)). Her award has a housing costs element of
    # £600, so DWP applies the lower work allowance, £427 a month (reg
    # 22(2)(b)). The taper then exceeds the maximum amount, and the award
    # comes to nil (Welfare Reform Act 2012 s.5(1)(b); reg 17). The bound
    # also works out the award with no housing costs element and the higher
    # work allowance, £710 a month, which leaves £461.10. The council
    # ignores the blind carer as a resident (HB Regs 2006 Sch 3 para
    # 14(4)(b)), and with no award she does not bar the premium (para
    # 14(2)(a)(iii)). So the disabled person keeps the premium in law.
    sim = Simulation(situation=small_housing_situation())
    award = sim.calculate("universal_credit_pre_benefit_cap", YEAR)
    bound = sim.calculate("uc_award_upper_bound", YEAR)
    housing = sim.calculate("uc_housing_costs_element", YEAR)
    allowance = sim.calculate("uc_work_allowance", YEAR)
    deductions = sim.calculate("uc_non_dep_deductions", YEAR)
    forgoes = sim.calculate("forgoes_universal_credit_for_tax_free_childcare", YEAR)
    lcwra = sim.calculate("uc_LCWRA_element", YEAR)
    carer_element = sim.calculate("uc_carer_element", YEAR)
    require(award[0] == 0 and bound[0] > 0, "the carer's award is not nil")
    require(housing[0] > 0 and allowance[0] == 427 * 12, "no lower work allowance")
    require(deductions[0] == 0 and not forgoes[0], "another route takes it to nil")
    require(lcwra[0] == 0 and carer_element[0] > 0, "the award has no carer element")
    severe = sim.calculate("severe_disability_premium", YEAR)
    assert severe[1] == pytest.approx(86.05 * WEEKS)


def test_the_bound_reads_neither_the_award_nor_pension_credit():
    # The carer test reads uc_award_upper_bound because the award reads
    # Pension Credit (through the non-dependant deduction's exemption), whose
    # addition reads the attribution. A pensioner on Attendance Allowance
    # shares a privately rented home with her blind son, who claims Universal
    # Credit with the carer element; the trace of the bound reaches none of
    # those variables.
    forbidden = {
        "pension_credit",
        "uc_housing_costs_element",
        "uc_non_dep_deductions",
        "uc_non_dep_deduction_exempt",
        "uc_maximum_amount",
        "uc_income_reduction",
        "universal_credit_pre_benefit_cap",
        "universal_credit",
        "is_cared_for_by_carer_benefit_recipient",
    }
    sim = Simulation(
        situation=situation(
            [
                dict(
                    country="ENGLAND",
                    tenure="RENT_PRIVATELY",
                    rent=9_000,
                    units=[
                        dict(adults=[single(75, disability="aa_higher")], children=[]),
                        dict(
                            adults=[single(40, blind=True, care_hours=35)],
                            children=[],
                        ),
                    ],
                )
            ]
        )
    )
    sim.trace = True
    sim.calculate("uc_award_upper_bound", YEAR)
    reached = set()

    def visit(node):
        reached.add(node.name)
        for child in node.children:
            visit(child)

    for tree in sim.tracer.trees:
        visit(tree)
    assert "uc_carer_element" in reached
    assert not reached & forbidden, reached & forbidden


# Families for the endpoint comparison, each in its own English household:
# every element of the maximum amount, both work allowances, owners, council
# and housing association renters, and private renters below and above the
# Local Housing Allowance rate. The award reads the earned and unearned
# income each row supplies.
PARITY_FAMILIES = [
    # A single owner, with no work allowance.
    dict(adults=[dict(age=30)], children=[], tenure="OWNED_OUTRIGHT", rent=0),
    # A lone parent renting privately, with a child (3) in childcare.
    dict(
        adults=[dict(age=30, employment_income=30_000)],
        children=[dict(age=3, childcare_expenses=6_000)],
        tenure="RENT_PRIVATELY",
        rent=9_000,
    ),
    # A lone parent of two who owns her home.
    dict(
        adults=[dict(age=35, employment_income=20_000)],
        children=[dict(age=4), dict(age=7)],
        tenure="OWNED_OUTRIGHT",
        rent=0,
    ),
    # A council renter with limited capability for work and work-related
    # activity.
    dict(
        adults=[dict(age=45, uc_limited_capability_for_WRA=True)],
        children=[],
        tenure="RENT_FROM_COUNCIL",
        rent=6_000,
    ),
    # A carer with limited capability for work and a small council rent,
    # where the calculation without housing costs gives the larger award.
    dict(
        adults=[dict(age=35, care_hours=35, uc_limited_capability_for_work=True)],
        children=[],
        tenure="RENT_FROM_COUNCIL",
        rent=600,
    ),
    # A couple, one caring, with a disabled child, renting from a housing
    # association.
    dict(
        adults=[
            dict(age=40, care_hours=35),
            dict(age=38, employment_income=15_000),
        ],
        children=[dict(age=6, dla_sc_category="MIDDLE")],
        tenure="RENT_FROM_HA",
        rent=7_200,
    ),
    # A lone parent earning £6,000, with a child (3) in childcare, who rents
    # privately for £30,000 a year. The model places a household with no
    # region in Inner South East London, where DWP caps the housing costs
    # element at the two-bedroom Local Housing Allowance rate, £1,550 a month.
    dict(
        adults=[dict(age=30, employment_income=6_000)],
        children=[dict(age=3, childcare_expenses=6_000)],
        tenure="RENT_PRIVATELY",
        rent=30_000,
    ),
]
# Earned income before the work allowance and unearned income, a year.
PARITY_INCOMES = [(0, 0), (6_000, 0), (18_000, 0), (12_000, 1_500)]
BOUNDARY_EARNINGS = 6_000
# The endpoints: the award with non-dependant deductions supplied as nil, and
# the award with the housing costs element supplied as nil.
ENDPOINTS = ("uc_non_dep_deductions", "uc_housing_costs_element")


def parity_situation(rows, endpoint=None):
    """One household per (family, earned income, unearned income) row. Each
    family claims and takes no Tax-Free Childcare instead, with no benefit cap
    reduction or debt deduction, so the final award equals the award before
    the cap. The situation supplies endpoint, a variable in ENDPOINTS, as
    nil."""
    people, benunits, households = {}, {}, {}
    for i, (family, earned, unearned) in enumerate(rows):
        members = []
        for role, group in (("a", family["adults"]), ("c", family["children"])):
            for j, inputs in enumerate(group):
                name = f"r{i}_{role}{j}"
                people[name] = {k: {YEAR: v} for k, v in inputs.items()}
                people[name]["is_claimant_or_partner"] = {YEAR: role == "a"}
                members.append(name)
        unit = {
            "members": members,
            "claims_universal_credit": {YEAR: True},
            "forgoes_universal_credit_for_tax_free_childcare": {YEAR: False},
            "uc_benefit_cap_reduction_after_floor": {YEAR: 0},
            "uc_deductions": {YEAR: 0},
            "uc_earned_income_before_work_allowance": {YEAR: float(earned)},
            "uc_unearned_income": {YEAR: float(unearned)},
        }
        if endpoint is not None:
            unit[endpoint] = {YEAR: 0}
        benunits[f"r{i}"] = unit
        households[f"r{i}"] = {
            "members": members,
            "country": {YEAR: "ENGLAND"},
            "tenure_type": {YEAR: family["tenure"]},
            "rent": {YEAR: family["rent"]},
        }
    return {"people": people, "benunits": benunits, "households": households}


def endpoint_values(rows, variables):
    """Each variable at each endpoint, from its own simulation."""
    results = []
    for endpoint in ENDPOINTS:
        sim = Simulation(situation=parity_situation(rows, endpoint))
        results.append({v: np.asarray(sim.calculate(v, YEAR)) for v in variables})
    return results


def boundary_rows():
    """Rows whose unearned income brings each endpoint's income reduction to
    within a few float32 steps of its maximum amount, where the award
    cancels to nil or a fraction of a penny."""
    seeds = [(family, BOUNDARY_EARNINGS, 0) for family in PARITY_FAMILIES]
    values = endpoint_values(seeds, ("uc_maximum_amount", "uc_income_reduction"))
    rows = []
    for at_endpoint in values:
        maximum = at_endpoint["uc_maximum_amount"].astype(np.float32)
        reduction = at_endpoint["uc_income_reduction"].astype(np.float32)
        assert (reduction < maximum).all(), "a seed's taper reaches its maximum"
        for f, family in enumerate(PARITY_FAMILIES):
            step = np.spacing(maximum[f])
            for k in range(-3, 4):
                unearned = np.float32(maximum[f] - reduction[f] + k * step)
                rows.append((family, BOUNDARY_EARNINGS, float(unearned)))
    return rows


def test_upper_bound_matches_real_award_endpoints():
    # The bound repeats the award's arithmetic at two endpoints, since the
    # carer test cannot read the award. At each row the bound must equal,
    # exactly, the larger of the two awards the model's own formulas give:
    # one with non-dependant deductions supplied as nil, one with the
    # housing costs element supplied as nil. Comparing the award before the
    # cap and the final award also catches a new amount the award adds
    # after the cap stage. Drift either way at these rows fails the test.
    rows = [
        (family, earned, unearned)
        for family in PARITY_FAMILIES
        for earned, unearned in PARITY_INCOMES
    ]
    n_seed_rows = len(rows)
    rows += boundary_rows()
    components = (
        "uc_standard_allowance",
        "uc_child_element",
        "uc_disability_elements",
        "uc_carer_element",
        "uc_housing_costs_element",
        "uc_childcare_element",
    )
    variables = components + (
        "uc_LHA_cap",
        "benunit_rent",
        "uc_work_allowance",
        "universal_credit_pre_benefit_cap",
        "universal_credit",
    )
    with_housing, without_housing = endpoint_values(rows, variables)
    base = Simulation(situation=parity_situation(rows))
    bound = np.asarray(base.calculate("uc_award_upper_bound", YEAR))

    # The rows cover every element, a housing costs element that DWP caps at
    # the Local Housing Allowance rate, both work allowances, both endpoints
    # deciding the bound, and awards that cancel to nil or under a penny.
    for component in components:
        assert (with_housing[component] > 0).any(), component
    lha_cap = with_housing["uc_LHA_cap"]
    assert (
        (lha_cap < with_housing["benunit_rent"])
        & (with_housing["uc_housing_costs_element"] == lha_cap)
    ).any()
    assert (with_housing["uc_work_allowance"] == 427 * 12).any()
    assert (without_housing["uc_work_allowance"] == 710 * 12).any()
    pre_cap = [
        values["universal_credit_pre_benefit_cap"]
        for values in (with_housing, without_housing)
    ]
    assert (pre_cap[0] > pre_cap[1]).any() and (pre_cap[1] > pre_cap[0]).any()
    for award in pre_cap:
        boundary = award[n_seed_rows:]
        assert (boundary == 0).any() and ((boundary > 0) & (boundary < 0.01)).any()

    for stage in ("universal_credit_pre_benefit_cap", "universal_credit"):
        larger = np.maximum(with_housing[stage], without_housing[stage])
        mismatched = np.flatnonzero(bound != larger)
        assert not mismatched.size, (stage, mismatched, bound[mismatched])


# The award's steps that the bound repeats, and the reads it leaves out: the
# non-dependant deduction and the Tax-Free Childcare choice, which read
# Pension Credit and the award, and the claim, which the carer test reads
# beside the bound.
AWARD_STEPS = (
    "uc_maximum_amount",
    "uc_housing_costs_element",
    "uc_work_allowance",
    "uc_earned_income",
    "uc_income_reduction",
    "universal_credit_pre_benefit_cap",
)
LEFT_OUT = {
    "uc_non_dep_deductions",
    "forgoes_universal_credit_for_tax_free_childcare",
    "claims_universal_credit",
}


def test_the_bound_reads_every_component_of_the_maximum_amount():
    # A new element in uc_maximum_amount, or a new read in any step of the
    # award, must reach the bound too. The couple with a disabled child
    # rents and has a carer, so every step runs.
    sim = Simulation(situation=parity_situation([(PARITY_FAMILIES[5], 12_000, 1_500)]))
    sim.trace = True
    sim.calculate("universal_credit_pre_benefit_cap", YEAR)
    sim.calculate("uc_award_upper_bound", YEAR)
    reads = {}

    def visit(node):
        if node.children:
            # A variable's formula runs once; later reads hit the cache.
            reads.setdefault(node.name, [child.name for child in node.children])
        for child in node.children:
            visit(child)

    for tree in sim.tracer.trees:
        visit(tree)
    bound_reads = reads["uc_award_upper_bound"]
    adds = sim.tax_benefit_system.get_variable("uc_maximum_amount").adds
    # The elements in uc_maximum_amount's order, which float32 addition
    # depends on; the bound rebuilds the housing costs element from rent.
    assert [name for name in bound_reads if name in adds] == [
        name for name in adds if name != "uc_housing_costs_element"
    ]
    for step in AWARD_STEPS:
        missing = set(reads[step]) - set(AWARD_STEPS) - LEFT_OUT - set(bound_reads)
        assert not missing, (step, missing)
