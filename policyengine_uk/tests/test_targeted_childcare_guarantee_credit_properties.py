"""Property-based tests for the Guarantee Credit route into targeted childcare.

An "eligible child" is a young child "whose parent is entitled to any one or
more of the following— ... the guaranteed element of state pension credit
under the State Pension Credit Act 2002" (SI 2014/2147 reg 1(2)). A claimant
is entitled to state pension credit only if "he has attained the qualifying
age" (SPCA 2002 s.1(2)(b)), and entitlement needs a claim. The route follows
in_receipt_of_guarantee_credit: Pension Credit is paid and includes a
guarantee credit.

Invariants, for any generated population of families with a 2-year-old:

1. Qualifying age: no benefit unit whose adults are all below the qualifying
   age is eligible through the Guarantee Credit route, however low its income
   and however large the guarantee credit computed for it.
2. Route identity: targeted childcare eligibility equals claiming it, living
   in England, not being eligible for the extended entitlement, and having at
   least one route open: Income Support, income-based JSA, income-related
   ESA, receipt of a guarantee credit, or a qualifying criterion (Universal
   Credit, and tax credits while they qualify).
3. Receipt: the Guarantee Credit route is open exactly when pension_credit
   and guarantee_credit are both positive, so it implies would_claim_pc and
   that every adult in the family is over State Pension age. The last part
   is stricter than the law for a mixed-age couple saved by SI 2019/37 art 4,
   which is_pension_credit_eligible omits (known departure).
4. Differential: against the pre-fix formula (route open on a computed
   guarantee credit), the fix never adds eligibility, and removes it exactly
   where a computed guarantee credit that is not paid was the only open
   route (intended).
5. Metamorphic: not claiming Pension Credit closes the route for everyone
   and never makes a family eligible.
6. Under the Pension Credit freeze the route follows the baseline receipt, so
   a working-age family still does not qualify.
"""

import numpy as np
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.model_api import YEAR as YEAR_PERIOD
from policyengine_uk.model_api import BenUnit, Variable

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
# State Pension age is 66 in every test year. 67 and over is unambiguously at
# the qualifying age and 65 and under unambiguously below it.
PENSION_AGE = st.integers(67, 100)
WORKING_AGE = st.integers(18, 65)
SHAPES = {
    "single_working": [WORKING_AGE],
    "couple_working": [WORKING_AGE, WORKING_AGE],
    "single_pension": [PENSION_AGE],
    "couple_pension": [PENSION_AGE, PENSION_AGE],
    "mixed_age": [PENSION_AGE, WORKING_AGE],
}
LEGACY_BENEFITS = [
    "income_support_reported",
    "jsa_income_reported",
    "esa_income_reported",
]
money = st.floats(0, 30_000, allow_nan=False, allow_infinity=False)


@st.composite
def families(draw):
    shape = draw(st.sampled_from(sorted(SHAPES)))
    return dict(
        ages=[draw(age) for age in SHAPES[shape]],
        region=draw(st.sampled_from(REGIONS)),
        earnings=draw(st.one_of(st.just(0.0), money)),
        state_pension=draw(st.one_of(st.just(0.0), money)),
        private_pension=draw(st.one_of(st.just(0.0), money)),
        savings=draw(st.one_of(st.just(0.0), st.floats(0, 40_000))),
        would_claim_pc=draw(st.booleans()),
        would_claim_uc=draw(st.booleans()),
        legacy_benefit=draw(st.sampled_from([None, None, None] + LEGACY_BENEFITS)),
    )


def family(ages, **overrides):
    unit = dict(
        ages=ages,
        region="LONDON",
        earnings=0.0,
        state_pension=0.0,
        private_pension=0.0,
        savings=0.0,
        would_claim_pc=True,
        would_claim_uc=False,
        legacy_benefit=None,
    )
    unit.update(overrides)
    return unit


# One family for each side of every rule: the working-age and non-claiming
# families have a computed guarantee credit that is not paid.
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
]
POPULATIONS = st.tuples(
    st.sampled_from(YEARS), st.lists(families(), min_size=1, max_size=30)
)


