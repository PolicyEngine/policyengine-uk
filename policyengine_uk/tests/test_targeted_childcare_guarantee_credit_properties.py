"""Property-based tests for the Guarantee Credit route into targeted childcare.

An "eligible child" is a young child "whose parent is entitled to any one or
more of the following— ... the guaranteed element of state pension credit
under the State Pension Credit Act 2002" (SI 2014/2147 reg 1(2)). A claimant
is entitled to state pension credit only if "he has attained the qualifying
age" (SPCA 2002 s.1(2)(b)), and entitlement needs a claim (SSAA 1992 s.1).

Three versions of the route are compared:

- filed: the route when #1956 was filed, a guarantee credit computed for
  every benefit unit, max(0, minimum guarantee - Pension Credit income),
  which is positive for low-income working-age families;
- main: `guarantee_credit` > 0. Since #1896 that is zero unless the benefit
  unit is eligible for Pension Credit, but it is still positive for an
  eligible family that does not claim Pension Credit;
- fix: `in_receipt_of_guarantee_credit`, which needs Pension Credit
  eligibility, a claim, a Pension Credit payment and a positive guarantee
  credit.

Invariants, for any generated population of families with a 2-year-old, some
also with a dependent young person aged 16 to 19 in non-advanced education:

1. Qualifying age: no benefit unit whose adults are all below the qualifying
   age qualifies through the Guarantee Credit route, however low its income.
   Fails for filed; holds for main and fix.
2. Route identity: targeted childcare eligibility equals claiming it, living
   in England, not being eligible for the extended entitlement, and having at
   least one route open: Income Support, income-based JSA, income-related
   ESA, receipt of a guarantee credit, or a qualifying criterion (Universal
   Credit, and tax credits while they qualify).
3. Receipt: in the unreformed model the Guarantee Credit route is open
   exactly when pension_credit and guarantee_credit are both positive. It
   implies would_claim_pc and that the claimant and any partner are over
   State Pension age; a dependent young person's age does not matter. That is
   stricter than the law for a mixed-age couple saved by SI 2019/37 art 4,
   which is_pension_credit_eligible omits (known departure).
4. Differential against main: the fix never adds eligibility, and removes it
   exactly where a guarantee credit is computed, no Pension Credit is paid,
   and no other route is open (intended: the eligible non-claimant).
5. Metamorphic: not claiming Pension Credit closes the route and never makes
   a family eligible. Fails for filed and main; holds for fix.
6. Not claiming targeted childcare never leaves a family eligible.
7. Payment: a reform that stops Pension Credit being paid closes the route,
   with or without the Pension Credit freeze (fixed examples).
8. Under the Pension Credit freeze the route follows the baseline receipt,
   even where the reformed guarantee credit is zero, so invariants 3 and 4
   are stated for the unreformed model only (fixed example).
"""

import numpy as np
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.model_api import YEAR as YEAR_PERIOD
from policyengine_uk.model_api import BenUnit, Variable
from policyengine_uk.utils.scenario import Scenario

# Tax credits still qualify in 2025; only Universal Credit does from 2026.
YEARS = [2025, 2026, 2029]
PROPERTY_SETTINGS = settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
OUTSIDE_ENGLAND = ["WALES", "SCOTLAND", "NORTHERN_IRELAND"]
REGIONS = ["LONDON", "NORTH_EAST", "SOUTH_WEST"] + OUTSIDE_ENGLAND
# State Pension age is at least 66 in every test year, under the flat age-66
# parameter and under the date-of-birth rule with the rise to 67, so 65 and
# under is always below it. 67 and over is above it in 2025 and 2026, where
# the known families sit; no invariant needs it to be above it in 2029.
PENSION_AGE = st.integers(67, 100)
WORKING_AGE = st.integers(18, 65)
SHAPES = {
    "single_working": [WORKING_AGE],
    "couple_working": [WORKING_AGE, WORKING_AGE],
    "single_pension": [PENSION_AGE],
    "couple_pension": [PENSION_AGE, PENSION_AGE],
    "mixed_age": [PENSION_AGE, WORKING_AGE],
}
# A dependent young person in non-advanced education: 16 and 17 are children
# for HBAI, and 18 and 19 are dependants because the benefit unit has an
# identified parent. None of them is the claimant or partner.
YOUNG_PERSON_AGES = [16, 17, 18, 19]
LEGACY_BENEFITS = [
    "income_support_reported",
    "jsa_income_reported",
    "esa_income_reported",
]
money = st.floats(0, 30_000, allow_nan=False, allow_infinity=False)


