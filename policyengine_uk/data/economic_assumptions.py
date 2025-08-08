from policyengine_uk.data import UKMultiYearDataset, UKSingleYearDataset

import yaml
from policyengine_core.parameters import ParameterNode
from pathlib import Path
import numpy as np
import logging


def extend_single_year_dataset(
    dataset: UKSingleYearDataset,
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
    return apply_uprating(multi_year_dataset)


def apply_uprating(
    dataset: UKMultiYearDataset,
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
        apply_single_year_uprating(current_year, prev_year, system.parameters)

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
            region.values
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
