import logging
from microdf import MicroDataFrame
import pandas as pd
import synthimpute as si
from typing import Dict, List
import h5py
import numpy as np
from numpy.typing import ArrayLike

from openfisca_uk.microdata.datasets.frs.frs import FRS
from openfisca_uk.microdata.datasets.spi.spi import SPI

PREDICTORS = [
    "age",
    "region",
]

IMPUTATIONS = [
    "employment_income",
    "self_employment_income",
    "savings_interest_income",
    "dividend_income",
    "pension_income",
    "employment_expenses",
    "property_income",
    "gift_aid",
    "pension_contributions",
]


def impute_incomes(dataset: type = FRS, year: int = 2019) -> MicroDataFrame:
    """Imputation of high incomes from the SPI.

    Args:
        dataset (type): The dataset to clone.
        year (int): The year to clone.

    Returns:
        Dict[str, ArrayLike]: The mapping from the original dataset to the cloned dataset.
    """
    from openfisca_uk import Microsimulation

    # Most recent SPI used - if it's before the FRS year then data will be uprated
    # automatically by OpenFisca-UK
    spi = Microsimulation(dataset=SPI, add_baseline_values=False)
    frs = Microsimulation(
        dataset=dataset,
        year=year,
        adjust_weights=False,
        add_baseline_values=False,
    )

    regions = spi.calc("region").unique()

    spi_df = spi.df(PREDICTORS + IMPUTATIONS)
    frs_df = frs.df(PREDICTORS)

    frs_df.region = frs_df.region.map(
        {name: float(i) for i, name in enumerate(regions)}
    )
    spi_df.region = spi_df.region.map(
        {name: float(i) for i, name in enumerate(regions)}
    )

    return si.rf_impute(
        x_train=spi_df.drop(IMPUTATIONS, axis=1),
        y_train=spi_df[IMPUTATIONS],
        x_new=frs_df,
        verbose=True,
    )
