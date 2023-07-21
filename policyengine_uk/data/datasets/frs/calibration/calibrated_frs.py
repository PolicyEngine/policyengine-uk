from policyengine_core.data import Dataset
import numpy as np
from pathlib import Path
from typing import Type
import pandas as pd
from ...utils import STORAGE_FOLDER
from ..frs import FRS_2019_20, FRS_2020_21
from ..uprated_frs import UpratedFRS
from ..spi_enhanced_frs import (
    SPIEnhancedFRS_2019_20,
    SPIEnhancedPooledFRS_2018_20,
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
        from .output_dataset import OutputDataset
        from survey_enhance.reweight import CalibratedWeights
        from .loss import Loss, calibration_parameters

        calibrated_weights = {}
        data = self.input_dataset().load_dataset()

        new_data = {}

        for variable in data:
            new_data[variable] = {
                self.input_dataset.time_period: data[variable]
            }

        for year in range(self.time_period, self.time_period + self.num_years):
            print(f"Calibrating weights for {year}...")
            input_dataset = OutputDataset.from_dataset(
                self.input_dataset, new_time_period=year
            )
            input_dataset = input_dataset()

            original_weights = input_dataset.household.household_weight.values

            weights = CalibratedWeights(
                original_weights,
                input_dataset,
                Loss,
                calibration_parameters,
            )
            log_dir = Path(self.log_dir) / f"{year}"
            calibrated_weights[year] = weights.calibrate(
                f"{year}-01-01",
                epochs=self.epochs,
                learning_rate=self.learning_rate,
                verbose=self.log_verbose,
                log_dir=log_dir,
                min_loss=self.min_loss,
                log_frequency=50,
            )

            new_data["household_weight"][year] = calibrated_weights[year]

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
