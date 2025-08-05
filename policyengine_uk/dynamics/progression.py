"""Labour supply progression (intensive margin) dynamics module.

This module handles the intensive margin of labour supply - how people adjust their
working hours in response to policy changes. It implements the elasticity-based
methodology from the OBR's labour supply framework.

Reference: https://obr.uk/docs/dlm_uploads/NICS-Cut-Impact-on-Labour-Supply-Note.pdf
"""

import numpy as np
import pandas as pd
from policyengine_uk import Simulation


def calculate_derivative(
    sim: Simulation,
    target_variable: str = "household_net_income",
    input_variable: str = "employment_income",
    year: int = 2025,
    count_adults: int = 2,
    delta: float = 1_000,
) -> np.ndarray:
    """Calculate the marginal rate of change of target variable with respect to input variable.

    This function computes numerical derivatives by applying small changes to the input
    variable and measuring the resulting change in the target variable. This is used
    to estimate marginal tax rates and benefit withdrawal rates.

    Args:
        sim: PolicyEngine simulation object
        target_variable: Variable to measure changes in (typically household_net_income)
        input_variable: Variable to change (typically employment_income)
        year: Year for calculation
        count_adults: Number of adults to apply changes to
        delta: Size of change to apply for derivative calculation (£)

    Returns:
        Array of marginal rates clipped between 0 and 1
    """
    # Get baseline values for input variable and identify adults
    input_variable_values = sim.calculate(input_variable, year)
    adult_index = sim.calculate("adult_index")
    entity_key = sim.tax_benefit_system.variables[input_variable].entity.key

    # Calculate baseline target values
    original_target_values = sim.calculate(
        target_variable, year, map_to=entity_key
    )
    new_target_values = original_target_values.copy()

    # Apply delta change to each adult sequentially to calculate marginal effects
    for i in range(count_adults):
        gets_pay_rise = adult_index == i + 1
        new_input_variable_values = input_variable_values.copy()
        new_input_variable_values[gets_pay_rise] += delta
        sim.reset_calculations()
        sim.set_input(input_variable, year, new_input_variable_values)
        new_target_values[gets_pay_rise] = sim.calculate(
            target_variable, year, map_to=entity_key
        )[gets_pay_rise]

    # Calculate marginal rate as change in target per unit change in input
    rel_marginal_wages = (new_target_values - original_target_values) / delta

    # Set non-adult observations to NaN
    rel_marginal_wages[
        ~pd.Series(adult_index).isin(range(1, count_adults + 1))
    ] = np.nan

    # Clip to ensure rates are between 0 and 1 (0% to 100% retention)
    return rel_marginal_wages.clip(0, 1)


def calculate_relative_income_change(
    sim: Simulation,
    target_variable: str = "household_net_income",
    year: int = 2025,
) -> pd.DataFrame:
    """Calculate relative change in income between baseline and scenario.

    This function compares the target variable values between the baseline
    simulation and the reform scenario to measure the income effect of the policy.

    Args:
        sim: PolicyEngine simulation object (should have baseline attribute)
        target_variable: Variable to measure changes in
        year: Year for calculation

    Returns:
        DataFrame with baseline, scenario, relative change, and absolute change columns
    """
    # Get income values from baseline and reform scenarios
    original_target_values = sim.baseline.calculate(
        target_variable, year, map_to="person"
    )
    reformed_target_values = sim.calculate(
        target_variable, year, map_to="person"
    )

    # Calculate relative change, handling division by zero
    rel_change = (
        reformed_target_values - original_target_values
    ) / original_target_values
    rel_change[original_target_values == 0] = np.nan

    # Clip extreme values and fill NaN with 0
    rel_changes = rel_change.clip(-1, 1).fillna(0)

    return pd.DataFrame(
        {
            "baseline": original_target_values,
            "scenario": reformed_target_values,
            "rel_change": rel_changes,
            "abs_change": reformed_target_values - original_target_values,
        }
    )


