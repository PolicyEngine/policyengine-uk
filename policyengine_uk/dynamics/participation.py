"""Labour supply participation (extensive margin) dynamics module.

This module handles the extensive margin of labour supply - how people decide
whether to work or not in response to policy changes. It implements the
methodology from the OBR's labour supply elasticity framework.

Reference: https://obr.uk/docs/dlm_uploads/NICS-Cut-Impact-on-Labour-Supply-Note.pdf
"""

import numpy as np
import pandas as pd
from policyengine_uk import Simulation
import warnings


def calculate_participation_elasticities(
    sim: Simulation,
    earnings_quintile: np.ndarray,
) -> np.ndarray:
    """Calculate labour force participation elasticities by demographic group.

    Uses OBR elasticity estimates (Table A1) to assign participation elasticities
    based on gender, marital status, presence/age of children, and earnings quintile.

    Args:
        sim: PolicyEngine simulation object
        earnings_quintile: Array indicating earnings quintile (1-5) for each person

    Returns:
        Array of participation elasticities for each person
    """
    # Get demographic characteristics
    gender = sim.calculate("gender")
    is_married = sim.calculate("is_married", map_to="person")
    has_children = sim.calculate("benunit_count_children", map_to="person") > 0
    youngest_child_age = sim.calculate("youngest_child_age", map_to="person")
    is_single = ~is_married

    # Get partner employment status for married individuals
    is_household_head = sim.calculate("is_household_head", map_to="person")
    benunit_count_adults = sim.calculate(
        "benunit_count_adults", map_to="person"
    )
    employment_income = sim.calculate("employment_income")
    benunit_id = sim.calculate("benunit_id", map_to="person")
    adult_index = sim.calculate("adult_index")

    # Create DataFrame for efficient partner employment calculation
    df = pd.DataFrame(
        {
            "benunit_id": benunit_id,
            "is_adult": adult_index > 0,
            "employed": employment_income > 0,
            "benunit_count_adults": benunit_count_adults,
        }
    )

    # Calculate total employed adults per benunit
    benunit_employed = (
        df[df["is_adult"]].groupby("benunit_id")["employed"].sum()
    )

    # Map back to individuals
    employed_adults_in_benunit = (
        df["benunit_id"].map(benunit_employed).fillna(0)
    )

    # Partner is employed if: 2-adult benunit and (both employed OR person not employed but other is)
    partner_employed = (benunit_count_adults == 2) & (
        (employed_adults_in_benunit == 2)
        | ((employed_adults_in_benunit == 1) & (employment_income == 0))
    )

    # Initialize elasticity array
    elasticities = np.zeros(gender.shape, dtype=float)

    # Define elasticity values by quintile (from Table A1)
    elasticity_matrices = {
        # Men (except lone fathers)
        "men": np.array([0.227, 0.182, 0.136, 0.091, 0.023]),
        # Single women without children
        "single_women_no_children": np.array(
            [0.216, 0.173, 0.130, 0.086, 0.022]
        ),
        # Women without children, non-working partner
        "women_no_children_nonworking_partner": np.array(
            [0.216, 0.173, 0.130, 0.086, 0.022]
        ),
        # Women without children, working partner
        "women_no_children_working_partner": np.array(
            [0.432, 0.345, 0.259, 0.173, 0.043]
        ),
        # Lone parents by youngest child age
        "lone_parent_0_2": np.array([1.195, 0.956, 0.717, 0.478, 0.120]),
        "lone_parent_3_5": np.array([1.554, 1.243, 0.932, 0.621, 0.155]),
        "lone_parent_6_10": np.array([1.195, 0.956, 0.717, 0.478, 0.120]),
        "lone_parent_11_plus": np.array([0.797, 0.637, 0.478, 0.319, 0.080]),
        # Women with non-working partner by youngest child age
        "women_nonworking_partner_0_2": np.array(
            [0.324, 0.259, 0.194, 0.129, 0.032]
        ),
        "women_nonworking_partner_3_5": np.array(
            [0.421, 0.336, 0.253, 0.168, 0.042]
        ),
        "women_nonworking_partner_6_10": np.array(
            [0.324, 0.259, 0.194, 0.130, 0.033]
        ),
        "women_nonworking_partner_11_plus": np.array(
            [0.216, 0.173, 0.130, 0.086, 0.021]
        ),
        # Women with working partner by youngest child age
        "women_working_partner_0_2": np.array(
            [0.755, 0.604, 0.453, 0.302, 0.076]
        ),
        "women_working_partner_3_5": np.array(
            [0.982, 0.786, 0.589, 0.393, 0.098]
        ),
        "women_working_partner_6_10": np.array(
            [0.755, 0.604, 0.453, 0.302, 0.076]
        ),
        "women_working_partner_11_plus": np.array(
            [0.504, 0.403, 0.302, 0.201, 0.051]
        ),
    }

    # Vectorized assignment function
    def assign_elasticities(mask, elasticity_key):
        if mask.any():
            # Ensure quintiles are in valid range
            valid_quintiles = np.clip(
                earnings_quintile[mask] - 1, 0, 4
            ).astype(int)
            elasticities[mask] = elasticity_matrices[elasticity_key][
                valid_quintiles
            ]

    # Men (except lone fathers)
    men_not_lone_parent = (gender == "MALE") & ~(is_single & has_children)
    assign_elasticities(men_not_lone_parent, "men")

    # Single women without children
    single_women_no_children = (gender == "FEMALE") & is_single & ~has_children
    assign_elasticities(single_women_no_children, "single_women_no_children")

    # Women without children by partner employment status
    women_no_children = (gender == "FEMALE") & ~has_children & is_married
    assign_elasticities(
        women_no_children & ~partner_employed,
        "women_no_children_nonworking_partner",
    )
    assign_elasticities(
        women_no_children & partner_employed,
        "women_no_children_working_partner",
    )

    # Lone parents by youngest child age
    lone_parents = (gender == "FEMALE") & is_single & has_children
    assign_elasticities(
        lone_parents & (youngest_child_age <= 2), "lone_parent_0_2"
    )
    assign_elasticities(
        lone_parents & (youngest_child_age >= 3) & (youngest_child_age <= 5),
        "lone_parent_3_5",
    )
    assign_elasticities(
        lone_parents & (youngest_child_age >= 6) & (youngest_child_age <= 10),
        "lone_parent_6_10",
    )
    assign_elasticities(
        lone_parents & (youngest_child_age >= 11), "lone_parent_11_plus"
    )

    # Women with children by partner employment status and youngest child age
    women_with_children = (gender == "FEMALE") & has_children & is_married

    # Non-working partner
    women_nonworking_partner = women_with_children & ~partner_employed
    assign_elasticities(
        women_nonworking_partner & (youngest_child_age <= 2),
        "women_nonworking_partner_0_2",
    )
    assign_elasticities(
        women_nonworking_partner
        & (youngest_child_age >= 3)
        & (youngest_child_age <= 5),
        "women_nonworking_partner_3_5",
    )
    assign_elasticities(
        women_nonworking_partner
        & (youngest_child_age >= 6)
        & (youngest_child_age <= 10),
        "women_nonworking_partner_6_10",
    )
    assign_elasticities(
        women_nonworking_partner & (youngest_child_age >= 11),
        "women_nonworking_partner_11_plus",
    )

    # Working partner
    women_working_partner = women_with_children & partner_employed
    assign_elasticities(
        women_working_partner & (youngest_child_age <= 2),
        "women_working_partner_0_2",
    )
    assign_elasticities(
        women_working_partner
        & (youngest_child_age >= 3)
        & (youngest_child_age <= 5),
        "women_working_partner_3_5",
    )
    assign_elasticities(
        women_working_partner
        & (youngest_child_age >= 6)
        & (youngest_child_age <= 10),
        "women_working_partner_6_10",
    )
    assign_elasticities(
        women_working_partner & (youngest_child_age >= 11),
        "women_working_partner_11_plus",
    )

    return elasticities


