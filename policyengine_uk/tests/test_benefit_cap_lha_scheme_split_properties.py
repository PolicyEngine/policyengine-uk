"""Differential and property tests for splitting the benefit cap and the LHA
shared accommodation rate between Universal Credit and Housing Benefit.

Until this change one set of variables served both schemes: the cap rate
(``is_benefit_cap_single_claimant_rate``), the exceptions
(``is_benefit_cap_exempt_health_disability``, ``_other``, ``_earnings``),
the cap and its reduction (``benefit_cap``, ``benefit_cap_reduction``) and
the shared accommodation test behind ``LHA_category``. A Universal Credit
claim by a member of a couple as a single person (UC Regs 2013 reg. 3(3))
followed the Universal Credit rule unless the family claimed legacy
benefits. ``REFERENCE`` re-adds those formulas from the parent commit
under ``reference_`` names, so one simulation computes the old and the new
values for the same families. They are verbatim except for the names they
read, the inlined stopgap helpers and the earnings exception's dead code.
The reference awards read the current ``uc_deductions``, which these
single-household simulations leave at nil.

Invariants, each over generated families and the explicit examples:

1. Cap rate. Where the two schemes' rates agree, the old shared rate is
   that rate. Where they differ, the old rate was the scheme the family
   claimed under for a reg. 3(3) single claim (legacy: Housing Benefit;
   otherwise Universal Credit), and otherwise the family rate whenever
   either scheme gave it (the old test took responsibility under either).
2. Exceptions. With nobody at State Pension age and no armed forces
   independence payment: where the schemes agree, the old exception is
   theirs; with no reg. 3(3) single claim, the old exception is exactly the
   union of the two schemes' (it listed both schemes' grounds). The age and
   AFIP cases are intended changes (the UC cap has no age exception; HB
   Regs 2006 reg. 5; AFIP lifts both caps under UC reg. 83(1)(c) with reg. 2
   and HB reg. 75F(1)(ea)) and are pinned in the YAML tests and examples.
3. LHA category. Without armed forces independence payment (added to the
   exceptions of both schemes here), the old category is the new category
   of the scheme the family claims under (legacy: Housing Benefit,
   otherwise Universal Credit), and with no reg. 3(3) single claim the two
   new categories are equal.
4. Reductions. 0 <= each scheme's reduction <= the excess of the welfare
   benefits over that scheme's cap; the UC reduction is the excess less
   the childcare costs element (reg. 81); Housing Benefit after the cap
   keeps at least min(its amount before the cap, 50 pence a week) (reg.
   75D(2)); ``benefit_cap_reduction`` is the sum of the two; no family has
   both awards before the cap.
5. Awards. Where a scheme's cap equals the old cap and neither reg. 81's
   childcare offset nor reg. 75D(2)'s minimum applies, its award equals the
   award under the old shared cap.
6. The maximum rent (LHA) is the rent capped at the Housing Benefit LHA
   rate, which equals the Universal Credit category's weekly rate wherever
   the two categories agree.
"""

import copy

import numpy as np
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from policyengine_core.reforms import Reform
from policyengine_uk import Simulation
from policyengine_uk.model_api import *
from policyengine_uk.utils.benefit_unit import add_for_members
from policyengine_uk.variables.gov.dwp.LHA_category import LHACategory

# model_api's YEAR is the period type the reference variables use.
PERIOD = 2026
PROPERTY_SETTINGS = settings(
    max_examples=12,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)


# ---------------------------------------------------------------------------
# The shared rules before the split (parent commit 17b9b8a16), verbatim but
# for the names and the inlined stopgap helpers.


def _single_claim_in_shared_rules(benunit, period):
    return benunit("uc_member_of_couple_claims_as_single_person", period) & ~benunit(
        "claims_legacy_benefits", period
    )


def _other_member_in_shared_rules(person, period):
    return (
        person("uc_is_ineligible_partner", period)
        & person.benunit("uc_member_of_couple_claims_as_single_person", period)
        & ~person.benunit("claims_legacy_benefits", period)
    )


