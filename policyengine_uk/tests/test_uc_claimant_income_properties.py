"""Property-based tests: Universal Credit counts only claimants' income.

UC Regs 2013 reg. 22(1) deducts "all of the claimant's unearned income (or in
the case of joint claimants all of their combined unearned income)" and "the
claimant's earned income (or, in the case of joint claimants, their combined
earned income)"; WRA 2012 s. 8(4) says the same of the Act's deductions. A
claim is made by a single person or jointly by a couple (s. 2(1)), so it has
at most two claimants. A child's or qualifying young person's income, and the
income of anyone else in the benefit unit, is not the claimant's. The benefit
cap's earnings exception (reg. 82(1)(a)), the benefit cap total (WRA 2012 s.
96(1)) and the childcare work condition (reg. 32(1)) are framed the same way.

Invariants, for any generated population of single claimants, couples and
mixed-age couples with up to four dependants aged 0 to 19 (in or out of
education), with or without rent, childcare costs and capital, in England,
Wales and Scotland. A third of the families are built to be over the benefit
cap, and a third to have working claimants paying for childcare:

1. A dependant's income never changes Universal Credit. Giving every
   dependant earnings, self-employment profits or losses, miscellaneous
   income, savings interest, dividends, property income, a private pension or
   contributory benefits leaves UC, UC before the benefit cap, the cap
   reduction, earned income, unearned income and the childcare costs element
   exactly as they are when the dependants have no income.
2. The assessed claimants are the claimants: in every generated family the
   model assesses the claimant and partner and nobody else.
3. Differential against the regulations, for 2026-27: with earnings below the
   personal allowance and primary threshold, earned income equals the
   claimants' combined earnings less the reg. 22 work allowance (£710 a
   month, or £427 with the housing costs element, where they are responsible
   for a child or qualifying young person), and unearned income equals the
   claimants' private pensions plus either their savings interest or, with
   capital over £6,000, the reg. 72 tariff income of £4.35 a month for each
   £250 or part. The amounts are written here from the regulations, not read
   from the model.
4. There are at most two assessed claimants however many members are flagged
   as claimants, they are flagged claimants, and they are every flagged
   member when two or fewer are flagged.
5. Order does not matter: entering the people of every family in reverse
   leaves the assessed claimants and UC unchanged. (Members of the same age
   rank in the order listed, so with more than two flagged claimants and a
   tie in age the order would decide; the generated families flag at most
   two.)

Marriage Allowance is switched off throughout, as in the other Universal
Credit property tests.
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
# What a dependant may receive. The last two are contributory benefits, which
# count towards the benefit cap total when they are the claimant's.
# Contributory ESA is left out: any member's ESA exempts the benefit unit from
# the cap in the model, which is a question of whose circumstances count, not
# whose income.
DEPENDANT_INCOME = {
    "employment_income": amount,
    "self_employment_income": st.one_of(st.just(0.0), st.floats(-5_000, 30_000)),
    "miscellaneous_income": amount,
    "savings_interest_income": amount,
    "dividend_income": amount,
    "property_income": amount,
    "private_pension_income": amount,
    "jsa_contrib": st.one_of(st.just(0.0), st.floats(0, 6_000)),
    "incapacity_benefit": st.one_of(st.just(0.0), st.floats(0, 8_000)),
}
BENUNIT_VARIABLES = [
    "universal_credit",
    "universal_credit_pre_benefit_cap",
    "benefit_cap_reduction",
    "uc_earned_income",
    "uc_unearned_income",
    "uc_childcare_element",
]


@st.composite
def dependants(draw, minimum=0, maximum=4, childcare=False):
    members = []
    for _ in range(draw(st.integers(minimum, maximum))):
        age = draw(st.integers(0, 19))
        member = dict(age=age, **{v: draw(s) for v, s in DEPENDANT_INCOME.items()})
        if age >= 16:
            # At 18 and 19 only a qualifying young person is a dependant:
            # in non-advanced education begun before 19 and, at 19, before
            # the 1 September after their birthday (reg. 5(1)). Anyone else
            # that age is an adult whom the calculator treats as a claimant.
            member["current_education"] = (
                draw(st.sampled_from(EDUCATION)) if age < 18 else "UPPER_SECONDARY"
            )
            member["age_started_or_accepted_current_education_or_training"] = draw(
                st.integers(16, min(age, 18))
            )
            if age == 19:
                member[
                    "is_before_universal_credit_qualifying_young_person_terminal_date"
                ] = True
        members.append(member)
    if childcare:
        # A young child in paid childcare, and an 18-year-old at school whose
        # job must neither meet nor block the parents' work condition.
        members.append(dict(age=3, childcare_expenses=draw(st.floats(1_000, 9_000))))
        members.append(
            dict(
                age=18,
                current_education="UPPER_SECONDARY",
                age_started_or_accepted_current_education_or_training=17,
                **{v: draw(s) for v, s in DEPENDANT_INCOME.items()},
            )
        )
    return members


@st.composite
def families(draw):
    kind = draw(st.sampled_from(["general", "capped", "childcare"]))
    shape = draw(st.sampled_from(list(SHAPES)))
    if kind == "capped":
        # Claimants without earnings, several children and a high council
        # rent: over the cap unless something exempts them.
        claimants = [dict(age=draw(age)) for age in SHAPES[shape]]
        return dict(
            claimants=claimants,
            dependants=draw(dependants(minimum=3)),
            tenure="RENT_FROM_COUNCIL",
            rent=draw(st.floats(12_000, 30_000)),
            region=draw(st.sampled_from(REGIONS)),
            savings=0.0,
        )
    if kind == "childcare":
        # Every claimant works, so the work condition is the claimants' to
        # meet.
        claimants = [
            dict(age=draw(age), employment_income=draw(st.floats(3_000, 30_000)))
            for age in SHAPES[shape]
        ]
        return dict(
            claimants=claimants,
            dependants=draw(dependants(maximum=1, childcare=True)),
            tenure=draw(st.sampled_from(TENURES)),
            rent=draw(st.one_of(st.just(0.0), st.floats(0, 15_000))),
            region=draw(st.sampled_from(REGIONS)),
            savings=0.0,
        )
    claimants = [
        dict(
            age=draw(age),
            employment_income=draw(amount),
            savings_interest_income=draw(amount),
            private_pension_income=draw(amount),
        )
        for age in SHAPES[shape]
    ]
    return dict(
        claimants=claimants,
        dependants=draw(dependants()),
        tenure=draw(st.sampled_from(TENURES)),
        rent=draw(st.one_of(st.just(0.0), st.floats(0, 30_000))),
        region=draw(st.sampled_from(REGIONS)),
        savings=draw(st.one_of(st.just(0.0), st.floats(0, 20_000))),
    )


populations = st.lists(families(), min_size=1, max_size=6)


def situation(units, year, zero_dependants=False, reverse=False, flag_all=False):
    """One simulation holding every family.

    With ``zero_dependants`` every dependant's income is nil. With
    ``reverse`` the people of each family are entered, and listed in their
    benefit unit and household, in reverse order. With ``flag_all`` every
    member is flagged as a claimant, as data or users may.
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
                key: {year: 0.0 if zero_dependants and key in DEPENDANT_INCOME else v}
                for key, v in dependant.items()
            }
            members.append((f"d{i}_{k}", person))
        if reverse:
            members = members[::-1]
        names = []
        for name, person in members:
            person["would_claim_marriage_allowance"] = {year: False}
            if flag_all:
                person["is_uc_claimant"] = {year: True}
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


