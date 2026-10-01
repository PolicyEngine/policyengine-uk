"""Property-based tests: Universal Credit counts only claimants' income.

UC Regs 2013 reg. 22(1) deducts "all of the claimant's unearned income (or in
the case of joint claimants all of their combined unearned income)" and "the
claimant's earned income (or, in the case of joint claimants, their combined
earned income)". A claim is made by a single person or jointly by a couple
(Welfare Reform Act 2012 s. 2(1)), so it has at most two claimants. A child's
or qualifying young person's income, and the income of anyone else in the
benefit unit, is not the claimant's.

Invariants, for any generated population of single claimants, couples and
mixed-age couples with up to three dependants aged 0 to 19 (in or out of
education), with or without rent, childcare costs and capital, in England,
Wales and Scotland:

1. A dependant's income never changes Universal Credit. Giving every member
   who is not one of the (at most two) assessed claimants earnings,
   self-employment profits or losses, miscellaneous income, savings interest,
   dividends, property income or a private pension leaves UC, UC before the
   benefit cap, earned income and unearned income exactly as they are when
   those members have no income.
2. Differential against the regulation: earned income equals the work
   allowance taken off the sum of the assessed claimants' own earned income
   (floored at zero), and unearned income equals the assessed claimants'
   listed unearned income plus tariff income, less the claimants' capital
   yield that tariff income replaces, written here from reg. 22(1) and the
   parameter list.
3. There are at most two assessed claimants in a benefit unit, they are
   members flagged as claimants, and they are every flagged member when two
   or fewer are flagged.
4. Order does not matter: listing the members of every benefit unit in
   reverse leaves the assessed claimants and UC unchanged.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

PROPERTY_SETTINGS = settings(
    max_examples=15,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
YEARS = [2020, 2026, 2027]
TENURES = ["RENT_FROM_COUNCIL", "RENT_PRIVATELY", "OWNED_OUTRIGHT"]
REGIONS = ["LONDON", "NORTH_EAST", "WALES", "SCOTLAND"]
EDUCATION = ["UPPER_SECONDARY", "TERTIARY", "NOT_IN_EDUCATION"]
WORKING_AGE = st.integers(20, 64)
PENSION_AGE = st.integers(67, 80)
SHAPES = {
    "single": [WORKING_AGE],
    "couple": [WORKING_AGE, WORKING_AGE],
    "mixed_age": [PENSION_AGE, WORKING_AGE],
}
amount = st.one_of(st.just(0.0), st.floats(0, 30_000))
INCOME_VARIABLES = {
    "employment_income": amount,
    "self_employment_income": st.one_of(st.just(0.0), st.floats(-5_000, 30_000)),
    "miscellaneous_income": amount,
    "savings_interest_income": amount,
    "dividend_income": amount,
    "property_income": amount,
    "private_pension_income": amount,
}
BENUNIT_VARIABLES = [
    "universal_credit",
    "universal_credit_pre_benefit_cap",
    "uc_earned_income",
    "uc_unearned_income",
    "uc_work_allowance",
    "uc_tariff_income",
]


@st.composite
def families(draw):
    shape = draw(st.sampled_from(list(SHAPES)))
    claimants = [
        dict(
            age=draw(age),
            employment_income=draw(amount),
            savings_interest_income=draw(amount),
            private_pension_income=draw(amount),
        )
        for age in SHAPES[shape]
    ]
    dependants = []
    for _ in range(draw(st.integers(0, 3))):
        age = draw(st.integers(0, 19))
        dependant = dict(
            age=age,
            childcare_expenses=draw(st.one_of(st.just(0.0), st.floats(0, 8_000))),
            **{v: draw(s) for v, s in INCOME_VARIABLES.items()},
        )
        if age >= 16:
            # At 18 and 19 only a qualifying young person (non-advanced
            # education begun before 19) is a dependant; anyone else that
            # age is an adult whom the calculator treats as a claimant.
            dependant["current_education"] = (
                draw(st.sampled_from(EDUCATION)) if age < 18 else "UPPER_SECONDARY"
            )
            dependant["age_started_or_accepted_current_education_or_training"] = draw(
                st.integers(16, min(age, 18))
            )
        dependants.append(dependant)
    return dict(
        claimants=claimants,
        dependants=dependants,
        tenure=draw(st.sampled_from(TENURES)),
        rent=draw(st.one_of(st.just(0.0), st.floats(0, 30_000))),
        region=draw(st.sampled_from(REGIONS)),
        savings=draw(st.one_of(st.just(0.0), st.floats(0, 20_000))),
    )


populations = st.lists(families(), min_size=1, max_size=6)


def situation(units, year, zero_dependants=False, reverse=False):
    """One simulation holding every family.

    With ``zero_dependants`` every dependant's income is nil. With
    ``reverse`` the people of each family are entered, and listed in their
    benefit unit and household, in reverse order.
    """
    people, benunits, households = {}, {}, {}
    for i, unit in enumerate(units):
        members = []
        for j, claimant in enumerate(unit["claimants"]):
            person = {k: {year: v} for k, v in claimant.items()}
            person["is_parent"] = {year: bool(unit["dependants"])}
            members.append((f"p{i}_{j}", person))
        for k, dependant in enumerate(unit["dependants"]):
            person = {
                key: {year: 0.0 if zero_dependants and key in INCOME_VARIABLES else v}
                for key, v in dependant.items()
            }
            members.append((f"d{i}_{k}", person))
        if reverse:
            members = members[::-1]
        names = []
        for name, person in members:
            person["would_claim_marriage_allowance"] = {year: False}
            people[name] = person
            names.append(name)
        benunits[f"b{i}"] = {"members": names}
        households[f"h{i}"] = {
            "members": names,
            "rent": {year: unit["rent"]},
            "tenure_type": {year: unit["tenure"]},
            "region": {year: unit["region"]},
            "savings": {year: unit["savings"]},
        }
    return {"people": people, "benunits": benunits, "households": households}


def simulate(units, year, **kwargs):
    return Simulation(situation=situation(units, year, **kwargs))


def benunit_values(sim, year):
    return {v: np.asarray(sim.calculate(v, year)) for v in BENUNIT_VARIABLES}


def assessed_claimants_dependants(units):
    """The model's assessed claimants are the claimants the test built."""
    flags = []
    for unit in units:
        flags += [True] * len(unit["claimants"]) + [False] * len(unit["dependants"])
    return np.array(flags)