def calculate_gain_to_work(
    sim: Simulation,
    year: int = 2025,
    hours_for_new_entrants: float = 18.8,
    count_adults: int = 1,
) -> pd.DataFrame:
    """Calculate gain-to-work metric for each individual.

    The gain-to-work is the difference between income when working vs not working.
    Uses adult_index to handle multi-adult benefit units correctly.

    Args:
        sim: PolicyEngine simulation object
        year: Year for calculation
        hours_for_new_entrants: Weekly hours for new labour market entrants
        count_adults: Number of adults to calculate responses for

    Returns:
        DataFrame with in-work income, out-of-work income, and gain-to-work
    """
    # Get current employment status and income
    employment_income = sim.calculate("employment_income", year)
    hours_worked = sim.calculate("hours_worked", year)
    household_net_income = sim.calculate(
        "household_net_income", year, map_to="person"
    )
    adult_index = sim.calculate("adult_index")

    # Initialize arrays
    out_of_work_income = household_net_income.copy()
    in_work_income = household_net_income.copy()

    # Calculate out-of-work income for each adult group
    original_employment = employment_income.copy()

    for i in range(1, count_adults + 1):
        is_adult_i = adult_index == i

        if is_adult_i.any():
            # Set employment income to 0 for this adult group
            temp_employment = employment_income.copy()
            temp_employment[is_adult_i] = 0

            sim.reset_calculations()
            sim.set_input("employment_income", year, temp_employment)

            # Get household income when these adults don't work
            out_of_work_income[is_adult_i] = sim.calculate(
                "household_net_income", year, map_to="person"
            )[is_adult_i]

    # Reset to original
    sim.reset_calculations()
    sim.set_input("employment_income", year, original_employment)

    # Calculate average hourly wage by demographic group for imputation
    working = employment_income > 0
    positive_hours = hours_worked > 0
    hourly_wage = np.zeros_like(employment_income, dtype=float)

    # Calculate actual hourly wages where available
    valid_wage_mask = working & positive_hours
    hourly_wage[valid_wage_mask] = (
        employment_income[valid_wage_mask] / hours_worked[valid_wage_mask]
    )

    # Get demographic characteristics
    gender = sim.calculate("gender")
    age = sim.calculate("age")

    # Create age groups
    age_groups = [
        (age >= 18) & (age < 25),
        (age >= 25) & (age < 35),
        (age >= 35) & (age < 45),
        (age >= 45) & (age < 55),
        (age >= 55) & (age < 65),
    ]

    # Impute wages by gender and age group
    for g_mask, g_name in [
        (gender == "MALE", "MALE"),
        (gender == "FEMALE", "FEMALE"),
    ]:
        for age_mask in age_groups:
            # Workers in this demographic
            demo_workers = g_mask & age_mask & valid_wage_mask

            if demo_workers.any():
                avg_wage = hourly_wage[demo_workers].mean()
                # Non-workers in this demographic
                demo_non_workers = g_mask & age_mask & ~working
                hourly_wage[demo_non_workers] = avg_wage

    # For any remaining without wages, use overall average
    if valid_wage_mask.any():
        overall_avg_wage = hourly_wage[valid_wage_mask].mean()
        hourly_wage[(hourly_wage == 0) & ~working] = overall_avg_wage

    # Calculate in-work income for non-workers
    not_working = employment_income == 0

    for i in range(1, count_adults + 1):
        is_adult_i = adult_index == i
        is_not_working = is_adult_i & not_working

        if is_not_working.any():
            # Estimate annual employment income
            temp_employment = employment_income.copy()
            temp_employment[is_not_working] = (
                hourly_wage[is_not_working] * hours_for_new_entrants * 52
            )

            sim.reset_calculations()
            sim.set_input("employment_income", year, temp_employment)

            # Get household income when these adults work
            in_work_income[is_not_working] = sim.calculate(
                "household_net_income", year, map_to="person"
            )[is_not_working]

    # Reset to original
    sim.reset_calculations()
    sim.set_input("employment_income", year, original_employment)

    # Calculate gain to work
    gain_to_work = in_work_income - out_of_work_income

    return pd.DataFrame(
        {
            "in_work_income": in_work_income,
            "out_of_work_income": out_of_work_income,
            "gain_to_work": gain_to_work,
            "potential_hourly_wage": hourly_wage,
        }
    )