@st.composite
def families(draw):
    shape = draw(st.sampled_from(sorted(SHAPES)))
    ages = [draw(age) for age in SHAPES[shape]]
    young_person = None
    # The young person must not be the eldest member (the benefit-unit head).
    if min(ages) >= 36:
        young_person = draw(st.sampled_from([None, None] + YOUNG_PERSON_AGES))
    return dict(
        ages=ages,
        young_person=young_person,
        region=draw(st.sampled_from(REGIONS)),
        earnings=draw(st.one_of(st.just(0.0), money)),
        state_pension=draw(st.one_of(st.just(0.0), money)),
        private_pension=draw(st.one_of(st.just(0.0), money)),
        savings=draw(st.one_of(st.just(0.0), st.floats(0, 40_000))),
        would_claim_pc=draw(st.booleans()),
        would_claim_uc=draw(st.booleans()),
        would_claim_targeted_childcare=draw(st.sampled_from([True, True, False])),
        legacy_benefit=draw(st.sampled_from([None, None, None] + LEGACY_BENEFITS)),
    )


def family(ages, **overrides):
    unit = dict(
        ages=ages,
        young_person=None,
        region="LONDON",
        earnings=0.0,
        state_pension=0.0,
        private_pension=0.0,
        savings=0.0,
        would_claim_pc=True,
        would_claim_uc=False,
        would_claim_targeted_childcare=True,
        legacy_benefit=None,
    )
    unit.update(overrides)
    return unit


# One family for each side of every rule.
KNOWN_FAMILIES = [
    family([30]),
    family([30, 32]),
    family([65]),
    family([30], would_claim_uc=True),
    family([68], state_pension=10_000.0),
    family([68], state_pension=10_000.0, would_claim_pc=False),
    family([68], state_pension=20_000.0),
    family([70, 40], state_pension=10_000.0),
    family([70, 68], state_pension=5_000.0, region="WALES"),
    family([40], legacy_benefit="esa_income_reported"),
    family([68], state_pension=10_000.0, young_person=18),
    family([68], state_pension=10_000.0, would_claim_targeted_childcare=False),
]
BELOW_AGE_FAMILIES = [0, 1, 2]  # No other route open, income below the MG.
NON_CLAIMANT = 5
POPULATIONS = st.tuples(
    st.sampled_from(YEARS), st.lists(families(), min_size=1, max_size=30)
)


def situation(year, units, would_claim_pc=None, would_claim_tce=None):
    people, benunits, households = {}, {}, {}
    for i, unit in enumerate(units):
        names = []
        for j, age in enumerate(unit["ages"]):
            name = f"p{i}_{j}"
            person = {"age": {year: age}, "is_parent": {year: True}}
            if age >= 67:
                person["state_pension_reported"] = {year: unit["state_pension"]}
                person["private_pension_income"] = {year: unit["private_pension"]}
            elif j == 0:
                person["employment_income"] = {year: unit["earnings"]}
                if unit["legacy_benefit"]:
                    person[unit["legacy_benefit"]] = {year: 3_000.0}
            people[name] = person
            names.append(name)
        if unit["young_person"] is not None:
            name = f"y{i}"
            people[name] = {
                "age": {year: unit["young_person"]},
                "is_in_non_advanced_education": {year: True},
            }
            names.append(name)
        child = f"c{i}"
        people[child] = {"age": {year: 2}}
        names.append(child)
        claims_pc = unit["would_claim_pc"] if would_claim_pc is None else would_claim_pc
        claims_tce = (
            unit["would_claim_targeted_childcare"]
            if would_claim_tce is None
            else would_claim_tce
        )
        benunits[f"b{i}"] = {
            "members": names,
            "would_claim_pc": {year: claims_pc},
            "would_claim_uc": {year: unit["would_claim_uc"]},
            "would_claim_targeted_childcare": {year: claims_tce},
        }
        households[f"h{i}"] = {
            "members": names,
            "region": {year: unit["region"]},
            "savings": {year: unit["savings"]},
        }
    return {"people": people, "benunits": benunits, "households": households}


