from policyengine_core.data import Dataset
from typing import Type
from pathlib import Path
from ..utils import STORAGE_FOLDER


class UpratedFRS(Dataset):
    data_format = Dataset.ARRAYS

    @staticmethod
    def from_dataset(
        dataset: Type[Dataset],
        out_year: int = 2023,
    ):
        class UpratedFRSFromDataset(UpratedFRS):
            name = f"{dataset.name}_uprated_{out_year}"
            label = f"{dataset.label}"
            input_dataset = dataset
            time_period = out_year
            file_path = (
                STORAGE_FOLDER / f"{dataset.name}_uprated_{out_year}.h5"
            )

        return UpratedFRSFromDataset

    def generate(self):
        from policyengine_uk import Microsimulation

        input_dataset = self.input_dataset()
        simulation = Microsimulation(dataset=self.input_dataset)

        data = {}
        for variable in input_dataset.variables:
            try:
                data[variable] = simulation.calculate(
                    variable, period=self.output_year
                ).values
            except:
                data[variable] = input_dataset.load(variable)

        self.save_dataset(data)