def benunit_values(sim, year):
    return {v: np.asarray(sim.calculate(v, year)) for v in BENUNIT_VARIABLES}


def built_claimants(units):
    """Person flags, in order: the claimants the test built, then dependants."""
    flags = []
    for unit in units:
        flags += [True] * len(unit["claimants"]) + [False] * len(unit["dependants"])
    return np.array(flags)


@PROPERTY_SETTINGS
@given(units=populations, year=st.sampled_from(YEARS))
def test_dependants_income_never_changes_universal_credit(units, year):
    with_income = Simulation(situation=situation(units, year))
    without_income = Simulation(situation=situation(units, year, zero_dependants=True))
    a = benunit_values(with_income, year)
    b = benunit_values(without_income, year)
    for v in BENUNIT_VARIABLES:
        np.testing.assert_allclose(a[v], b[v], atol=0.01, err_msg=f"{v}: {units}")


@PROPERTY_SETTINGS
@given(units=populations, year=st.sampled_from(YEARS))
def test_assessed_claimants_are_the_claimant_and_partner(units, year):
    sim = Simulation(situation=situation(units, year))
    np.testing.assert_array_equal(
        np.asarray(sim.calculate("is_uc_assessed_claimant", year)),
        built_claimants(units),
        err_msg=str(units),
    )


# Reg. 22(2) table and reg. 72(1), 2026-27, a month.
HIGHER_WORK_ALLOWANCE = 710
LOWER_WORK_ALLOWANCE = 427
TARIFF_INCOME_PER_STEP = 4.35
TARIFF_STEP = 250
TARIFF_LOWER_LIMIT = 6_000
# Below the 2026-27 personal allowance and primary threshold (£12,570), so
# nothing is deducted from the claimant's earnings (reg. 55(5)).
untaxed_earnings = st.one_of(st.just(0.0), st.floats(0, 12_000))


