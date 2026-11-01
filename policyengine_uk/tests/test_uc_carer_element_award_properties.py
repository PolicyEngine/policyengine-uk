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
(receives_uc_carer_element), or from 1 April 2022 to 31 March 2025, when an
award of nil counted, the award's conditions. Each example simulates the
households as drawn, and
again with has_uc_award_with_carer_element supplied as false for everyone, the
attribution as it ran before the limb (its carers are then
receives_carer_benefit alone). The Scottish premium's counterpart without the
limb is carer_premium.

Invariants, on generated households under baseline law:

1. No change without a carer element: where no one has
   has_uc_award_with_carer_element or receives_uc_carer_element, the
   attribution, the severe disability premiums and the addition equal their
   values without the limb, and the Scottish premium equals carer_premium,
   exactly.
2. Never raises: no carer element raises the severe disability premium (the
   shared, council tax reduction and pension-age premiums) or the Pension
   Credit addition.
3. Never lowers, and only in Scotland: council_tax_reduction_carer_premium is
   never below carer_premium, and differs from it only for a Scottish
   working-age family.
4. Bounds: the Scottish premium is a whole number of weekly amounts, at most
   the number of claimants and partners, and at most one where partners care
   for the same person; a person with both an allowance and a carer element
   counts once.
5. Where the bound is nil, the award is nil: uc_award_upper_bound is at least
   universal_credit_pre_benefit_cap, which is at least universal_credit, so
   receives_uc_carer_element implies has_uc_award_with_carer_element. That
   implication also holds where the simulation stores the award.
6. Attribution: no one is their own carer, everyone cared for is severely
   disabled for Carer's Allowance, and a household has no more people cared
   for than carers (carer benefit recipients and carer element holders).
7. No cycle: every reader calculates on one simulation, whichever is requested
   first, and also where the simulation stores the award.

A reform that makes is_uc_eligible read Pension Credit would cycle through the
attribution, which reads eligibility; these tests do not cover reforms.

The no-change invariant compares the two code paths in this tree; the
differential against origin/main itself runs on hand-built datasets outside
the test suite (see the pull request).
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
        # The qualifying hours, with or without a Carer's Allowance claim: the
        # Universal Credit carer element needs no claim (UC Regs 2013 reg
        # 30(2)), and its test ignores the allowance's earnings limit.
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
    # Renters pay the housing costs element, and the household head's family
    # bears a deduction for each non-dependant in another benefit unit, which
    # the upper bound leaves out.
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

    Without the limb, has_uc_award_with_carer_element is supplied as false
    for everyone, in a second simulation: a variable supplied for some people
    takes its default, not its formula, for the rest.
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
    # The blind carer: a Universal Credit carer element in another benefit
    # unit bars the disabled person's premium.
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
    # A pensioner cared for by a son on a qualifying benefit.
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
    # #2120: the blind carer's award includes the carer element, 209.34 x 12,
    # so the disabled person has no severe disability premium (86.05 x 52
    # without it). #2124: the Scottish carer's applicable amount includes the
    # carer premium, (95.55 + 48.15) x 52, not 95.55 x 52. Only variables
    # that predate the fix are read, so the test also runs on the old code.
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

    # 5. Where the bound is nil the award is nil, exactly, so the carer test
    # misses no award.
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

    # 6. Everyone cared for is severely disabled for Carer's Allowance; no
    # household has more people cared for than carers, and a lone carer is
    # not cared for.
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
    works out to nil, with neither family claiming; the award is supplied
    instead: nil for the disabled person's family, £100 for the carer's."""
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
    # A neutralized award reads no other variable and is nil, so no one has
    # an award and the blind carer of the issue no longer bars the premium.
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
    # A broken premise is an error, not the disclosed failure.
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
        "Disclosed limit: the carer test reads the award before the "
        "non-dependant deduction, which takes this award to nil."
    ),
)
def test_a_non_dependant_deduction_that_takes_the_award_to_nil_leaves_no_award():
    # The non-dependant's deduction (UC Regs 2013 Sch 4 paras 13 and 16; a
    # blind non-dependant has no exemption, and the carer is no exempt renter
    # under para 15) takes the carer's award to nil, so she has no award
    # (Welfare Reform Act 2012 s.5(1)(b); reg 17). The disabled person is a
    # joint tenant, not her non-dependant (para 9(2)(d)), and she is not his
    # (HB Regs 2006 reg 3(2)(d)); a blind non-dependant does not bar the
    # premium (Sch 3 para 14(4)). So the law pays him the premium.
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
        "Disclosed limit: the carer test cannot read whether a family takes "
        "Tax-Free Childcare instead, which reads the award."
    ),
)
def test_a_family_that_takes_tax_free_childcare_instead_has_no_award():
    # The family is better off with the Tax-Free Childcare top-up, so it
    # takes no award (forgoes_universal_credit_for_tax_free_childcare); with
    # no award, no one has one in respect of caring for the disabled person,
    # and the law pays him the premium.
    sim = Simulation(situation=tax_free_childcare_situation())
    forgoes = sim.calculate("forgoes_universal_credit_for_tax_free_childcare", YEAR)
    award = sim.calculate("universal_credit_pre_benefit_cap", YEAR)
    bound = sim.calculate("uc_award_upper_bound", YEAR)
    require(forgoes[0] and award[0] == 0 and bound[0] > 0, "the family claims")
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
