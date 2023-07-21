from policyengine_core.data import Dataset
from pathlib import Path
import numpy as np
from typing import Type
from ..utils import STORAGE_FOLDER
from .stacked_frs import PooledFRS_2018_20
from .frs import FRS_2019_20
from .uprated_frs import UpratedFRS


class SPIEnhancedFRS(Dataset):
    name = "spi_enhanced_frs"
    label = "SPI-Enhanced FRS"
    file_path = STORAGE_FOLDER / "spi_enhanced_frs.h5"
    data_format = Dataset.ARRAYS
    input_dataset = None

    @staticmethod
    def from_dataset(
        dataset: Type[Dataset],
        new_name: str = "spi_enhanced_frs",
        new_label: str = "SPI-Enhanced FRS",
        new_url: str = None,
    ):
        class SPIEnhancedFRSFromDataset(SPIEnhancedFRS):
            name = new_name
            label = new_label
            input_dataset = dataset
            file_path = STORAGE_FOLDER / f"{new_name}.h5"
            time_period = dataset.time_period
            url = new_url

        return SPIEnhancedFRSFromDataset

    def generate(self):
        from policyengine_uk import Microsimulation
        from survey_enhance.impute import Imputation

        frs = self.input_dataset().load()

        new_values = {}

        for variable in frs.keys():
            if "_id" in variable:
                # e.g. [1, 2, 3] -> [11, 12, 13, 21, 22, 23]
                marker = 10 ** np.ceil(max(np.log10(frs[variable][...])))
                values = list(frs[variable][...] + marker) + list(
                    frs[variable][...] + marker * 2
                )
                new_values[variable] = values
            elif "_weight" in variable:
                new_values[variable] = list(frs[variable][...]) + list(
                    frs[variable][...] * 0
                )
            else:
                new_values[variable] = list(frs[variable][...]) * 2

        TARGETS = [
            1.016e12,  # From up-to-date published RTI data
            123.3e9,  # This and below from the 2019-20 SPI, uprated by 16% (2019 -> 2022)
            7.25e9,  # 16% is the relative change from 2019 SPI total pay to 2022 EOY RTI total pay
            78.0e9,
            133.0e9,
            10.3e9,
            30.9e9,
            4.0e9,
            31.9e9,
        ]

        income = Imputation.load(
            Path(__file__).parent.parent.parent
            / "storage"
            / "imputations"
            / "income.pkl"
        )

        simulation = Microsimulation(
            dataset=self.input_dataset,
        )

        input_df = simulation.calculate_dataframe(
            ["age", "gender", "region"], 2022
        )

        SOLVE_QUANTILES = False
        APPLY_QUANTILES = False
        HIGH_INCOME_SAMPLES = True
        if SOLVE_QUANTILES:
            mean_quantiles = income.solve_quantiles(
                TARGETS,
                input_df,
                simulation.calculate(
                    "household_weight", map_to="person"
                ).values,
            )
        elif APPLY_QUANTILES:
            mean_quantiles = [
                0.38,
                0.24,
                0.39,
                0.28,
                0.45,
                0.43,
                0.29,
                0.52,
                0.5,
            ]
        elif HIGH_INCOME_SAMPLES:
            mean_quantiles = [0.7] * 9
        else:
            mean_quantiles = None

        full_imputations = income.predict(input_df, mean_quantiles)
        for variable in full_imputations.columns:
            # Assign over the second half of the dataset
            if variable in new_values.keys():
                new_values[variable][
                    len(new_values[variable]) // 2 :
                ] = full_imputations[variable].values

        self.save_dataset(new_values)


SPIEnhancedPooledFRS_2018_20 = SPIEnhancedFRS.from_dataset(
    PooledFRS_2018_20,
    "spi_enhanced_pooled_frs_2018_20",
    "SPI-enhanced FRS 2018-20",
)

SPIEnhancedFRS_2019_20 = SPIEnhancedFRS.from_dataset(
    UpratedFRS.from_dataset(FRS_2019_20),
    "spi_enhanced_frs_2019",
    "SPI-enhanced FRS 2019-20",
)

IMPUTATIONS = [
    "employment_income",
    "self_employment_income",
    "savings_interest_income",
    "dividend_income",
    "pension_income",
    "employment_expenses",
    "property_income",
    "gift_aid",
    "pension_contributions",
]
