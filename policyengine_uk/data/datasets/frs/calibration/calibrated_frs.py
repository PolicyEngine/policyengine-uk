from policyengine_core.data import Dataset
import numpy as np
from pathlib import Path
from typing import Type
import pandas as pd
from ...utils import STORAGE_FOLDER
from ..imputation_extended_frs import ImputationExtendedFRS_2019_21


class CalibratedFRS(Dataset):
    input_dataset: Type[Dataset]
    time_period: int
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
        if not input_dataset.exists:
            input_dataset.generate()
        data = input_dataset.load()
        for year in range(self.time_period, self.time_period + self.num_years):
            year = str(year)
            adjusted_weights = calibrate(
                self.input_dataset.name,
                time_period=year,
            )
            for variable in input_dataset.variables:
                if variable not in new_data:
                    new_data[variable] = {}
                if variable == "household_weight":
                    new_data[variable][year] = adjusted_weights
                elif "_weight" not in variable and (
                    (year == str(self.time_period)) or ("_id" in variable)
                ):
                    new_data[variable][year] = data[variable][year]

        self.save_dataset(new_data)


EnhancedFRS = CalibratedFRS.from_dataset(
    ImputationExtendedFRS_2019_21,
    "enhanced_frs",
    "Enhanced FRS",
    new_num_years=1,
)
