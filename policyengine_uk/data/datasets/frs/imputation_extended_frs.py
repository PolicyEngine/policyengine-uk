from policyengine_core.data import Dataset
from pathlib import Path
import numpy as np
from typing import Type
from ..utils import STORAGE_FOLDER
from .frs import FRS_2019_20
from .spi_enhanced_frs import SPIEnhancedPooledFRS_2019_21
import yaml


class ImputationExtendedFRS(Dataset):
    name = "imputation_extended_frs"
    label = "Imputation-extended FRS"
    file_path = STORAGE_FOLDER / "imputation_extended_frs.h5"
    data_format = Dataset.TIME_PERIOD_ARRAYS
    input_dataset = None
    num_years = 1

    @staticmethod
    def from_dataset(
        dataset: Type[Dataset],
        new_name: str = "imputation_extended_frs",
        new_label: str = "Imputation-extended FRS",
        new_url: str = None,
        new_time_period: int = None,
        new_num_years: int = 1,
    ):
        class ImputationExtendedFRSFromDataset(ImputationExtendedFRS):
            name = new_name
            label = new_label
            input_dataset = dataset
            file_path = STORAGE_FOLDER / f"{new_name}.h5"
            time_period = new_time_period or dataset.time_period
            data_format = Dataset.TIME_PERIOD_ARRAYS
            url = new_url
            num_years = new_num_years

        return ImputationExtendedFRSFromDataset

    def generate(self):
        from policyengine_uk import Microsimulation
        from survey_enhance import Imputation

        simulation = Microsimulation(dataset=self.input_dataset)

        data = self.input_dataset().load_dataset()

        for variable in data.keys():
            data[variable] = {
                year: data[variable] for year in range(self.time_period, self.time_period + self.num_years)
            }

        # We're imputing consumption, wealth and VAT.

        IMPUTATIONS = STORAGE_FOLDER / "imputations"

        consumption = Imputation.load(IMPUTATIONS / "consumption.pkl")
        wealth = Imputation.load(IMPUTATIONS / "wealth.pkl")
        vat = Imputation.load(IMPUTATIONS / "vat.pkl")

        i = 0
        for imputation_model in [consumption, vat, wealth]:
            i += 1
            predictors = imputation_model.X_columns

            X_input = simulation.calculate_dataframe(
                predictors, map_to="household"
            )
            if i == 3:
                # WAS doesn't sample NI -> put NI households in Wales (closest aggregate)
                X_input.loc[
                    X_input["region"] == "NORTHERN_IRELAND", "region"
                ] = "WALES"
            Y_output = imputation_model.predict(X_input)

            for output_variable in Y_output.columns:
                values = Y_output[output_variable].values
                data[output_variable] = {
                    year: values
                    for year in range(
                        self.time_period, self.time_period + self.num_years
                    )
                }

        self.save_dataset(data)


ImputationExtendedFRS_2019_21 = ImputationExtendedFRS.from_dataset(
    SPIEnhancedPooledFRS_2019_21,
    "imputation_extended_frs_2019_21",
    "Imputation-extended FRS 2019-21",
    new_time_period=2024,
    new_num_years=5,
)