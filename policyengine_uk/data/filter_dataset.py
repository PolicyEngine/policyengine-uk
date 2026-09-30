import typing

import numpy as np
import pandas as pd

if typing.TYPE_CHECKING:
    from policyengine_uk import Microsimulation
    from policyengine_uk.data import UKSingleYearDataset


def filter_dataset(
    sim: "Microsimulation", household_id: int, year: int = 2026
) -> "UKSingleYearDataset":
    from policyengine_uk import Microsimulation
    from policyengine_uk.data import UKSingleYearDataset

    """
    Extract a single household from a simulation dataset.

    This function creates a new dataset containing only the specified household
    and the associated benefit units and people within that household.

    Values imputed across the whole population (months_since_last_birthday and
    attends_private_school) are taken from sim for the given year and carried
    in as inputs, so the extract keeps them in later years too. Private school
    attendance ranks incomes, so the first extract from a simulation computes
    its taxes and benefits.

    Parameters
    ----------
    sim : Microsimulation
        The microsimulation object containing the dataset.
    household_id : int
        The ID of the household to extract.
    year : int, default 2026
        The dataset year to filter.

    Returns
    -------
    UKSingleYearDataset
        A new dataset containing only data for the specified household.
    """
    dataset: UKSingleYearDataset = sim.dataset[year]
    new_dataset = dataset.copy()
    person = new_dataset.person
    # These are imputed across the whole population: birthdays are spread over
    # the year, and private school attendance follows each household's income
    # percentile (one household alone would rank at the 100th). Carry each
    # person's value across rather than recompute it for one household.
    for variable in ("months_since_last_birthday", "attends_private_school"):
        if variable not in person.columns:
            values = pd.Series(
                np.asarray(sim.calculate(variable, year)),
                index=np.asarray(sim.calculate("person_id", year)),
            )
            person = person.assign(**{variable: values.loc[person.person_id].values})
    new_dataset.person = person[person.person_household_id == household_id]
    new_dataset.household = new_dataset.household[
        new_dataset.household.household_id == household_id
    ]
    benunits = new_dataset.person.person_benunit_id.unique()
    new_dataset.benunit = new_dataset.benunit[
        new_dataset.benunit.benunit_id.isin(benunits)
    ]

    return UKSingleYearDataset(
        person=new_dataset.person,
        household=new_dataset.household,
        benunit=new_dataset.benunit,
        fiscal_year=year,
    )