def route(label, formula):
    # A stand-in for in_receipt_of_guarantee_credit, to run an earlier
    # version of the route through the same eligibility formula.
    return type(
        "in_receipt_of_guarantee_credit",
        (Variable,),
        dict(
            value_type=bool,
            entity=BenUnit,
            definition_period=YEAR_PERIOD,
            label=label,
            formula=formula,
        ),
    )


ROUTES = {
    "fix": None,
    "main": route(
        "guarantee credit computed for a Pension Credit eligible family",
        lambda benunit, period, parameters: benunit("guarantee_credit", period) > 0,
    ),
    "filed": route(
        "guarantee credit computed for every benefit unit",
        lambda benunit, period, parameters: (
            benunit("minimum_guarantee", period)
            > benunit("pension_credit_income", period)
        ),
    ),
}

VARIABLES = [
    "targeted_childcare_entitlement_eligible",
    "would_claim_targeted_childcare",
    "extended_childcare_entitlement_eligible",
    "in_receipt_of_guarantee_credit",
    "guarantee_credit",
    "pension_credit",
    "is_pension_credit_eligible",
    "would_claim_pc",
    "income_support",
    "jsa_income",
    "esa_income",
]
BOOLEANS = [
    "targeted_childcare_entitlement_eligible",
    "would_claim_targeted_childcare",
    "extended_childcare_entitlement_eligible",
    "in_receipt_of_guarantee_credit",
    "is_pension_credit_eligible",
    "would_claim_pc",
]


def calculate(year, units, version="fix", reform=None, scenario=None, **kwargs):
    sim = Simulation(
        situation=situation(year, units, **kwargs), reform=reform, scenario=scenario
    )
    if ROUTES[version] is not None:
        sim.tax_benefit_system.update_variable(ROUTES[version])
    values = {v: np.asarray(sim.calculate(v, year)) for v in VARIABLES}
    parameters = sim.tax_benefit_system.parameters(str(year))
    criteria = parameters.gov.dfe.targeted_childcare_entitlement.qualifying_criteria
    values["criteria"] = (
        sum(np.asarray(sim.calculate(v, year)).astype(int) for v in criteria) > 0
    )
    values["legacy"] = (
        values["income_support"] + values["jsa_income"] + values["esa_income"]
    ) > 0
    values["in_england"] = np.array(
        [unit["region"] not in OUTSIDE_ENGLAND for unit in units]
    )
    values["any_over_sp_age"] = (
        np.asarray(sim.calculate("is_SP_age", year, map_to="benunit")) > 0
    )
    for name in BOOLEANS:
        values[name] = values[name].astype(bool)
    return values


def all_adults_below_qualifying_age(unit):
    # Every member aged 18 or over, including a dependent young person.
    adults = list(unit["ages"])
    if unit["young_person"] is not None and unit["young_person"] >= 18:
        adults.append(unit["young_person"])
    return all(age <= 65 for age in adults)


def claimant_and_partner_over_sp_age(unit):
    return all(age >= 67 for age in unit["ages"])


def qualifying_age_violations(units, values):
    below = np.array([all_adults_below_qualifying_age(unit) for unit in units])
    eligible = values["targeted_childcare_entitlement_eligible"]
    other_route = values["legacy"] | values["criteria"]
    return below & eligible & ~other_route


def claim_violations(not_claiming):
    # Families eligible without a Pension Credit claim through no other route.
    return not_claiming["targeted_childcare_entitlement_eligible"] & ~(
        not_claiming["legacy"] | not_claiming["criteria"]
    )


@PROPERTY_SETTINGS
@given(POPULATIONS)
@example((2026, KNOWN_FAMILIES))
@example((2025, KNOWN_FAMILIES))
def test_no_family_below_the_qualifying_age_qualifies_through_guarantee_credit(
    population,
):
    year, units = population
    values = calculate(year, units)
    below = np.array([all_adults_below_qualifying_age(unit) for unit in units])
    # The generated ages agree with the model's State Pension age.
    assert not np.any(below & values["any_over_sp_age"])
    assert not np.any(below & values["in_receipt_of_guarantee_credit"])
    assert not np.any(below & (values["pension_credit"] > 0))
    assert not np.any(qualifying_age_violations(units, values))


