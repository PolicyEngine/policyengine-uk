import typing

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
    new_dataset.person = new_dataset.person[
        new_dataset.person.person_household_id == household_id
    ]
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
