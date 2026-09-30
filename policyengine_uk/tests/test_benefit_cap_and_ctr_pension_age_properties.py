"""Property tests: the benefit cap and Council Tax Reduction for families with a
member over State Pension age.

The law:

- The Universal Credit benefit cap has no age exception (UC Regs 2013 regs
  79, 82 and 83). A mixed-age couple can claim Universal Credit jointly (reg
  3(2)(a)), and the cap applies to that award.
- The Housing Benefit cap (HB Regs 2006 Part 8A) reaches only Housing Benefit
  under the working-age regulations. By reg 5 those cover a claimant or
  partner over the qualifying age for State Pension Credit only while either
  of them is on Universal Credit, Income Support, income-based JSA or
  income-related ESA.
- For Council Tax Reduction a "pensioner" has reached the qualifying age and
  neither they nor any partner is on those legacy benefits or has an award of
  Universal Credit (England SI 2012/2885 reg 3(1); Wales SI 2013/3029 reg
  3(1); Scotland SSI 2021/249 reg 3 and SSI 2012/319 reg 12).

Universal Credit needs a claimant or partner under the qualifying age (UC
Regs 2013 reg 3(2)(a)). The model's is_uc_eligible counts any working-age
adult, so it can pay Universal Credit to a pensioner whose only younger adult
is a qualifying young person; such an award does not count as being on
Universal Credit here. "On Universal Credit" below means an award before the
cap with a claimant or partner under State Pension age. Legacy income-related
benefit is set as an input.

Invariants, for every drawn population of families:

P1  Both new tests hold exactly when a claimant or partner is over State
    Pension age and the family is neither on Universal Credit nor on a legacy
    income-related benefit.
P2  Every Universal Credit award is capped unless a non-age exception applies:
    such a family has a finite benefit cap.
P3  Differential against the formulas before this change. A family with no
    member over State Pension age, or one over it with neither Universal
    Credit nor a legacy income-related benefit, gets exactly the same benefit
    cap, Universal Credit, Housing Benefit, Council Tax Reduction and household
    net income.
P4  The change only removes exemptions: exempt now implies exempt before, the
    cap is never higher, and Universal Credit and Housing Benefit never rise.
    A CTR pensioner now was a CTR pensioner before.
P5  The model's Welsh and Scottish CTR formulas do not route on pensioner
    status, but they count Universal Credit as income. So their CTR changes
    only through Universal Credit: unchanged where Universal Credit is
    unchanged, and never lower where the cap has lowered Universal Credit.
P6  Metamorphic: with a Universal Credit award, adding a member over State
    Pension age to a couple's ages (making it mixed-age) never exempts it from
    the cap.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from policyengine_core.reforms import Reform

from policyengine_uk import Simulation
from policyengine_uk.model_api import *

PERIOD = 2026
PROPERTY_SETTINGS = settings(
    max_examples=15,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
PENSION_AGE = st.integers(67, 95)
WORKING_AGE = st.integers(25, 60)
# Qualifying young people are 18: at 19 the UC definition also needs the
# course to have started before 19, which is a separate input.
YOUNG_PERSON = st.just(18)
SHAPES = {
    "single_pension": [("adult", PENSION_AGE)],
    "couple_pension": [("adult", PENSION_AGE), ("adult", PENSION_AGE)],
    "mixed_age": [("adult", PENSION_AGE), ("adult", WORKING_AGE)],
    "single_working": [("adult", WORKING_AGE)],
    "couple_working": [("adult", WORKING_AGE), ("adult", WORKING_AGE)],
    "pension_with_young_person": [("adult", PENSION_AGE), ("young", YOUNG_PERSON)],
}
# Weighted towards the families this change is about.
SHAPE_DRAWS = sorted(SHAPES) + ["mixed_age", "mixed_age", "pension_with_young_person"]
PLACES = [
    ("ENGLAND", "MAIDSTONE", "SOUTH_EAST"),
    ("ENGLAND", "NEWHAM", "LONDON"),
    ("ENGLAND", "WESTMINSTER", "LONDON"),
    ("ENGLAND", "OXFORD", "SOUTH_EAST"),
    ("WALES", "CARDIFF", "WALES"),
    ("SCOTLAND", "GLASGOW_CITY", "SCOTLAND"),
]
TENURES = ["RENT_FROM_COUNCIL", "RENT_PRIVATELY", "OWNED_OUTRIGHT"]


# The two formulas as they were before this change, kept as the reference for
# the differential invariants.
class is_benefit_cap_exempt_other(Variable):
    value_type = bool
    entity = BenUnit
    label = "Benefit cap exemption before this change"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        has_pensioner = benunit.any(benunit.members("is_SP_age", period))
        afcs = benunit("afcs", period) > 0
        esa_support_component = benunit("esa_contrib", period) > 0
        return has_pensioner | afcs | esa_support_component


class council_tax_reduction_household_has_pensioner(Variable):
    value_type = bool
    entity = Household
    label = "CTR pensioner test before this change"
    definition_period = YEAR

    def formula(household, period, parameters):
        person = household.members
        claimant_benunit = person.benunit("benunit_contains_household_head", period)
        return household.any(claimant_benunit & person("is_SP_age", period))


class before_this_change(Reform):
    def apply(self):
        self.update_variable(is_benefit_cap_exempt_other)
        self.update_variable(council_tax_reduction_household_has_pensioner)


@st.composite
def families(draw):
    shape = draw(st.sampled_from(SHAPE_DRAWS))
    country, local_authority, region = draw(st.sampled_from(PLACES))
    tenure = draw(st.sampled_from(TENURES))
    return dict(
        shape=shape,
        members=[(role, draw(age)) for role, age in SHAPES[shape]],
        children=draw(st.integers(0, 4)),
        country=country,
        local_authority=local_authority,
        region=region,
        tenure=tenure,
        rent=0 if tenure == "OWNED_OUTRIGHT" else draw(st.integers(0, 30_000)),
        earnings=draw(st.sampled_from([0, 0, 5_000, 25_000])),
        state_pension=draw(st.sampled_from([0, 9_000, 12_000])),
        would_claim_uc=draw(st.sampled_from([True, True, False])),
        hb_reported=draw(st.sampled_from([0, 0, 5_000])),
        ctb_reported=draw(st.sampled_from([0, 0, 700])),
        legacy=draw(st.sampled_from([0, 0, 0, 3_000])),
    )


def situation(units):
    people, benunits, households = {}, {}, {}
    for i, unit in enumerate(units):
        names = []
        has_young_person = any(role == "young" for role, _ in unit["members"])
        for j, (role, age) in enumerate(unit["members"]):
            name = f"p{i}_{j}"
            person = {"age": {PERIOD: age}}
            if role == "young":
                person["current_education"] = {PERIOD: "UPPER_SECONDARY"}
            elif age >= 67:
                person["state_pension_reported"] = {PERIOD: unit["state_pension"]}
            else:
                person["employment_income"] = {PERIOD: unit["earnings"]}
            if role == "adult" and has_young_person:
                person["is_parent"] = {PERIOD: True}
            if j == 0:
                person["housing_benefit_reported"] = {PERIOD: unit["hb_reported"]}
                person["council_tax_benefit_reported"] = {PERIOD: unit["ctb_reported"]}
            people[name] = person
            names.append(name)
        for k in range(unit["children"]):
            name = f"p{i}_c{k}"
            people[name] = {"age": {PERIOD: 2 + 3 * k}}
            names.append(name)
        benunit = {
            "members": names,
            "would_claim_uc": {PERIOD: unit["would_claim_uc"]},
            # claims_all_entitled_benefits sums reported benefits across the
            # whole simulation, so it is set per family.
            "claims_all_entitled_benefits": {
                PERIOD: unit["hb_reported"] == 0 and unit["ctb_reported"] == 0
            },
        }
        if unit["legacy"]:
            benunit["jsa_income"] = {PERIOD: unit["legacy"]}
        benunits[f"b{i}"] = benunit
        households[f"h{i}"] = {
            "members": names,
            "country": {PERIOD: unit["country"]},
            "local_authority": {PERIOD: unit["local_authority"]},
            "region": {PERIOD: unit["region"]},
            "tenure_type": {PERIOD: unit["tenure"]},
            "rent": {PERIOD: unit["rent"]},
            "council_tax": {PERIOD: 1_800},
            "savings": {PERIOD: 0},
        }
    return {"people": people, "benunits": benunits, "households": households}


BENUNIT = [
    "is_uc_entitled",
    "housing_benefit_pension_age_regulations_apply",
    "council_tax_reduction_pensioner",
    "is_benefit_cap_exempt",
    "is_benefit_cap_exempt_health_disability",
    "is_benefit_cap_exempt_earnings",
    "is_benefit_cap_exempt_other",
    "benefit_cap",
    "universal_credit",
    "housing_benefit",
    "council_tax_benefit",
    "afcs",
    "esa_contrib",
]
HOUSEHOLD = ["council_tax_reduction_household_has_pensioner", "household_net_income"]
BEFORE = [
    "is_benefit_cap_exempt",
    "benefit_cap",
    "universal_credit",
    "housing_benefit",
    "council_tax_benefit",
    "council_tax_reduction_household_has_pensioner",
    "household_net_income",
]


def calculate(units, before=False):
    simulation = Simulation(situation=situation(units))
    if before:
        simulation.apply_reform(before_this_change)
        names = BEFORE
    else:
        names = BENUNIT + HOUSEHOLD
    return {name: np.asarray(simulation.calculate(name, PERIOD)) for name in names}


def has_pension_age_claimant(unit):
    return any(role == "adult" and age >= 67 for role, age in unit["members"])


def has_working_age_claimant(unit):
    return any(role == "adult" and age < 67 for role, age in unit["members"])


def close(a, b):
    return (a == b) or abs(a - b) < 0.01


@PROPERTY_SETTINGS
@given(st.lists(families(), min_size=10, max_size=30))
def test_benefit_cap_and_ctr_pension_age_invariants(units):
    now = calculate(units)
    before = calculate(units, before=True)
    for i, unit in enumerate(units):
        on_uc = bool(now["is_uc_entitled"][i]) and has_working_age_claimant(unit)
        legacy = unit["legacy"] > 0
        # P1
        expected = has_pension_age_claimant(unit) and not (on_uc or legacy)
        assert now["housing_benefit_pension_age_regulations_apply"][i] == expected
        assert now["council_tax_reduction_pensioner"][i] == expected, unit
        # P2
        other_exception = (
            now["is_benefit_cap_exempt_health_disability"][i]
            or now["is_benefit_cap_exempt_earnings"][i]
            or now["afcs"][i] > 0
            or now["esa_contrib"][i] > 0
        )
        if on_uc and not other_exception:
            assert not now["is_benefit_cap_exempt"][i], unit
            assert np.isfinite(now["benefit_cap"][i]), unit
        # P3
        if not has_pension_age_claimant(unit) or not (on_uc or legacy):
            for name in BEFORE:
                assert close(now[name][i], before[name][i]), (name, unit)
        # P4
        if now["is_benefit_cap_exempt"][i]:
            assert before["is_benefit_cap_exempt"][i], unit
        assert now["benefit_cap"][i] <= before["benefit_cap"][i], unit
        assert now["universal_credit"][i] <= before["universal_credit"][i] + 0.01
        assert now["housing_benefit"][i] <= before["housing_benefit"][i] + 0.01
        if now["council_tax_reduction_household_has_pensioner"][i]:
            assert before["council_tax_reduction_household_has_pensioner"][i], unit
        # P5
        if unit["country"] in ("WALES", "SCOTLAND"):
            ctr_now, ctr_before = (
                now["council_tax_benefit"][i],
                before["council_tax_benefit"][i],
            )
            if close(now["universal_credit"][i], before["universal_credit"][i]):
                assert close(ctr_now, ctr_before), unit
            else:
                assert ctr_now >= ctr_before - 0.01, unit


@PROPERTY_SETTINGS
@given(
    st.lists(
        st.fixed_dictionaries(
            dict(
                working_age=WORKING_AGE,
                pension_age=PENSION_AGE,
                children=st.integers(0, 4),
                uc=st.integers(1, 40_000),
                child_benefit=st.integers(0, 5_000),
                london=st.booleans(),
            )
        ),
        min_size=1,
        max_size=20,
    )
)
def test_a_pension_age_partner_never_exempts_a_uc_award(couples):
    # P6: the same couple on the same Universal Credit award, first with two
    # working-age members, then with the older member over State Pension age.
    def run(older_is_pension_age):
        people, benunits, households = {}, {}, {}
        for i, c in enumerate(couples):
            older = c["pension_age"] if older_is_pension_age else c["working_age"]
            names = [f"p{i}_a", f"p{i}_b"] + [
                f"p{i}_c{k}" for k in range(c["children"])
            ]
            people[names[0]] = {"age": {PERIOD: older}}
            people[names[1]] = {"age": {PERIOD: c["working_age"]}}
            for k, name in enumerate(names[2:]):
                people[name] = {"age": {PERIOD: 2 + 3 * k}}
            benunits[f"b{i}"] = {
                "members": names,
                "universal_credit_pre_benefit_cap": {PERIOD: c["uc"]},
                "child_benefit": {PERIOD: c["child_benefit"]},
                "uc_deductions": {PERIOD: 0},
            }
            households[f"h{i}"] = {
                "members": names,
                "region": {PERIOD: "LONDON" if c["london"] else "NORTH_WEST"},
            }
        simulation = Simulation(
            situation={"people": people, "benunits": benunits, "households": households}
        )
        return {
            name: np.asarray(simulation.calculate(name, PERIOD))
            for name in ["is_benefit_cap_exempt", "benefit_cap_reduction"]
        }

    working, mixed = run(False), run(True)
    for i, c in enumerate(couples):
        assert mixed["is_benefit_cap_exempt"][i] == working["is_benefit_cap_exempt"][i]
        assert close(
            mixed["benefit_cap_reduction"][i], working["benefit_cap_reduction"][i]
        ), c
