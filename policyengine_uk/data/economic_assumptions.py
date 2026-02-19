from policyengine_uk.data import UKMultiYearDataset, UKSingleYearDataset

import yaml
from policyengine_core.parameters import ParameterNode
from pathlib import Path
import numpy as np
import logging

# Base year for the FRS dataset - used to calculate age offsets
_FRS_BASE_YEAR = 2023  # FRS 2023-24 represents calendar year 2024

# Approximate take-up rate for assigning loans to tertiary-educated NONE people.
# This represents P(has loan AND earning above threshold | tertiary educated).
# Derived from SLC forecasts (~4M Plan 2 above threshold) vs UK graduate
# population (~8-10M in relevant age bands), giving roughly 40-50%.
# We use a conservative 0.4 as many graduates have paid off loans or earn
# below threshold.
_GRADUATE_LOAN_TAKE_UP = 0.4

_ENGLAND_REGIONS = {
    "NORTH_EAST",
    "NORTH_WEST",
    "YORKSHIRE",
    "EAST_MIDLANDS",
    "WEST_MIDLANDS",
    "EAST_OF_ENGLAND",
    "LONDON",
    "SOUTH_EAST",
    "SOUTH_WEST",
}

_PLAN1_WRITEOFF_YEARS = 29


def extend_single_year_dataset(
    dataset: UKSingleYearDataset,
    tax_benefit_system_parameters: ParameterNode,
    end_year: int = 2030,
) -> UKMultiYearDataset:
    # Extend years and uprate
    start_year = int(dataset.time_period)
    datasets = [dataset]
    for year in range(start_year, end_year + 1):
        next_year = dataset.copy()
        next_year.time_period = str(year)
        datasets.append(next_year)
    multi_year_dataset = UKMultiYearDataset(datasets=datasets)
    return apply_uprating(
        multi_year_dataset,
        tax_benefit_system_parameters=tax_benefit_system_parameters,
    )


def apply_uprating(
    dataset: UKMultiYearDataset,
    tax_benefit_system_parameters: ParameterNode = None,
):
    from policyengine_uk.system import system

    # Apply uprating to the dataset.
    dataset = dataset.copy()

    if not isinstance(dataset, UKMultiYearDataset):
        raise TypeError("dataset must be of type UKMultiYearDataset.")

    for year in dataset.datasets.keys():
        if year == min(dataset.datasets.keys()):
            continue  # Don't uprate the first year
        current_year = dataset.datasets[year]
        prev_year = dataset.datasets[year - 1]
        apply_single_year_uprating(
            current_year, prev_year, tax_benefit_system_parameters
        )

    return dataset


def apply_single_year_uprating(
    current_year: UKSingleYearDataset,
    previous_year: UKSingleYearDataset,
    parameters: ParameterNode,
):
    # Apply uprating to a single year dataset.

    # First, apply standard variable-YoY growth based uprating.

    with open(Path(__file__).parent / "uprating_indices.yaml", "r") as f:
        uprating = yaml.safe_load(f)
    for index_name, variables in uprating.items():
        index_rel_change = parameters.get_child(index_name)(
            current_year.time_period
        )
        for variable in variables:
            for table_name, df in zip(
                current_year.table_names, current_year.tables
            ):
                if variable in df.columns:
                    prev_year_value = getattr(previous_year, table_name)[
                        variable
                    ]
                    current_year_value = prev_year_value * (
                        1 + index_rel_change
                    )
                    getattr(current_year, table_name)[
                        variable
                    ] = current_year_value

    # Next, apply custom uprating.

    # Council Tax is uprated by OBR forecasts/outturns by country.

    current_year = uprate_council_tax(current_year, previous_year, parameters)

    # Rent is uprated by OBR forecasts/outturns by region.

    current_year = uprate_rent(current_year, previous_year, parameters)

    current_year = uprate_student_loan_plans(
        current_year, previous_year, parameters
    )

    current_year.validate()

    return current_year


