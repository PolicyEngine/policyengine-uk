import logging
from pathlib import Path
from openfisca_uk.microdata.datasets.frs.frs_enhanced.general import (
    add_variables,
    clone_and_replace_half,
    subsample,
)
from openfisca_uk.microdata.datasets.frs.frs_enhanced.spi_imputation import (
    impute_incomes,
)
from openfisca_uk.microdata.datasets.frs.frs_enhanced.uc_transition import (
    migrate_to_universal_credit,
)
from openfisca_uk.microdata.utils import dataset, UK, PACKAGE_DIR
from openfisca_uk.microdata.datasets.frs.frs import FRS
from openfisca_uk.microdata.datasets.frs.frs_enhanced.was_imputation import (
    impute_wealth,
)
from openfisca_uk.microdata.datasets.frs.frs_enhanced.lcf_imputation import (
    impute_consumption,
)
import h5py
import numpy as np
from time import time
import pandas as pd


@dataset
class FRSEnhanced:
    name = "frs_enhanced"
    model = UK

    def generate(year: int) -> None:
        logging.info(f"Generating FRSEnhanced for year {year}")
        logging.info("Loading FRS")
        FRS.generate(year)

        frs = FRS.load(year)
        frs_enhanced = h5py.File(FRSEnhanced.file(year), mode="w")
        for key in frs.keys():
            frs_enhanced[key] = frs[key][...]
        frs.close()
        frs_enhanced.close()

        logging.info("Adding high incomes imputed from the SPI")
        pred_income = impute_incomes()
        clone_and_replace_half(
            FRSEnhanced,
            year,
            {field: pred_income[field] for field in pred_income.columns},
            weighting=0,
        )

        logging.info("Adding UC-migrated households")
        uc_migrated = migrate_to_universal_credit(FRSEnhanced, year)
        clone_and_replace_half(FRSEnhanced, year, uc_migrated, weighting=0)

        logging.info("Adding wealth imputed from the WAS")
        pred_wealth = impute_wealth(year, dataset=FRSEnhanced)
        add_variables(
            FRSEnhanced,
            year,
            {field: pred_wealth[field] for field in pred_wealth.columns},
        )

        logging.info("Adding consumption imputed from the LCFS")
        pred_consumption = impute_consumption(year, dataset=FRSEnhanced)
        add_variables(
            FRSEnhanced,
            year,
            {
                field: pred_consumption[field]
                for field in pred_consumption.columns
            },
        )

        # Save imputed variables to a CSV file

        logging.info("Saving imputed variables to CSV")

        from openfisca_uk import Microsimulation

        sim = Microsimulation(dataset=FRSEnhanced, adjust_weights=False)
        hnet = sim.calc("household_net_income")
        hnet.weights *= sim.calc("people", map_to="household").values
        pd.concat(
            [
                sim.df(
                    [
                        "household_net_income",
                        "household_market_income",
                        "household_id",
                    ]
                ),
                pred_wealth,
                pred_consumption,
                pd.DataFrame(
                    {
                        "decile": hnet.decile_rank(),
                    }
                ),
            ],
            axis=1,
        ).to_csv(PACKAGE_DIR / "imputations" / f"imputations_{year}.csv")
