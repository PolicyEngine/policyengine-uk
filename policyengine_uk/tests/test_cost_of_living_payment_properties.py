"""Properties of the Cost of Living Payments.

Under section 1 of the Social Security (Additional Payments) Acts 2022 and
2023, the Secretary of State pays the means-tested payment to each person,
meaning an individual or a couple, with Universal Credit, Pension Credit,
income-based JSA, income-related ESA or Income Support, and HMRC pays the same
amount to each person with Child Tax Credit or Working Tax Credit and none of
those benefits. In 2022-23 a tax credit counts only where its award comes to
at least £26 (2022 Act sections 2(2) and 4); Parliament set no minimum in the
2023 Act (section 3(1)). Under section 5 of each Act the Secretary of State
pays £150 to each individual with a listed disability benefit. The model
treats each benefit unit as a person in the Acts' sense, and pays the
pensioner payment once to each household with a Winter Fuel Payment.

The tests set as inputs, in every year they check, every benefit the
payment formulas read, so the properties hold for any amounts of those
benefits:

1. Dates: in every model year from 2015 (the first the model computes) to
   2021, and from 2024 to 2040, every household's, benefit unit's and
   person's payment comes to zero. Each example checks all those years.
2. Decomposition: in 2022 and in 2023, a household's payment equals the
   means-tested amount (£326 + £324 in 2022, £301 + £300 + £299 in 2023)
   times its qualifying benefit units, plus £150 times its qualifying people,
   plus the £300 pensioner amount if it has a Winter Fuel Payment. The test
   counts qualifying units and people from the Acts' lists and takes every
   amount from the Acts or the sources below, never from the model's
   parameters. It checks each benefit unit's and person's payment the same
   way.
3. Monotonicity: in 2022 and in 2023, adding a qualifying benefit unit to a
   household raises its payment by that unit's own payments, and adding a
   person with a qualifying disability benefit to one of its units raises it
   by £150, so neither ever lowers it.

Each test builds one simulation per example: up to eight households, or up
to sixteen for the monotonicity test, which puts each household beside its
grown copy.
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

# Section 1(3) of each Act: the social security benefits.
LISTED_BENEFITS = [
    "universal_credit",
    "pension_credit",
    "jsa_income",
    "esa_income",
    "income_support",
]
# Section 1(2) of each Act: the tax credits.
TAX_CREDITS = ["child_tax_credit", "working_tax_credit"]
# On neither list; the strategies still draw it, so units on Housing Benefit
# alone occur.
UNLISTED_BENEFITS = ["housing_benefit"]
BENEFIT_UNIT_INPUTS = LISTED_BENEFITS + TAX_CREDITS + UNLISTED_BENEFITS
# Section 5(2) of each Act: the disability benefits the model has variables
# for.
DISABILITY_BENEFITS = [
    "pip",
    "dla",
    "attendance_allowance",
    "armed_forces_independence_payment",
]
# Section 1(1) and (2): £326 and £324 under the 2022 Act, and £301, £300 and
# £299 under the 2023 Act.
MEANS_TESTED_AMOUNT = {2022: 326 + 324, 2023: 301 + 300 + 299}
# 2022 Act sections 2(2) and 4. Parliament set no minimum in the 2023 Act
# (section 3(1)).
MINIMUM_TAX_CREDIT_AWARD = {2022: 26, 2023: 0}
# Section 5(1) of each Act.
DISABILITY_AMOUNT = 150
# Neither Act sets the pensioner payment. pensioners/amount.yaml takes £300 a
# year from the May 2022 package announcement and DWP's 2023-24 guidance.
PENSIONER_AMOUNT = 300
PAID_YEARS = [2022, 2023]
UNPAID_YEARS = [*range(2015, 2022), *range(2024, 2041)]
PAYMENTS = [
    "cost_of_living_support_payment",
    "cost_of_living_means_tested_payment",
    "cost_of_living_disability_payment",
]
# A penny: float32 holds a total of a few thousand pounds to within 0.001.
TOLERANCE = 1e-2
SETTINGS = settings(
    max_examples=40,
    deadline=None,
    derandomize=True,
    database=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)


def float32(amount):
    return float(np.float32(amount))


# Awards either side of the £26 minimum and any other amount up to £20,000,
# each as float32 holds it, so the test compares the amounts the model reads.
AWARDS = st.one_of(
    st.sampled_from([0.01, 25.99, 26.0, 26.01]),
    st.floats(0.01, 20_000, allow_nan=False, allow_infinity=False),
).map(float32)


@st.composite
def people(draw):
    """A person with up to two disability benefits, the rest zero."""
    paid = draw(st.sets(st.sampled_from(DISABILITY_BENEFITS), max_size=2))
    return {name: draw(AWARDS) if name in paid else 0.0 for name in DISABILITY_BENEFITS}


# The benefits a unit may have: none, Housing Benefit alone, tax credits
# alone, listed benefits alone, or any mix, so that each route to the
# means-tested payment, and Housing Benefit alone, occur often.
BENEFIT_POOLS = [
    [],
    UNLISTED_BENEFITS,
    TAX_CREDITS,
    LISTED_BENEFITS,
    BENEFIT_UNIT_INPUTS,
]


@st.composite
def benefit_units(draw):
    """One to three people, and up to three non-zero benefits or tax credits
    from one of BENEFIT_POOLS, the rest zero."""
    pool = draw(st.sampled_from(BENEFIT_POOLS))
    paid = (
        draw(st.sets(st.sampled_from(pool), min_size=1, max_size=min(3, len(pool))))
        if pool
        else set()
    )
    return {
        "benefits": {
            name: draw(AWARDS) if name in paid else 0.0 for name in BENEFIT_UNIT_INPUTS
        },
        "people": draw(st.lists(people(), min_size=1, max_size=3)),
    }


@st.composite
def households(draw):
    return {
        "winter_fuel_allowance": draw(st.one_of(st.just(0.0), AWARDS)),
        "units": draw(st.lists(benefit_units(), min_size=1, max_size=3)),
    }


HOUSEHOLD_LISTS = st.lists(households(), min_size=1, max_size=8)


@st.composite
def qualifying_units(draw):
    """A benefit unit with a listed benefit, or a tax credit of at least £26,
    so that it qualifies in 2022 and in 2023 whatever else it has."""
    benefit_unit = draw(benefit_units())
    name = draw(st.sampled_from(LISTED_BENEFITS + TAX_CREDITS))
    benefit_unit["benefits"][name] = draw(
        st.floats(26, 20_000, allow_nan=False, allow_infinity=False).map(float32)
    )
    return benefit_unit


@st.composite
def qualifying_people(draw):
    """A person with at least one listed disability benefit."""
    new_person = draw(people())
    new_person[draw(st.sampled_from(DISABILITY_BENEFITS))] = draw(AWARDS)
    return new_person


def person(**benefits):
    return {name: float32(benefits.get(name, 0)) for name in DISABILITY_BENEFITS}


def unit(*members, **benefits):
    """A benefit unit with these benefits and members: one member with no
    disability benefit when the call names none."""
    return {
        "benefits": {
            name: float32(benefits.get(name, 0)) for name in BENEFIT_UNIT_INPUTS
        },
        "people": list(members) or [person()],
    }


# Households that exercise each rule, whatever Hypothesis draws: every strand
# in one household, Housing Benefit alone, Child Tax Credit at and just under
# £26, both credits at £20 each, Universal Credit with tax credits, and a
# couple both on PIP.
PINNED_HOUSEHOLDS = [
    {
        "winter_fuel_allowance": 200.0,
        "units": [
            unit(person(attendance_allowance=3_000), pension_credit=1_000),
            unit(person(), person(), child_tax_credit=2_000),
        ],
    },
    {"winter_fuel_allowance": 0.0, "units": [unit(housing_benefit=3_000)]},
    {
        "winter_fuel_allowance": 0.0,
        "units": [unit(child_tax_credit=26), unit(child_tax_credit=25.99)],
    },
    {
        "winter_fuel_allowance": 0.0,
        "units": [unit(child_tax_credit=20, working_tax_credit=20)],
    },
    {
        "winter_fuel_allowance": 0.0,
        "units": [
            unit(universal_credit=1_000, child_tax_credit=2_000, working_tax_credit=500)
        ],
    },
    {
        "winter_fuel_allowance": 0.0,
        "units": [unit(person(pip=4_000), person(pip=2_000))],
    },
]
# For each pinned household: whether it gains a unit, the unit, the person a
# unit gains otherwise, and which unit gains the person. The first household
# already has two qualifying units and gains a third.
PINNED_ADDITIONS = [
    (True, unit(universal_credit=1_000), person(pip=1_000), 0),
    (False, unit(universal_credit=1_000), person(dla=500), 0),
    (True, unit(working_tax_credit=26), person(pip=1_000), 0),
    (True, unit(child_tax_credit=26), person(pip=1_000), 0),
    (False, unit(universal_credit=1_000), person(attendance_allowance=3_000), 0),
    (False, unit(universal_credit=1_000), person(pip=1_000), 0),
    (True, unit(pension_credit=1_000), person(pip=1_000), 0),
    (True, unit(pension_credit=1_000), person(pip=1_000), 0),
]


def situation(households_, years):
    """The households, with every input set to the same value in each year."""

    def each_year(value):
        return {year: value for year in years}

    people_, benunits, households_by_name = {}, {}, {}
    for h, household in enumerate(households_):
        members = []
        for u, benefit_unit in enumerate(household["units"]):
            unit_members = []
            for p, member in enumerate(benefit_unit["people"]):
                name = f"h{h}_u{u}_p{p}"
                people_[name] = {key: each_year(value) for key, value in member.items()}
                unit_members.append(name)
            benunits[f"h{h}_u{u}"] = {
                "members": unit_members,
                **{
                    key: each_year(value)
                    for key, value in benefit_unit["benefits"].items()
                },
            }
            members += unit_members
        households_by_name[f"h{h}"] = {
            "members": members,
            "winter_fuel_allowance": each_year(household["winter_fuel_allowance"]),
        }
    return {"people": people_, "benunits": benunits, "households": households_by_name}


@pytest.fixture(scope="module")
def template():
    return Simulation(situation={"people": {"template": {}}})


def simulate(template, households_, years):
    # No test here reforms parameters or variable definitions, so simulate()
    # builds each example's population on the template's tax-benefit system.
    simulation = template.clone(clone_tax_benefit_system=False)
    simulation.build_from_situation(situation(households_, years))
    simulation.input_variables = simulation.get_known_variables()
    simulation.calculated_periods = []
    return simulation


def calculate(simulation, variable, year):
    return np.asarray(simulation.calculate(variable, year), dtype=float)


def unit_qualifies(benefit_unit, year):
    """Section 1(1) and (3), or section 1(2) with the minimum award."""
    benefits = benefit_unit["benefits"]
    if any(benefits[name] > 0 for name in LISTED_BENEFITS):
        return True
    minimum = MINIMUM_TAX_CREDIT_AWARD[year]
    return any(benefits[name] > 0 and benefits[name] >= minimum for name in TAX_CREDITS)


def person_qualifies(member):
    """Section 5(1) and (2)."""
    return any(member[name] > 0 for name in DISABILITY_BENEFITS)


def unit_payments(benefit_unit, year):
    """A unit's means-tested payment and its members' disability payments."""
    return MEANS_TESTED_AMOUNT[year] * unit_qualifies(
        benefit_unit, year
    ) + DISABILITY_AMOUNT * sum(person_qualifies(p) for p in benefit_unit["people"])


def household_payment(household, year):
    return sum(unit_payments(u, year) for u in household["units"]) + (
        PENSIONER_AMOUNT * (household["winter_fuel_allowance"] > 0)
    )


@SETTINGS
@given(HOUSEHOLD_LISTS)
@example(PINNED_HOUSEHOLDS)
def test_no_household_payment_before_2022_or_from_2024(template, households_):
    simulation = simulate(template, households_, UNPAID_YEARS)
    for year in UNPAID_YEARS:
        payment = calculate(simulation, PAYMENTS[0], year)
        assert np.all(payment == 0), (year, payment)


@SETTINGS
@given(HOUSEHOLD_LISTS)
@example(PINNED_HOUSEHOLDS)
def test_no_unit_or_person_payment_before_2022_or_from_2024(template, households_):
    simulation = simulate(template, households_, UNPAID_YEARS)
    for year in UNPAID_YEARS:
        for variable in PAYMENTS[1:]:
            payment = calculate(simulation, variable, year)
            assert np.all(payment == 0), (year, variable, payment)


@SETTINGS
@given(HOUSEHOLD_LISTS)
@example(PINNED_HOUSEHOLDS)
def test_household_payment_counts_each_qualifying_unit_and_person(
    template, households_
):
    simulation = simulate(template, households_, PAID_YEARS)
    for year in PAID_YEARS:
        np.testing.assert_allclose(
            calculate(simulation, PAYMENTS[0], year),
            [household_payment(household, year) for household in households_],
            rtol=0,
            atol=TOLERANCE,
            err_msg=str(year),
        )


@SETTINGS
@given(HOUSEHOLD_LISTS)
@example(PINNED_HOUSEHOLDS)
def test_each_unit_and_person_gets_its_own_payment(template, households_):
    simulation = simulate(template, households_, PAID_YEARS)
    units = [u for household in households_ for u in household["units"]]
    for year in PAID_YEARS:
        np.testing.assert_array_equal(
            calculate(simulation, PAYMENTS[1], year),
            [MEANS_TESTED_AMOUNT[year] * unit_qualifies(u, year) for u in units],
            err_msg=str(year),
        )
        np.testing.assert_array_equal(
            calculate(simulation, PAYMENTS[2], year),
            [
                DISABILITY_AMOUNT * person_qualifies(p)
                for u in units
                for p in u["people"]
            ],
            err_msg=str(year),
        )


@SETTINGS
@given(
    households_=HOUSEHOLD_LISTS,
    additions=st.lists(
        st.tuples(
            st.booleans(), qualifying_units(), qualifying_people(), st.integers(0, 2)
        ),
        min_size=8,
        max_size=8,
    ),
)
@example(households_=PINNED_HOUSEHOLDS, additions=PINNED_ADDITIONS)
def test_adding_a_qualifying_unit_or_person_never_lowers_the_payment(
    template, households_, additions
):
    """Each household gains a qualifying benefit unit, or one of its units
    gains a person with a qualifying disability benefit."""
    grown, rises = [], {year: [] for year in PAID_YEARS}
    for household, (add_unit, new_unit, new_person, index) in zip(
        households_, additions
    ):
        units = [dict(u, people=list(u["people"])) for u in household["units"]]
        if add_unit:
            units.append(new_unit)
        else:
            units[index % len(units)]["people"].append(new_person)
        for year in PAID_YEARS:
            rises[year].append(
                unit_payments(new_unit, year) if add_unit else DISABILITY_AMOUNT
            )
        grown.append(dict(household, units=units))
    # One simulation holds the households and, after them, their grown copies.
    simulation = simulate(template, households_ + grown, PAID_YEARS)
    count = len(households_)
    for year in PAID_YEARS:
        payment = calculate(simulation, PAYMENTS[0], year)
        rise = payment[count:] - payment[:count]
        assert np.all(rise >= -TOLERANCE), (year, rise)
        np.testing.assert_allclose(
            rise, rises[year], rtol=0, atol=TOLERANCE, err_msg=str(year)
        )
