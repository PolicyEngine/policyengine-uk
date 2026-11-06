"""Universal Credit carer-element awards as a carer benefit.

HB Regs 2006 Sch 3 para 14(2)(a)(iii) and (b) (with the IS, JSA, ESA,
pension-age Housing Benefit and council tax reduction schedules) and SPC Regs
2002 Sch I para 1(1) and (4) withhold the severe disability premium and the
Pension Credit severe disability addition where someone "has an award of
universal credit which includes the carer element in respect of caring for"
the claimant or partner. Scotland's working-age council tax reduction (SSI
2021/249 Sch 1 paras 5 and 6(1)(c), from 1 April 2022) pays the carer premium
to an applicant or partner with such an award.

The severe disability carer test (has_uc_award_with_carer_element) reads the
award before the benefit cap, universal_credit_pre_benefit_cap, since the cap
reads Pension Credit, or the award itself where the simulation stores it.
Scotland's carer premium reads the positive award (receives_uc_carer_element)
in every year. Each example simulates the households as drawn, and again with
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
5. The carer test is the award: has_uc_award_with_carer_element equals
   receives_uc_carer_element for every person, and
   universal_credit_pre_benefit_cap comes to more than nil wherever
   universal_credit does, and for every family whose award includes the
   carer element in respect of someone, exactly where universal_credit does.
   The equality also holds where the simulation stores the award.
6. Attribution: the attribution makes no one their own carer, everyone it
   counts as cared for meets Carer's Allowance's severe disability test, and
   no household has more people cared for than carers (carer benefit
   recipients and carer element holders).
7. No cycle: every reader calculates on one simulation, whichever the test
   requests first, and also where the simulation stores the award.
8. The cut: the non-dependant deduction's Pension Credit exemption reads the
   non-dependant family's Pension Credit in a branch with every housing costs
   element set to nil, where the carer test reads the award without housing
   costs. test_the_non_dependant_branch_reads_the_award_without_housing_costs
   pins that reading in three request orders, for a household where the
   branch's result changes no deduction, and
   test_the_branch_decides_a_blind_partners_deduction pins a household where
   the branch's result decides one.

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
    "universal_credit_pre_benefit_cap",
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
    # non-dependant in another benefit unit.
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
        "universal_credit_pre_benefit_cap",
        "universal_credit",
        "uc_carer_element",
    )
    sim, values = with_and_without_limb(population, variables)
    drawn = {v: pair[0] for v, pair in values.items()}
    without = {v: pair[1] for v, pair in values.items()}
    n_benunits = len(drawn["carer_premium"])
    benunit_household = household_index(sim, "benunit")
    person_household = household_index(sim, "person")

    # 5. The carer test is the award: the award before the cap is positive
    # wherever the final award is, and exactly where it is for a family whose
    # award includes the carer element, so the two tests agree.
    award = drawn["universal_credit_pre_benefit_cap"]
    final = drawn["universal_credit"]
    assert not ((final > 0) & ~(award > 0)).any()
    carer_family = drawn["uc_carer_element"] > 0
    assert ((award > 0) == (final > 0))[carer_family].all()
    has_award = drawn["has_uc_award_with_carer_element"]
    positive_award = drawn["receives_uc_carer_element"]
    assert (has_award == positive_award).all()

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
    assert has_award.tolist() == receives.tolist()
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
    # Raise RuntimeError when a premise fails, so a failure names the premise
    # apart from the premium assertion.
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
    deductions = sim.calculate("uc_non_dep_deductions", YEAR)
    without_deduction = non_dependant_situation()
    without_deduction["benunits"]["carer_unit"]["uc_non_dep_deductions"] = {YEAR: 0}
    award_without = Simulation(situation=without_deduction).calculate(
        "universal_credit_pre_benefit_cap", YEAR
    )
    require(award[0] == 0 and deductions[0] > 0, "the carer's award is not nil")
    require(award_without[0] > 0, "the deduction does not take it to nil")
    assert not sim.calculate("has_uc_award_with_carer_element", YEAR).any()
    severe = sim.calculate("severe_disability_premium", YEAR)
    assert severe[1] == pytest.approx(86.05 * WEEKS)


def test_a_family_that_takes_tax_free_childcare_instead_has_no_award():
    # The family gets more from the Tax-Free Childcare top-up than from the
    # award, so it takes no award (forgoes_universal_credit_for_tax_free_
    # childcare). No one then has an award in respect of caring for the
    # disabled person, so he keeps the premium in law.
    sim = Simulation(situation=tax_free_childcare_situation())
    forgoes = sim.calculate("forgoes_universal_credit_for_tax_free_childcare", YEAR)
    award = sim.calculate("universal_credit_pre_benefit_cap", YEAR)
    maximum = sim.calculate("uc_maximum_amount", YEAR)
    reduction = sim.calculate("uc_income_reduction", YEAR)
    require(forgoes[0] and award[0] == 0, "the family claims")
    require(maximum[0] > reduction[0], "the award would come to nil anyway")
    assert not sim.calculate("has_uc_award_with_carer_element", YEAR).any()
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


def test_small_housing_costs_with_a_work_allowance_leave_no_award():
    # DWP has determined that the carer has limited capability for work, so
    # her award has a work allowance (UC Regs 2013 reg 22(1)(b)), and she
    # gets the carer element with it: DWP gives the LCWRA element in its
    # place only for limited capability for work and work-related activity
    # (reg 29(4)), and ignores the allowance's earnings limit and the missing
    # claim (reg 30(1)(a)(i) and (2)). Her award has a housing costs element of
    # £600, so DWP applies the lower work allowance, £427 a month (reg
    # 22(2)(b)). The taper then exceeds the maximum amount, and the award
    # comes to nil (Welfare Reform Act 2012 s.5(1)(b); reg 17), although an
    # award with no housing costs element and the higher work allowance,
    # £710 a month, would leave £461.10. The council
    # ignores the blind carer as a resident (HB Regs 2006 Sch 3 para
    # 14(4)(b)), and with no award she does not bar the premium (para
    # 14(2)(a)(iii)). So the disabled person keeps the premium in law.
    sim = Simulation(situation=small_housing_situation())
    award = sim.calculate("universal_credit_pre_benefit_cap", YEAR)
    housing = sim.calculate("uc_housing_costs_element", YEAR)
    allowance = sim.calculate("uc_work_allowance", YEAR)
    deductions = sim.calculate("uc_non_dep_deductions", YEAR)
    forgoes = sim.calculate("forgoes_universal_credit_for_tax_free_childcare", YEAR)
    lcwra = sim.calculate("uc_LCWRA_element", YEAR)
    carer_element = sim.calculate("uc_carer_element", YEAR)
    require(award[0] == 0, "the carer's award is not nil")
    require(housing[0] > 0 and allowance[0] == 427 * 12, "no lower work allowance")
    require(deductions[0] == 0 and not forgoes[0], "another route takes it to nil")
    require(lcwra[0] == 0 and carer_element[0] > 0, "the award has no carer element")
    assert not sim.calculate("has_uc_award_with_carer_element", YEAR).any()
    severe = sim.calculate("severe_disability_premium", YEAR)
    assert severe[1] == pytest.approx(86.05 * WEEKS)


def veteran_situation(pension_credit=None, veteran_exempt=None, blind_partner=False):
    """A blind carer (40) earning £20,000 rents from the council at £6,000 a
    year as household head and cares 35 hours a week for a veteran (70) in
    another family of the household, who receives armed forces independence
    payment and £13,000 of State Pension. The carer claims alone, so UC Regs
    2013 Sch 4 para 15(1)(a) and (2)(a) exempt the carer, a blind single
    renter, from every non-dependant deduction; the model holds no such
    exemption. pension_credit, if given, supplies the veteran family's
    uc_non_dep_receives_pension_credit, which the model otherwise reads from
    a branch. veteran_exempt, if given, supplies the veteran's
    uc_non_dep_deduction_exempt. blind_partner adds the veteran's blind
    partner (68), who receives no disability benefit, and raises the
    veteran's State Pension to £21,000."""
    people = {
        "carer": {
            "age": {YEAR: 40},
            "is_blind": {YEAR: True},
            "care_hours": {YEAR: 35},
            "would_claim_carers_allowance": {YEAR: False},
            "employment_income": {YEAR: 20_000},
            "is_household_head": {YEAR: True},
        },
        "veteran": {
            "age": {YEAR: 70},
            "armed_forces_independence_payment": {YEAR: 150 * WEEKS},
            "state_pension": {YEAR: 13_000},
        },
    }
    benunits = {
        "carer_unit": {"members": ["carer"]},
        "veteran_unit": {"members": ["veteran"], "would_claim_uc": {YEAR: False}},
    }
    if pension_credit is not None:
        benunits["veteran_unit"]["uc_non_dep_receives_pension_credit"] = {
            YEAR: pension_credit
        }
    if veteran_exempt is not None:
        people["veteran"]["uc_non_dep_deduction_exempt"] = {YEAR: veteran_exempt}
    household = {
        "members": ["carer", "veteran"],
        "country": {YEAR: "ENGLAND"},
        "tenure_type": {YEAR: "RENT_FROM_COUNCIL"},
        "rent": {YEAR: 6_000},
    }
    if blind_partner:
        people["veteran"]["state_pension"] = {YEAR: 21_000}
        people["partner"] = {"age": {YEAR: 68}, "is_blind": {YEAR: True}}
        benunits["veteran_unit"]["members"].append("partner")
        household["members"].append("partner")
    return {"people": people, "benunits": benunits, "households": {"h": household}}