def situation(year, units, would_claim_pc=None):
    people, benunits, households = {}, {}, {}
    for i, unit in enumerate(units):
        names = []
        for j, age in enumerate(unit["ages"]):
            name = f"p{i}_{j}"
            person = {"age": {year: age}}
            if age >= 67:
                person["state_pension_reported"] = {year: unit["state_pension"]}
                person["private_pension_income"] = {year: unit["private_pension"]}
            elif j == 0:
                person["employment_income"] = {year: unit["earnings"]}
                if unit["legacy_benefit"]:
                    person[unit["legacy_benefit"]] = {year: 3_000.0}
            people[name] = person
            names.append(name)
        child = f"c{i}"
        people[child] = {"age": {year: 2}}
        names.append(child)
        claims = unit["would_claim_pc"] if would_claim_pc is None else would_claim_pc
        benunits[f"b{i}"] = {
            "members": names,
            "would_claim_pc": {year: claims},
            "would_claim_uc": {year: unit["would_claim_uc"]},
        }
        households[f"h{i}"] = {
            "members": names,
            "region": {year: unit["region"]},
            "savings": {year: unit["savings"]},
        }
    return {"people": people, "benunits": benunits, "households": households}


class in_receipt_of_guarantee_credit(Variable):
    # The route on main before this fix: a computed guarantee credit, which
    # is positive for working-age families and for non-claimants.
    value_type = bool
    entity = BenUnit
    definition_period = YEAR_PERIOD
    label = "computed guarantee credit (pre-fix route)"

    def formula(benunit, period, parameters):
        return benunit("guarantee_credit", period) > 0


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


def calculate(year, units, old_formula=False, reform=None, **kwargs):
    sim = Simulation(situation=situation(year, units, **kwargs), reform=reform)
    if old_formula:
        sim.tax_benefit_system.update_variable(in_receipt_of_guarantee_credit)
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
    for name in [
        "targeted_childcare_entitlement_eligible",
        "would_claim_targeted_childcare",
        "extended_childcare_entitlement_eligible",
        "in_receipt_of_guarantee_credit",
        "is_pension_credit_eligible",
        "would_claim_pc",
    ]:
        values[name] = values[name].astype(bool)
    return values


def all_adults_below_qualifying_age(unit):
    return all(age <= 65 for age in unit["ages"])


def all_adults_over_sp_age(unit):
    return all(age >= 67 for age in unit["ages"])


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
    eligible = values["targeted_childcare_entitlement_eligible"]
    other_route = values["legacy"] | values["criteria"]
    # The generated ages agree with the model's State Pension age.
    assert not np.any(below & values["any_over_sp_age"])
    assert not np.any(below & values["in_receipt_of_guarantee_credit"])
    assert not np.any(below & (values["pension_credit"] > 0))
    assert not np.any(below & eligible & ~other_route)
    if units is KNOWN_FAMILIES:
        # Not vacuous: families below the qualifying age do have a computed
        # guarantee credit, and it does not make them eligible.
        computed = below & (values["guarantee_credit"] > 0) & ~other_route
        assert computed.sum() >= 3
        assert not np.any(computed & eligible)


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
            assert all_adults_over_sp_age(unit), unit
    expected = (
        values["would_claim_targeted_childcare"]
        & values["in_england"]
        & ~values["extended_childcare_entitlement_eligible"]
        & (values["legacy"] | values["criteria"] | receipt)
    )
    assert np.array_equal(values["targeted_childcare_entitlement_eligible"], expected)
    if units is KNOWN_FAMILIES:
        assert receipt.tolist() == [
            False,
            False,
            False,
            False,
            True,
            False,
            False,
            False,
            True,
            False,
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
        ]


@PROPERTY_SETTINGS
@given(POPULATIONS)
@example((2026, KNOWN_FAMILIES))
@example((2025, KNOWN_FAMILIES))
def test_fix_only_removes_the_unpaid_computed_guarantee_credit_route(population):
    year, units = population
    new = calculate(year, units)
    old = calculate(year, units, old_formula=True)
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
    # Where Pension Credit is claimed by an eligible family, nothing changes.
    claimed = new["would_claim_pc"] & new["is_pension_credit_eligible"]
    assert np.array_equal(new_eligible[claimed], old_eligible[claimed])
    if units is KNOWN_FAMILIES:
        assert removed.tolist() == [
            True,  # Working-age lone parent.
            True,  # Working-age couple.
            True,  # One year below the qualifying age.
            False,
            False,
            True,  # Pension-age parent not claiming Pension Credit.
            False,
            True,  # Mixed-age couple (see the module docstring).
            False,
            False,
        ]


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
    assert not np.any(
        not_claiming["targeted_childcare_entitlement_eligible"]
        & ~(not_claiming["legacy"] | not_claiming["criteria"])
    )


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
