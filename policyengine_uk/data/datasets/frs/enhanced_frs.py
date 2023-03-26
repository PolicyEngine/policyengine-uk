from policyengine_core.data import Dataset
from pathlib import Path
import numpy as np
from typing import Type
from ..utils import STORAGE_FOLDER
from .stacked_frs import PooledFRS_2018_20
from .frs import FRS_2019_20
from .calibration.calibrated_frs import CalibratedSPIEnhancedPooledFRS_2018_20


class ImputationExtendedFRS(Dataset):
    name = "imputation_extended_frs"
    label = "Imputation-extended FRS"
    file_path = STORAGE_FOLDER / "imputation_extended_frs.h5"
    data_format = Dataset.ARRAYS
    input_dataset = None
    url = "https://api.github.com/repos/PolicyEngine/non-public-microdata/releases/assets/100228682"

    @staticmethod
    def from_dataset(
        dataset: Type[Dataset],
        new_name: str = "imputation_extended_frs",
        new_label: str = "Imputation-extended FRS",
    ):
        class ImputationExtendedFRSFromDataset(ImputationExtendedFRS):
            name = new_name
            label = new_label
            input_dataset = dataset
            file_path = STORAGE_FOLDER / f"{new_name}.h5"
            time_period = dataset.time_period
            data_format = Dataset.ARRAYS

        return ImputationExtendedFRSFromDataset

    def generate(self):
        from policyengine_uk import Microsimulation
        from survey_enhance import Imputation

        simulation = Microsimulation(dataset=self.input_dataset)

        data = self.input_dataset().load_dataset()

        # We're imputing consumption, wealth and VAT.

        IMPUTATIONS = STORAGE_FOLDER / "imputations"

        consumption = Imputation.load(IMPUTATIONS / "consumption.pkl")
        wealth = Imputation.load(IMPUTATIONS / "wealth.pkl")
        vat = Imputation.load(IMPUTATIONS / "vat.pkl")
        i = 0
        for imputation_model in [wealth, vat, consumption]:
            i += 1
            predictors = imputation_model.X_columns
            outputs = imputation_model.Y_columns

            X_input = simulation.calculate_dataframe(
                predictors, map_to="household"
            )
            if i == 1:
                # WAS doesn't sample NI -> put NI households in Wales (closest aggregate)
                X_input.loc[
                    X_input["region"] == "NORTHERN_IRELAND", "region"
                ] = "WALES"
            Y_output = imputation_model.predict(X_input, verbose=True)

            for output_variable in Y_output.columns:
                data[output_variable] = Y_output[output_variable].values

        self.save_dataset(data)


EnhancedFRS = ImputationExtendedFRS.from_dataset(
    CalibratedSPIEnhancedPooledFRS_2018_20,
    "enhanced_frs",
    "Enhanced FRS",
)
