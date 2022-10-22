from typing import Dict
import h5py
from numpy.typing import ArrayLike
import numpy as np
from policyengine_core.data.dataset import Dataset


def clone_and_replace_half(
    dataset: Dataset,
    year: int,
    mapping: Dict[str, ArrayLike],
    weighting: float = 0.5,
    target_dataset: Dataset = None,
):
    """Clones a dataset and replaces half of the values with the values in the mapping.

    Args:
        dataset (Dataset): The dataset to clone.
        year (int): The year to clone.
        mapping (Dict[str, ArrayLike]): The mapping from the original dataset to the cloned dataset.
        weighting (float): The weighting to apply to the cloned dataset. The original dataset has
                            (1 - weighting) weight.
        target_dataset (Dataset, optional): The dataset to write to. Defaults to None.
    """
    if target_dataset is None:
        target_dataset = dataset
    data = dataset.load(year)
    previous_data = {}
    for variable in data.keys():
        for period in data[variable].keys():
            previous_data[f"{variable}/{period}"] = data[variable][period][...]
    data.close()
    file = h5py.File(target_dataset.file(year), "w")
    for field in previous_data:
        if "_id" in field and not "state" in field:
            values = np.array(
                list(previous_data[field] * 10)
                + [x * 10 + 1 for x in previous_data[field]]
            )
        elif "_weight" in field and not "state" in field:
            values = np.concatenate(
                [
                    previous_data[field] * (1 - weighting),
                    previous_data[field] * weighting,
                ]
            )
        elif field in ("state_id", "state_weight"):
            values = previous_data[field]
        elif field in mapping:
            assert len(previous_data[field]) == len(
                mapping[field]
            ), f"Lengths don't match for {field}: {len(previous_data[field])} != {len(mapping[field])}"
            values = np.concatenate([previous_data[field], mapping[field]])
        else:
            values = np.concatenate(
                [previous_data[field], previous_data[field]]
            )
        try:
            file[field] = values
        except TypeError:
            file[field] = values.astype("S")
    file.close()


def add_variables(
    dataset: Dataset, year: int, variables: Dict[str, ArrayLike]
):
    data = dataset.load(year)
    previous_data = {}
    for variable in data.keys():
        for period in data[variable].keys():
            previous_data[f"{variable}/{period}"] = data[variable][period][...]
    data.close()
    f = h5py.File(dataset.file(year), "w")
    for field in previous_data:
        if field in f.keys():
            # Remove
            del f[field]
        try:
            f[field] = previous_data[field]
        except TypeError:
            f[field] = previous_data[field].astype("S")
    for field in variables:
        if field in f.keys():
            # Remove
            del f[field]
        try:
            f[field] = variables[field]
        except TypeError:
            f[field] = variables[field].astype("S")
    f.close()
