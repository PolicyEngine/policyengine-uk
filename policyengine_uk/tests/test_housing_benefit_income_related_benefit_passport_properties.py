"""Property-based tests for the Housing Benefit passport through Income Support,
income-based JSA and income-related ESA.

SI 2006/213 Sch 5 para 4 and Sch 6 para 5 (NI: SR 2006/405 Sch 6 para 4 and
Sch 7 para 5) disregard the whole of the income and capital of a claimant on
income support, an income-based jobseeker's allowance or an income-related
employment and support allowance. Housing Benefit is then the maximum: the
eligible rent, capped at the LHA rate for LHA tenants, less non-dependant
deductions (regs 70 and 74). Reg 5(1)(b) applies the working-age regulations
to a claimant over State Pension Credit age whose partner is on one of these
benefits, so the passport has no age condition.

Invariants, for any generated population of renting families with a
continuing award (some with a non-dependant in the household):

1. Receipt: in_receipt_of_income_support_jsa_ib_or_esa_ir is true exactly when
   Income Support, income-based JSA or income-related ESA is positive.
2. Passport: a family in receipt has nil applicable income, assessable
   capital and tariff income, and meets the capital limit.
3. Maximum: every family's entitlement is at most the maximum (rent, capped at
   the LHA rate for LHA tenants, less non-dependant deductions, floored at
   zero); a family in receipt gets exactly the maximum.
4. Metamorphic: for a family in receipt, raising its earnings, pensions and
   savings changes neither its entitlement nor its eligibility.
5. Metamorphic: adding a positive Income Support, income-based JSA or
   income-related ESA amount never lowers Housing Benefit before the benefit
   cap. (After the cap it can: those benefits count towards the cap. That is
   an intended difference, so the test reads the pre-cap amount.)
6. Ages: for social tenants with no non-dependants, the entitlement of a
   family in receipt equals the rent whether its members are of working age,
   a mixed-age couple or over State Pension age.
7. Contributory JSA and ESA are not a passport: moving an amount from
   income-based to contribution-based JSA or ESA turns the passport off, and
   with no guarantee credit either (which passports a pension-age family in
   its own right) the family's savings stay its capital.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

YEAR = 2025
PROPERTY_SETTINGS = settings(
    max_examples=5,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
# State Pension age is 66 until 2026-27 finishes phasing up; 67 and over is
# unambiguously pension age and 60 and under unambiguously working age.
PENSION_AGE = st.integers(67, 90)
WORKING_AGE = st.integers(18, 60)
SHAPES = {
    "single_working": ([WORKING_AGE], 0),
    "couple_working": ([WORKING_AGE, WORKING_AGE], 0),
    "lone_parent": ([WORKING_AGE], 2),
    "couple_with_children": ([WORKING_AGE, WORKING_AGE], 1),
    "mixed_age": ([PENSION_AGE, WORKING_AGE], 0),
    "single_pension": ([PENSION_AGE], 0),
}
RENTING_TENURES = ["RENT_FROM_COUNCIL", "RENT_FROM_HA", "RENT_PRIVATELY"]
SOCIAL_TENURES = ["RENT_FROM_COUNCIL", "RENT_FROM_HA"]
BENEFITS = ["income_support", "jsa_income", "esa_income"]
money = st.floats(0, 20_000, allow_nan=False, allow_infinity=False)
award = st.one_of(st.just(0.0), st.floats(1, 12_000, allow_nan=False))


@st.composite
def families(draw, tenures=RENTING_TENURES, non_dependants=True, shapes=None):
    shape = draw(st.sampled_from(sorted(shapes or SHAPES)))
    ages, n_children = SHAPES[shape]
    return dict(
        shape=shape,
        adults=[
            dict(
                age=draw(age),
                employment_income=draw(st.one_of(st.just(0.0), money)),
                private_pension_income=draw(st.one_of(st.just(0.0), money)),
                state_pension=draw(money),
            )
            for age in ages
        ],
        children=[draw(st.integers(0, 15)) for _ in range(n_children)],
        tenure=draw(st.sampled_from(tenures)),
        rent=draw(money),
        savings=draw(st.one_of(st.just(0.0), st.floats(0, 40_000))),
        awards={benefit: draw(award) for benefit in BENEFITS},
        non_dependant_earnings=(
            draw(st.one_of(st.none(), st.floats(0, 40_000))) if non_dependants else None
        ),
    )


def situation(units, bump=0.0, awards=None, ages=None):
    """Build a simulation with one claimant benefit unit per family, first in
    each household, followed by any non-dependant's own benefit unit.

    bump raises every adult's earnings and pensions and the savings; awards
    overrides each family's benefit amounts; ages overrides adult ages.
    """
    people, benunits, households = {}, {}, {}
    for i, unit in enumerate(units):
        members = []
        for j, adult in enumerate(unit["adults"]):
            name = f"a{i}_{j}"
            age = adult["age"] if ages is None else ages[i][j]
            person = {
                "age": {YEAR: age},
                "employment_income": {YEAR: adult["employment_income"] + bump},
                "private_pension_income": {
                    YEAR: adult["private_pension_income"] + bump
                },
            }
            if age >= 67:
                person["state_pension_reported"] = {YEAR: adult["state_pension"]}
            if j == 0:
                person["housing_benefit_reported"] = {YEAR: 1.0}
            people[name] = person
            members.append(name)
        for k, child_age in enumerate(unit["children"]):
            name = f"c{i}_{k}"
            people[name] = {"age": {YEAR: child_age}}
            members.append(name)
        family_awards = unit["awards"] if awards is None else awards[i]
        benunits[f"b{i}"] = {
            "members": list(members),
            "would_claim_uc": {YEAR: False},
            **{benefit: {YEAR: family_awards[benefit]} for benefit in BENEFITS},
        }
        household_members = list(members)
        if unit["non_dependant_earnings"] is not None:
            name = f"n{i}"
            people[name] = {
                "age": {YEAR: 30},
                "employment_income": {YEAR: unit["non_dependant_earnings"]},
            }
            benunits[f"nb{i}"] = {"members": [name], "would_claim_uc": {YEAR: False}}
            household_members.append(name)
        households[f"h{i}"] = {
            "members": household_members,
            "tenure_type": {YEAR: unit["tenure"]},
            "rent": {YEAR: unit["rent"]},
            "savings": {YEAR: unit["savings"] + bump},
        }
    return {"people": people, "benunits": benunits, "households": households}


VARIABLES = [
    "in_receipt_of_income_support_jsa_ib_or_esa_ir",
    "income_support",
    "jsa_income",
    "esa_income",
    "housing_benefit_applicable_income",
    "housing_benefit_assessable_capital",
    "housing_benefit_tariff_income",
    "housing_benefit_entitlement",
    "housing_benefit_eligible",
    "housing_benefit_pre_benefit_cap",
    "housing_benefit_non_dep_deductions",
    "benunit_rent",
    "LHA_eligible",
    "LHA_cap",
]


def calculate(units, **kwargs):
    sim = Simulation(situation=situation(units, **kwargs))
    values = {v: np.asarray(sim.calculate(v, YEAR)) for v in VARIABLES}
    benunit_ids = list(sim.populations["benunit"].ids)
    claimants = [benunit_ids.index(f"b{i}") for i in range(len(units))]
    values = {k: v[claimants] for k, v in values.items()}
    capital = sim.tax_benefit_system.parameters(
        YEAR
    ).gov.dwp.housing_benefit.means_test.capital
    values["capital_limit"] = min(capital.working_age.limit, capital.pension_age.limit)
    return values


def maximum_housing_benefit(values):
    rent = values["benunit_rent"]
    lha = values["LHA_eligible"].astype(bool)
    capped_rent = np.where(lha, np.minimum(rent, values["LHA_cap"]), rent)
    return np.maximum(0, capped_rent - values["housing_benefit_non_dep_deductions"])


def receipt(values):
    return values["in_receipt_of_income_support_jsa_ib_or_esa_ir"].astype(bool)


@PROPERTY_SETTINGS
@given(st.lists(families(), min_size=1, max_size=20))
def test_receipt_passport_and_maximum(units):
    values = calculate(units)
    on_benefit = receipt(values)
    amounts = np.stack([values[benefit] for benefit in BENEFITS])
    # 1. Receipt.
    assert np.array_equal(on_benefit, (amounts > 0).any(axis=0))
    # 2. Passport.
    for variable in [
        "housing_benefit_applicable_income",
        "housing_benefit_assessable_capital",
        "housing_benefit_tariff_income",
    ]:
        assert np.all(values[variable][on_benefit] == 0), variable
    assert np.all(
        values["housing_benefit_assessable_capital"][on_benefit]
        <= values["capital_limit"]
    )
    # 3. Maximum.
    maximum = maximum_housing_benefit(values)
    entitlement = values["housing_benefit_entitlement"]
    assert np.all(entitlement <= maximum + 0.01)
    assert np.allclose(entitlement[on_benefit], maximum[on_benefit], atol=0.01)


@PROPERTY_SETTINGS
@given(
    st.lists(families(), min_size=1, max_size=20),
    st.floats(1, 50_000, allow_nan=False),
)
def test_passported_entitlement_ignores_income_and_capital(units, bump):
    before = calculate(units)
    after = calculate(units, bump=bump)
    on_benefit = receipt(before)
    assert np.array_equal(on_benefit, receipt(after))
    for variable in ["housing_benefit_entitlement", "housing_benefit_eligible"]:
        assert np.allclose(
            before[variable][on_benefit], after[variable][on_benefit], atol=0.01
        ), variable


@PROPERTY_SETTINGS
@given(
    st.lists(families(), min_size=1, max_size=20),
    st.sampled_from(BENEFITS),
    st.floats(1, 12_000, allow_nan=False),
)
def test_receipt_never_lowers_pre_cap_housing_benefit(units, benefit, amount):
    without = [{b: 0.0 for b in BENEFITS} for _ in units]
    with_benefit = [{**w, benefit: amount} for w in without]
    off = calculate(units, awards=without)
    on = calculate(units, awards=with_benefit)
    assert not receipt(off).any()
    assert receipt(on).all()
    assert np.all(
        on["housing_benefit_pre_benefit_cap"]
        >= off["housing_benefit_pre_benefit_cap"] - 0.01
    )
    assert np.all(on["housing_benefit_eligible"] >= off["housing_benefit_eligible"])


@PROPERTY_SETTINGS
@given(
    st.lists(
        families(
            tenures=SOCIAL_TENURES,
            non_dependants=False,
            shapes=["couple_working", "mixed_age"],
        ),
        min_size=1,
        max_size=20,
    ),
    st.sampled_from(BENEFITS),
    st.floats(1, 12_000, allow_nan=False),
)
def test_passported_social_tenant_gets_the_rent_at_any_age(units, benefit, amount):
    awards = [{**{b: 0.0 for b in BENEFITS}, benefit: amount} for _ in units]
    rents = np.array([unit["rent"] for unit in units])
    for first, second in [(40, 35), (70, 35), (70, 68)]:
        ages = [[first, second] for _ in units]
        values = calculate(units, awards=awards, ages=ages)
        assert receipt(values).all()
        assert values["housing_benefit_eligible"].all()
        assert np.allclose(values["housing_benefit_entitlement"], rents, atol=0.01)


@PROPERTY_SETTINGS
@given(
    st.lists(families(non_dependants=False), min_size=1, max_size=20),
    st.floats(1, 12_000, allow_nan=False),
)
def test_contributory_jsa_and_esa_are_not_a_passport(units, amount):
    no_awards = [{b: 0.0 for b in BENEFITS} for _ in units]
    contributory = situation(units, awards=no_awards)
    for name, person in contributory["people"].items():
        # The first adult of each family is its claimant.
        if name.startswith("a") and name.endswith("_0"):
            person["jsa_contrib"] = {YEAR: amount}
            person["esa_contrib"] = {YEAR: amount}
    # A pension-age family can still have its capital disregarded through the
    # Guarantee Credit passport, so hold that at nil to isolate this one.
    for name, benunit in contributory["benunits"].items():
        if name.startswith("b"):
            benunit["guarantee_credit"] = {YEAR: 0.0}
    sim = Simulation(situation=contributory)
    on_benefit = np.asarray(
        sim.calculate("in_receipt_of_income_support_jsa_ib_or_esa_ir", YEAR)
    )
    assert not on_benefit.any()
    capital = np.asarray(sim.calculate("housing_benefit_assessable_capital", YEAR))
    savings = np.array([unit["savings"] for unit in units])
    # With neither passport the family's savings count as its capital (no
    # non-dependants here, so no household apportionment).
    assert np.allclose(capital, savings, atol=0.01)
