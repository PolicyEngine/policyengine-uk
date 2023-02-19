from microdf.generic import MicroDataFrame
from policyengine_uk.data.datasets.was import WAS
from policyengine_uk.data.datasets.frs.frs import FRS
import pandas as pd
import microdf as mdf
import synthimpute as si

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

PREDICTOR_VARIABLES = [
    "household_net_income",
    "num_adults",
    "num_children",
    "pension_income",
    "employment_income",
    "self_employment_income",
    "capital_income",
    "num_bedrooms",
    "council_tax",
    "is_renting",
    "region",
]

IMPUTE_VARIABLES = [
    "owned_land",
    "property_wealth",
    "corporate_wealth",
    "gross_financial_wealth",
    "net_financial_wealth",
    "main_residence_value",
    "other_residential_property_value",
    "non_residential_property_value",
]


def impute_wealth(year: int, dataset: type = FRS) -> pd.Series:
    """Impute wealth by fitting a random forest model.

    Args:
        year (int): The year of simulation.
        dataset (type): The dataset to use.

    Returns:
        pd.Series: The predicted wealth values.
    """

    from policyengine_uk import Microsimulation

    sender = Microsimulation(
        dataset=WAS,
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