@st.composite
def untaxed_families(draw):
    """Working-age claimants whose earnings carry no tax or NI, with capital
    under the £16,000 limit (reg. 18)."""
    claimants = [
        dict(
            age=draw(st.integers(25, 60)),
            employment_income=draw(untaxed_earnings),
            savings_interest_income=draw(st.one_of(st.just(0.0), st.floats(0, 500))),
            private_pension_income=draw(st.one_of(st.just(0.0), st.floats(0, 500))),
        )
        for _ in range(draw(st.integers(1, 2)))
    ]
    return dict(
        claimants=claimants,
        dependants=draw(dependants()),
        tenure=draw(st.sampled_from(TENURES)),
        rent=draw(st.one_of(st.just(0.0), st.floats(1_000, 12_000))),
        region=draw(st.sampled_from(REGIONS)),
        savings=draw(st.one_of(st.just(0.0), st.floats(0, 15_900))),
    )


@PROPERTY_SETTINGS
@given(units=st.lists(untaxed_families(), min_size=1, max_size=6))
def test_income_matches_regulations_22_and_72(units):
    year = 2026
    sim = Simulation(situation=situation(units, year))
    earned = np.asarray(sim.calculate("uc_earned_income", year))
    unearned = np.asarray(sim.calculate("uc_unearned_income", year))
    # The model says only whether the award has a housing costs element and
    # whether a dependant is a child or qualifying young person.
    housing = np.asarray(sim.calculate("uc_housing_costs_element", year)) > 0
    qualifying = np.asarray(
        sim.calculate("is_child_or_qualifying_young_person_for_universal_credit", year)
    )
    person = 0
    for i, unit in enumerate(units):
        n_claimants, n_dependants = len(unit["claimants"]), len(unit["dependants"])
        responsible = qualifying[
            person + n_claimants : person + n_claimants + n_dependants
        ].any()
        person += n_claimants + n_dependants
        work_allowance = 0
        if responsible:
            monthly = LOWER_WORK_ALLOWANCE if housing[i] else HIGHER_WORK_ALLOWANCE
            work_allowance = monthly * 12
        earnings = sum(c["employment_income"] for c in unit["claimants"])
        expected_earned = max(0, earnings - work_allowance)
        pensions = sum(c["private_pension_income"] for c in unit["claimants"])
        interest = sum(c["savings_interest_income"] for c in unit["claimants"])
        excess = unit["savings"] - TARIFF_LOWER_LIMIT
        if excess > 0:
            # Tariff income replaces the capital's actual yield (reg. 72(3)).
            steps = np.ceil(excess / TARIFF_STEP)
            expected_unearned = pensions + steps * TARIFF_INCOME_PER_STEP * 12
        else:
            expected_unearned = pensions + interest
        np.testing.assert_allclose(
            earned[i], expected_earned, atol=0.5, err_msg=str(unit)
        )
        np.testing.assert_allclose(
            unearned[i], expected_unearned, atol=0.5, err_msg=str(unit)
        )


@PROPERTY_SETTINGS
@given(units=populations, year=st.sampled_from(YEARS), flag_all=st.booleans())
def test_at_most_two_assessed_claimants_drawn_from_flagged_claimants(
    units, year, flag_all
):
    sim = Simulation(situation=situation(units, year, flag_all=flag_all))
    claimant = np.asarray(sim.calculate("is_uc_claimant", year))
    assessed = np.asarray(sim.calculate("is_uc_assessed_claimant", year))
    flagged = np.asarray(sim.map_result(claimant.astype(float), "person", "benunit"))
    counted = np.asarray(sim.map_result(assessed.astype(float), "person", "benunit"))
    assert np.all(counted <= 2), units
    assert np.all(claimant[assessed]), units
    np.testing.assert_array_equal(counted, np.minimum(flagged, 2), err_msg=str(units))


def test_three_flagged_claimants_leave_two_assessed():
    # A deterministic case of the property above: a couple and their child,
    # all flagged, in each of three years.
    units = [
        dict(
            claimants=[dict(age=40), dict(age=38)],
            dependants=[dict(age=12)],
            tenure="OWNED_OUTRIGHT",
            rent=0.0,
            region="NORTH_EAST",
            savings=0.0,
        )
    ]
    for year in YEARS:
        sim = Simulation(situation=situation(units, year, flag_all=True))
        assert list(sim.calculate("is_uc_claimant", year)) == [True, True, True]
        assert list(sim.calculate("is_uc_assessed_claimant", year)) == [
            True,
            True,
            False,
        ]


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