class reference_is_benefit_cap_single_claimant_rate(Variable):
    value_type = bool
    entity = BenUnit
    label = "Old shared benefit cap single claimant rate"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        single_claimant = ~benunit("is_couple", period) | _single_claim_in_shared_rules(
            benunit, period
        )
        return single_claimant & ~benunit(
            "is_responsible_for_child_or_young_person_for_uc_or_housing_benefit",
            period,
        )


class reference_is_benefit_cap_exempt_health_disability(Variable):
    value_type = bool
    entity = BenUnit
    label = "Old shared health and disability exception"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        person = benunit.members
        not_a_claimant = _other_member_in_shared_rules(person, period)
        has_lcwra = benunit.any(
            person("uc_limited_capability_for_WRA", period) & ~not_a_claimant
        )
        gets_uc_carer_element = benunit("uc_carer_element", period) > 0
        qualifying_personal_benefits = add_for_members(
            benunit,
            period,
            [
                "attendance_allowance",
                "carers_allowance",
                "carer_support_payment",
                "dla",
                "pip_dl",
                "pip_m",
                "iidb",
            ],
            ~not_a_claimant,
        )
        qualifying_benunit_benefits = add(
            benunit, period, ["esa_income", "working_tax_credit"]
        )
        afcs = add_for_members(benunit, period, ["afcs"], ~not_a_claimant) > 0
        esa_support_component = (
            add_for_members(benunit, period, ["esa_contrib"], ~not_a_claimant) > 0
        )
        return (
            has_lcwra
            | gets_uc_carer_element
            | (qualifying_personal_benefits > 0)
            | (qualifying_benunit_benefits > 0)
            | afcs
            | esa_support_component
        )


class reference_is_benefit_cap_exempt_other(Variable):
    value_type = bool
    entity = BenUnit
    label = "Old shared other exception"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        person = benunit.members
        has_pensioner = benunit.any(person("is_SP_age", period))
        not_a_claimant = _other_member_in_shared_rules(person, period)
        afcs = add_for_members(benunit, period, ["afcs"], ~not_a_claimant) > 0
        esa_support_component = (
            add_for_members(benunit, period, ["esa_contrib"], ~not_a_claimant) > 0
        )
        return has_pensioner | afcs | esa_support_component


class reference_is_benefit_cap_exempt_earnings(Variable):
    value_type = bool
    entity = BenUnit
    label = "Old shared earnings exception"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        uc_earned = benunit.sum(
            benunit.members("employment_income", period)
            + benunit.members("self_employment_income", period)
            - benunit.members("income_tax", period)
            - benunit.members("national_insurance", period)
        )
        return uc_earned >= 10_152


class reference_is_benefit_cap_exempt(Variable):
    value_type = bool
    entity = BenUnit
    label = "Old shared benefit cap exemption"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return (
            benunit("reference_is_benefit_cap_exempt_health_disability", period)
            | benunit("reference_is_benefit_cap_exempt_earnings", period)
            | benunit("reference_is_benefit_cap_exempt_other", period)
        )


class reference_benefit_cap(Variable):
    value_type = float
    entity = BenUnit
    label = "Old shared benefit cap"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        single_claimant = benunit(
            "reference_is_benefit_cap_single_claimant_rate", period
        )
        household_region = benunit.members.household("region", period)
        region = benunit.value_from_first_person(household_region)
        in_london = region == household_region.possible_values.LONDON
        cap = parameters(period).gov.dwp.benefit_cap
        rate = select(
            [
                single_claimant & in_london,
                single_claimant & ~in_london,
                ~single_claimant & in_london,
                ~single_claimant & ~in_london,
            ],
            [
                cap.single.in_london,
                cap.single.outside_london,
                cap.non_single.in_london,
                cap.non_single.outside_london,
            ],
        )
        exempt = benunit("reference_is_benefit_cap_exempt", period)
        return where(exempt, np.inf, rate)


class reference_benefit_cap_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Old shared benefit cap reduction"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        capped = add(
            benunit,
            period,
            [
                "child_benefit",
                "child_tax_credit",
                "jsa_income",
                "income_support",
                "esa_income",
                "universal_credit_pre_benefit_cap",
                "housing_benefit_pre_benefit_cap",
                "jsa_contrib",
                "incapacity_benefit",
                "esa_contrib",
                "sda",
            ],
        )
        return max_(capped - benunit("reference_benefit_cap", period), 0)


