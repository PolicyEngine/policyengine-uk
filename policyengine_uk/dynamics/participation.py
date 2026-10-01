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

from policyengine_uk.model_api import WEEKS_IN_YEAR

# Weekly hours treated as full time when putting non-workers on a comparable
# footing with observed earnings for quintile placement.
FULL_TIME_WEEKLY_HOURS = 37.5


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
    benunit_count_adults = sim.calculate("benunit_count_adults", map_to="person")
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
    benunit_employed = df[df["is_adult"]].groupby("benunit_id")["employed"].sum()

    # Map back to individuals
    employed_adults_in_benunit = df["benunit_id"].map(benunit_employed).fillna(0)

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
        "single_women_no_children": np.array([0.216, 0.173, 0.130, 0.086, 0.022]),
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
        "women_nonworking_partner_0_2": np.array([0.324, 0.259, 0.194, 0.129, 0.032]),
        "women_nonworking_partner_3_5": np.array([0.421, 0.336, 0.253, 0.168, 0.042]),
        "women_nonworking_partner_6_10": np.array([0.324, 0.259, 0.194, 0.130, 0.033]),
        "women_nonworking_partner_11_plus": np.array(
            [0.216, 0.173, 0.130, 0.086, 0.021]
        ),
        # Women with working partner by youngest child age
        "women_working_partner_0_2": np.array([0.755, 0.604, 0.453, 0.302, 0.076]),
        "women_working_partner_3_5": np.array([0.982, 0.786, 0.589, 0.393, 0.098]),
        "women_working_partner_6_10": np.array([0.755, 0.604, 0.453, 0.302, 0.076]),
        "women_working_partner_11_plus": np.array([0.504, 0.403, 0.302, 0.201, 0.051]),
    }

    # Vectorized assignment function
    def assign_elasticities(mask, elasticity_key):
        if mask.any():
            # Ensure quintiles are in valid range
            valid_quintiles = np.clip(earnings_quintile[mask] - 1, 0, 4).astype(int)
            elasticities[mask] = elasticity_matrices[elasticity_key][valid_quintiles]

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
    assign_elasticities(lone_parents & (youngest_child_age <= 2), "lone_parent_0_2")
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
        women_working_partner & (youngest_child_age >= 3) & (youngest_child_age <= 5),
        "women_working_partner_3_5",
    )
    assign_elasticities(
        women_working_partner & (youngest_child_age >= 6) & (youngest_child_age <= 10),
        "women_working_partner_6_10",
    )
    assign_elasticities(
        women_working_partner & (youngest_child_age >= 11),
        "women_working_partner_11_plus",
    )

    return elasticities


def hourly_wage(sim: Simulation, year: int = 2025):
    """Hourly wage implied by annual earnings and annual hours.

    ``hours_worked`` is an annual quantity — its label is "Annual hours worked",
    it has a YEAR definition period, and ``weekly_hours`` derives from it as
    ``hours_worked / WEEKS_IN_YEAR``. Dividing earnings by it therefore already
    gives an hourly rate; multiplying the denominator by 52 first would divide
    by a year a second time and understate the wage roughly a hundredfold.

    Args:
        sim: PolicyEngine simulation object
        year: Year for calculation

    Returns:
        (employment income, hourly wage, mask of people with earnings and hours)
    """
    employment_income = sim.calculate("employment_income", year)
    hours_worked = sim.calculate("hours_worked", year)
    working_mask = (employment_income > 0) & (hours_worked > 0)
    hourly_wages = np.where(
        working_mask,
        employment_income / np.where(working_mask, hours_worked, 1),
        0,
    )
    return employment_income, hourly_wages, working_mask


