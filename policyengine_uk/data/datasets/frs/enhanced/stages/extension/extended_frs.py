import logging
import numpy as np
from policyengine_core.data import PrivateDataset, Dataset
from policyengine_uk.data.datasets.frs.frs import FRS
import h5py
from policyengine_uk.data.datasets.frs.enhanced.stages.extension.spi_imputation import (
    impute_incomes,
)
from policyengine_uk.data.datasets.frs.enhanced.utils import (
    clone_and_replace_half,
)
from policyengine_uk.data.datasets.frs.enhanced.stages.extension.uc_transition import (
    migrate_to_universal_credit,
)
from policyengine_uk.data.storage import policyengine_uk_MICRODATA_FOLDER
from time import time


class ExtendedFRS(PrivateDataset):
    name = "extended_frs"
    label = "Extended FRS"
    is_openfisca_compatible = True
    folder_path = policyengine_uk_MICRODATA_FOLDER

    filename_by_year = {
        2022: "extended_frs_2022.h5",
    }

    data_format = Dataset.TIME_PERIOD_ARRAYS

    def generate(self, year: int):
        """Generates the enhanced FRS dataset for OpenFisca-UK.

        Args:
            year (int): The year to generate for (uses the raw FRS from this year).
        """

        logging.info(f"Generating Extended FRS for year {year}")
        frs = FRS.load(year)
        frs_enhanced = h5py.File(self.file(year), mode="w")
        for key in frs.keys():
            frs_enhanced[f"{key}/{year}"] = frs[key][...]
        HOUSEHOLD_COUNT = frs_enhanced[f"household_id/{year}"][...].shape[0]
        frs_enhanced[f"in_original_frs/{year}"] = [True] * HOUSEHOLD_COUNT
        frs_enhanced[f"spi_imputed/{year}"] = [False] * HOUSEHOLD_COUNT
        frs_enhanced[f"uc_migrated/{year}"] = [False] * HOUSEHOLD_COUNT
        frs.close()
        frs_enhanced.close()

        logging.info("Imputing incomes from the SPI")

        pred_income = impute_incomes(year=year)
        clone_and_replace_half(
            self,
            year,
            {
                **{
                    f"{field}/{year}": pred_income[field]
                    for field in pred_income.columns
                },
                f"in_original_frs/{year}": [False] * HOUSEHOLD_COUNT,
                f"spi_imputed/{year}": [True] * HOUSEHOLD_COUNT,
            },
            weighting=0,
        )

        logging.info("Migrating to universal credit")

        uc_migrated = migrate_to_universal_credit(self, year)
        clone_and_replace_half(
            self,
            year,
            {
                **uc_migrated,
                f"in_original_frs/{year}": [False] * HOUSEHOLD_COUNT * 2,
                f"uc_migrated/{year}": [True] * HOUSEHOLD_COUNT * 2,
            },
            weighting=0,
        )
        from ..baseline_variables import generate_baseline_variables

        # Import here to avoid circular dependency
        generate_baseline_variables(self, year)

        self.save(
            year,
            f"original_weight/{year}",
            self.load(year, f"household_weight/{year}"),
        )

        logging.info("Finished generating SPI-enhanced FRS.")


ExtendedFRS = ExtendedFRS()
