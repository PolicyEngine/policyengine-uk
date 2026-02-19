from policyengine_uk.data import UKMultiYearDataset, UKSingleYearDataset

import yaml
from policyengine_core.parameters import ParameterNode
from pathlib import Path
import numpy as np
import logging


_PLAN5_TAKE_UP = {
    21: [0.013, 0.018, 0.023, 0.061, 0.111, 0.176, 0.750, 0.000, 0.000, 0.000],
    22: [0.012, 0.026, 0.000, 0.111, 0.047, 0.050, 0.154, 0.000, 0.000, 0.000],
    23: [0.048, 0.000, 0.056, 0.025, 0.121, 0.333, 0.312, 0.200, 0.000, 0.000],
    24: [0.058, 0.089, 0.204, 0.069, 0.171, 0.382, 0.526, 0.250, 0.000, 0.000],
    25: [0.104, 0.065, 0.151, 0.218, 0.353, 0.259, 0.400, 0.342, 0.000, 0.000],
    26: [0.167, 0.111, 0.000, 0.100, 0.161, 0.317, 0.383, 0.633, 0.000, 0.000],
    27: [0.085, 0.097, 0.193, 0.217, 0.309, 0.333, 0.475, 0.422, 0.000, 0.000],
    28: [0.089, 0.256, 0.176, 0.204, 0.176, 0.324, 0.420, 0.539, 0.000, 0.000],
    29: [0.122, 0.293, 0.206, 0.307, 0.284, 0.281, 0.378, 0.564, 0.000, 0.000],
    30: [0.127, 0.133, 0.342, 0.281, 0.338, 0.389, 0.382, 0.444, 0.000, 0.000],
}

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
    """Re-label student loan plans and add new Plan 5 entrants each year."""
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
    plan = person["student_loan_plan"].values.copy().astype(str)
    region = person["region"].values.astype(str)
    uni_start_year = year - age + 18

    # Step 1 — Re-label existing loan holders (Transition A).
    has_loan = plan != "NONE"
    is_england = np.isin(region, list(_ENGLAND_REGIONS))

    written_off = has_loan & (uni_start_year + _PLAN1_WRITEOFF_YEARS <= year)
    is_plan1 = has_loan & ~written_off & (uni_start_year < 2012)
    is_plan2_start = (
        has_loan
        & ~written_off
        & (uni_start_year >= 2012)
        & (uni_start_year < 2023)
    )
    is_plan5_start = has_loan & ~written_off & (uni_start_year >= 2023)

    new_plan = plan.copy()
    new_plan[written_off] = "NONE"
    new_plan[is_plan1] = "PLAN_1"
    new_plan[is_plan2_start] = "PLAN_2"
    new_plan[is_plan5_start & is_england] = "PLAN_5"
    new_plan[is_plan5_start & ~is_england] = "PLAN_2"

    repayments = person["student_loan_repayments"].values.copy()
    repayments[written_off] = 0.0

    # Step 2 — Create new Plan 5 entrants (Transition B).
    # Eligible: currently NONE, aged 21-30, started uni 2023+ (age <= year-2005),
    # living in England.
    plan_none = new_plan == "NONE"
    age_eligible = (age >= 21) & (age <= 30)
    started_2023_plus = age <= (year - 2005)
    new_entrant_mask = (
        plan_none & age_eligible & started_2023_plus & is_england
    )

    if new_entrant_mask.any():
        import pandas as pd

        rng = np.random.default_rng(seed=year)
        income = person["employment_income"].values

        for a in range(21, 31):
            age_mask = new_entrant_mask & (age == a)
            if not age_mask.any():
                continue
            take_up_probs = _PLAN5_TAKE_UP[a]
            indices = np.where(age_mask)[0]
            inc_vals = income[indices]
            # Compute income decile within this age band.
            try:
                deciles = pd.qcut(
                    inc_vals,
                    q=10,
                    labels=False,
                    duplicates="drop",
                )
            except ValueError:
                deciles = np.zeros(len(inc_vals), dtype=int)
            deciles = np.where(pd.isna(deciles), 0, deciles).astype(int)
            probs = np.array([take_up_probs[min(d, 9)] for d in deciles])
            draws = rng.random(len(indices))
            sampled = draws < probs
            new_plan[indices[sampled]] = "PLAN_5"
            repayments[indices[sampled]] = 0.0

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
