"""Synthetic properties for the separate statutory income concepts.

ITA 2007 s.23 Step 1 sums "the amounts of income on which the taxpayer is
charged to income tax"; Step 2 deducts reliefs. The differential below sums
the tax chain's parameter components, restores the carried-forward trading
loss already deducted inside a component, and deducts net-pay pension relief
which the model instead gives through allowances. It also checks the result
against the raw income inputs independently of the aggregation's formula.
The existing treatment of deficiency relief inside dividend income is held
at zero: correcting that component's law is outside this refactor.

HB reg 35(1)(i), pension-age HB reg 35(1)(h)-(i), and the non-dependant gross
income rules count SSP, SMP and SPP once. With actual tax, NI and pension
deductions held at zero, each pound must enter each earnings/gross concept
once. The historical post-tax and hypothetical UBI income bases deliberately
exclude statutory pay; their invariance is tested with positive phase-outs.
All populations are generated situations; no survey dataset is loaded.
"""

import numpy as np
import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

YEAR = 2026
STATUTORY_PAY = (
    "statutory_sick_pay",
    "statutory_maternity_pay",
    "statutory_paternity_pay",
)
COUNTRIES = ("ENGLAND", "SCOTLAND", "WALES")
ONCE = (
    "total_income",
    "total_income_charged_to_tax",
    "housing_benefit_non_dep_gross_income",
    "council_tax_reduction_non_dep_gross_income",
    "housing_benefit_net_earnings",
    "council_tax_reduction_net_earnings",
)
PRESERVED = (
    "gross_taxable_inputs",
    "post_tax_income",
    "bi_individual_phaseout",
    "bi_household_phaseout",
)
PROPERTY_SETTINGS = settings(
    max_examples=12, deadline=None, derandomize=True, database=None
)


@pytest.fixture(scope="module")
def template():
    # Positive rates make excluding statutory pay from the chosen UBI base an
    # observable design choice, rather than relying on baseline zero rates.
    reform = {
        f"gov.contrib.ubi_center.basic_income.phase_out.{scope}.{field}": {
            f"{YEAR}-01-01.{YEAR}-12-31": value
        }
        for scope in ("individual", "household")
        for field, value in (("rate", 0.1), ("threshold", 0))
    }
    return Simulation(
        situation={"people": {"template": {"age": {YEAR: 45}}}},
        reform=reform,
    )


def simulate(template, cases):
    """Clone the model once, giving every case its own family and household."""
    situation = {"people": {}, "benunits": {}, "households": {}}
    for index, case in enumerate(cases):
        person = f"person_{index}"
        inputs = {
            "age": 45,
            "is_claimant_or_partner": True,
            "is_council_tax_reduction_applicant_or_partner": True,
            "employer_pension_contributions": 0,
            "deficiency_relief": 0,
            "basic_income": 0,
            **{name: value for name, value in case.items() if name != "country"},
        }
        situation["people"][person] = {
            name: {YEAR: value} for name, value in inputs.items()
        }
        situation["benunits"][f"unit_{index}"] = {"members": [person]}
        situation["households"][f"household_{index}"] = {
            "members": [person],
            "country": {YEAR: case.get("country", "ENGLAND")},
        }
    simulation = template.clone(clone_tax_benefit_system=False)
    simulation.build_from_situation(situation)
    simulation.input_variables = simulation.get_known_variables()
    simulation.calculated_periods = []
    return simulation


def calculate(simulation, name):
    return np.asarray(simulation.calculate(name, YEAR), dtype=float)


money = st.integers(0, 20_000)
pay_case = st.fixed_dictionaries(
    {
        "employment_income": st.integers(10_000, 60_000),
        "self_employment_income": money,
        "private_pension_income": money,
        "spousal_maintenance_income": money,
        "maintenance_income": money,
        **{name: st.integers(1, 5_000) for name in STATUTORY_PAY},
        "country": st.sampled_from(COUNTRIES),
    }
)


@PROPERTY_SETTINGS
@given(people=st.lists(pay_case, min_size=1, max_size=8))
def test_statutory_pay_is_counted_once_in_each_programme_concept(template, people):
    cases, expected_pay = [], []
    for person in people:
        # Zero deductions isolate whether each statutory pay source enters
        # the base. Hold non-taxable awards fixed to avoid entitlement effects.
        base = {
            **person,
            **{name: 0 for name in STATUTORY_PAY},
            "social_security_income": 0,
            "employment_expenses": 0,
            "employee_pension_contributions": 0,
            "personal_pension_contributions": 0,
            "pension_contributions": 0,
            "income_tax": 0,
            "income_tax_before_winter_fuel_payment_charge": 0,
            "national_insurance": 0,
            "ni_class_1_employee": 0,
            "ni_class_2": 0,
            "ni_class_4": 0,
            "maternity_allowance": 0,
            "iidb": 0,
            "sda": 0,
            "war_widows_pension": 0,
            "bi_maximum": 100_000,
        }
        cases.append(base)
        expected_pay.append(0)
        for name in STATUTORY_PAY:
            cases.append({**base, name: person[name]})
            expected_pay.append(person[name])
        cases.append({**base, **{name: person[name] for name in STATUTORY_PAY}})
        expected_pay.append(sum(person[name] for name in STATUTORY_PAY))

    simulation = simulate(template, cases)
    expected_pay = np.asarray(expected_pay).reshape(-1, 5)
    for name in ONCE + PRESERVED:
        values = calculate(simulation, name).reshape(-1, 5)
        expected_delta = expected_pay if name in ONCE else 0
        np.testing.assert_allclose(
            values - values[:, :1],
            expected_delta,
            atol=0.03,
            rtol=1e-6,
            err_msg=name,
        )
    # With uncapped positive phase-outs and one person per household, both
    # consumers must use exactly the same preserved raw-input base.
    gross = calculate(simulation, "gross_taxable_inputs")
    np.testing.assert_allclose(
        calculate(simulation, "post_tax_income"), gross, atol=0.03
    )
    for name in ("bi_individual_phaseout", "bi_household_phaseout"):
        np.testing.assert_allclose(calculate(simulation, name), gross * 0.1, atol=0.03)


