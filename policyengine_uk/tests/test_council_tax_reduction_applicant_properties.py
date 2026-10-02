"""Property-based tests for whose circumstances the Council Tax Reduction
means test assesses.

The means test covers the applicant's own income and their partner's (SSI
2012/319 regs 14, 21, 23 and 26; SI 2012/2885 Sch 1 para 11; WSI 2013/3029
Sch 1 para 5 and Sch 6 para 7; SSI 2021/249 reg 36), and the applicant is the
person liable for the council tax. The model takes the household head as
liable (council_tax_reduction_liable_person). Usually the head is the
benefit unit's claimant or partner, but a grandmother who heads the household
can share a benefit unit with a young couple who are its claimant and
partner (#1896's parent-couple rule). She then applies alone.

Invariants, for any generated population of households: heads alone, in a
couple (with partners aged 16 and over), or sharing a benefit unit with two
parents aged 16 to 30 and their baby; another family, sometimes a sharer;
income-based Jobseeker's Allowance and Universal Credit supplied for the
head's benefit unit; disability and caring flags; all eight modelled schemes.

1. Head's income counts: raising the liable household head's own private
   pension by £5,000 raises their family's applicable income. Raising a
   young parent's earnings by £5,000 leaves the family's applicable income
   unchanged where the head applies alone.
2. Monotone: raising the head's pension never raises any family's simulated
   reduction.
3. High income: with £250,000 more pension, the head's family gets no
   simulated reduction, unless an income-based benefit passports it or its
   applicant has a Universal Credit award (both supplied as inputs here;
   those routes are outside this invariant).
4. Identity: a liable head is always an applicant or partner of their own
   family. Where the head does not apply alone, the applicant and partner
   are exactly the benefit unit's claimant and partner (ordinary families
   are unchanged). Where the head applies alone, the head is the only one.
5. Differential: a head over State Pension age sharing a benefit unit with
   parents aged 16 or 17 and their baby has the same applicable income,
   applicable amount, premiums, scheme, exemption and simulated reduction as
   the same head entered as her own benefit unit, with the young family as
   another. The two inputs describe the same people, so the law gives the
   same answer.
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
SHAPES = ["alone", "couple", "young_parents"]
FLAGS = [
    "is_disabled_for_benefits",
    "is_severely_disabled_for_benefits",
    "is_carer_for_benefits",
    "is_blind",
]
money = st.floats(0, 40_000, allow_nan=False, allow_infinity=False)
head_age = st.one_of(
    st.sampled_from([18, 25, 40, 60, 66, 68, 80]), st.integers(18, 100)
)
PENSION_STEP = 5_000
HIGH_PENSION = 250_000


@st.composite
def households(draw):
    return dict(
        scheme=draw(st.sampled_from(SCHEMES)),
        shape=draw(st.sampled_from(SHAPES)),
        head_age=draw(head_age),
        head_pension=draw(money),
        head_flags=draw(st.fixed_dictionaries({f: st.booleans() for f in FLAGS})),
        partner_age=draw(st.integers(16, 100)),
        parent_age=draw(st.integers(16, 30)),
        other_earnings=draw(st.lists(money, min_size=2, max_size=2)),
        jsa_income=draw(st.sampled_from([None, None, 3_000])),
        universal_credit=draw(st.sampled_from([None, None, 5_000])),
        other_family=draw(st.sampled_from([None, "non_dependant", "sharer"])),
        other_age=draw(st.integers(16, 90)),
        council_tax=draw(st.floats(0, 4_000, allow_nan=False)),
        savings=draw(st.floats(0, 20_000, allow_nan=False)),
    )


def person_input(values):
    return {key: {YEAR: value} for key, value in values.items()}


def add_household(people, benunits, homes, name, house, variant):
    """Add one household. variant: "base", "pension", "high_pension" or
    "parent_earnings" (the young mother's earnings raised)."""
    country, local_authority = house["scheme"]
    pension = house["head_pension"] + {
        "pension": PENSION_STEP,
        "high_pension": HIGH_PENSION,
    }.get(variant, 0)
    head = f"{name}_head"
    people[head] = person_input(
        dict(
            age=house["head_age"],
            is_household_head=True,
            private_pension_income=pension,
            **house["head_flags"],
        )
    )
    family = [head]
    if house["shape"] == "couple":
        people[f"{name}_partner"] = person_input(
            dict(
                age=house["partner_age"],
                is_household_head=False,
                employment_income=house["other_earnings"][0],
            )
        )
        family.append(f"{name}_partner")
    elif house["shape"] == "young_parents":
        for i, parent in enumerate(["mother", "father"]):
            earnings = house["other_earnings"][i]
            if variant == "parent_earnings" and parent == "mother":
                earnings += PENSION_STEP
            people[f"{name}_{parent}"] = person_input(
                dict(
                    age=house["parent_age"],
                    is_parent=True,
                    is_household_head=False,
                    employment_income=earnings,
                )
            )
            family.append(f"{name}_{parent}")
        people[f"{name}_baby"] = person_input(dict(age=0, is_household_head=False))
        family.append(f"{name}_baby")
    head_benunit = dict(
        members=family,
        claims_all_entitled_benefits={YEAR: True},
        would_claim_uc={YEAR: False},
    )
    for benefit in ["jsa_income", "universal_credit"]:
        if house[benefit] is not None:
            head_benunit[benefit] = {YEAR: house[benefit]}
    benunits[f"{name}_family"] = head_benunit
    members = list(family)
    if house["other_family"] is not None:
        other = f"{name}_other"
        people[other] = person_input(
            dict(
                age=house["other_age"],
                is_household_head=False,
                employment_income=house["other_earnings"][1],
            )
        )
        benunits[f"{name}_other_family"] = dict(
            members=[other],
            claims_all_entitled_benefits={YEAR: True},
            would_claim_uc={YEAR: False},
            liable_for_share_of_household_rent={
                YEAR: house["other_family"] == "sharer"
            },
        )
        members.append(other)
    homes[name] = person_input(
        dict(
            country=country,
            local_authority=local_authority,
            council_tax=house["council_tax"],
            savings=house["savings"],
        )
    )
    homes[name]["members"] = members


VARIANTS = ["base", "pension", "high_pension", "parent_earnings"]


def simulate(population):
    """One simulation holding every household in every variant."""
    people, benunits, homes = {}, {}, {}
    for h, house in enumerate(population):
        for variant in VARIANTS:
            add_household(people, benunits, homes, f"h{h}_{variant}", house, variant)
    return Simulation(
        situation=dict(people=people, benunits=benunits, households=homes)
    )


def by_benunit(sim, variable, names):
    """A benefit-unit variable for the named benefit units."""
    values = sim.calculate(variable, YEAR)
    ids = list(sim.populations["benunit"].ids)
    return np.array([values[ids.index(name)] for name in names])


@given(st.lists(households(), min_size=1, max_size=6))
@PROPERTY_SETTINGS
def test_council_tax_reduction_assesses_the_liable_head(population):
    sim = simulate(population)
    head_family = {
        variant: [f"h{h}_{variant}_family" for h in range(len(population))]
        for variant in VARIANTS
    }

    def family(variable, variant):
        return by_benunit(sim, variable, head_family[variant])

    head_alone = family("council_tax_reduction_head_applies_alone", "base")

    # 1. The head's pension counts; a young parent's earnings do not where
    # the head applies alone.
    income = family("council_tax_reduction_applicable_income", "base")
    assert (family("council_tax_reduction_applicable_income", "pension") > income).all()
    parent_income = family("council_tax_reduction_applicable_income", "parent_earnings")
    assert np.allclose(parent_income[head_alone], income[head_alone])

    # 2. Monotone in the head's pension, for every family.
    all_ids = list(sim.populations["benunit"].ids)
    simulated = sim.calculate("simulated_council_tax_reduction_benunit", YEAR)

    def every_family(variant):
        return np.array(
            [simulated[all_ids.index(name)] for name in _all_names(population, variant)]
        )

    base_ctr = every_family("base")
    for variant in ["pension", "high_pension"]:
        assert (every_family(variant) <= base_ctr + 1e-6).all()

    # 3. No reduction on a very high income, outside the passport and UC
    # routes.
    passported = family("council_tax_reduction_relevant_income_based_benefit", "base")
    universal_credit = family("universal_credit", "base") > 0
    high = family("simulated_council_tax_reduction_benunit", "high_pension")
    assessed_on_income = ~passported & ~(universal_credit & ~head_alone)
    assert (high[assessed_on_income] == 0).all()

    # 4. Identity.
    liable = sim.calculate("council_tax_reduction_liable_person", YEAR)
    head = sim.calculate("council_tax_reduction_household_head", YEAR)
    applicant = sim.calculate("is_council_tax_reduction_applicant_or_partner", YEAR)
    claimant_or_partner = sim.calculate("is_claimant_or_partner", YEAR)
    alone = sim.populations["person"].benunit(
        "council_tax_reduction_head_applies_alone", YEAR
    )
    assert (applicant[liable & head]).all()
    assert (applicant[~alone] == claimant_or_partner[~alone]).all()
    assert (applicant[alone] == (liable & head)[alone]).all()


def _all_names(population, variant):
    """Every benefit unit of every household in one variant, in order."""
    names = []
    for h, house in enumerate(population):
        names.append(f"h{h}_{variant}_family")
        if house["other_family"] is not None:
            names.append(f"h{h}_{variant}_other_family")
    return names


@st.composite
def grandmother_households(draw):
    return dict(
        scheme=draw(st.sampled_from(SCHEMES)),
        head_age=draw(st.integers(68, 100)),
        head_pension=draw(money),
        head_flags=draw(st.fixed_dictionaries({f: st.booleans() for f in FLAGS})),
        parent_age=draw(st.integers(16, 17)),
        parent_earnings=draw(st.lists(money, min_size=2, max_size=2)),
        jsa_income=draw(st.sampled_from([None, 3_000])),
        universal_credit=draw(st.sampled_from([None, 5_000])),
        council_tax=draw(st.floats(0, 4_000, allow_nan=False)),
        savings=draw(st.floats(0, 20_000, allow_nan=False)),
    )


def add_grandmother_household(people, benunits, homes, name, house, split):
    country, local_authority = house["scheme"]
    head = f"{name}_grandmother"
    people[head] = person_input(
        dict(
            age=house["head_age"],
            is_household_head=True,
            private_pension_income=house["head_pension"],
            **house["head_flags"],
        )
    )
    young = []
    for i, parent in enumerate(["mother", "father"]):
        people[f"{name}_{parent}"] = person_input(
            dict(
                age=house["parent_age"],
                is_parent=True,
                is_household_head=False,
                employment_income=house["parent_earnings"][i],
            )
        )
        young.append(f"{name}_{parent}")
    people[f"{name}_baby"] = person_input(dict(age=0, is_household_head=False))
    young.append(f"{name}_baby")
    young_benefits = {
        benefit: {YEAR: house[benefit]}
        for benefit in ["jsa_income", "universal_credit"]
        if house[benefit] is not None
    }
    common = dict(
        claims_all_entitled_benefits={YEAR: True}, would_claim_uc={YEAR: False}
    )
    if split:
        benunits[f"{name}_family"] = dict(members=[head], **common)
        benunits[f"{name}_young"] = dict(members=young, **common, **young_benefits)
    else:
        benunits[f"{name}_family"] = dict(
            members=[head] + young, **common, **young_benefits
        )
    homes[name] = person_input(
        dict(
            country=country,
            local_authority=local_authority,
            council_tax=house["council_tax"],
            savings=house["savings"],
        )
    )
    homes[name]["members"] = [head] + young


DIFFERENTIAL_VARIABLES = [
    "council_tax_reduction_applicable_income",
    "council_tax_reduction_applicable_amount",
    "council_tax_reduction_premiums",
    "council_tax_reduction_relevant_income_based_benefit",
    "simulated_council_tax_reduction_benunit",
]


@given(st.lists(grandmother_households(), min_size=1, max_size=6))
@PROPERTY_SETTINGS
def test_head_applying_alone_matches_her_own_benefit_unit(population):
    people, benunits, homes = {}, {}, {}
    for h, house in enumerate(population):
        for split in [False, True]:
            add_grandmother_household(
                people,
                benunits,
                homes,
                f"h{h}_{'split' if split else 'merged'}",
                house,
                split,
            )
    sim = Simulation(situation=dict(people=people, benunits=benunits, households=homes))
    merged = [f"h{h}_merged_family" for h in range(len(population))]
    split = [f"h{h}_split_family" for h in range(len(population))]
    assert by_benunit(sim, "council_tax_reduction_head_applies_alone", merged).all()
    assert not by_benunit(sim, "council_tax_reduction_head_applies_alone", split).any()
    for variable in DIFFERENTIAL_VARIABLES:
        assert np.allclose(
            by_benunit(sim, variable, merged), by_benunit(sim, variable, split)
        ), variable
    household_ids = list(sim.populations["household"].ids)
    for variable in [
        "council_tax_reduction_household_has_pensioner",
        "council_tax_reduction_household_has_non_dep_exemption",
        "council_tax_reduction",
    ]:
        values = sim.calculate(variable, YEAR)
        merged_values = [
            values[household_ids.index(f"h{h}_merged")] for h in range(len(population))
        ]
        split_values = [
            values[household_ids.index(f"h{h}_split")] for h in range(len(population))
        ]
        assert np.allclose(merged_values, split_values), variable
