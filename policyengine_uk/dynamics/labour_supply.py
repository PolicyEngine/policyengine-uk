"""Labour supply dynamics module for PolicyEngine UK.

This module coordinates labour supply responses by combining progression (intensive margin)
and participation (extensive margin) models. It implements the methodology from the OBR's
labour supply elasticity framework to estimate how changes in tax and benefit policies
affect employment and working hours.

Reference: https://obr.uk/docs/dlm_uploads/NICS-Cut-Impact-on-Labour-Supply-Note.pdf
"""

import numpy as np
import pandas as pd
from policyengine_uk import Simulation
from microdf import MicroDataFrame
from pydantic import BaseModel
from typing import Optional

from .progression import (
    calculate_derivative_change,
    calculate_relative_income_change,
    calculate_labour_substitution_elasticities,
    calculate_labour_net_income_elasticities,
    calculate_employment_income_change,
)
from .participation import (
    apply_participation_responses,
)


def calculate_excluded_from_labour_supply_responses(
    sim: Simulation, count_adults: int = 1
):
    """Calculate which individuals are excluded from labour supply responses.

    Excludes self-employed, full-time students, aged 60+, and individuals
    outside the specified adult range.

    Args:
        sim: PolicyEngine simulation object
        count_adults: Number of adults to include in calculations

    Returns:
        Boolean array indicating which individuals are excluded
    """
    # Exclude self-employed, full-time students, aged 60+, and adult_index == (0, >= count_adults + 1)
    employment_status = sim.calculate("employment_status")
    self_employed = np.isin(
        employment_status, ["FT_SELF_EMPLOYED", "PT_SELF_EMPLOYED"]
    )
    student = employment_status == "STUDENT"
    age = sim.calculate("age")
    age_60_plus = age >= 60
    adult_index = sim.calculate("adult_index")
    excluded = (
        self_employed
        | student
        | age_60_plus
        | (adult_index == 0)
        | (adult_index >= count_adults + 1)
    )
    return excluded


class FTEImpacts(BaseModel):
    """Data model for FTE impacts of labour supply responses."""

    substitution_response_ftes: float
    """FTE impact from substitution effects."""
    income_response_ftes: float
    """FTE impact from income effects."""
    total_response_ftes: float
    """Total FTE impact from both substitution and income effects."""

    participation_response_employment: Optional[float] = None
    """FTE impact from participation responses, if available."""
    participation_response_ftes: Optional[float] = None
    """FTE impact from participation responses, if available."""

    ftes: Optional[float] = None
    """Total FTE impact across all responses."""


class LabourSupplyResponseData(BaseModel):
    progression: pd.DataFrame
    """DataFrame containing intensive margin (progression) responses."""
    participation: Optional[pd.DataFrame] = None
    """DataFrame containing extensive margin (participation) responses, if available."""

    # Specific outputs for comparison with OBR outputs
    fte_impacts: FTEImpacts
    """FTE impacts of labour supply responses, including both progression and participation."""

    model_config = {
        "arbitrary_types_allowed": True,
    }


def apply_labour_supply_responses(
    sim: Simulation,
    target_variable: str = "household_net_income",
    input_variable: str = "employment_income",
    year: int = 2025,
    count_adults: int = 1,
    delta: float = 1_000,
) -> pd.DataFrame:
    """Apply labour supply responses to simulation and return the response vector.

    This is the main function for applying dynamic labour supply responses to
    a PolicyEngine simulation. It coordinates both intensive margin (progression)
    and extensive margin (participation) responses to policy changes.

    Args:
        sim: PolicyEngine simulation object (should have baseline attribute)
        target_variable: Variable that drives labour supply decisions
        input_variable: Variable representing labour supply (typically employment_income)
        year: Year for calculation
        count_adults: Number of adults to calculate responses for
        delta: Size of change for marginal rate calculation (£)

    Returns:
        DataFrame with labour supply response information
    """
    follow_obr = sim.tax_benefit_system.parameters.gov.dynamic.obr_labour_supply_assumptions(
        year
    )
    if (not follow_obr) or (sim.baseline is None):
        return

    # Apply intensive margin responses (progression model)
    progression_responses = apply_progression_responses(
        sim=sim,
        target_variable=target_variable,
        input_variable=input_variable,
        year=year,
        count_adults=count_adults,
        delta=delta,
    )

    # Apply extensive margin responses (participation model)
    participation_responses = apply_participation_responses(sim=sim, year=year)

    # Add FTE impacts to the response data
    fte_impacts = FTEImpacts(
        substitution_response_ftes=progression_responses[
            "substitution_response_ftes"
        ].sum(),
        income_response_ftes=progression_responses[
            "income_response_ftes"
        ].sum(),
        total_response_ftes=progression_responses["total_response_ftes"].sum(),
        participation_response_employment=(
            participation_responses["participation_change"].sum()
            if participation_responses is not None
            else None
        ),
        participation_response_ftes=(
            participation_responses["participation_change_ftes"].sum()
            if participation_responses is not None
            else None
        ),
    )

    fte_impacts.ftes = fte_impacts.total_response_ftes + (
        fte_impacts.participation_response_ftes
        if fte_impacts.participation_response_ftes is not None
        else 0
    )

    # For now, return only progression responses since participation is placeholder
    # TODO: Combine progression and participation responses when participation model is implemented
    return LabourSupplyResponseData(
        progression=progression_responses,
        participation=participation_responses,
        fte_impacts=fte_impacts,
    )


