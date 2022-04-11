import logging
import numpy as np
from openfisca_tools.data import PrivateDataset, Dataset
from openfisca_uk.data.datasets.frs.enhanced.lcfs_imputation import (
    impute_consumption,
)

from openfisca_uk.repo import REPO
from openfisca_uk.data.datasets.frs.enhanced.uc_transition import (
    migrate_to_universal_credit,
)
from openfisca_uk.data.datasets.frs.enhanced.was_imputation import (
    impute_wealth,
)
from openfisca_uk.data.datasets.frs.frs import FRS
import h5py
from openfisca_uk.data.datasets.frs.enhanced.spi_imputation import (
    impute_incomes,
)
from openfisca_uk.data.datasets.frs.enhanced.utils import (
    add_variables,
    clone_and_replace_half,
)
from openfisca_uk.data.storage import OPENFISCA_UK_MICRODATA_FOLDER
from openfisca_uk.tools.baseline_variables import generate_baseline_variables
from time import time


class EnhancedFRS(PrivateDataset):
    name = "enhanced_frs"
    label = "Enhanced FRS"
    is_openfisca_compatible = True
    folder_path = OPENFISCA_UK_MICRODATA_FOLDER

    data_format = Dataset.TIME_PERIOD_ARRAYS

    def generate(self, year: int):
        """Generates the enhanced FRS dataset for OpenFisca-UK.

        Args:
            year (int): The year to generate for (uses the raw FRS from this year).
        """

        start_time = time()

        logging.info(f"Generating FRSEnhanced for year {year}")
        logging.info(f"1 / 7 | Generating default FRS")
        FRS.generate(year)

        frs = FRS.load(year)
        frs_enhanced = h5py.File(self.file(year), mode="w")
        for key in frs.keys():
            frs_enhanced[f"{key}/{year}"] = frs[key][...]
        frs_enhanced[f"in_original_frs/{year}"] = np.ones(frs[key].shape[0])
        frs.close()
        frs_enhanced.close()

        logging.info(f"2 / 7 | Imputing incomes from the SPI")

        pred_income = impute_incomes()
        clone_and_replace_half(
            self,
            year,
            {
                f"{field}/{year}": pred_income[field]
                for field in pred_income.columns
            },
            weighting=0,
        )

        logging.info(f"3 / 7 | Cloning with UC-migrated households")

        uc_migrated = migrate_to_universal_credit(self, year)
        clone_and_replace_half(self, year, uc_migrated, weighting=0)

        logging.info(f"4 / 7 | Calibrating FRS weights")

        from openfisca_uk.calibration.calibrate import HouseholdWeights

        # Import TensorFlow-using modules here to avoid unnecessary loading of
        # TensorFlow.

        weights = HouseholdWeights(
            start_year=2019,
            end_year=2027,
        )
        weights.calibrate(
            num_epochs=200,
            validation_split=0,
            learning_rate=1e3,
            dataset=self,
        )

        self.save(
            year,
            f"frs_household_weight/{year}",
            self.load(year, f"household_weight/{year}"),
        )
        for period in range(2019, 2027):
            self.save(
                year, f"household_weight/{period}", weights.get_weights(period)
            )

        logging.info(f"5 / 7 | Imputing consumption from the LCFS")

        pred_consumption = impute_consumption(year, dataset=self)
        add_variables(
            self,
            year,
            {
                f"{field}/{year}": pred_consumption[field]
                for field in pred_consumption.columns
            },
        )

        logging.info(f"6 / 7 | Imputing wealth from the WAS")

        pred_wealth = impute_wealth(year, dataset=self)
        add_variables(
            self,
            year,
            {
                f"{field}/{year}": pred_wealth[field]
                for field in pred_wealth.columns
            },
        )

        logging.info(f"7 / 7 | Pre-entering default simulation variables")

        generate_baseline_variables()

        with h5py.File(
            REPO / "data" / "baseline_variables.h5", mode="r"
        ) as baseline_variables:
            for variable in baseline_variables.keys():
                for period in baseline_variables[variable].keys():
                    self.save(
                        year,
                        f"{variable}/{period}",
                        baseline_variables[variable][period][...],
                    )

        logging.info(
            f"Finished generating FRSEnhanced for year {year} in {time() - start_time} seconds"
        )


EnhancedFRS = EnhancedFRS()
