"""UC expense disregards use already-allowable amounts, not raw-cost claims."""

import numpy as np
import pytest

from policyengine_uk import Simulation

YEAR = 2024


def situation(people=None, *, year=YEAR, benunit=None):
    people = people or {"claimant": {"age": 30, "employment_income": 6_000}}
    names = list(people)
    return {
        "people": {
            name: {key: {year: value} for key, value in inputs.items()}
            for name, inputs in people.items()
        },
        "benunits": {
            "family": {
                "members": names,
                "would_claim_uc": {year: True},
                **{key: {year: value} for key, value in (benunit or {}).items()},
            }
        },
        "households": {
            "household": {
                "members": names,
                "region": {year: "LONDON"},
                "tenure_type": {year: "OWNED_OUTRIGHT"},
            }
        },
    }


def simulation(people=None, *, year=YEAR, benunit=None):
    return Simulation(situation=situation(people, year=year, benunit=benunit))


def test_allowable_expenses_increase_natural_final_uc_cash():
    ordinary = simulation()
    expenses = simulation(
        {
            "claimant": {
                "age": 30,
                "employment_income": 6_000,
                "employment_expenses": 600,
            }
        }
    )
    for sim, earned in [(ordinary, 6_000), (expenses, 5_400)]:
        np.testing.assert_allclose(
            sim.calculate("uc_individual_earned_income_before_mif", YEAR),
            [earned],
            atol=0.01,
        )
        assert sim.calculate("is_uc_eligible", YEAR)[0]
        assert sim.calculate("claims_universal_credit", YEAR)[0]
        assert not sim.calculate("uc_mif_applies", YEAR)[0]
        for variable in [
            "income_tax",
            "national_insurance",
            "pension_contributions",
            "uc_work_allowance",
            "uc_benefit_cap_reduction",
            "uc_deductions",
        ]:
            np.testing.assert_allclose(sim.calculate(variable, YEAR), [0], atol=0.01)
    # Both awards are positive and below the unchanged maximum: the
    # 55% earnings taper passes on 600 * .55 = 330, without clipping.
    for variable in ["universal_credit_pre_benefit_cap", "universal_credit"]:
        low = ordinary.calculate(variable, YEAR)
        high = expenses.calculate(variable, YEAR)
        assert low[0] > 0
        assert high[0] < expenses.calculate("uc_maximum_amount", YEAR)[0]
        np.testing.assert_allclose(high - low, [330], atol=0.01)


@pytest.mark.parametrize("year", [2020, 2024, 2026])
def test_zero_expenses_preserve_the_default(year):
    default = simulation(year=year)
    zero = simulation(
        {"claimant": {"age": 30, "employment_income": 6_000, "employment_expenses": 0}},
        year=year,
    )
    for variable in [
        "uc_individual_earned_income_before_mif",
        "uc_earned_income",
        "universal_credit",
    ]:
        np.testing.assert_array_equal(
            default.calculate(variable, year), zero.calculate(variable, year)
        )


@pytest.mark.parametrize("expenses, expected", [(600, 5_400), (6_000, 0)])
def test_allowed_deduction_and_exact_earnings_limit(expenses, expected):
    # The supplied amount has already satisfied per-employment legal limits.
    sim = simulation(
        {
            "claimant": {
                "age": 30,
                "employment_income": 6_000,
                "employment_expenses": expenses,
            }
        }
    )
    np.testing.assert_allclose(
        sim.calculate("uc_individual_earned_income_before_mif", YEAR),
        [expected],
        atol=0.01,
    )
    np.testing.assert_allclose(
        sim.calculate("taxable_employment_income", YEAR), [expected], atol=0.01
    )


def test_each_claimants_deduction_is_used_once():
    sim = simulation(
        {
            "claimant": {
                "age": 40,
                "employment_income": 6_000,
                "employment_expenses": 600,
            },
            "partner": {
                "age": 38,
                "employment_income": 4_000,
                "employment_expenses": 400,
            },
        }
    )
    np.testing.assert_allclose(
        sim.calculate("uc_individual_earned_income_before_mif", YEAR),
        [5_400, 3_600],
        atol=0.01,
    )
    np.testing.assert_allclose(
        sim.calculate("uc_earned_income", YEAR), [9_000], atol=0.01
    )


