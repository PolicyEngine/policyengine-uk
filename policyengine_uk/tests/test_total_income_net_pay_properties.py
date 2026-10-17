"""Property-based tests for pension contributions in total income.

The winter fuel payment charge tests total income (ITA 2007 s.23 Step 1).
Employee pension contributions, which the model takes as paid under a net pay
arrangement, are deducted from employment income (FA 2004 s.193(2)), so total
income is after them. Contributions relieved at source (s.192) are not.
Invariants, for any single pensioner in England with pay, employment
expenses, a private pension and both kinds of contribution, in 2025:

1. Net pay relief is the employee contributions, up to taxable employment
   income, and nothing from age 75 (s.188(3)(a)).
2. Total income is taxable employment income plus the pension, less that
   relief. Contributions relieved at source never change it.
3. Adjusted total income (s.24A(8)), which reads total income for Step 1,
   still deducts each relieved contribution once: it is the pay and pension
   less the contributions relieved, up to the greater of £3,600 and the pay.
4. The charge is the whole payment when total income exceeds £35,000, and
   nothing otherwise (no relevant benefit is entered).

All populations are synthetic situations; these tests never load a dataset.
"""

import numpy as np
import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

YEAR = 2025
VARIABLES = (
    "taxable_employment_income",
    "net_pay_pension_relief",
    "total_income_charged_to_tax",
    "adjusted_total_income",
    "winter_fuel_payment",
    "winter_fuel_payment_charge",
)


@pytest.fixture(scope="module")
def template():
    return Simulation(situation={"people": {"template": {"age": {YEAR: 70}}}})


def simulate(template, people):
    """Give each pensioner their own English household and benefit unit."""
    situation = {"people": {}, "benunits": {}, "households": {}}
    for index, person in enumerate(people):
        name = f"pensioner_{index}"
        situation["people"][name] = {
            key: {YEAR: value} for key, value in person.items()
        }
        situation["people"][name]["employer_pension_contributions"] = {YEAR: 0}
        situation["benunits"][f"unit_{index}"] = {
            "members": [name],
            "pension_credit": {YEAR: 0},
        }
        situation["households"][f"household_{index}"] = {
            "members": [name],
            "country": {YEAR: "ENGLAND"},
        }
    simulation = template.clone(clone_tax_benefit_system=False)
    simulation.build_from_situation(situation)
    simulation.input_variables = simulation.get_known_variables()
    simulation.calculated_periods = []
    return {
        name: np.asarray(simulation.calculate(name, YEAR), dtype=float)
        for name in VARIABLES
    }


def money(top):
    return st.integers(0, top).map(float)


pensioner = st.fixed_dictionaries(
    {
        "age": st.integers(66, 90),
        "employment_income": money(60_000),
        "employment_expenses": money(3_000),
        "private_pension_income": money(50_000),
        "employee_pension_contributions": money(20_000),
        "personal_pension_contributions": money(20_000),
    }
)
# Pay of £36,000 with £2,000 of employee contributions: total income £34,000.
NET_PAY = {
    "age": 70,
    "employment_income": 36_000.0,
    "employment_expenses": 0.0,
    "private_pension_income": 0.0,
    "employee_pension_contributions": 2_000.0,
    "personal_pension_contributions": 0.0,
}


@settings(max_examples=12, deadline=None, derandomize=True, database=None)
@given(people=st.lists(pensioner, min_size=1, max_size=20))
@example(
    people=[
        NET_PAY,
        {**NET_PAY, "age": 80},
        {**NET_PAY, "employment_expenses": 1_500.0},
    ]
)
def test_net_pay_contributions_and_only_they_come_off_total_income(template, people):
    with_ras = simulate(template, people)
    without_ras = simulate(
        template,
        [{**person, "personal_pension_contributions": 0.0} for person in people],
    )
    for i, person in enumerate(people):
        taxable_pay = max(
            0.0, person["employment_income"] - person["employment_expenses"]
        )
        under_75 = person["age"] < 75
        net_pay = under_75 * min(person["employee_pension_contributions"], taxable_pay)
        total_income = taxable_pay + person["private_pension_income"] - net_pay
        contributions = (
            person["employee_pension_contributions"]
            + person["personal_pension_contributions"]
        )
        relieved = under_75 * min(contributions, max(3_600.0, taxable_pay))
        adjusted_total_income = max(
            0.0, taxable_pay + person["private_pension_income"] - relieved
        )
        charge = with_ras["winter_fuel_payment"][i] * (total_income > 35_000)
        expected = {
            "net_pay_pension_relief": net_pay,
            "total_income_charged_to_tax": total_income,
            "adjusted_total_income": adjusted_total_income,
            "winter_fuel_payment_charge": charge,
        }
        for name, value in expected.items():
            assert with_ras[name][i] == pytest.approx(value, abs=0.05), (
                name,
                person,
            )
        # Relief at source leaves total income, and so the charge, alone.
        for name in ("total_income_charged_to_tax", "winter_fuel_payment_charge"):
            assert with_ras[name][i] == without_ras[name][i], (name, person)