@PROPERTY_SETTINGS
@given(POPULATIONS)
@example((2026, KNOWN_FAMILIES))
@example((2025, KNOWN_FAMILIES))
def test_eligibility_is_the_union_of_the_routes(population):
    year, units = population
    values = calculate(year, units)
    receipt = values["in_receipt_of_guarantee_credit"]
    paid = (values["pension_credit"] > 0) & (values["guarantee_credit"] > 0)
    assert np.array_equal(receipt, paid)
    assert not np.any(receipt & ~values["is_pension_credit_eligible"])
    assert not np.any(receipt & ~values["would_claim_pc"])
    for i, unit in enumerate(units):
        if receipt[i]:
            assert claimant_and_partner_over_sp_age(unit), unit
    expected = (
        values["would_claim_targeted_childcare"]
        & values["in_england"]
        & ~values["extended_childcare_entitlement_eligible"]
        & (values["legacy"] | values["criteria"] | receipt)
    )
    assert np.array_equal(values["targeted_childcare_entitlement_eligible"], expected)
    # Not claiming targeted childcare never leaves a family eligible.
    assert not np.any(
        values["targeted_childcare_entitlement_eligible"]
        & ~values["would_claim_targeted_childcare"]
    )
    if units is KNOWN_FAMILIES:
        assert receipt.tolist() == [
            False,
            False,
            False,
            False,
            True,
            False,  # Not claiming Pension Credit.
            False,
            False,
            True,
            False,
            True,  # An 18-year-old dependant is not a partner.
            True,
        ]
        assert values["targeted_childcare_entitlement_eligible"].tolist() == [
            False,
            False,
            False,
            True,  # Universal Credit with no earnings.
            True,  # Paid a guarantee credit.
            False,
            False,
            False,
            False,  # Paid a guarantee credit, but in Wales.
            True,  # Income-related ESA.
            True,  # Paid a guarantee credit, with an 18-year-old dependant.
            False,  # Paid a guarantee credit, but not claiming childcare.
        ]


@PROPERTY_SETTINGS
@given(POPULATIONS)
@example((2026, KNOWN_FAMILIES))
@example((2025, KNOWN_FAMILIES))
def test_fix_only_removes_the_unpaid_guarantee_credit_route(population):
    year, units = population
    new = calculate(year, units)
    old = calculate(year, units, version="main")
    new_eligible = new["targeted_childcare_entitlement_eligible"]
    old_eligible = old["targeted_childcare_entitlement_eligible"]
    # Only the route changes: every other input to eligibility is the same.
    for name in ["guarantee_credit", "pension_credit", "legacy", "criteria"]:
        assert np.array_equal(new[name], old[name]), name
    assert not np.any(new_eligible & ~old_eligible)
    base = (
        new["would_claim_targeted_childcare"]
        & new["in_england"]
        & ~new["extended_childcare_entitlement_eligible"]
    )
    computed_not_paid = (new["guarantee_credit"] > 0) & ~(new["pension_credit"] > 0)
    removed = base & computed_not_paid & ~new["legacy"] & ~new["criteria"]
    assert np.array_equal(old_eligible & ~new_eligible, removed)
    # Main computes a guarantee credit only for Pension Credit eligible
    # families, so everyone who loses the route is an eligible non-claimant.
    assert not np.any(removed & ~new["is_pension_credit_eligible"])
    assert not np.any(removed & new["would_claim_pc"])
    # Where an eligible family claims Pension Credit, nothing changes.
    claimed = new["would_claim_pc"] & new["is_pension_credit_eligible"]
    assert np.array_equal(new_eligible[claimed], old_eligible[claimed])
    if units is KNOWN_FAMILIES:
        expected = [False] * len(KNOWN_FAMILIES)
        expected[NON_CLAIMANT] = True
        assert removed.tolist() == expected


@PROPERTY_SETTINGS
@given(POPULATIONS)
@example((2026, KNOWN_FAMILIES))
def test_not_claiming_pension_credit_never_makes_a_family_eligible(population):
    year, units = population
    claiming = calculate(year, units, would_claim_pc=True)
    not_claiming = calculate(year, units, would_claim_pc=False)
    assert not np.any(not_claiming["in_receipt_of_guarantee_credit"])
    assert not np.any(
        not_claiming["targeted_childcare_entitlement_eligible"]
        & ~claiming["targeted_childcare_entitlement_eligible"]
    )
    # Without a Pension Credit claim only the other routes are left.
    assert not np.any(claim_violations(not_claiming))