taxpayer = st.fixed_dictionaries(
    {
        "age": st.integers(18, 85),
        "employment_income": st.integers(0, 100_000),
        "employment_expenses": st.integers(0, 5_000),
        **{name: st.integers(0, 5_000) for name in STATUTORY_PAY},
        "private_pension_income": money,
        "social_security_income": money,
        "self_employment_income": money,
        "capital_allowances": st.integers(0, 5_000),
        "trading_allowance_deduction": st.integers(0, 1_000),
        "loss_relief": st.integers(0, 30_000),
        "trading_loss": st.integers(0, 30_000),
        "property_income": money,
        "property_allowance_deduction": st.integers(0, 1_000),
        "savings_interest_income": money,
        "other_investment_income": money,
        "individual_savings_account_interest_income": money,
        "dividend_income": money,
        "miscellaneous_income": st.integers(-20_000, 20_000),
        "employee_pension_contributions": money,
        "personal_pension_contributions": money,
        "gift_aid": st.integers(0, 5_000),
    }
)


@PROPERTY_SETTINGS
@given(people=st.lists(taxpayer, min_size=1, max_size=12))
@example(
    people=[
        {
            "employment_income": 40_000,
            "self_employment_income": 5_000,
            "capital_allowances": 500,
            "trading_allowance_deduction": 100,
            "loss_relief": 20_000,
            "trading_loss": 30_000,
            "employee_pension_contributions": 2_000,
            "personal_pension_contributions": 3_000,
        }
    ]
)
def test_total_income_equals_tax_components_before_step_two_reliefs(template, people):
    cases, expected, losses_deducted, net_pay = [], [], [], []
    for person in people:
        inputs = {**person, "deductible_property_finance_costs": 0}

        def get(name):
            return person.get(name, 0)

        pay = max(
            0,
            get("employment_income")
            + sum(get(name) for name in STATUTORY_PAY)
            - get("employment_expenses"),
        )
        trading_before_reliefs = max(
            0,
            get("self_employment_income")
            - get("capital_allowances")
            - get("trading_allowance_deduction"),
        )
        carried_loss_deducted = min(trading_before_reliefs, get("loss_relief"))
        net_pay_relief = (
            min(get("employee_pension_contributions"), pay)
            if person.get("age", 45) < 75
            else 0
        )
        expected.append(
            pay
            + get("private_pension_income")
            + get("social_security_income")
            + trading_before_reliefs
            + max(0, get("property_income") - get("property_allowance_deduction"))
            + max(
                0,
                get("savings_interest_income")
                + get("other_investment_income")
                - get("individual_savings_account_interest_income"),
            )
            + get("dividend_income")
            + max(0, get("miscellaneous_income"))
            - net_pay_relief
        )
        losses_deducted.append(carried_loss_deducted)
        net_pay.append(net_pay_relief)
        cases.extend(
            [
                inputs,
                {
                    **inputs,
                    "loss_relief": 0,
                    "trading_loss": 0,
                    "personal_pension_contributions": 0,
                    "gift_aid": 0,
                },
            ]
        )

    simulation = simulate(template, cases)
    components = simulation.tax_benefit_system.parameters(
        YEAR
    ).gov.hmrc.income_tax.adjusted_net_income_components
    component_sum = sum(calculate(simulation, name) for name in components)
    before_step_two = (
        component_sum[::2] + np.asarray(losses_deducted) - np.asarray(net_pay)
    )
    for name in ("total_income", "total_income_charged_to_tax"):
        values = calculate(simulation, name).reshape(-1, 2)
        np.testing.assert_allclose(values[:, 0], expected, atol=0.1, rtol=1e-6)
        np.testing.assert_allclose(values[:, 0], before_step_two, atol=0.1, rtol=1e-6)
        # Removing current and carried-forward trading losses, RAS relief
        # and Gift Aid cannot alter Step 1. Net-pay relief remains unchanged.
        np.testing.assert_allclose(
            values[:, 0], values[:, 1], atol=0.1, rtol=1e-6, err_msg=name
        )
