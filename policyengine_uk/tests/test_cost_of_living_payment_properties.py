"""Properties of the Cost of Living Payments.

Under section 1 of the Social Security (Additional Payments) Acts 2022 and
2023, the Secretary of State pays the means-tested payment to each person,
meaning an individual or a couple, with Universal Credit, Pension Credit,
income-based JSA, income-related ESA or Income Support, and HMRC pays the same
amount to each person with Child Tax Credit or Working Tax Credit and none of
those benefits. In 2022-23 a tax credit counts only where its award comes to
at least £26 (2022 Act section 2(2)); Parliament set no minimum in the 2023
Act (section 3(1)). Under section 5 of each Act the Secretary of State pays
£150 to each individual with a listed disability benefit. The model treats
each benefit unit as a person in the Acts' sense, and pays the pensioner
payment once to each household with a Winter Fuel Payment.

The households here set every benefit the payments read as an input, so the
properties hold for any amounts of those benefits:

1. Dates: in every model year from 2015 (the first the model computes) to
   2021, and from 2024 to 2040, every household's, benefit unit's and
   person's payment is zero.
2. Decomposition: in 2022 and 2023, a household's payment equals the
   means-tested amount (£326 + £324 in 2022, £301 + £300 + £299 in 2023)
   times its qualifying benefit units, plus £150 times its qualifying people,
   plus the pensioner amount if it has a Winter Fuel Payment. The test counts
   qualifying units and people from the Acts' lists, not from the model's
   parameters, and checks each benefit unit's and person's payment the same
   way.
3. Monotonicity: in any year, adding a benefit unit to a household, or a
   person to one of its benefit units, never lowers the household's payment.

Each example builds one simulation of up to eight households.
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
# On neither list; the households vary in it all the same.
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
# 2022 Act section 2(2). The 2023 Act sets no minimum (section 3(1)).
MINIMUM_TAX_CREDIT_AWARD = {2022: 26, 2023: 0}
# Section 5(1) of each Act.
DISABILITY_AMOUNT = 150
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


def populations(years):
    return st.fixed_dictionaries(
        {
            "year": st.sampled_from(years),
            "households": st.lists(households(), min_size=1, max_size=8),
        }
    )


def unit(*people, **benefits):
    """A benefit unit with the given benefits, and people with the given
    disability benefits (one person with none if no people are given)."""
    return {
        "benefits": {
            name: float32(benefits.get(name, 0)) for name in BENEFIT_UNIT_INPUTS
        },
        "people": [
            {name: float32(person.get(name, 0)) for name in DISABILITY_BENEFITS}
            for person in (people or ({},))
        ],
    }


# Households that exercise each rule, whatever Hypothesis draws: every strand
# in one household, Housing Benefit alone, Child Tax Credit at and just under
# £26, both credits at £20 each, Universal Credit with tax credits, and a
# couple both on PIP.
PINNED_HOUSEHOLDS = [
    {
        "winter_fuel_allowance": 200.0,
        "units": [
            unit({"attendance_allowance": 3_000}, pension_credit=1_000),
            unit({}, {}, child_tax_credit=2_000),
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
        "units": [unit({"pip": 4_000}, {"pip": 2_000})],
    },
]


def pinned(year):
    return {"year": year, "households": PINNED_HOUSEHOLDS}


def situation(population):
    year = population["year"]
    people_, benunits, households_ = {}, {}, {}
    for h, household in enumerate(population["households"]):
        members = []
        for u, benefit_unit in enumerate(household["units"]):
            unit_members = []
            for p, person in enumerate(benefit_unit["people"]):
                name = f"h{h}_u{u}_p{p}"
                people_[name] = {key: {year: value} for key, value in person.items()}
                unit_members.append(name)
            benunits[f"h{h}_u{u}"] = {
                "members": unit_members,
                **{
                    key: {year: value}
                    for key, value in benefit_unit["benefits"].items()
                },
            }
            members += unit_members
        households_[f"h{h}"] = {
            "members": members,
            "winter_fuel_allowance": {year: household["winter_fuel_allowance"]},
        }
    return {"people": people_, "benunits": benunits, "households": households_}


@pytest.fixture(scope="module")
def template():
    return Simulation(situation={"people": {"template": {}}})


def simulate(template, population):
    # These properties never reform parameters or variable definitions, so
    # each example rebuilds its population on the template's system.
    simulation = template.clone(clone_tax_benefit_system=False)
    simulation.build_from_situation(situation(population))
    simulation.input_variables = simulation.get_known_variables()
    simulation.calculated_periods = []
    return simulation


def calculate(simulation, population, variable):
    return np.asarray(simulation.calculate(variable, population["year"]), dtype=float)


def unit_qualifies(benefit_unit, year):
    """Section 1(1) and (3), or section 1(2) with the minimum award."""
    benefits = benefit_unit["benefits"]
    if any(benefits[name] > 0 for name in LISTED_BENEFITS):
        return True
    minimum = MINIMUM_TAX_CREDIT_AWARD[year]
    return any(benefits[name] > 0 and benefits[name] >= minimum for name in TAX_CREDITS)


def person_qualifies(person):
    """Section 5(1) and (2)."""
    return any(person[name] > 0 for name in DISABILITY_BENEFITS)


def pensioner_amount(template, year):
    parameters = template.tax_benefit_system.parameters(f"{year}-01-01")
    return parameters.gov.treasury.cost_of_living_support.pensioners.amount


@SETTINGS
@given(populations(UNPAID_YEARS))
@example(pinned(2021))
@example(pinned(2024))
def test_no_household_payment_before_2022_or_from_2024(template, population):
    simulation = simulate(template, population)
    payment = calculate(simulation, population, "cost_of_living_support_payment")
    assert np.all(payment == 0), payment


@SETTINGS
@given(populations(UNPAID_YEARS))
@example(pinned(2021))
def test_no_unit_or_person_payment_before_2022_or_from_2024(template, population):
    simulation = simulate(template, population)
    for variable in PAYMENTS[1:]:
        payment = calculate(simulation, population, variable)
        assert np.all(payment == 0), (variable, payment)


@SETTINGS
@given(populations(PAID_YEARS))
@example(pinned(2022))
@example(pinned(2023))
def test_household_payment_counts_each_qualifying_unit_and_person(template, population):
    year = population["year"]
    expected = [
        MEANS_TESTED_AMOUNT[year]
        * sum(unit_qualifies(u, year) for u in household["units"])
        + DISABILITY_AMOUNT
        * sum(person_qualifies(p) for u in household["units"] for p in u["people"])
        + pensioner_amount(template, year) * (household["winter_fuel_allowance"] > 0)
        for household in population["households"]
    ]
    simulation = simulate(template, population)
    payment = calculate(simulation, population, "cost_of_living_support_payment")
    np.testing.assert_allclose(payment, expected, rtol=0, atol=TOLERANCE)


@SETTINGS
@given(populations(PAID_YEARS))
@example(pinned(2022))
@example(pinned(2023))
def test_each_unit_and_person_gets_its_own_payment(template, population):
    year = population["year"]
    units = [u for household in population["households"] for u in household["units"]]
    simulation = simulate(template, population)
    np.testing.assert_array_equal(
        calculate(simulation, population, "cost_of_living_means_tested_payment"),
        [MEANS_TESTED_AMOUNT[year] * unit_qualifies(u, year) for u in units],
    )
    np.testing.assert_array_equal(
        calculate(simulation, population, "cost_of_living_disability_payment"),
        [DISABILITY_AMOUNT * person_qualifies(p) for u in units for p in u["people"]],
    )


@SETTINGS
@given(
    population=populations(PAID_YEARS + UNPAID_YEARS),
    additions=st.lists(
        st.tuples(st.booleans(), benefit_units(), st.integers(0, 2)),
        min_size=8,
        max_size=8,
    ),
)
def test_adding_a_unit_or_person_never_lowers_the_payment(
    template, population, additions
):
    """Each household gains a benefit unit, or one of its units gains a
    person, drawn like any other."""
    grown = []
    for household, (add_unit, new_unit, index) in zip(
        population["households"], additions
    ):
        units = [dict(u, people=list(u["people"])) for u in household["units"]]
        if add_unit:
            units.append(new_unit)
        else:
            units[index % len(units)]["people"].append(new_unit["people"][0])
        grown.append(dict(household, units=units))
    payment = "cost_of_living_support_payment"
    before = calculate(simulate(template, population), population, payment)
    grown_population = dict(population, households=grown)
    after = calculate(simulate(template, grown_population), grown_population, payment)
    assert np.all(after >= before - TOLERANCE), (before, after)