@PROPERTY_SETTINGS
@given(units=populations, year=st.sampled_from(YEARS))
def test_dependants_income_never_changes_universal_credit(units, year):
    with_income = simulate(units, year)
    without_income = simulate(units, year, zero_dependants=True)
    np.testing.assert_array_equal(
        np.asarray(with_income.calculate("is_uc_assessed_claimant", year)),
        assessed_claimants_dependants(units),
        err_msg=str(units),
    )
    a = benunit_values(with_income, year)
    b = benunit_values(without_income, year)
    for v in BENUNIT_VARIABLES:
        np.testing.assert_allclose(a[v], b[v], atol=0.01, err_msg=f"{v}: {units}")


@PROPERTY_SETTINGS
@given(units=populations, year=st.sampled_from(YEARS))
def test_income_matches_regulation_22_closed_form(units, year):
    sim = simulate(units, year)
    assessed = np.asarray(sim.calculate("is_uc_assessed_claimant", year))

    def claimant_sum(variable):
        values = np.asarray(sim.calculate(variable, year)) * assessed
        return np.asarray(sim.map_result(values, "person", "benunit"))

    v = benunit_values(sim, year)
    np.testing.assert_allclose(
        v["uc_earned_income"],
        np.maximum(
            0, claimant_sum("uc_individual_earned_income") - v["uc_work_allowance"]
        ),
        atol=0.01,
        err_msg=str(units),
    )
    p = sim.tax_benefit_system.parameters(year).gov.dwp.universal_credit
    listed = p.means_test.income_definitions.unearned
    person_level = [
        name
        for name in listed
        if sim.tax_benefit_system.variables[name].entity.is_person
    ]
    benunit_level = [name for name in listed if name not in person_level]
    expected = sum(claimant_sum(name) for name in person_level) + sum(
        np.asarray(sim.calculate(name, year)) for name in benunit_level
    )
    # Tariff income replaces the actual yield of the capital it is charged
    # on (reg. 72(3)). The generated households hold savings only (no
    # corporate wealth or other property), so only the claimants' savings
    # interest is replaced.
    tariff = v["uc_tariff_income"] > 0
    has_savings = np.array([unit["savings"] > 0 for unit in units])
    expected = expected - tariff * has_savings * claimant_sum("savings_interest_income")
    np.testing.assert_allclose(
        v["uc_unearned_income"], expected, atol=0.01, err_msg=str(units)
    )


@PROPERTY_SETTINGS
@given(
    units=populations,
    year=st.sampled_from(YEARS),
    extra_claimants=st.lists(st.booleans(), min_size=6, max_size=6),
)
def test_at_most_two_assessed_claimants_drawn_from_flagged_claimants(
    units, year, extra_claimants
):
    data = situation(units, year)
    # Flag some dependants as claimants too, as data or users may.
    for i, unit in enumerate(units):
        if extra_claimants[i] and unit["dependants"]:
            data["people"][f"d{i}_0"]["is_uc_claimant"] = {year: True}
    sim = Simulation(situation=data)
    claimant = np.asarray(sim.calculate("is_uc_claimant", year))
    assessed = np.asarray(sim.calculate("is_uc_assessed_claimant", year))
    flagged = np.asarray(sim.map_result(claimant.astype(float), "person", "benunit"))
    counted = np.asarray(sim.map_result(assessed.astype(float), "person", "benunit"))
    assert np.all(counted <= 2), units
    assert np.all(claimant[assessed]), units
    np.testing.assert_array_equal(counted, np.minimum(flagged, 2), err_msg=str(units))


@PROPERTY_SETTINGS
@given(units=populations, year=st.sampled_from(YEARS))
def test_member_order_does_not_matter(units, year):
    forward_data = situation(units, year)
    backward_data = situation(units, year, reverse=True)
    forward = Simulation(situation=forward_data)
    backward = Simulation(situation=backward_data)
    a = benunit_values(forward, year)
    b = benunit_values(backward, year)
    for v in BENUNIT_VARIABLES:
        np.testing.assert_allclose(a[v], b[v], atol=0.01, err_msg=f"{v}: {units}")

    # The assessed claimants are the same people, by name.
    def assessed(sim, data):
        flags = np.asarray(sim.calculate("is_uc_assessed_claimant", year))
        return {name for name, flag in zip(data["people"], flags) if flag}

    assert assessed(forward, forward_data) == assessed(backward, backward_data), units
