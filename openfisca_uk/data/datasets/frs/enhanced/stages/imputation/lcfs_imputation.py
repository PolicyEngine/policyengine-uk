from typing import Tuple
import pandas as pd
from pathlib import Path
from openfisca_uk.data.datasets.frs.frs import FRS
from openfisca_uk.data.datasets.lcfs import RawLCFS
from microdf import MicroDataFrame
import synthimpute as si




def impute_consumption(year: int, dataset: type = FRS) -> pd.Series:
    """Impute consumption by fitting a random forest model.

    Args:
        year (int): The year of LCFS to use.
        dataset (type): The dataset to use.

    Returns:
        pd.Series: The imputed consumption categories.
    """

    # Load the LCFS data with carbon consumption
    lcfs = load_lcfs(year)

    # Impute LCFS consumption to FRS households
    return impute_consumption_to_FRS(lcfs, year, dataset)


def impute_consumption_to_FRS(
    lcf: MicroDataFrame, year: int, dataset: type = FRS
) -> pd.Series:
    """Impute consumption to the FRS.

    Args:
        LCFS (MicroDataFrame): The LCFS data.
        year (int): The year of the FRS to use.
        dataset (type): The dataset to use.

    Returns:
        MicroDataFrame: The imputed consumption.
    """

    from openfisca_uk import Microsimulation

    sim = Microsimulation(
        dataset=dataset,
        year=year,
    )

    frs = sim.df(
        [
            "is_adult",
            "is_child",
            "region",
            "employment_income",
            "self_employment_income",
            "state_pension",
            "pension_income",
        ],
        map_to="household",
    )

    frs.region = frs.region.map(
        {name: float(i) for i, name in REGIONS.items()}
    )
    lcf.region = lcf.region.map(
        {name: float(i) for i, name in REGIONS.items()}
    )
    return si.rf_impute(
        x_train=lcf.drop(CATEGORY_VARIABLES, axis=1),
        y_train=lcf[CATEGORY_VARIABLES],
        x_new=frs,
        verbose=True,
        ignore_target=True,
    )

