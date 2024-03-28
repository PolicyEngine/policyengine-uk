from policyengine_core.data import Dataset
from pathlib import Path
import numpy as np
from typing import Type
from ..utils import STORAGE_FOLDER
from .stacked_frs import PooledFRS_2019_21
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

        input_dataset = self.input_dataset()
        if not input_dataset.exists:
            input_dataset.generate()
        frs = input_dataset.load()

        new_values = {}

        for variable in frs.keys():
            if "_id" in variable:
                # e.g. [1, 2, 3] -> [11, 12, 13, 21, 22, 23]
                marker = 10 ** np.ceil(max(np.log10(frs[variable][...])))
                values = (
                    list(frs[variable][...] + marker)
                    + list(frs[variable][...] + marker * 2)
                    + list(frs[variable][...] + marker * 3)
                )
                new_values[variable] = values
            elif "_weight" in variable:
                new_values[variable] = (
                    list(frs[variable][...]) + list(frs[variable][...] * 0) * 2
                )
            else:
                new_values[variable] = list(frs[variable][...]) * 3

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
            ["age", "gender", "region"],
        )

        full_imputations = income.predict(input_df)

        full_imputations[input_df.age.values < 18] *= 0
        for variable in full_imputations.columns:
            # Assign over the second third of the dataset
            if variable in new_values.keys():
                length = len(new_values[variable])
                new_values[variable][length // 3 : (length * 2) // 3] = (
                    full_imputations[variable].values
                )

        high_income = Imputation.load(
            Path(__file__).parent.parent.parent
            / "storage"
            / "imputations"
            / "high_income.pkl"
        )

        high_income_imputations = high_income.predict(input_df)

        high_income_imputations[input_df.age.values < 18] *= 0

        for variable in high_income_imputations.columns:
            # Assign over the last third of the dataset
            if variable in new_values.keys():
                length = len(new_values[variable])
                new_values[variable][(length * 2) // 3 :] = (
                    high_income_imputations[variable].values
                )

        self.save_dataset(new_values)


SPIEnhancedPooledFRS_2019_21 = SPIEnhancedFRS.from_dataset(
    PooledFRS_2019_21,
    "spi_enhanced_pooled_frs_2019_21",
    "SPI-enhanced FRS 2019-21",
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
