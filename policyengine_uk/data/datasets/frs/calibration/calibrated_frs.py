from policyengine_core.data import Dataset
import numpy as np
from pathlib import Path
from typing import Type
import pandas as pd
from ...utils import STORAGE_FOLDER
from ..frs import FRS_2019_20, FRS_2020_21
from ..stacked_frs import PooledFRS_2019_21
from ..uprated_frs import UpratedFRS
from ..spi_enhanced_frs import (
    SPIEnhancedPooledFRS_2019_21,
)


def sum_by_household(values: pd.Series, dataset: Dataset) -> np.ndarray:
    return (
        pd.Series(values)
        .groupby(dataset.person.person_household_id.values)
        .sum()
        .values
    )


class CalibratedFRS(Dataset):
    input_dataset: Type[Dataset]
    time_period: int
    epochs: int = None
    learning_rate: float = 1e3
    min_loss: float = 0.035
    log_dir: str = "."
    time_period: str = None
    log_verbose: bool = False
    num_years: int = 1
    data_format: str = Dataset.TIME_PERIOD_ARRAYS

    @staticmethod
    def from_dataset(
        dataset: Type[Dataset],
        new_name: str = None,
        new_label: str = None,
        new_time_period: int = None,
        new_num_years: int = 1,
        log_folder: str = None,
        verbose: bool = True,
        new_url: str = None,
    ):
        class CalibratedFRSFromDataset(CalibratedFRS):
            name = new_name
            label = new_label
            input_dataset = dataset
            time_period = new_time_period or dataset.time_period
            log_dir = log_folder
            file_path = STORAGE_FOLDER / f"{new_name}.h5"
            log_verbose = verbose
            num_years = new_num_years
            url = new_url

        return CalibratedFRSFromDataset

    def generate(self):
        from .calibrate import calibrate

        new_data = {}
        input_dataset = self.input_dataset(require=True)
        data = input_dataset.load()
        for year in range(self.time_period, self.time_period + self.num_years):
            year = str(year)
            for variable in input_dataset.variables:
                if variable not in new_data:
                    new_data[variable] = {}
                if variable == "household_weight":
                    pass
                elif "_weight" not in variable and (
                    (year == str(self.time_period)) or ("_id" in variable)
                ):
                    new_data[variable][year] = data[variable][...]

            adjusted_weights = calibrate(
                self.input_dataset.name,
                time_period=year,
                training_log_path="calibration_log.csv.gz",
                overwrite_existing_log=year == str(self.time_period),
            )
            for partial_weights in adjusted_weights:
                new_data["household_weight"][year] = partial_weights

        self.save_dataset(new_data)


CalibratedSPIEnhancedPooledFRS_2019_21 = CalibratedFRS.from_dataset(
    SPIEnhancedPooledFRS_2019_21,
    "calibrated_spi_enhanced_pooled_frs_2019_21",
    "Calibrated SPI-enhanced FRS 2019-21",
    log_folder=".",
    new_num_years=7,
)