def calculate_earnings_quintile(
    sim: Simulation,
    year: int = 2025,
    hours_for_new_entrants: float = 18.8,
) -> np.ndarray:
    """Calculate earnings quintile for each person based on potential earnings.

    For workers, uses actual earnings. For non-workers, uses imputed potential earnings.

    Args:
        sim: PolicyEngine simulation object
        year: Year for calculation
        hours_for_new_entrants: Weekly hours assumed for new entrants

    Returns:
        Array of quintiles (1-5) for each person
    """
    employment_income = sim.calculate("employment_income", year)

    # Get potential hourly wages from gain_to_work calculation
    gtw_df = calculate_gain_to_work(sim, year, hours_for_new_entrants)
    potential_hourly_wage = gtw_df["potential_hourly_wage"].values

    # Calculate annual earnings: actual for workers, potential for non-workers
    working = employment_income > 0
    annual_earnings = employment_income.copy()
    annual_earnings[~working] = (
        potential_hourly_wage[~working] * hours_for_new_entrants * 52
    )

    # Calculate quintiles
    # Use pandas qcut for equal-sized bins
    quintiles = pd.qcut(
        annual_earnings, q=5, labels=[1, 2, 3, 4, 5], duplicates="drop"
    )

    return quintiles.astype(int).values