def calculate_derivative_change(
    sim: Simulation,
    target_variable: str = "household_net_income",
    input_variable: str = "employment_income",
    year: int = 2025,
    count_adults: int = 1,
    delta: float = 1_000,
) -> pd.DataFrame:
    """Calculate change in marginal rates between baseline and scenario.

    This function computes how marginal tax rates or benefit withdrawal rates
    change as a result of the policy reform, which drives substitution effects
    in labour supply responses.

    Args:
        sim: PolicyEngine simulation object (should have baseline attribute)
        target_variable: Variable to measure marginal rates for
        input_variable: Variable to change for derivative calculation
        year: Year for calculation
        count_adults: Number of adults to calculate derivatives for
        delta: Size of change for derivative calculation (£)

    Returns:
        DataFrame with baseline, scenario, relative change, and absolute change in derivatives
    """
    # Calculate marginal rates under baseline and reform scenarios
    original_deriv = calculate_derivative(
        sim=sim.baseline,
        target_variable=target_variable,
        input_variable=input_variable,
        year=year,
        count_adults=count_adults,
        delta=delta,
    )

    reformed_deriv = calculate_derivative(
        sim=sim,
        target_variable=target_variable,
        input_variable=input_variable,
        year=year,
        count_adults=count_adults,
        delta=delta,
    )

    # Calculate relative and absolute changes in marginal rates
    rel_change = reformed_deriv / original_deriv - 1
    abs_change = reformed_deriv - original_deriv

    # Clip extreme relative changes to avoid misleading results from small baseline derivatives
    rel_change = rel_change.clip(-1, 1)

    rel_change[rel_change == np.inf] = 0

    return pd.DataFrame(
        {
            "baseline": original_deriv,
            "scenario": reformed_deriv,
            "rel_change": rel_change,
            "abs_change": abs_change,
        }
    ).fillna(0)


def calculate_labour_substitution_elasticities(
    sim: Simulation,
) -> np.ndarray:
    """Calculate labour supply substitution elasticities by demographic group.

    Uses OBR elasticity estimates to assign substitution elasticities based on
    gender, marital status, and presence/age of children. These elasticities
    measure how labour supply responds to changes in marginal tax rates.

    Reference: https://obr.uk/docs/dlm_uploads/NICS-Cut-Impact-on-Labour-Supply-Note.pdf

    Args:
        sim: PolicyEngine simulation object

    Returns:
        Array of substitution elasticities for each person
    """
    # Get demographic characteristics for elasticity assignment
    gender = sim.calculate("gender")
    is_married = sim.calculate("is_married", map_to="person")
    has_children = sim.calculate("benunit_count_children", map_to="person") > 0
    youngest_child_age = sim.calculate("youngest_child_age", map_to="person")

    # Initialize elasticity array
    elasticities = np.zeros(gender.shape, dtype=float)

    # Married or cohabiting women - higher elasticities, especially with young children
    married_women = (gender == "FEMALE") & is_married
    elasticities[married_women & ~has_children] = 0.14  # No children

    # Elasticities vary significantly by youngest child's age
    elasticities[married_women & has_children & (youngest_child_age <= 2)] = (
        0.301  # 0-2 years
    )
    elasticities[
        married_women
        & has_children
        & (youngest_child_age >= 3)
        & (youngest_child_age <= 4)
    ] = 0.439  # 3-4 years (highest)
    elasticities[
        married_women
        & has_children
        & (youngest_child_age >= 5)
        & (youngest_child_age <= 10)
    ] = 0.173  # 5-10 years
    elasticities[married_women & has_children & (youngest_child_age >= 11)] = (
        0.160  # 11+ years
    )

    # Lone parents - lower elasticities than married women, reflecting different constraints
    lone_parents = (gender == "FEMALE") & ~is_married & has_children
    elasticities[lone_parents & (youngest_child_age <= 4)] = 0.094  # 0-4 years
    elasticities[
        lone_parents & (youngest_child_age >= 5) & (youngest_child_age <= 10)
    ] = 0.128  # 5-10 years
    elasticities[
        lone_parents & (youngest_child_age >= 11) & (youngest_child_age <= 18)
    ] = 0.136  # 11-18 years

    # Men (excluding lone fathers) - moderate, consistent elasticity
    elasticities[(gender == "MALE") & ~(~is_married & has_children)] = 0.15

    # Single women without children - same as men
    elasticities[(gender == "FEMALE") & ~is_married & ~has_children] = 0.15

    return elasticities