def test_known_families_detect_the_earlier_routes():
    # The properties are not vacuous: each earlier version of the route
    # breaks the invariant it was written against, on the known families.
    year = 2026
    filed = calculate(year, KNOWN_FAMILIES, version="filed")
    assert (
        qualifying_age_violations(KNOWN_FAMILIES, filed).nonzero()[0].tolist()
        == BELOW_AGE_FAMILIES
    )
    main = calculate(year, KNOWN_FAMILIES, version="main")
    assert not np.any(qualifying_age_violations(KNOWN_FAMILIES, main))
    not_claiming = {
        version: calculate(year, KNOWN_FAMILIES, version=version, would_claim_pc=False)
        for version in ROUTES
    }
    for version in ["filed", "main"]:
        assert claim_violations(not_claiming[version])[NON_CLAIMANT], version
    assert not np.any(claim_violations(not_claiming["fix"]))


def test_stopping_pension_credit_payments_closes_the_route():
    # A reform that stops Pension Credit being paid leaves the guarantee
    # credit computed but ends receipt, and with it the route.
    year = 2026
    units = [family([68], state_pension=10_000.0)]
    stopped = calculate(
        year,
        units,
        scenario=Scenario(
            simulation_modifier=lambda sim: sim.tax_benefit_system.neutralize_variable(
                "pension_credit"
            )
        ),
    )
    # 12,376 + 3,638.96 - 10,000 = 6,014.96.
    assert abs(stopped["guarantee_credit"][0] - 6_014.96) < 0.01
    assert stopped["pension_credit"].tolist() == [0]
    assert stopped["in_receipt_of_guarantee_credit"].tolist() == [False]
    assert stopped["targeted_childcare_entitlement_eligible"].tolist() == [False]

    # The same holds with Pension Credit frozen: the frozen award is not
    # paid either, so the baseline receipt does not carry over.
    frozen_and_stopped = calculate(
        year,
        units,
        scenario=Scenario(
            parameter_changes={"gov.contrib.freeze_pension_credit": True},
            simulation_modifier=lambda sim: sim.tax_benefit_system.neutralize_variable(
                "pension_credit"
            ),
        ),
    )
    assert frozen_and_stopped["pension_credit"].tolist() == [0]
    assert frozen_and_stopped["in_receipt_of_guarantee_credit"].tolist() == [False]
    assert frozen_and_stopped["targeted_childcare_entitlement_eligible"].tolist() == [
        False
    ]


def test_pension_credit_freeze_keeps_the_baseline_route():
    # With Pension Credit frozen the baseline award is paid, so receipt of a
    # guarantee credit is the baseline receipt. A reform setting the single
    # minimum guarantee to zero ends the computed guarantee credit; the
    # pension-age parent keeps the frozen award and the route, and the
    # working-age parent never had either.
    year = 2026
    units = [family([68], state_pension=10_000.0), family([30])]
    no_minimum_guarantee = {
        "gov.dwp.pension_credit.guarantee_credit.minimum_guarantee.SINGLE": 0,
        "gov.dwp.pension_credit.guarantee_credit.child.addition": 0,
    }
    frozen = calculate(
        year,
        units,
        reform={**no_minimum_guarantee, "gov.contrib.freeze_pension_credit": True},
    )
    assert frozen["guarantee_credit"].tolist() == [0, 0]
    # 12,376 + 3,638.96 - 10,000 = 6,014.96 in the baseline.
    assert abs(frozen["pension_credit"][0] - 6_014.96) < 0.01
    assert frozen["pension_credit"][1] == 0
    assert frozen["in_receipt_of_guarantee_credit"].tolist() == [True, False]
    assert frozen["targeted_childcare_entitlement_eligible"].tolist() == [True, False]

    unfrozen = calculate(year, units, reform=no_minimum_guarantee)
    assert unfrozen["pension_credit"].tolist() == [0, 0]
    assert unfrozen["in_receipt_of_guarantee_credit"].tolist() == [False, False]
    assert unfrozen["targeted_childcare_entitlement_eligible"].tolist() == [
        False,
        False,
    ]
