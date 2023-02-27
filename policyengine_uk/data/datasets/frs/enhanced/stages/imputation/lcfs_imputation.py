from typing import Tuple
import pandas as pd
from pathlib import Path
from policyengine_uk.data.datasets.frs.frs import FRS
from policyengine_uk.data.datasets.lcfs import LCFS
from microdf import MicroDataFrame
import synthimpute as si

IMPUTE_VARIABLES = [
    "food_and_non_alcoholic_beverages_consumption",
    "alcohol_and_tobacco_consumption",
    "clothing_and_footwear_consumption",
    "housing_water_and_electricity_consumption",
    "household_furnishings_consumption",
    "health_consumption",
    "transport_consumption",
    "communication_consumption",
    "recreation_consumption",
    "education_consumption",
    "restaurants_and_hotels_consumption",
    "miscellaneous_consumption",
    "petrol_spending",
    "diesel_spending",
    "domestic_energy_consumption",
]

PREDICTOR_VARIABLES = [
    "is_adult",
    "is_child",
    "region",
    "employment_income",
    "self_employment_income",
    "state_pension",
    "pension_income",
]

REGIONS = {
    1: "NORTH_EAST",
    2: "NORTH_WEST",
    3: "YORKSHIRE",
    4: "EAST_MIDLANDS",
    5: "WEST_MIDLANDS",
    6: "EAST_OF_ENGLAND",
    7: "LONDON",
    8: "SOUTH_EAST",
    9: "SOUTH_WEST",
    10: "WALES",
    11: "SCOTLAND",
    12: "NORTHERN_IRELAND",
}


def impute_consumption(year: int, dataset: type = FRS) -> pd.Series:
    """Impute consumption by fitting a random forest model.

    Args:
        year (int): The year of LCFS to use.
        dataset (type): The dataset to use.

    Returns:
        pd.Series: The imputed consumption categories.
    """

    from policyengine_uk import Microsimulation

    sender = Microsimulation(
        dataset=LCFS,
        dataset_year=year,
    ).df(
        PREDICTOR_VARIABLES + IMPUTE_VARIABLES,
        map_to="household",
    )

    receiver = Microsimulation(
        dataset=dataset,
        dataset_year=year,
    ).df(
        PREDICTOR_VARIABLES,
        map_to="household",
    )

    sender.region = sender.region.map(
        {name: float(i) for i, name in REGIONS.items()}
    )
    receiver.region = receiver.region.map(
        {name: float(i) for i, name in REGIONS.items()}
    )

    return si.rf_impute(
        x_train=sender[PREDICTOR_VARIABLES],
        y_train=sender[IMPUTE_VARIABLES],
        x_new=receiver,
        verbose=True,
    )