class reference_is_lha_shared_accommodation_rate_specified_renter(Variable):
    value_type = bool
    entity = BenUnit
    label = "Old shared specified renter test"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.LHA
        person = benunit.members
        claims_as_single_person = _single_claim_in_shared_rules(benunit, period)
        other_member = _other_member_in_shared_rules(person, period)
        renter = person("is_claimant_or_partner", period) & ~other_member
        renter_age = benunit.max(where(renter, person("age", period), -np.inf))
        # The list before this change, without armed forces independence
        # payment.
        excepted_disabled_renter = benunit.any(
            renter
            & (
                add(
                    person,
                    period,
                    ["attendance_allowance", "dla_sc_middle_plus", "pip_dl"],
                )
                > 0
            )
        )
        return (
            (~benunit("is_couple", period) | claims_as_single_person)
            & (renter_age < p.shared_accommodation_age_threshold)
            & ~benunit(
                "is_responsible_for_child_or_young_person_for_uc_or_housing_benefit",
                period,
            )
            & ~benunit("lha_renter_has_non_dependant", period)
            & ~excepted_disabled_renter
        )


class reference_LHA_category(Variable):
    value_type = Enum
    entity = BenUnit
    label = "Old shared LHA category"
    definition_period = YEAR
    possible_values = LHACategory
    default_value = LHACategory.C

    def formula(benunit, period, parameters):
        num_rooms = benunit("LHA_allowed_bedrooms", period.this_year)
        household = benunit.members.household
        is_shared = benunit.any(household("is_shared_accommodation", period.this_year))
        can_only_claim_shared = benunit(
            "reference_is_lha_shared_accommodation_rate_specified_renter", period
        )
        return select(
            [
                is_shared | can_only_claim_shared,
                num_rooms == 1,
                num_rooms == 2,
                num_rooms == 3,
                num_rooms > 3,
            ],
            [
                LHACategory.A,
                LHACategory.B,
                LHACategory.C,
                LHACategory.D,
                LHACategory.E,
            ],
        )


