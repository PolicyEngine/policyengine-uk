from policyengine_uk.data import UKMultiYearDataset, UKSingleYearDataset
from policyengine_uk.system import system
import yaml
from policyengine_core.parameters import ParameterNode
from pathlib import Path


def apply_uprating(
    dataset: UKMultiYearDataset,
):
    # Apply uprating to the dataset.

    if not isinstance(dataset, UKMultiYearDataset):
        raise TypeError("dataset must be of type UKMultiYearDataset.")

    for year, single_year_dataset in dataset.datasets.items():
        apply_single_year_uprating(single_year_dataset, system.parameters)


def apply_single_year_uprating(
    dataset: UKSingleYearDataset,
    parameters: ParameterNode,
):
    # Apply uprating to a single year dataset.

    if not isinstance(dataset, UKSingleYearDataset):
        raise TypeError("dataset must be of type UKSingleYearDataset.")

    with open(Path(__file__).parent / "uprating_indices.yaml", "r") as f:
        uprating = yaml.safe_load(f)
    for index_name, variables in uprating.items():
        index_rel_change = parameters.get_child(index_name)(
            dataset.time_period
        )
        for variable in variables:
            for df in dataset.tables:
                if variable in df.columns:
                    df[variable] *= 1 + index_rel_change

    dataset.validate()


def reset_uprating(
    dataset: UKMultiYearDataset,
):
    # Remove all uprating from the dataset.

    first_year = min(dataset.datasets.keys())
    for year in dataset.datasets:
        if year != first_year:
            dataset.datasets[year] = dataset.datasets[first_year].copy()
