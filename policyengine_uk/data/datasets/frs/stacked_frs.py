from policyengine_core.data import Dataset
import numpy as np
from pathlib import Path
from ..utils import STORAGE_FOLDER
from .frs import FRS_2018_19, FRS_2019_20, FRS_2020_21
from .uprated_frs import UpratedFRS


class StackedFRS(Dataset):
    sub_datasets = []
    weighting_factors = []

    @staticmethod
    def from_dataset(
        datasets,
        weight_factors,
        new_name,
        new_label,
        new_time_period,
        new_url=None,
    ):
        class StackedDatasetFromDataset(StackedFRS):
            sub_datasets = datasets
            weighting_factors = weight_factors
            name = new_name
            label = new_label
            data_format = datasets[0].data_format
            file_path = STORAGE_FOLDER / f"{new_name}.h5"
            time_period = new_time_period
            url = new_url

        return StackedDatasetFromDataset

    def generate(self):
        sub_datasets = [dataset() for dataset in self.sub_datasets]
        variable_names = sub_datasets[0].variables
        data = {}
        for variable in variable_names:
            if "_id" in variable:
                new_ids = []
                max_id = 0
                for dataset in sub_datasets:
                    new_ids.append(dataset.load(variable) + max_id)
                    max_id += dataset.load(variable).max()
                data[variable] = np.concatenate(new_ids)
            elif "_weight" in variable:
                data[variable] = np.concatenate(
                    [
                        dataset.load(variable) * weight
                        for dataset, weight in zip(
                            sub_datasets, self.weighting_factors
                        )
                    ]
                )
            else:
                data[variable] = np.concatenate(
                    [dataset.load(variable) for dataset in sub_datasets]
                )
        self.save_dataset(data)


PooledFRS_2018_20 = StackedFRS.from_dataset(
    [
        UpratedFRS.from_dataset(FRS_2018_19),
        UpratedFRS.from_dataset(FRS_2019_20),
        UpratedFRS.from_dataset(FRS_2020_21),
    ],
    [0.0, 1.0, 0.0],
    "pooled_frs_2018_20",
    "FRS 2018-20",
    2023,
)