@pytest.mark.parametrize(
    "first", ["universal_credit", "pension_credit", "has_uc_award_with_carer_element"]
)
def test_the_non_dependant_branch_reads_the_award_without_housing_costs(first):
    # The carer's award: income tax 1,486.00 and National Insurance 594.40
    # leave earned income of 17,919.60, and the taper, 0.55 x 17,919.60 =
    # 9,855.78, leaves (424.90 + 209.34) x 12 + 6,000 - 9,855.78 = 3,755.10
    # with no non-dependant deduction. The award includes the carer element,
    # so the veteran, whom DWP and the model treat as severely disabled
    # through armed forces independence payment, gets no severe disability
    # addition. The veteran pays income tax of 86.00 and keeps 12,914.00 of
    # State Pension, which exceeds the standard minimum guarantee of 238.00
    # x 52 = 12,376.00, so the veteran gets no Pension Credit.
    #
    # uc_non_dep_receives_pension_credit reads the veteran's Pension Credit
    # in a branch with every housing costs element set to nil. There the
    # carer's award, 7,610.88 - 9,855.78, comes to nil, the veteran gets the
    # addition (DWP ignores a blind resident, SPC Regs 2002 Sch I para
    # 2(2)(b)) and Pension Credit of (238.00 + 86.05) x 52 - 12,914.00 =
    # 3,936.60, so the branch returns true.
    #
    # In law DWP deducts nothing for this household, on two grounds. UC Regs
    # 2013 Sch 4 para 15(1)(a) and (2)(a) exempt the carer, a blind single
    # renter, from every deduction. Para 16(2)(d) exempts the veteran, who
    # receives "attendance allowance" under head (f) of reg 2's definition,
    # armed forces independence payment. The model holds the second ground
    # (uc_receives_attendance_allowance) but not the first, so the model's
    # award and the law's agree at 3,755.10, and the branch's result changes
    # neither. This test pins the model's figures, whichever variable the
    # simulation requests first.
    sim = Simulation(situation=veteran_situation())
    sim.calculate(first, YEAR)
    assert sim.calculate("has_uc_award_with_carer_element", YEAR).tolist() == [
        True,
        False,
    ]
    assert sim.calculate("pension_credit", YEAR).tolist() == [0, 0]
    assert sim.calculate("uc_non_dep_receives_pension_credit", YEAR).tolist() == [
        False,
        True,
    ]
    assert sim.calculate("uc_non_dep_deductions", YEAR)[0] == 0
    award = sim.calculate("universal_credit_pre_benefit_cap", YEAR)
    assert award[0] == pytest.approx(3_755.10, abs=0.01)
    # The branch's result set to its value in law, false, since the veteran
    # gets no Pension Credit: the model still exempts the veteran through
    # armed forces independence payment and deducts nothing.
    law = Simulation(situation=veteran_situation(pension_credit=False))
    assert law.calculate("uc_non_dep_deduction_exempt", YEAR).tolist() == [
        False,
        True,
    ]
    assert law.calculate("uc_non_dep_deductions", YEAR)[0] == 0
    law_award = law.calculate("universal_credit_pre_benefit_cap", YEAR)
    assert law_award[0] == pytest.approx(3_755.10, abs=0.01)
    assert law.calculate("has_uc_award_with_carer_element", YEAR)[0]
    assert law.calculate("pension_credit", YEAR)[1] == 0
    # A counterfactual that neither the law nor the model gives this
    # household: with the veteran's exemption supplied as false, the model
    # deducts 96.55 x 12 = 1,158.60 and leaves an award of 3,755.10 -
    # 1,158.60 = 2,596.50. The award still includes the carer element, so
    # even a deduction would leave the carer test and the veteran's nil
    # Pension Credit unchanged.
    counterfactual = Simulation(situation=veteran_situation(veteran_exempt=False))
    assert counterfactual.calculate("uc_non_dep_deductions", YEAR)[0] == pytest.approx(
        96.55 * 12
    )
    counterfactual_award = counterfactual.calculate(
        "universal_credit_pre_benefit_cap", YEAR
    )
    assert counterfactual_award[0] == pytest.approx(2_596.50, abs=0.01)
    assert counterfactual.calculate("has_uc_award_with_carer_element", YEAR)[0]
    assert counterfactual.calculate("pension_credit", YEAR)[1] == 0