def apply_participation_responses(
    sim: Simulation,
    year: int = 2025,
    hours_for_new_entrants: float = 18.8,
    count_adults: int = 1,
) -> pd.DataFrame:
    """Apply participation responses to simulation.

    Calculates aggregate labour force entry by demographic group and randomly
    selects individuals from the out-of-work population to enter employment.

    Args:
        sim: PolicyEngine simulation object (must have baseline)
        year: Year for calculation
        hours_for_new_entrants: Weekly hours for new labour market entrants
        count_adults: Number of adults to calculate responses for

    Returns:
        DataFrame with participation response information
    """
    if sim.baseline is None:
        return pd.DataFrame()

    # Calculate excluded individuals
    from .labour_supply import calculate_excluded_from_labour_supply_responses

    excluded = calculate_excluded_from_labour_supply_responses(
        sim, count_adults
    )

    # Get employment status
    employment_income = sim.calculate("employment_income", year)
    adult_index = sim.calculate("adult_index")
    eligible = ~excluded & (adult_index > 0) & (adult_index <= count_adults)
    not_working = (employment_income == 0) & eligible

    # Calculate gain-to-work for baseline and reform
    baseline_gtw = calculate_gain_to_work(
        sim.baseline, year, hours_for_new_entrants, count_adults
    )
    reform_gtw = calculate_gain_to_work(
        sim, year, hours_for_new_entrants, count_adults
    )

    # Calculate percentage change in gain-to-work
    gtw_baseline = baseline_gtw["gain_to_work"].values
    gtw_reform = reform_gtw["gain_to_work"].values

    # Avoid division by zero
    gtw_pct_change = np.zeros_like(gtw_baseline)
    positive_baseline = gtw_baseline > 0
    gtw_pct_change[positive_baseline] = (
        gtw_reform[positive_baseline] - gtw_baseline[positive_baseline]
    ) / gtw_baseline[positive_baseline]

    # Get elasticities
    earnings_quintile = calculate_earnings_quintile(
        sim, year, hours_for_new_entrants
    )
    elasticities_wrt_income = calculate_participation_elasticities(
        sim, earnings_quintile
    )

    # Transform elasticities from w.r.t. in-work income to w.r.t. gain-to-work
    # Following OBR Appendix E methodology: multiply by (1 - replacement_rate)
    in_work_income = baseline_gtw["in_work_income"].values
    out_of_work_income = baseline_gtw["out_of_work_income"].values

    # Calculate replacement rates (out-of-work income / in-work income)
    replacement_rate = np.zeros_like(in_work_income)
    positive_in_work = in_work_income > 0
    replacement_rate[positive_in_work] = (
        out_of_work_income[positive_in_work] / in_work_income[positive_in_work]
    )
    replacement_rate = np.clip(
        replacement_rate, 0, 1
    )  # Ensure between 0 and 1

    # Transform elasticities
    elasticities = elasticities_wrt_income * (1 - replacement_rate)

    # Calculate participation probability change for each person
    # From OBR methodology: percentage change in participation = elasticity * percentage change in GTW
    participation_change = elasticities * gtw_pct_change

    # Apply only to those not working
    participation_change[~not_working] = 0

    # Create results DataFrame
    results = pd.DataFrame(
        {
            "not_working_baseline": not_working,
            "participation_elasticity": elasticities,
            "gtw_baseline": gtw_baseline,
            "gtw_reform": gtw_reform,
            "gtw_pct_change": gtw_pct_change,
            "participation_change": participation_change,
            "excluded": excluded,
        }
    )

    weights = sim.calculate("household_weight", year, map_to="person")

    # Weight and filter
    from microdf import MicroDataFrame

    weighted_results = MicroDataFrame(results, weights=weights)

    return weighted_results[~weighted_results.excluded].drop(
        columns=["excluded"]
    )
