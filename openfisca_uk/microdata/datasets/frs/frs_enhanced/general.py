from typing import Dict
import h5py
from numpy.typing import ArrayLike
import numpy as np


def clone_and_replace_half(
    dataset: type,
    year: int,
    mapping: Dict[str, ArrayLike],
    weighting: float = 0.5,
    target_dataset: type = None,
):
    """Clones a dataset and replaces half of the values with the values in the mapping.

    Args:
        dataset (type): The dataset to clone.
        year (int): The year to clone.
        mapping (Dict[str, ArrayLike]): The mapping from the original dataset to the cloned dataset.
        weighting (float): The weighting to apply to the cloned dataset. The original dataset has
                            (1 - weighting) weight.
        target_dataset (type, optional): The dataset to write to. Defaults to None.
    """
    if target_dataset is None:
        target_dataset = dataset
    data = dataset.load(year)
    previous_data = {key: data[key][...] for key in data.keys()}
    data.close()
    file = h5py.File(target_dataset.file(year), "w")
    for field in previous_data:
        if "_id" in field and "state" not in field:
            values = np.concatenate(
                [previous_data[field] * 10, previous_data[field] * 10 + 1]
            )
        elif "_weight" in field and "state" not in field:
            values = np.concatenate(
                [
                    previous_data[field] * (1 - weighting),
                    previous_data[field] * weighting,
                ]
            )
        elif field in mapping:
            values = np.concatenate([previous_data[field], mapping[field]])
        elif len(previous_data[field]) > 1:
            values = np.concatenate(
                [previous_data[field], previous_data[field]]
            )
        else:
            values = previous_data[field]
        try:
            file[field] = values
        except TypeError:
            file[field] = values.astype("S")
    file.close()


def add_variables(dataset: type, year: int, variables: Dict[str, ArrayLike]):
    data = dataset.load(year)
    previous_data = {key: data[key][...] for key in data.keys()}
    data.close()
    f = h5py.File(dataset.file(year), "w")
    for field in previous_data:
        try:
            f[field] = previous_data[field]
        except TypeError:
            f[field] = previous_data[field].astype("S")
    for field in variables:
        try:
            f[field] = variables[field]
        except TypeError:
            f[field] = variables[field].astype("S")
    f.close()


def subsample(dataset: type, year: int, frac: float = 0.5):
    # Not yet working
    """Subsamples a dataset.

    Args:
        dataset (type): The dataset to subsample.
        year (int): The year to subsample.
        frac (float, optional): The fraction of the data to subsample. Defaults to 0.5.
    """
    from openfisca_uk import Microsimulation

    sim = Microsimulation(
        dataset=dataset,
        year=year,
        adjust_weights=False,
        add_baseline_values=False,
    )

    household_ids = sim.calc("household_id").sample(frac=frac)
    person_in_sample = sim.calc("household_id", map_to="person").isin(
        household_ids
    )
    benunit_in_sample = sim.map_to(
        sim.calc("household_id", map_to="person").values,
        "person",
        "benunit",
        how="value_from_first_person",
    )
    household_in_sample = sim.calc("household_id").isin(household_ids)
    state_in_sample = np.array([True])

    weight_multiplier = (
        sim.calc("households").sum()
        / sim.calc("households")[household_in_sample].sum()
    )

    data = dataset.load(year)
    previous_data = {key: data[key][...] for key in data.keys()}
    data.close()

    for variable in previous_data:
        try:
            entity = sim.simulation.tax_benefit_system.variables[
                variable
            ].entity.key
        except KeyError:
            if len(previous_data[variable]) == len(person_in_sample):
                entity = "person"
            elif len(previous_data[variable]) == len(benunit_in_sample):
                entity = "benunit"
            else:
                entity = "household"

        in_sample = dict(
            person=person_in_sample,
            benunit=benunit_in_sample,
            household=household_in_sample,
            state=state_in_sample,
        )[entity]

        previous_data[variable] = previous_data[variable][in_sample]

    previous_data["household_weight"] = (
        previous_data["household_weight"].astype(float) * weight_multiplier
    )
    previous_data["benunit_weight"] = (
        previous_data["benunit_weight"].astype(float) * weight_multiplier
    )

    file = h5py.File(dataset.file(year), "w")
    for field in previous_data:
        try:
            file[field] = previous_data[field]
        except TypeError:
            file[field] = previous_data[field].astype("S")
    file.close()