def apply_progression_responses(
    sim: Simulation,
    target_variable: str = "household_net_income",
    input_variable: str = "employment_income",
    year: int = 2025,
    count_adults: int = 1,
    delta: float = 1_000,
) -> pd.DataFrame:
    """Apply progression (intensive margin) labour supply responses.

    This function handles the intensive margin of labour supply by calculating
    how individuals adjust their working hours in response to policy changes.

    Args:
        sim: PolicyEngine simulation object (should have baseline attribute)
        target_variable: Variable that drives labour supply decisions
        input_variable: Variable representing labour supply (typically employment_income)
        year: Year for calculation
        count_adults: Number of adults to calculate responses for
        delta: Size of change for marginal rate calculation (£)

    Returns:
        DataFrame with progression response information
    """
    # Calculate changes in marginal rates (drives substitution effects)
    derivative_changes = calculate_derivative_change(
        sim=sim,
        target_variable=target_variable,
        input_variable=input_variable,
        year=year,
        count_adults=count_adults,
        delta=delta,
    )

    derivative_changes = derivative_changes.rename(
        columns={col: f"deriv_{col}" for col in derivative_changes.columns}
    )

    # Add in actual implied wages
    gross_wage = sim.calculate("employment_income", year) / sim.calculate(
        "hours_worked", year
    )
    gross_wage = gross_wage.fillna(0).replace([np.inf, -np.inf], 0)
    derivative_changes["wage_gross"] = gross_wage
    derivative_changes["wage_baseline"] = (
        gross_wage * derivative_changes["deriv_baseline"]
    )
    derivative_changes["wage_scenario"] = (
        gross_wage * derivative_changes["deriv_scenario"]
    )
    derivative_changes["wage_rel_change"] = (
        derivative_changes["wage_scenario"]
        / derivative_changes["wage_baseline"]
        - 1
    ).replace([np.inf, -np.inf], 0)
    derivative_changes["wage_abs_change"] = (
        derivative_changes["wage_scenario"]
        - derivative_changes["wage_baseline"]
    )

    # Calculate changes in income levels (drives income effects)
    income_changes = calculate_relative_income_change(
        sim, target_variable, year
    )

    income_changes = income_changes.rename(
        columns={col: f"income_{col}" for col in income_changes.columns}
    )

    df = pd.concat([derivative_changes, income_changes], axis=1).fillna(0)

    # Get elasticity parameters by demographic group
    substitution_elasticities = calculate_labour_substitution_elasticities(sim)
    income_elasticities = calculate_labour_net_income_elasticities(sim)

    df["income_elasticity"] = income_elasticities
    df["substitution_elasticity"] = substitution_elasticities

    # Get baseline employment income levels
    employment_income = sim.calculate(input_variable, year)

    df["employment_income"] = employment_income
    df["hours_per_week"] = sim.calculate("hours_worked", year) / 52

    # Calculate total labour supply response
    response_df = calculate_employment_income_change(
        employment_income=employment_income,
        derivative_changes=derivative_changes,
        income_changes=income_changes,
        substitution_elasticities=substitution_elasticities,
        income_elasticities=income_elasticities,
    )

    df = pd.concat([df, response_df], axis=1)

    # Apply relative {substitution, income, total} changes to hours as well
    # Apply relative changes to hours using the same factor for all response types
    for response_type in [
        "substitution_response",
        "income_response",
        "total_response",
    ]:
        df[f"{response_type}_ftes"] = (
            df[response_type]
            / df["employment_income"]
            * df["hours_per_week"]
            / 37.5
        )

    excluded = calculate_excluded_from_labour_supply_responses(
        sim, count_adults=count_adults
    )

    for col in df.columns:
        df.loc[excluded, col] = 0

    df["excluded"] = excluded

    response = response_df["total_response"].values

    # Apply the labour supply response to the simulation
    sim.reset_calculations()
    sim.set_input(input_variable, year, employment_income + response)

    weight = sim.calculate("household_weight", year, map_to="person")

    result = MicroDataFrame(df, weights=weight)

    return result[~result.excluded].drop(columns=["excluded"])