def uprate_council_tax(
    current_year: UKSingleYearDataset,
    previous_year: UKSingleYearDataset,
    parameters: ParameterNode,
):
    # Uprate council tax for a single year dataset.

    council_tax = (
        parameters.gov.economic_assumptions.yoy_growth.obr.council_tax
    )
    region = current_year.household["region"]
    country = np.select(
        [
            region == "WALES",
            region == "SCOTLAND",
            region == "NORTHERN IRELAND",
        ],
        [
            "WALES",
            "SCOTLAND",
            "NORTHERN IRELAND",
        ],
        default="ENGLAND",
    )
    growth_rates = np.select(
        [
            country == "ENGLAND",
            country == "WALES",
            country == "SCOTLAND",
        ],
        [
            council_tax.england(current_year.time_period),
            council_tax.wales(current_year.time_period),
            council_tax.scotland(current_year.time_period),
        ],
        default=0,
    )

    current_year.household["council_tax"] = previous_year.household[
        "council_tax"
    ] * (1 + growth_rates)
    return current_year


def uprate_rent(
    current_year: UKSingleYearDataset,
    previous_year: UKSingleYearDataset,
    parameters: ParameterNode,
):
    # Uprate rent for a single year dataset.
    is_private_rented = (
        current_year.household["tenure_type"] == "RENT_PRIVATELY"
    )
    region = current_year.household["region"]
    prev_rent = previous_year.household["rent"]
    growth = parameters.gov.economic_assumptions.yoy_growth
    year = int(current_year.time_period)
    social_rent_growth = growth.obr.social_rent(year)

    if year < 2022:
        logging.warning(
            "Rent uprating is not supported for years before 2022. Not applying uprating."
        )
        pass
    elif year < 2025:
        # We have regional growth rates for private rent.
        regional_growth_rate = growth.ons.private_rental_prices(year)[
            region.values.astype(str)
        ]
        current_year.household["rent"] = np.where(
            is_private_rented,
            prev_rent * (1 + regional_growth_rate),
            prev_rent * (1 + social_rent_growth),
        )
    elif year >= 2025:
        # Back out private rent growth from the aggregate
        # from latest English Housing Survey data
        PRIVATE_RENTAL_HOUSEHOLDS = 0.188
        SOCIAL_RENTAL_HOUSEHOLDS = 0.164

        total_rental_households = (
            PRIVATE_RENTAL_HOUSEHOLDS + SOCIAL_RENTAL_HOUSEHOLDS
        )

        private_weight = PRIVATE_RENTAL_HOUSEHOLDS / total_rental_households
        social_weight = SOCIAL_RENTAL_HOUSEHOLDS / total_rental_households

        aggregate_growth = growth.obr.rent(year)
        private_rent_growth = (
            aggregate_growth - social_weight * social_rent_growth
        ) / private_weight

        current_year.household["rent"] = np.where(
            is_private_rented,
            prev_rent * (1 + private_rent_growth),
            prev_rent * (1 + social_rent_growth),
        )

    return current_year