def calculate_labour_net_income_elasticities(
    sim: Simulation,
) -> np.ndarray:
    """Calculate labour supply income elasticities by demographic group.

    Uses OBR elasticity estimates to assign income elasticities based on
    gender, marital status, and presence/age of children. These elasticities
    measure how labour supply responds to changes in unearned income.

    Reference: https://obr.uk/docs/dlm_uploads/NICS-Cut-Impact-on-Labour-Supply-Note.pdf
    Table A2 - Income elasticities

    Args:
        sim: PolicyEngine simulation object

    Returns:
        Array of income elasticities for each person (typically negative)
    """
    # Get demographic characteristics for elasticity assignment
    gender = sim.calculate("gender")
    is_married = sim.calculate("is_married", map_to="person")
    has_children = sim.calculate("benunit_count_children", map_to="person") > 0
    youngest_child_age = sim.calculate("youngest_child_age", map_to="person")

    # Initialize elasticity array
    elasticities = np.zeros(gender.shape, dtype=float)

    # Married or cohabiting women - negative income elasticities (normal good)
    married_women = (gender == "FEMALE") & is_married
    elasticities[married_women & ~has_children] = (
        0.0  # No income effect without children
    )

    # Stronger negative income effects with younger children
    elasticities[married_women & has_children & (youngest_child_age <= 2)] = (
        -0.185
    )  # 0-2 years
    elasticities[
        married_women
        & has_children
        & (youngest_child_age >= 3)
        & (youngest_child_age <= 4)
    ] = -0.173  # 3-4 years
    elasticities[
        married_women
        & has_children
        & (youngest_child_age >= 5)
        & (youngest_child_age <= 10)
    ] = -0.102  # 5-10 years
    elasticities[married_women & has_children & (youngest_child_age >= 11)] = (
        -0.063
    )  # 11+ years

    # Lone parents - smaller negative income effects than married women
    lone_parents = (gender == "FEMALE") & ~is_married & has_children
    elasticities[lone_parents & (youngest_child_age <= 4)] = (
        -0.037
    )  # 0-4 years
    elasticities[
        lone_parents & (youngest_child_age >= 5) & (youngest_child_age <= 10)
    ] = -0.075  # 5-10 years
    elasticities[
        lone_parents & (youngest_child_age >= 11) & (youngest_child_age <= 18)
    ] = -0.054  # 11-18 years

    # Men (excluding lone fathers) - small negative income effect
    elasticities[(gender == "MALE") & ~(~is_married & has_children)] = -0.05

    # Single women without children - same as men
    elasticities[(gender == "FEMALE") & ~is_married & ~has_children] = -0.05

    return elasticities


def calculate_employment_income_change(
    employment_income: np.ndarray,
    derivative_changes: pd.DataFrame,
    income_changes: pd.DataFrame,
    substitution_elasticities: np.ndarray,
    income_elasticities: np.ndarray,
) -> np.ndarray:
    """Calculate total labour supply response combining substitution and income effects.

    This function implements the Slutsky equation decomposition of labour supply
    responses into substitution and income effects. The total response is the
    sum of these two components.

    Args:
        employment_income: Baseline employment income levels
        derivative_changes: Changes in marginal rates (substitution effect driver)
        income_changes: Changes in income levels (income effect driver)
        substitution_elasticities: Elasticities for substitution effects
        income_elasticities: Elasticities for income effects

    Returns:
        Array of employment income changes due to labour supply responses
    """
    # Calculate substitution effect: response to changes in marginal rates
    substitution_response = (
        employment_income
        * derivative_changes["wage_rel_change"]
        * substitution_elasticities
    )

    # Calculate income effect: response to changes in unearned income
    income_response = (
        employment_income
        * income_changes["income_rel_change"]
        * income_elasticities
    )

    # Total labour supply response is sum of substitution and income effects
    total_response = substitution_response + income_response

    # No response for people with zero employment income
    total_response[employment_income == 0] = 0

    df = pd.DataFrame(
        {
            "substitution_response": substitution_response,
            "income_response": income_response,
            "total_response": total_response,
        }
    )

    return df.fillna(0)
