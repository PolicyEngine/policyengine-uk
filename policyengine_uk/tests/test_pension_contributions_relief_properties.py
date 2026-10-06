"""Property-based tests for pension contributions relief (FA 2004 ss.188-190).

Invariants, for any employment income, self-employment profit or loss,
contributions and age:

1. Bounds: 0 <= relief <= contributions, and relief <= relevant UK earnings,
   the positive part of employment income plus the positive part of trading
   income (s.189(2), s.190(1)). A loss never makes relief negative.
2. Age: no relief on contributions paid at or after the age limit
   (s.188(3)(a)).
3. Differential: relief equals an independent scalar implementation,
   min(contributions, earnings, max(basic amount, annual allowance)) under
   the age limit, with the annual allowance read from the model.
4. Loss invariance: replacing a self-employment loss with zero changes
   neither the relief nor allowances nor income tax.
5. Monotonicity: with income held fixed, relief is non-decreasing in
   contributions.

Earnings are read from the model's employment_income and
self_employment_income, not the raw inputs: from 2029 employment_income
includes the salary sacrifice broad-base haircut.

Comparisons allow float32 rounding: the model stores values as float32.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

YEARS = list(range(2018, 2031))
PROPERTY_SETTINGS = settings(
    max_examples=25,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)


def tolerance(*amounts):
    # float32 has a 24-bit significand: a few ulps of the largest amount
    # involved, plus a penny.
    return 0.01 + 4e-7 * max(abs(float(a)) for a in amounts)


def amounts(low, high):
    return st.one_of(
        st.just(0.0),
        st.integers(low, high).map(float),
        st.floats(low, high, allow_nan=False, allow_infinity=False),
    )


losses = st.one_of(
    st.integers(-400_000, -1).map(float),
    st.floats(-400_000, -0.01, allow_nan=False, allow_infinity=False),
)


def person_strategy(self_employment_income):
    return st.fixed_dictionaries(
        {
            "age": st.one_of(st.integers(16, 90), st.sampled_from([74, 75, 76])),
            "employment_income": st.one_of(amounts(0, 300_000), amounts(-5_000, 0)),
            "self_employment_income": self_employment_income,
            "personal_pension_contributions": amounts(0, 120_000),
            "employee_pension_contributions_reported": amounts(0, 60_000),
        }
    )


# Losses as large as or larger than any wages, profits and zero.
people = person_strategy(st.one_of(amounts(-400_000, 300_000), losses))
people_with_losses = person_strategy(losses)


def simulate(year, population):
    situation = {
        "people": {
            f"p{i}": {name: {year: value} for name, value in person.items()}
            for i, person in enumerate(population)
        },
        "benunits": {f"b{i}": {"members": [f"p{i}"]} for i in range(len(population))},
        "households": {f"h{i}": {"members": [f"p{i}"]} for i in range(len(population))},
    }
    sim = Simulation(situation=situation)
    values = {
        variable: sim.calculate(variable, year).astype(np.float64)
        for variable in [
            "pension_contributions_relief",
            "pension_contributions",
            "relevant_uk_earnings",
            "pension_annual_allowance",
            "employment_income",
            "self_employment_income",
            "allowances",
            "income_tax",
        ]
    }
    parameters = sim.tax_benefit_system.parameters(f"{year}-01-01").gov.hmrc
    values["basic_amount"] = float(
        parameters.income_tax.reliefs.pension_contribution.basic_amount
    )
    values["age_limit"] = float(
        parameters.pensions.pension_contributions_relief_age_limit
    )
    return values


def relevant_uk_earnings(values, i):
    """FA 2004 s.189(2): each source counts only if positive."""
    return max(values["employment_income"][i], 0) + max(
        values["self_employment_income"][i], 0
    )


def reference_relief(person, earnings, annual_allowance, basic_amount, age_limit):
    """FA 2004 ss.188-190 as modelled, from the contribution inputs."""
    if person["age"] >= age_limit:
        return 0.0
    contributions = (
        person["personal_pension_contributions"]
        + person["employee_pension_contributions_reported"]
    )
    return max(
        min(contributions, earnings, max(basic_amount, annual_allowance)),
        0,
    )


@PROPERTY_SETTINGS
@given(st.sampled_from(YEARS), st.lists(people, min_size=1, max_size=12))
def test_relief_is_bounded_and_matches_reference(year, population):
    values = simulate(year, population)
    for i, person in enumerate(population):
        relief = values["pension_contributions_relief"][i]
        contributions = values["pension_contributions"][i]
        earnings = relevant_uk_earnings(values, i)
        tol = tolerance(relief, contributions, earnings)

        assert relief >= 0, (i, person, relief)
        assert relief <= max(contributions, 0) + tol, (i, person, relief)
        assert relief <= earnings + tol, (i, person, relief, earnings)
        assert abs(values["relevant_uk_earnings"][i] - earnings) <= tol
        if person["age"] >= values["age_limit"]:
            assert relief == 0, (i, person, relief)

        expected = reference_relief(
            person,
            earnings,
            values["pension_annual_allowance"][i],
            values["basic_amount"],
            values["age_limit"],
        )
        assert abs(relief - expected) <= tol, (i, person, relief, expected)


@PROPERTY_SETTINGS
@given(
    st.sampled_from(YEARS),
    st.lists(people_with_losses, min_size=1, max_size=10),
)
def test_self_employment_loss_does_not_change_relief_or_tax(year, population):
    without_loss = [{**person, "self_employment_income": 0.0} for person in population]
    # Both versions of each person in one simulation.
    values = simulate(year, population + without_loss)
    n = len(population)
    for variable in ["pension_contributions_relief", "allowances", "income_tax"]:
        with_loss_values = values[variable][:n]
        without_loss_values = values[variable][n:]
        for i in range(n):
            tol = tolerance(with_loss_values[i], without_loss_values[i])
            assert abs(with_loss_values[i] - without_loss_values[i]) <= tol, (
                variable,
                population[i],
                with_loss_values[i],
                without_loss_values[i],
            )


@PROPERTY_SETTINGS
@given(
    st.sampled_from(YEARS),
    people,
    st.lists(amounts(0, 150_000), min_size=2, max_size=12),
)
def test_relief_is_non_decreasing_in_contributions(year, person, contributions):
    ordered = sorted(contributions)
    population = [
        {
            **person,
            "personal_pension_contributions": amount,
            "employee_pension_contributions_reported": 0.0,
        }
        for amount in ordered
    ]
    relief = simulate(year, population)["pension_contributions_relief"]
    for i in range(1, len(ordered)):
        tol = tolerance(relief[i - 1], relief[i], ordered[i])
        assert relief[i] >= relief[i - 1] - tol, (person, ordered, relief)