def impute_wages_for_nonworkers(
    sim: Simulation,
    year: int = 2025,
    hours_for_new_entrants: float = 18.8,
) -> np.ndarray:
    """Impute annual earnings for non-workers entering employment.

    Assumes a non-worker would work ``hours_for_new_entrants`` hours a week at
    the median hourly wage of workers of the same sex and age band.

    Donors are grouped by sex and age band rather than by elasticity group.
    The elasticity group is keyed off :func:`calculate_earnings_quintile`, and
    quintiles of *potential* earnings cannot be computed until non-workers have
    an imputed wage — so grouping donors that way is circular. In practice it
    left the lowest quintiles with no employed donors at all and their
    non-workers with an imputed wage of zero, and a zero imputed wage silently
    bars someone from entering employment in
    :func:`apply_participation_responses`, whatever the reform.

    The median is used rather than the mean because a small share of workers
    have implausibly low implied hourly wages.

    Args:
        sim: PolicyEngine simulation object
        year: Year for calculation
        hours_for_new_entrants: Weekly hours assumed for new entrants

    Returns:
        Array of imputed annual employment income for non-workers
    """
    employment_income, hourly_wages, working_mask = hourly_wage(sim, year)
    age = np.asarray(sim.calculate("age", year), dtype=float)
    gender = np.asarray(sim.calculate("gender", year))
    weights = np.asarray(
        sim.calculate("household_weight", year, map_to="person"), dtype=float
    )

    age_band = np.clip(age // 10 * 10, 10, 60)
    overall_median = weighted_median(hourly_wages[working_mask], weights[working_mask])

    imputed_wages = np.zeros_like(employment_income, dtype=float)
    nonworker_mask = ~working_mask
    for sex in np.unique(gender):
        for band in np.unique(age_band):
            group = (gender == sex) & (age_band == band)
            donors = group & working_mask
            median_wage = weighted_median(hourly_wages[donors], weights[donors])
            if median_wage <= 0:
                # No donors, or donors carrying no weight. Either way the
                # group median is unusable and the overall one stands in; a
                # zero here would silently bar entry into employment.
                median_wage = overall_median
            imputed_wages[group & nonworker_mask] = median_wage

    return imputed_wages * hours_for_new_entrants * WEEKS_IN_YEAR


def weighted_median(values: np.ndarray, weights: np.ndarray) -> float:
    """Weighted median of ``values``.

    Falls back to the unweighted median where the group carries no weight, so
    that a zero-weight donor group still yields a wage. Returning zero there
    would silently bar the people it is imputed for from entering employment,
    since :func:`apply_participation_responses` gates entry on a positive
    imputed wage. Only a genuinely empty group returns zero.
    """
    values = np.asarray(values, dtype=float)
    weights = np.asarray(weights, dtype=float)
    if values.shape != weights.shape:
        raise ValueError(
            f"weighted_median got {values.shape} values and {weights.shape} weights"
        )
    # np.argsort sorts NaN last, so a single NaN would otherwise be returned as
    # the group maximum rather than flagged. Drop non-finite pairs instead.
    usable = np.isfinite(values) & np.isfinite(weights)
    values, weights = values[usable], weights[usable]
    if not len(values):
        return 0.0
    order = np.argsort(values)
    cumulative = np.cumsum(weights[order])
    if cumulative[-1] <= 0:
        return float(np.median(values))
    return float(values[order][np.searchsorted(cumulative, cumulative[-1] / 2)])


def calculate_gain_to_work(
    sim: Simulation,
    year: int = 2025,
    hours_for_new_entrants: float = 18.8,
    count_adults: int = 1,
    impute_nonworker_wages: bool = True,
) -> pd.DataFrame:
    """Calculate gain-to-work metric for each individual.

    The gain-to-work is the difference between income when working vs not working.
    Uses adult_index to handle multi-adult benefit units correctly.
    Optionally imputes wages for non-workers.

    Args:
        sim: PolicyEngine simulation object
        year: Year for calculation
        hours_for_new_entrants: Weekly hours for new labour market entrants
        count_adults: Number of adults to calculate responses for
        impute_nonworker_wages: Whether to impute wages for non-workers

    Returns:
        DataFrame with in-work income, out-of-work income, and gain-to-work
    """
    # Get current employment status and income
    employment_income = sim.calculate("employment_income", year)
    hours_worked = sim.calculate("hours_worked", year)
    household_net_income = sim.calculate("household_net_income", year, map_to="person")
    adult_index = sim.calculate("adult_index")

    # Impute wages for non-workers if requested
    if impute_nonworker_wages:
        imputed_wages = impute_wages_for_nonworkers(sim, year, hours_for_new_entrants)
        # For non-workers, use imputed wages; for workers, use actual income
        working_mask = employment_income > 0
        employment_income_with_imputation = np.where(
            working_mask, employment_income, imputed_wages
        )
    else:
        employment_income_with_imputation = employment_income

    # Initialize arrays
    out_of_work_income = household_net_income.copy()
    in_work_income = household_net_income.copy()

    # Calculate both in-work and out-of-work income for each adult group
    original_employment = employment_income.copy()

    for i in range(1, count_adults + 1):
        is_adult_i = adult_index == i

        if is_adult_i.any():
            # Calculate out-of-work income (set employment to 0)
            temp_employment_out = employment_income.copy()
            temp_employment_out[is_adult_i] = 0

            sim.reset_calculations()
            sim.set_input("employment_income", year, temp_employment_out)
            out_of_work_income[is_adult_i] = sim.calculate(
                "household_net_income", year, map_to="person"
            )[is_adult_i]

            # Calculate in-work income (use imputed wages if applicable).
            # employment_income is stored as float32; imputed wages are float64,
            # and assigning them raises under pandas 3 rather than down-casting.
            # set_input down-casts on storage anyway, so float32 is already the
            # model's precision and casting here just moves the truncation
            # earlier (max relative error about 5e-08).
            temp_employment_in = employment_income.copy()
            temp_employment_in[is_adult_i] = employment_income_with_imputation[
                is_adult_i
            ].astype(temp_employment_in.dtype)

            sim.reset_calculations()
            sim.set_input("employment_income", year, temp_employment_in)
            in_work_income[is_adult_i] = sim.calculate(
                "household_net_income", year, map_to="person"
            )[is_adult_i]

    # Reset to original state
    sim.reset_calculations()
    sim.set_input("employment_income", year, original_employment)

    # Calculate gain to work
    gain_to_work = in_work_income - out_of_work_income

    return pd.DataFrame(
        {
            "in_work_income": in_work_income,
            "out_of_work_income": out_of_work_income,
            "gain_to_work": gain_to_work,
        }
    )


def weighted_quantiles(
    values: np.ndarray, weights: np.ndarray, quantiles: list[float]
) -> np.ndarray:
    """Weighted quantiles of ``values``, for use as distribution thresholds."""
    if not len(values):
        return np.zeros(len(quantiles))
    # Aggregate weight by *distinct* value before building the CDF. Sorting
    # rows and taking each row's own weight midpoint splits a tied value into
    # as many positions as it has rows, and `np.argsort` orders those rows by
    # input position — so two equal-earning workers carrying unequal weights
    # produced different thresholds depending only on which came first in the
    # file, and could land either side of a boundary. One value must have one
    # position on the distribution however many rows carry it.
    sorted_values, inverse = np.unique(values, return_inverse=True)
    sorted_weights = np.bincount(inverse, weights=weights, minlength=len(sorted_values))
    cumulative = np.cumsum(sorted_weights)
    total = cumulative[-1]
    if not np.isfinite(total) or total <= 0:
        # No usable weights. Returning zeros would put every positive value in
        # the top quintile — the lowest-elasticity end of the OBR table — so
        # fall back to unweighted quantiles of the values themselves.
        return np.quantile(values, quantiles)
    # Midpoint of each value's total weight, so a heavy point mass does not
    # pull a threshold to one of its edges.
    position = (cumulative - sorted_weights / 2) / total
    return np.interp(quantiles, position, sorted_values)


def calculate_earnings_quintile(
    sim: Simulation,
    year: int = 2025,
    hours_for_new_entrants: float = 18.8,
    random_seed: int = 42,
) -> np.ndarray:
    """Calculate earnings quintile for each adult based on potential earnings.

    Thresholds are the weighted quintile boundaries of the **observed earnings
    distribution of working adults**. Everyone is then placed against those
    thresholds: workers on their actual earnings, non-workers on the potential
    earnings imputed by :func:`impute_wages_for_nonworkers`.

    Two properties matter for the OBR Table A1 elasticities this feeds.

    * **The distribution is of adult earnings.** Ranking every person in the
      dataset put roughly a quarter of each lower quintile into children, and
      left the bottom two quintiles entirely without earners — so the
      elasticity table was indexed by a distribution that contained no wages
      at its lower end.
    * **Placement is by value against a fixed threshold, not by rank within a
      pooled ranking.** Every non-worker in a donor group shares one imputed
      wage, so potential earnings carry large point masses. Ranking a pooled
      distribution splits such a mass across a quintile boundary, and which
      member of the mass falls on which side then depends on the order of rows
      in the dataset — making elasticities and stochastic responses vary with
      serialisation. Thresholds avoid this: a tied mass lands wholly in the
      quintile its value belongs to.

    Because non-workers are placed rather than ranked, quintiles are not equal
    shares of the adult population. That is intended — they are quintiles of
    the earnings distribution, which is what Table A1 is indexed on.

    Args:
        sim: PolicyEngine simulation object
        year: Year for calculation
        hours_for_new_entrants: Weekly hours assumed for new entrants
        random_seed: Unused. Placement is deterministic; retained so existing
            callers do not break.

    Returns:
        Array of quintiles (1-5) for each person. Non-adults are assigned 1;
        they are excluded from labour supply responses elsewhere.
    """
    employment_income = np.asarray(
        sim.calculate("employment_income", year), dtype=float
    )
    adult_index = np.asarray(sim.calculate("adult_index", year), dtype=float)
    weights = np.asarray(
        sim.calculate("household_weight", year, map_to="person"), dtype=float
    )
    # Imputed earnings are for an entrant working `hours_for_new_entrants` a
    # week, but the thresholds come from observed earnings at whatever hours
    # workers actually do — mostly full time. Placing a part-time figure against
    # a mostly-full-time distribution is not a like-for-like comparison, and it
    # pushes every non-worker down by roughly the hours ratio: at 18.8 hours the
    # imputed values span a single threshold interval. Scaling to full-time
    # equivalent for placement — the entrant's actual earnings stay at the
    # assumed hours — moves them off that single interval.
    #
    # It does not spread them across the table. Because every non-worker
    # inherits one of about a dozen sex-and-age-band medians, the placement is
    # still coarse: on enhanced_frs_2024_25 they occupy quintiles 2 to 4 only, with
    # no entrant placed at either end, so the Table A1 gradient is only
    # partially exercised for exactly the
    # population whose entry this module models. Fixing that needs a finer
    # imputation, not a different placement rule.
    #
    # This scaling is an assumption, not something the sources state. The OBR
    # note assumes entrants work 18.8 hours a week and labels Table A1 by
    # position in the earnings distribution, without saying which basis places
    # a non-worker on it; Adam and Phillips (2013) do not allocate elasticities
    # to non-workers at all. The choice is material and runs one way: placing
    # entrants at their unscaled 18.8-hour income moves them down the table to
    # quintile 1, roughly *doubling* the elasticity each demographic row draws
    # and so the modelled entry response. Callers wanting that bound can pass
    # `hours_for_new_entrants=FULL_TIME_WEEKLY_HOURS` to disable the scaling.
    # Neither end is validated against an observed entry rate — see #1836.
    imputed = impute_wages_for_nonworkers(sim, year, hours_for_new_entrants)
    full_time_equivalent = imputed * (FULL_TIME_WEEKLY_HOURS / hours_for_new_entrants)
    potential = np.where(employment_income > 0, employment_income, full_time_equivalent)

    adults = adult_index > 0
    workers = adults & (employment_income > 0)
    thresholds = weighted_quantiles(
        employment_income[workers], weights[workers], [0.2, 0.4, 0.6, 0.8]
    )

    quintile = np.ones(len(potential), dtype=int)
    if len(np.unique(thresholds)) == 1:
        # No dispersion to place anyone against — a population with no workers
        # leaves every threshold at zero, and `searchsorted(side="right")` would
        # then put every adult in the top quintile, the end of the OBR table
        # with the *smallest* elasticities. That is the opposite of what a
        # population of non-workers implies. With no earnings distribution to
        # read, spread adults evenly rather than assert one.
        index = np.flatnonzero(adults)
        if len(index):
            adult_potential = potential[index]
            adult_weights = weights[index]
            total = adult_weights.sum()
            if total > 0:
                # Place each *distinct* potential-earnings value at the midpoint
                # of its own block of weight, not each row at the midpoint of
                # its own weight. Spreading row by row would sort ties in input
                # order, so two identical records would land in different
                # quintiles purely because of serialisation — the invariant this
                # function documents. Blocking on the value makes placement a
                # function of the data alone.
                values, inverse = np.unique(adult_potential, return_inverse=True)
                block = np.bincount(inverse, weights=adult_weights)
                below = np.concatenate([[0.0], np.cumsum(block)[:-1]])
                position = (below + block / 2) / total
                quintile[index] = np.clip((position[inverse] * 5).astype(int) + 1, 1, 5)
            else:
                quintile[index] = 3
        return quintile

    quintile[adults] = np.searchsorted(thresholds, potential[adults], side="right") + 1
    return np.clip(quintile, 1, 5)


def apply_participation_responses(
    sim: Simulation,
    year: int = 2025,
    hours_for_new_entrants: float = 18.8,
    count_adults: int = 2,
    random_seed: int = 42,
) -> pd.DataFrame:
    """Apply participation responses to simulation at microdata level.

    Stochastically applies participation responses to individual workers and
    non-workers based on their calculated participation elasticities.

    Args:
        sim: PolicyEngine simulation object (must have baseline)
        year: Year for calculation
        hours_for_new_entrants: Weekly hours for new labour market entrants
        count_adults: Number of adults to calculate responses for
        random_seed: Seed for random number generation

    Returns:
        DataFrame with participation response information and updated employment
    """
    if sim.baseline is None:
        return pd.DataFrame()

    # Set random seed for reproducibility
    np.random.seed(random_seed)

    # Calculate excluded individuals
    from .labour_supply import calculate_excluded_from_labour_supply_responses

    excluded = calculate_excluded_from_labour_supply_responses(sim, count_adults)

    # Get employment status
    employment_income = sim.calculate("employment_income", year)
    adult_index = sim.calculate("adult_index")
    eligible = ~excluded & (adult_index > 0) & (adult_index <= count_adults)
    currently_working = (employment_income > 0) & eligible
    currently_not_working = (employment_income == 0) & eligible

    # Calculate gain-to-work for baseline and reform (with wage imputation)
    baseline_gtw = calculate_gain_to_work(
        sim.baseline,
        year,
        hours_for_new_entrants,
        count_adults,
        impute_nonworker_wages=True,
    )
    reform_gtw = calculate_gain_to_work(
        sim,
        year,
        hours_for_new_entrants,
        count_adults,
        impute_nonworker_wages=True,
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
        sim, year, hours_for_new_entrants, random_seed
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
    replacement_rate = np.clip(replacement_rate, 0, 1)  # Ensure between 0 and 1

    # Transform elasticities
    elasticities = elasticities_wrt_income * (1 - replacement_rate)

    # Calculate participation probability change for each person
    # From OBR methodology: percentage change in participation = elasticity * percentage change in GTW
    direct_participation_change = elasticities * gtw_pct_change

    # Calculate surplus participation effects (OBR methodology)
    # When workers have better incentives (positive GTW change), this creates a "surplus"
    # that pulls non-workers into employment
    # When workers have worse incentives (negative GTW change), this creates a "deficit"
    # that pushes non-workers further away from employment

    # Group people by elasticity group for surplus calculation
    elasticity_groups = pd.cut(elasticities, bins=20, labels=False, duplicates="drop")

    surplus_participation_change = np.zeros_like(direct_participation_change)

    for group in np.unique(elasticity_groups[~np.isnan(elasticity_groups)]):
        group_mask = elasticity_groups == group
        workers_in_group = group_mask & currently_working
        nonworkers_in_group = group_mask & currently_not_working

        if workers_in_group.any() and nonworkers_in_group.any():
            # Calculate average GTW change for workers in this elasticity group
            avg_worker_gtw_change = np.mean(gtw_pct_change[workers_in_group])

            # Apply a fraction of this to non-workers in the same group
            # Using spillover factor of 1 (100% of worker effect) to match OBR
            spillover_factor = 1
            surplus_participation_change[nonworkers_in_group] = (
                elasticities[nonworkers_in_group]
                * avg_worker_gtw_change
                * spillover_factor
            )

            # Similarly, non-worker GTW changes affect workers (pushing them out if negative)
            avg_nonworker_gtw_change = np.mean(gtw_pct_change[nonworkers_in_group])
            surplus_participation_change[workers_in_group] = (
                elasticities[workers_in_group]
                * avg_nonworker_gtw_change
                * spillover_factor
            )

    # Total participation change includes both direct and surplus effects
    participation_change = direct_participation_change + surplus_participation_change

    # Apply stochastic participation responses
    new_employment_income = employment_income.copy()
    participation_response = np.zeros_like(employment_income, dtype=bool)

    # For currently working individuals: chance of leaving work
    for i in np.where(currently_working)[0]:
        # Negative participation change means lower probability of working
        exit_probability = max(
            0, -participation_change[i]
        )  # Only consider negative changes
        if np.random.random() < exit_probability:
            new_employment_income[i] = 0
            participation_response[i] = True  # Exited work

    # For currently non-working individuals: chance of entering work
    imputed_wages = impute_wages_for_nonworkers(sim, year, hours_for_new_entrants)
    for i in np.where(currently_not_working)[0]:
        # Positive participation change means higher probability of working
        entry_probability = max(
            0, participation_change[i]
        )  # Only consider positive changes
        if np.random.random() < entry_probability and imputed_wages[i] > 0:
            # Cast for the same reason as the in-work assignment above.
            new_employment_income[i] = new_employment_income.dtype.type(
                imputed_wages[i]
            )
            participation_response[i] = True  # Entered work

    # Update simulation with new employment incomes
    sim.set_input("employment_income", year, new_employment_income)

    # Update hours worked for new entrants
    hours_worked = sim.calculate("hours_worked", year)
    new_hours_worked = hours_worked.copy()

    # Set hours for new entrants. hours_worked is annual, so the weekly figure
    # has to be annualised before it is written back.
    new_workers = currently_not_working & (new_employment_income > 0)
    new_hours_worked[new_workers] = hours_for_new_entrants * WEEKS_IN_YEAR

    # Set hours to 0 for those who left work
    left_work = currently_working & (new_employment_income == 0)
    new_hours_worked[left_work] = 0

    sim.set_input("hours_worked", year, new_hours_worked)

    # Create results DataFrame
    results = pd.DataFrame(
        {
            "originally_working": currently_working,
            "originally_not_working": currently_not_working,
            "participation_elasticity": elasticities,
            "elasticity_group": elasticity_groups,
            "gtw_baseline": gtw_baseline,
            "gtw_reform": gtw_reform,
            "gtw_pct_change": gtw_pct_change,
            "direct_participation_change": direct_participation_change,
            "surplus_participation_change": surplus_participation_change,
            "participation_change": participation_change,
            "participation_response": participation_response,
            "new_employment_income": new_employment_income,
            "excluded": excluded,
        }
    )

    results["participation_change_ftes"] = results["participation_change"] * (
        hours_for_new_entrants / 37.5
    )  # Convert to FTEs

    weights = sim.calculate("household_weight", year, map_to="person")

    # Weight and filter
    from microdf import MicroDataFrame

    weighted_results = MicroDataFrame(results, weights=weights)

    return weighted_results[~weighted_results.excluded].drop(columns=["excluded"])
