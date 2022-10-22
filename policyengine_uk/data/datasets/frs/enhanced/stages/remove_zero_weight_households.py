from policyengine_core.data import Dataset
import h5py

from policyengine_uk.data.datasets.frs.enhanced.stages.imputation.enhanced_frs import (
    EnhancedFRS,
)


def remove_zero_weight_households(dataset: Dataset, year: int):
    """Removes zero-weight households (and benefit units and people) from a year of the given dataset.

    Args:
        dataset (Dataset): The dataset to edit.
        year (int): The year of the dataset to edit.
    """

    from policyengine_uk import Microsimulation

    sim = Microsimulation(dataset=dataset, dataset_year=year)

    # To be removed, households must have zero weight in all of these years
    YEARS = list(range(year, 2027))

    variables = dataset.keys(year)

    for variable in variables:
        if variable not in sim.tax_benefit_system.variables:
            continue
        entity = sim.tax_benefit_system.variables[variable].entity.key
        has_nonzero_weight = (
            sum(
                [
                    sim.calc(f"{entity}_weight", period=year).values
                    for year in YEARS
                ]
            )
            > 0
        )
        if dataset.data_format == Dataset.ARRAYS:
            dataset.save(
                year,
                variable,
                dataset.load(year, variable)[has_nonzero_weight],
            )
        elif dataset.data_format == Dataset.TIME_PERIOD_ARRAYS:
            for period in dataset.load(year, variable):
                key = f"{variable}/{period}"
                dataset.save(
                    year, key, dataset.load(year, key)[has_nonzero_weight]
                )


if __name__ == "__main__":
    remove_zero_weight_households(EnhancedFRS, 2022)