class reference_universal_credit(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit under the old shared cap"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        # The parent's formula, reading the old shared reduction. Deductions
        # are the current uc_deductions, which read the UC reduction; the
        # single-household simulations here have none (uc_has_deduction).
        uc_max_entitlement = benunit("universal_credit_pre_benefit_cap", period)
        benefit_cap_reduction = benunit("reference_benefit_cap_reduction", period)
        deductions = benunit("uc_deductions", period)
        floor_rate = parameters(
            period
        ).gov.dwp.universal_credit.deductions.protected_floor
        total_reductions = benefit_cap_reduction + deductions
        max_reductions = where(
            floor_rate > 0,
            (1 - floor_rate) * benunit("uc_standard_allowance", period),
            np.inf,
        )
        return max_(uc_max_entitlement - min_(total_reductions, max_reductions), 0)


class reference_housing_benefit(Variable):
    value_type = float
    entity = BenUnit
    label = "Housing Benefit under the old shared cap"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return max_(
            0,
            benunit("housing_benefit_pre_benefit_cap", period)
            - benunit("reference_benefit_cap_reduction", period),
        )


REFERENCE_VARIABLES = [
    reference_is_benefit_cap_single_claimant_rate,
    reference_is_benefit_cap_exempt_health_disability,
    reference_is_benefit_cap_exempt_other,
    reference_is_benefit_cap_exempt_earnings,
    reference_is_benefit_cap_exempt,
    reference_benefit_cap,
    reference_benefit_cap_reduction,
    reference_is_lha_shared_accommodation_rate_specified_renter,
    reference_LHA_category,
    reference_universal_credit,
    reference_housing_benefit,
]


class REFERENCE(Reform):
    def apply(self):
        for variable in REFERENCE_VARIABLES:
            self.add_variable(variable)


# ---------------------------------------------------------------------------
# Families.

REGIONS = ["LONDON", "NORTH_EAST", "WALES", "SCOTLAND"]
rarely = st.integers(0, 5).map(lambda n: n == 0)
sometimes_paid = st.one_of(*[st.just(0.0)] * 4, st.floats(500, 6_000))
earnings = st.one_of(st.just(0.0), st.just(0.0), st.floats(0, 40_000))


@st.composite
def adults(draw, ages):
    return dict(
        age=draw(ages),
        employment_income=draw(earnings),
        uc_limited_capability_for_WRA=draw(rarely),
        care_hours=draw(st.sampled_from([0, 0, 0, 0, 35])),
        attendance_allowance=draw(sometimes_paid),
        pip_dl=draw(sometimes_paid),
        carers_allowance=draw(sometimes_paid),
        afcs=draw(sometimes_paid),
        esa_contrib=draw(sometimes_paid),
        armed_forces_independence_payment=draw(
            st.one_of(*[st.just(0.0)] * 6, st.just(6_000.0))
        ),
    )


@st.composite
def families(draw):
    has_partner = draw(st.booleans())
    return dict(
        claimant=draw(adults(st.integers(18, 75))),
        partner=draw(adults(st.integers(16, 80))) if has_partner else None,
        partner_flag=draw(st.sampled_from([None, None, True, False])),
        children=[
            dict(
                age=draw(st.integers(0, 19)),
                in_education=draw(st.booleans()),
            )
            for _ in range(draw(st.integers(0, 3)))
        ],
        legacy=draw(st.booleans()),
        working_tax_credit=draw(st.one_of(*[st.just(0.0)] * 4, st.just(1_500.0))),
        childcare=draw(st.one_of(*[st.just(0.0)] * 3, st.floats(500, 8_000))),
        rent=draw(st.floats(3_000, 30_000)),
        region=draw(st.sampled_from(REGIONS)),
        lodger=draw(rarely),
    )


populations = st.lists(families(), min_size=1, max_size=6)


def adult_inputs(age, **inputs):
    values = dict(
        age=age,
        employment_income=0.0,
        uc_limited_capability_for_WRA=False,
        care_hours=0,
        attendance_allowance=0.0,
        pip_dl=0.0,
        carers_allowance=0.0,
        afcs=0.0,
        esa_contrib=0.0,
        armed_forces_independence_payment=0.0,
    )
    values.update(inputs)
    return values


def family(claimant, partner=None, **kw):
    values = dict(
        claimant=claimant,
        partner=partner,
        partner_flag=None,
        children=[],
        legacy=False,
        working_tax_credit=0.0,
        childcare=0.0,
        rent=12_000.0,
        region="NORTH_EAST",
        lodger=False,
        benunit_inputs={},
    )
    values.update(kw)
    return values


def example_families():
    """Families in which each scheme difference occurs."""
    return [
        # A reg. 3(3) single claim, Universal Credit (partner 17, no reg. 8
        # circumstance): single for the UC cap and shared rate.
        family(adult_inputs(24), adult_inputs(17), rent=8_000.0),
        # The same couple claiming legacy benefits.
        family(adult_inputs(24), adult_inputs(17), legacy=True, rent=8_000.0),
        # A large family on UC above the cap, with childcare costs (reg. 81).
        family(
            adult_inputs(30, employment_income=3_000.0),
            adult_inputs(30),
            children=[dict(age=a, in_education=False) for a in (1, 3, 5)],
            childcare=4_000.0,
            rent=24_000.0,
            region="LONDON",
        ),
        # A lone parent with an HB-only young person (19, started at 17).
        family(
            adult_inputs(30),
            children=[dict(age=19, in_education=True)],
            rent=9_000.0,
        ),
        # A single renter under 35 receiving AFIP.
        family(adult_inputs(28, armed_forces_independence_payment=6_000.0)),
        # A mixed-age couple on UC with no other ground.
        family(adult_inputs(70), adult_inputs(40)),
        # A single claimant with LCWRA continuing a Housing Benefit award.
        family(adult_inputs(30, uc_limited_capability_for_WRA=True), legacy=True),
        # A lone parent of five on Housing Benefit and income support whose
        # excess is more than their Housing Benefit (reg. 75D(2)).
        family(
            adult_inputs(30),
            children=[dict(age=a, in_education=False) for a in (1, 3, 5, 7, 9)],
            legacy=True,
            rent=20_000.0,
            region="LONDON",
            benunit_inputs=dict(income_support=24_000.0),
        ),
    ]


EXAMPLE_FAMILIES = example_families()


def situation(population, year=PERIOD):
    people, benunits, households, lodger_units = {}, {}, {}, {}
    for i, f in enumerate(population):
        members = []
        adults_in = [("claimant", f["claimant"])]
        if f["partner"] is not None:
            adults_in.append(("partner", f["partner"]))
        for role, inputs in adults_in:
            name = f"{role}{i}"
            person = {k: {year: v} for k, v in inputs.items()}
            person["is_claimant_or_partner"] = {year: True}
            person["would_claim_marriage_allowance"] = {year: False}
            if role == "partner" and f["partner_flag"] is not None:
                person["uc_is_ineligible_partner"] = {year: f["partner_flag"]}
            people[name] = person
            members.append(name)
        for k, child in enumerate(f["children"]):
            name = f"child{i}_{k}"
            people[name] = {
                "age": {year: child["age"]},
                "is_claimant_or_partner": {year: False},
                "current_education": {
                    year: "UPPER_SECONDARY"
                    if child["in_education"]
                    else "NOT_IN_EDUCATION"
                },
            }
            if child["age"] == 19 and child["in_education"]:
                # Started at 17 and past UC's terminal date: a Child Benefit
                # (HB) young person but not a UC qualifying young person.
                people[name][
                    "age_started_or_accepted_current_education_or_training"
                ] = {year: 17}
                people[name][
                    "is_before_universal_credit_qualifying_young_person_terminal_date"
                ] = {year: False}
            members.append(name)
        benunit = {
            "members": list(members),
            "would_claim_uc": {year: not f["legacy"]},
            "working_tax_credit": {year: f["working_tax_credit"]},
        }
        if f["childcare"]:
            benunit["uc_childcare_element"] = {year: f["childcare"]}
        for variable, value in f.get("benunit_inputs", {}).items():
            benunit[variable] = {year: value}
        benunits[f"b{i}"] = benunit
        household_members = list(members)
        if f["lodger"]:
            name = f"lodger{i}"
            people[name] = {"age": {year: 45}}
            lodger_units[f"lodger_unit{i}"] = {"members": [name]}
            household_members.append(name)
        if f["legacy"]:
            # A continuing Housing Benefit award (SI 2014/1230 reg. 8).
            people[f"claimant{i}"]["housing_benefit_reported"] = {year: 3_000.0}
        households[f"h{i}"] = {
            "members": household_members,
            "rent": {year: f["rent"]},
            "tenure_type": {year: "RENT_PRIVATELY"},
            "region": {year: f["region"]},
        }
    benunits.update(lodger_units)
    return {"people": people, "benunits": benunits, "households": households}


BENUNIT_VARIABLES = [
    "is_couple",
    "claims_legacy_benefits",
    "uc_member_of_couple_claims_as_single_person",
    "is_uc_benefit_cap_single_claimant_rate",
    "is_housing_benefit_benefit_cap_single_claimant_rate",
    "reference_is_benefit_cap_single_claimant_rate",
    "is_responsible_for_child_or_qualifying_young_person_for_universal_credit",
    "is_responsible_for_child_or_young_person_for_legacy_benefits",
    "is_uc_benefit_cap_exempt",
    "is_housing_benefit_benefit_cap_exempt",
    "reference_is_benefit_cap_exempt",
    "uc_benefit_cap",
    "housing_benefit_benefit_cap",
    "reference_benefit_cap",
    "benefit_cap_welfare_benefits",
    "uc_benefit_cap_reduction",
    "housing_benefit_benefit_cap_reduction",
    "benefit_cap_reduction",
    "reference_benefit_cap_reduction",
    "uc_childcare_element",
    "universal_credit_pre_benefit_cap",
    "housing_benefit_pre_benefit_cap",
    "universal_credit",
    "housing_benefit",
    "reference_universal_credit",
    "reference_housing_benefit",
    "benunit_rent",
    "LHA_cap",
    "housing_benefit_LHA_rate",
    "BRMA_LHA_rate",
]
CATEGORIES = ["LHA_category", "housing_benefit_LHA_category", "reference_LHA_category"]


def calculate(population):
    sim = Simulation(situation=situation(population), reform=REFERENCE)
    values = {v: np.asarray(sim.calculate(v, PERIOD)) for v in BENUNIT_VARIABLES}
    for v in CATEGORIES:
        values[v] = np.asarray(sim.calculate(v, PERIOD)).astype(str)
    sp_age = np.asarray(sim.calculate("is_SP_age", PERIOD, map_to="benunit"))
    values["anyone_sp_age"] = sp_age > 0
    afip = np.asarray(
        sim.calculate("armed_forces_independence_payment", PERIOD, map_to="benunit")
    )
    values["afip"] = afip > 0
    values["wtc_exempt"] = np.asarray(
        sim.calculate(
            "is_housing_benefit_benefit_cap_exempt_working_tax_credit", PERIOD
        )
    ).astype(bool)
    return values


# ---------------------------------------------------------------------------
# Properties.


@PROPERTY_SETTINGS
@given(population=populations)
@example(population=example_families())
def test_cap_rate_is_the_old_rate_where_the_schemes_agree(population):
    v = calculate(population)
    uc, hb, ref = (
        v["is_uc_benefit_cap_single_claimant_rate"],
        v["is_housing_benefit_benefit_cap_single_claimant_rate"],
        v["reference_is_benefit_cap_single_claimant_rate"],
    )
    agree = uc == hb
    np.testing.assert_array_equal(ref[agree], uc[agree], err_msg=str(population))
    single_claim = v["uc_member_of_couple_claims_as_single_person"].astype(bool)
    legacy = v["claims_legacy_benefits"].astype(bool)
    same_responsibility = (
        v["is_responsible_for_child_or_qualifying_young_person_for_universal_credit"]
        == v["is_responsible_for_child_or_young_person_for_legacy_benefits"]
    )
    # A reg. 3(3) single claim with no responsibility difference: the old
    # rate was the claimed scheme's.
    stopgap = ~agree & single_claim & same_responsibility
    np.testing.assert_array_equal(
        ref[stopgap], np.where(legacy, hb, uc)[stopgap], err_msg=str(population)
    )
    # A responsibility difference: the old test gave the family rate if
    # either scheme did.
    union = ~agree & ~single_claim
    np.testing.assert_array_equal(ref[union], (uc & hb)[union], err_msg=str(population))
    # HB has no single claim by a member of a couple (HB Regs 2006 reg. 2(1)).
    assert not np.any(hb[v["is_couple"].astype(bool)]), population


@PROPERTY_SETTINGS
@given(population=populations)
@example(population=example_families())
def test_exceptions_are_the_old_exception_where_the_schemes_agree(population):
    v = calculate(population)
    uc, hb, ref = (
        v["is_uc_benefit_cap_exempt"].astype(bool),
        v["is_housing_benefit_benefit_cap_exempt"].astype(bool),
        v["reference_is_benefit_cap_exempt"].astype(bool),
    )
    # Intended changes, pinned in YAML instead: the UC cap has no age
    # exception and HB reg 5 sets the pension-age one; armed forces
    # independence payment now lifts both caps (UC reg 83(1)(c) with reg 2;
    # HB reg 75F(1)(ea)).
    working_age = ~v["anyone_sp_age"] & ~v["afip"]
    single_claim = v["uc_member_of_couple_claims_as_single_person"].astype(bool)
    legacy = v["claims_legacy_benefits"].astype(bool)
    # The old exception listed both schemes' grounds.
    union = working_age & ~single_claim
    np.testing.assert_array_equal(ref[union], (uc | hb)[union], err_msg=str(population))
    agree = union & (uc == hb)
    np.testing.assert_array_equal(ref[agree], uc[agree], err_msg=str(population))
    # A reg. 3(3) single claim outside legacy benefits: the old exception
    # left out the other member as UC does, and added working tax credit.
    uc_single_claim = working_age & single_claim & ~legacy
    np.testing.assert_array_equal(
        ref[uc_single_claim],
        (uc | v["wtc_exempt"])[uc_single_claim],
        err_msg=str(population),
    )


@PROPERTY_SETTINGS
@given(population=populations)
@example(population=example_families())
def test_lha_category_is_the_claimed_schemes_old_category(population):
    v = calculate(population)
    uc, hb, ref = (
        v["LHA_category"],
        v["housing_benefit_LHA_category"],
        v["reference_LHA_category"],
    )
    legacy = v["claims_legacy_benefits"].astype(bool)
    no_afip = ~v["afip"]
    claimed = np.where(legacy, hb, uc)
    np.testing.assert_array_equal(
        ref[no_afip], claimed[no_afip], err_msg=str(population)
    )
    no_single_claim = ~v["uc_member_of_couple_claims_as_single_person"].astype(bool)
    np.testing.assert_array_equal(
        uc[no_single_claim], hb[no_single_claim], err_msg=str(population)
    )


@PROPERTY_SETTINGS
@given(population=populations)
@example(population=example_families())
def test_each_scheme_reduces_by_its_own_excess(population):
    v = calculate(population)
    welfare = v["benefit_cap_welfare_benefits"]
    uc_excess = np.maximum(welfare - v["uc_benefit_cap"], 0)
    hb_excess = np.maximum(welfare - v["housing_benefit_benefit_cap"], 0)
    uc_red, hb_red = (
        v["uc_benefit_cap_reduction"],
        v["housing_benefit_benefit_cap_reduction"],
    )
    on_uc = v["universal_credit_pre_benefit_cap"] > 0
    hb_pre = v["housing_benefit_pre_benefit_cap"]
    # UC Regs 2013 reg. 81: the excess less the childcare costs element, on
    # an award only.
    np.testing.assert_allclose(
        uc_red,
        np.where(on_uc, np.maximum(uc_excess - v["uc_childcare_element"], 0), 0),
        atol=0.01,
        err_msg=str(population),
    )
    assert np.all((0 <= hb_red) & (hb_red <= hb_excess + 0.01)), population
    # HB Regs 2006 reg. 75D(2) with reg. 75: at least 50 pence a week stays.
    minimum = 0.5 * 52
    assert np.all(v["housing_benefit"] >= np.minimum(hb_pre, minimum) - 0.01), (
        population
    )
    assert np.all(v["housing_benefit"] <= hb_pre + 0.01), population
    np.testing.assert_allclose(
        v["benefit_cap_reduction"], uc_red + hb_red, atol=0.01, err_msg=str(population)
    )
    assert not np.any(on_uc & (hb_pre > 0)), population


@PROPERTY_SETTINGS
@given(population=populations)
@example(population=example_families())
def test_awards_are_the_old_awards_where_the_caps_agree(population):
    v = calculate(population)
    old_cap = v["reference_benefit_cap"]
    uc_same = (
        np.isclose(v["uc_benefit_cap"], old_cap, equal_nan=False)
        | (np.isinf(v["uc_benefit_cap"]) & np.isinf(old_cap))
    ) & (v["uc_childcare_element"] == 0)
    np.testing.assert_allclose(
        v["universal_credit"][uc_same],
        v["reference_universal_credit"][uc_same],
        atol=0.01,
        err_msg=str(population),
    )
    hb_pre = v["housing_benefit_pre_benefit_cap"]
    old_reduction = v["reference_benefit_cap_reduction"]
    hb_same = (
        np.isclose(v["housing_benefit_benefit_cap"], old_cap)
        | (np.isinf(v["housing_benefit_benefit_cap"]) & np.isinf(old_cap))
    ) & ((old_reduction == 0) | (hb_pre - old_reduction >= 0.5 * 52))
    np.testing.assert_allclose(
        v["housing_benefit"][hb_same],
        v["reference_housing_benefit"][hb_same],
        atol=0.01,
        err_msg=str(population),
    )


@PROPERTY_SETTINGS
@given(population=populations)
@example(population=example_families())
def test_maximum_rent_reads_the_housing_benefit_category(population):
    v = calculate(population)
    np.testing.assert_allclose(
        v["LHA_cap"],
        np.minimum(v["benunit_rent"], v["housing_benefit_LHA_rate"]),
        atol=0.01,
        err_msg=str(population),
    )
    same = v["LHA_category"] == v["housing_benefit_LHA_category"]
    np.testing.assert_allclose(
        v["housing_benefit_LHA_rate"][same],
        v["BRMA_LHA_rate"][same],
        atol=0.01,
        err_msg=str(population),
    )


def test_examples_reach_the_cases():
    """Each example changes the result it is there for."""
    v = calculate(EXAMPLE_FAMILIES)
    (
        uc_family,
        legacy_family,
        capped,
        lone_parent,
        afip,
        mixed_age,
        hb_lcwra,
        hb_floor,
    ) = range(8)
    # Reg. 3(3): single for UC, a couple for HB, whatever the legacy claim.
    for i in (uc_family, legacy_family):
        assert v["uc_member_of_couple_claims_as_single_person"][i]
        assert v["is_uc_benefit_cap_single_claimant_rate"][i]
        assert not v["is_housing_benefit_benefit_cap_single_claimant_rate"][i]
        assert v["LHA_category"][i] == "A"
        assert v["housing_benefit_LHA_category"][i] == "B"
    assert v["claims_legacy_benefits"][legacy_family]
    assert v["reference_LHA_category"][uc_family] == "A"
    assert v["reference_LHA_category"][legacy_family] == "B"
    # Reg. 81: the childcare costs element comes off the UC reduction.
    excess = v["benefit_cap_welfare_benefits"][capped] - v["uc_benefit_cap"][capped]
    assert excess > 0
    assert v["uc_benefit_cap_reduction"][capped] < excess
    assert v["universal_credit"][capped] > v["reference_universal_credit"][capped]
    # The HB-only young person: UC single claimant rate, HB lone parent.
    assert v["is_uc_benefit_cap_single_claimant_rate"][lone_parent]
    assert not v["is_housing_benefit_benefit_cap_single_claimant_rate"][lone_parent]
    assert not v["reference_is_benefit_cap_single_claimant_rate"][lone_parent]
    # AFIP: excepted from both shared rates, and lifts both caps, which the
    # old lists did not do.
    assert v["LHA_category"][afip] == v["housing_benefit_LHA_category"][afip] == "B"
    assert v["reference_LHA_category"][afip] == "A"
    assert v["is_uc_benefit_cap_exempt"][afip]
    assert v["is_housing_benefit_benefit_cap_exempt"][afip]
    assert not v["reference_is_benefit_cap_exempt"][afip]
    # The mixed-age couple on UC: the UC cap has no age exception, and with
    # the younger member on UC the HB Regs 2006 apply (reg. 5(1)(b)); the old
    # shared cap exempted any family with a pensioner.
    assert v["anyone_sp_age"][mixed_age]
    assert v["universal_credit_pre_benefit_cap"][mixed_age] > 0
    assert not v["is_uc_benefit_cap_exempt"][mixed_age]
    assert not v["is_housing_benefit_benefit_cap_exempt"][mixed_age]
    assert v["reference_is_benefit_cap_exempt"][mixed_age]
    # LCWRA is a UC exception (reg. 83(1)(a)), not an HB one (reg. 75F).
    assert v["housing_benefit_pre_benefit_cap"][hb_lcwra] > 0
    assert v["is_uc_benefit_cap_exempt"][hb_lcwra]
    assert not v["is_housing_benefit_benefit_cap_exempt"][hb_lcwra]
    assert v["reference_is_benefit_cap_exempt"][hb_lcwra]
    # Reg. 75D(2): the excess is more than the Housing Benefit, which keeps
    # 50 pence a week; the old shared reduction took it all.
    hb_pre = v["housing_benefit_pre_benefit_cap"][hb_floor]
    assert hb_pre > 0
    assert (
        v["benefit_cap_welfare_benefits"][hb_floor]
        - v["housing_benefit_benefit_cap"][hb_floor]
        > hb_pre
    )
    assert abs(v["housing_benefit"][hb_floor] - 0.5 * 52) < 0.01
    assert v["reference_housing_benefit"][hb_floor] == 0
