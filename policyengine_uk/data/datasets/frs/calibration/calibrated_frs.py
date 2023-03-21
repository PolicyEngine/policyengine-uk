from policyengine_core.data import Dataset
from survey_enhance.reweight import CalibratedWeights
from .loss import Loss, calibration_parameters
import numpy as np
from pathlib import Path
from typing import Type
import pandas as pd
from ...utils import STORAGE_FOLDER
from ..frs import FRS_2019_20
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
    epochs: int = 512
    learning_rate: float = 5e1
    log_dir: str = None
    time_period: str = None
    log_verbose: bool = False

    @staticmethod
    def from_dataset(
        dataset: Type[Dataset],
        new_name: str = None,
        new_label: str = None,
        out_year: int = 2022,
        log_folder: str = None,
        verbose: bool = True,
    ):
        class CalibratedFRSFromDataset(CalibratedFRS):
            name = new_name
            label = new_label
            input_dataset = dataset
            time_period = out_year or dataset.time_period
            log_dir = log_folder
            file_path = STORAGE_FOLDER / f"{new_name}.h5"
            data_format = dataset.data_format
            log_verbose = verbose

        return CalibratedFRSFromDataset

    def generate(self):
        from .output_dataset import OutputDataset

        input_dataset = OutputDataset.from_dataset(self.input_dataset)
        input_dataset = input_dataset()

        original_weights = input_dataset.household.household_weight.values

        calibrated_weights = CalibratedWeights(
            original_weights,
            input_dataset,
            Loss,
            calibration_parameters,
        )
        weights = calibrated_weights.calibrate(
            "2022-01-01",
            epochs=self.epochs,
            learning_rate=self.learning_rate,
            verbose=self.log_verbose,
            log_dir=self.log_dir,
        )

        data = self.input_dataset().load_dataset()

        data["household_weight"] = weights

        self.save_dataset(data)

        # Remove zero-weighted households

        from policyengine_uk.system import system
        from policyengine_uk import Microsimulation

        simulation = Microsimulation(dataset=self)
        household_has_weight = (
            simulation.calculate("household_weight").values > 0
        )
        person_has_weight = (
            simulation.calculate("household_weight", map_to="person").values
            > 0
        )
        benunit_has_weight = (
            simulation.calculate("household_weight", map_to="benunit").values
            > 0
        )

        for variable in data.keys():
            if variable in system.variables:
                if system.variables[variable].entity.key == "household":
                    data[variable] = data[variable][household_has_weight]
                elif system.variables[variable].entity.key == "person":
                    data[variable] = data[variable][person_has_weight]
                elif system.variables[variable].entity.key == "benunit":
                    data[variable] = data[variable][benunit_has_weight]

        self.save_dataset(data)


CalibratedFRS_2019_20 = CalibratedFRS.from_dataset(
    FRS_2019_20,
    "calibrated_frs_2019",
    "Calibrated FRS 2019-20",
)

CalibratedSPIEnhancedFRS_2019_20 = CalibratedFRS.from_dataset(
    SPIEnhancedFRS_2019_20,
    "calibrated_spi_enhanced_frs_2019",
    "Calibrated SPI-enhanced FRS 2019-20",
)

CalibratedSPIEnhancedPooledFRS_2018_20 = CalibratedFRS.from_dataset(
    SPIEnhancedPooledFRS_2018_20,
    "calibrated_spi_enhanced_pooled_frs_2018_20",
    "Calibrated SPI-enhanced FRS 2018-20",
)