def uprate_student_loan_plans(
    current_year: UKSingleYearDataset,
    previous_year: UKSingleYearDataset,
    parameters: ParameterNode,
) -> UKSingleYearDataset:
    """Assign student loan plans based on cohort and add new entrants.

    This function is idempotent: for any given year, it produces the same
    cross-sectional snapshot regardless of whether previous years were
    processed. It operates on the base year data, not accumulated state.

    The FRS base year (2023-24) captures loan holders up to certain ages.
    As we project forward, we need to:
    1. Re-label existing holders to correct plan based on uni start year
    2. Add Plan 1/2 holders in age bands beyond the base year's coverage
    3. Add Plan 5 holders (new plan starting 2023)

    For (2) and (3), we use highest_education == TERTIARY as the signal
    for who is a graduate, then apply a flat take-up probability.
    """
    year = int(current_year.time_period)

    person = current_year.person.copy()
    household = current_year.household[["household_id", "region"]].copy()

    # Join region onto person via person_household_id.
    person = person.merge(
        household.rename(columns={"household_id": "person_household_id"}),
        on="person_household_id",
        how="left",
    )

    age = person["age"].values.astype(int)
    base_plan = person["student_loan_plan"].values.copy().astype(str)
    region = person["region"].values.astype(str)
    highest_ed = person["highest_education"].values.astype(str)

    # Age in the base year (used to identify "new" cohorts)
    base_year_age = age - (year - _FRS_BASE_YEAR)

    uni_start_year = year - age + 18
    is_england = np.isin(region, list(_ENGLAND_REGIONS))
    is_tertiary = highest_ed == "TERTIARY"

    # Initialize output arrays
    new_plan = base_plan.copy()
    repayments = person["student_loan_repayments"].values.copy()

    # Deterministic RNG seeded by year for reproducibility
    rng = np.random.default_rng(seed=year)

    # Helper to assign plans to eligible people
    def assign_with_probability(mask, plan_value, prob=_GRADUATE_LOAN_TAKE_UP):
        """Assign plan_value to a random subset of masked people."""
        if not mask.any():
            return
        indices = np.where(mask)[0]
        draws = rng.random(len(indices))
        sampled = draws < prob
        new_plan[indices[sampled]] = plan_value
        repayments[indices[sampled]] = 0.0

    # === Step 1: Re-label existing loan holders ===
    has_loan = base_plan != "NONE"
    written_off = has_loan & (uni_start_year + _PLAN1_WRITEOFF_YEARS <= year)
    is_plan1_cohort = has_loan & ~written_off & (uni_start_year < 2012)
    is_plan2_cohort = (
        has_loan
        & ~written_off
        & (uni_start_year >= 2012)
        & (uni_start_year < 2023)
    )
    is_plan5_cohort = has_loan & ~written_off & (uni_start_year >= 2023)

    new_plan[written_off] = "NONE"
    repayments[written_off] = 0.0
    new_plan[is_plan1_cohort] = "PLAN_1"
    new_plan[is_plan2_cohort] = "PLAN_2"
    new_plan[is_plan5_cohort & is_england] = "PLAN_5"
    new_plan[is_plan5_cohort & ~is_england] = "PLAN_2"

    # === Step 2: Add Plan 1 holders in extended age bands ===
    # In base year, Plan 1 holders exist up to ~age 40 (started pre-2012).
    # By 2029, Plan 1 should include people up to age 46.
    # Target: NONE people who are tertiary-educated, in the "new" age band,
    # whose uni_start_year < 2012 and loan not written off.
    max_plan1_age_base = 40  # Approximate max age of Plan 1 in base year
    plan1_new_cohort = (
        (new_plan == "NONE")
        & is_tertiary
        & (base_year_age > max_plan1_age_base)
        & (uni_start_year < 2012)
        & (uni_start_year + _PLAN1_WRITEOFF_YEARS > year)
    )
    assign_with_probability(plan1_new_cohort, "PLAN_1")

    # === Step 3: Add Plan 2 holders in extended age bands ===
    # In base year (2024), Plan 2 holders exist up to age 29 (started 2012).
    # By 2029, Plan 2 should include people up to age 35.
    # Target: NONE people who are tertiary-educated, in the "new" age band,
    # whose uni_start_year is 2012-2022.
    max_plan2_age_base = 29  # Max age of Plan 2 in base year
    plan2_new_cohort = (
        (new_plan == "NONE")
        & is_tertiary
        & (base_year_age > max_plan2_age_base)
        & (uni_start_year >= 2012)
        & (uni_start_year < 2023)
    )
    assign_with_probability(plan2_new_cohort, "PLAN_2")

    # === Step 4: Add Plan 5 holders (new plan from 2023) ===
    # Plan 5 didn't exist in base year. Eligible: tertiary-educated NONE
    # people in England who would have started uni 2023+.
    # Age constraint: must be 21+ (finished 3-year degree) to be repaying.
    plan5_eligible = (
        (new_plan == "NONE")
        & is_tertiary
        & is_england
        & (uni_start_year >= 2023)
        & (age >= 21)
    )
    assign_with_probability(plan5_eligible, "PLAN_5")

    # Write back to the person table (without the merged region column).
    person_out = current_year.person.copy()
    person_out["student_loan_plan"] = new_plan
    person_out["student_loan_repayments"] = repayments
    current_year.person = person_out

    return current_year


def reset_uprating(
    dataset: UKMultiYearDataset,
):
    # Remove all uprating from the dataset.

    first_year = min(dataset.datasets.keys())
    for year in dataset.datasets:
        if year != first_year:
            dataset.datasets[year] = dataset.datasets[first_year].copy()
            dataset.datasets[year].time_period = str(year)

    return dataset