def test_nonclaimants_expense_does_not_reduce_claimants_earnings():
    sim = simulation(
        {
            "parent": {"age": 40, "is_parent": True, "employment_income": 10_000},
            "child": {
                "age": 17,
                "current_education": "UPPER_SECONDARY",
                "employment_income": 3_000,
                "employment_expenses": 600,
            },
        }
    )
    np.testing.assert_array_equal(
        sim.calculate("is_uc_assessed_claimant", YEAR), [True, False]
    )
    np.testing.assert_allclose(
        sim.calculate("uc_individual_earned_income_before_mif", YEAR),
        [10_000, 2_400],
        atol=0.01,
    )
    np.testing.assert_allclose(
        sim.calculate("uc_earned_income", YEAR),
        10_000 - sim.calculate("uc_work_allowance", YEAR),
        atol=0.01,
    )


@pytest.mark.parametrize("trade, expected", [(2_000, 7_400), (-2_000, 5_400)])
def test_trade_earnings_keep_their_separate_nil_floor(trade, expected):
    sim = simulation(
        {
            "claimant": {
                "age": 30,
                "employment_income": 6_000,
                "employment_expenses": 600,
                "self_employment_income": trade,
                "uc_is_in_startup_period": True,
            }
        }
    )
    np.testing.assert_allclose(
        sim.calculate("uc_individual_earned_income_before_mif", YEAR),
        [expected],
        atol=0.01,
    )


def test_mif_still_compares_with_expense_net_actual_earnings():
    # Supplied MIF statuses/threshold are composition controls, not a
    # natural claim that every worker is subject to the floor.
    sim = simulation(
        {
            "claimant": {
                "age": 30,
                "employment_income": 6_000,
                "employment_expenses": 600,
                "uc_mif_applies": True,
                "uc_minimum_income_floor": 8_000,
            }
        }
    )
    np.testing.assert_allclose(
        sim.calculate("uc_individual_earned_income_before_mif", YEAR),
        [5_400],
        atol=0.01,
    )
    np.testing.assert_allclose(
        sim.calculate("uc_individual_earned_income", YEAR), [8_000], atol=0.01
    )


def test_annual_flow_is_allocated_to_month_without_changing_input():
    sim = simulation(
        {
            "claimant": {
                "age": 30,
                "employment_income": 6_000,
                "employment_expenses": 600,
            }
        }
    )
    np.testing.assert_allclose(
        sim.calculate("employment_expenses", "2024-04"), [50], atol=0.01
    )
    np.testing.assert_allclose(
        sim.calculate("uc_individual_earned_income_before_mif", "2024-04"),
        [450],
        atol=0.01,
    )


def test_direct_final_uc_input_remains_an_override():
    sim = simulation(
        {
            "claimant": {
                "age": 30,
                "employment_income": 6_000,
                "employment_expenses": 600,
            }
        },
        benunit={"universal_credit": 1_234},
    )
    np.testing.assert_allclose(
        sim.calculate("universal_credit", YEAR), [1_234], atol=0.01
    )


def test_multiunit_vector_keeps_expenses_with_their_owner():
    units = [
        situation(
            {
                "claimant": {
                    "age": 30,
                    "employment_income": 6_000,
                    "employment_expenses": expense,
                }
            }
        )
        for expense in [0, 600]
    ]
    merged = {entity: {} for entity in ["people", "benunits", "households"]}
    for index, unit in enumerate(units):
        for entity, rows in unit.items():
            for name, row in rows.items():
                row = dict(row)
                if "members" in row:
                    row["members"] = [f"{member}_{index}" for member in row["members"]]
                merged[entity][f"{name}_{index}"] = row
    sim = Simulation(situation=merged)
    np.testing.assert_allclose(
        sim.calculate("uc_individual_earned_income_before_mif", YEAR),
        [6_000, 5_400],
        atol=0.01,
    )


def test_statutory_pay_and_pension_components_are_retained():
    # The pension and statutory-pay inputs exercise existing composition,
    # with qualified expenses below the worker's employment earnings.
    sim = simulation(
        {
            "claimant": {
                "age": 30,
                "employment_income": 6_000,
                "employment_expenses": 600,
                "statutory_sick_pay": 1_000,
                "pension_contributions": 100,
            }
        }
    )
    np.testing.assert_allclose(
        sim.calculate("uc_individual_earned_income_before_mif", YEAR),
        [6_300],
        atol=0.01,
    )


def test_only_the_specific_expense_input_is_disregarded():
    # Supplied aggregate override: this checks consumer routing, not
    # statutory admissibility of a separate class of deduction.
    sim = simulation(
        {
            "claimant": {
                "age": 30,
                "employment_income": 6_000,
                "employment_expenses": 600,
                "employment_deductions": 2_500,
            }
        }
    )
    np.testing.assert_allclose(
        sim.calculate("taxable_employment_income", YEAR), [3_500], atol=0.01
    )
    np.testing.assert_allclose(
        sim.calculate("uc_individual_earned_income_before_mif", YEAR),
        [5_400],
        atol=0.01,
    )