def test_the_branch_decides_a_blind_partners_deduction():
    # The veteran of the test above, now with £21,000 of State Pension and a
    # blind partner (68) who receives no disability benefit. Para 16(2)
    # exempts the veteran through armed forces independence payment but
    # lists no blindness, so only the family's Pension Credit can exempt the
    # partner, and the branch's result decides the partner's deduction.
    #
    # The veteran pays income tax of (21,000 - 12,570) x 0.20 - 1,260 x 0.20
    # = 1,434.00, with the partner's marriage allowance, and the couple keep
    # 19,566.00, which exceeds the couple's standard minimum guarantee of
    # 363.25 x 52 = 18,889.00, so the couple get no Pension Credit. In the
    # branch, the carer's award comes to nil, and SPC Regs 2002 Sch I para
    # 1(1)(c) gives the couple the addition (the veteran receives armed
    # forces independence payment, the partner is blind, and DWP ignores the
    # blind carer as a resident under para 2(2)(b)): Pension Credit comes to
    # (363.25 + 86.05) x 52 - 19,566.00 = 3,797.60, the branch returns true,
    # and the model exempts the partner and deducts nothing.
    #
    # In law DWP deducts nothing either, because para 15(1)(a) and (2)(a)
    # exempt the carer, a blind single renter, from every deduction; the
    # carer's award then comes to 3,755.10, includes the carer element and
    # leaves the couple without the addition or Pension Credit. The model
    # holds no para 15 exemption, so with the branch's result supplied at
    # its value in law, false, the model deducts 96.55 x 12 = 1,158.60 for
    # the partner and leaves an award of 2,596.50.
    sim = Simulation(situation=veteran_situation(blind_partner=True))
    assert sim.calculate("has_uc_award_with_carer_element", YEAR).tolist() == [
        True,
        False,
        False,
    ]
    assert sim.calculate("pension_credit", YEAR).tolist() == [0, 0]
    assert sim.calculate("uc_non_dep_receives_pension_credit", YEAR).tolist() == [
        False,
        True,
    ]
    assert sim.calculate("uc_non_dep_deduction_exempt", YEAR).tolist() == [
        False,
        True,
        True,
    ]
    assert sim.calculate("uc_non_dep_deductions", YEAR)[0] == 0
    award = sim.calculate("universal_credit_pre_benefit_cap", YEAR)
    assert award[0] == pytest.approx(3_755.10, abs=0.01)
    branch = Simulation(situation=veteran_situation(blind_partner=True))
    branch.set_input("uc_housing_costs_element", YEAR, [0, 0])
    assert branch.calculate("pension_credit", YEAR)[1] == pytest.approx(
        3_797.60, abs=0.01
    )
    flag_false = Simulation(
        situation=veteran_situation(pension_credit=False, blind_partner=True)
    )
    assert flag_false.calculate("uc_non_dep_deduction_exempt", YEAR).tolist() == [
        False,
        True,
        False,
    ]
    assert flag_false.calculate("uc_non_dep_deductions", YEAR)[0] == pytest.approx(
        96.55 * 12
    )
    flag_false_award = flag_false.calculate("universal_credit_pre_benefit_cap", YEAR)
    assert flag_false_award[0] == pytest.approx(2_596.50, abs=0.01)
    assert flag_false.calculate("has_uc_award_with_carer_element", YEAR)[0]
