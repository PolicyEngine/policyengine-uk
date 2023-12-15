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
    SPIEnhancedFRS_2019_20,
    SPIEnhancedPooledFRS_2018_20,
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
    learning_rate: float = 5e2
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
        input_dataset = self.input_dataset()
        data = input_dataset.load()
        for year in range(self.time_period, self.time_period + self.num_years):
            year = str(year)
            adjusted_weights = calibrate(
                self.input_dataset.name,
                time_period=year,
                training_log_path="calibration_log_cps.csv.gz",
                overwrite_existing_log=year == str(self.time_period),
            )
            for variable in input_dataset.variables:
                if variable not in new_data:
                    new_data[variable] = {}
                if variable == "household_weight":
                    new_data[variable][year] = adjusted_weights
                elif "_weight" not in variable and (
                    (year == str(self.time_period)) or ("_id" in variable)
                ):
                    new_data[variable][year] = data[variable][...]

        self.save_dataset(new_data)


CalibratedFRS_2019_20 = CalibratedFRS.from_dataset(
    FRS_2019_20,
    "calibrated_frs_2019",
    "Calibrated FRS 2019-20",
    new_num_years=1,
)


CalibratedFRS_2020_21 = CalibratedFRS.from_dataset(
    UpratedFRS.from_dataset(FRS_2020_21, out_year=2023),
    "calibrated_frs_2020",
    "Calibrated FRS 2020-21",
    new_num_years=1,
    log_folder=".",
)

CalibratedFRS_2019_21 = CalibratedFRS.from_dataset(
    PooledFRS_2019_21,
    "calibrated_frs_2019_21",
    "Calibrated FRS 2019-21",
    new_num_years=2,
    log_folder=".",
)


CalibratedSPIEnhancedFRS_2019_20 = CalibratedFRS.from_dataset(
    SPIEnhancedFRS_2019_20,
    "calibrated_spi_enhanced_frs_2019",
    "Calibrated SPI-enhanced FRS 2019-20",
    new_num_years=1,
)

CalibratedSPIEnhancedPooledFRS_2018_20 = CalibratedFRS.from_dataset(
    SPIEnhancedPooledFRS_2018_20,
    "calibrated_spi_enhanced_pooled_frs_2018_20",
    "Calibrated SPI-enhanced FRS 2018-20",
    log_folder=".",
    new_num_years=3,
)

CalibratedSPIEnhancedPooledFRS_2019_21 = CalibratedFRS.from_dataset(
    SPIEnhancedPooledFRS_2019_21,
    "calibrated_spi_enhanced_pooled_frs_2019_21",
    "Calibrated SPI-enhanced FRS 2019-21",
    log_folder=".",
    new_num_years=5,
)
