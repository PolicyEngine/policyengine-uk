from policyengine_core.data import Dataset
from policyengine_uk import Microsimulation
import numpy as np


def drop_zero_weight_households(dataset):
    sim = Microsimulation(dataset=dataset)
    assert sim.dataset.data_format == Dataset.TIME_PERIOD_ARRAYS

    is_zero_weight_all_years = np.ones_like(
        sim.calculate("household_weight").values
    )

    for year in range(2021, 2028):
        is_zero_weight_all_years = is_zero_weight_all_years * (
            sim.calculate("household_weight", period=year).values == 0
        )

    hh_zero_weight = is_zero_weight_all_years
    person_zero_weight = sim.map_result(
        is_zero_weight_all_years, "household", "person"
    )
    benunit_zero_weight = sim.map_result(
        is_zero_weight_all_years, "household", "benunit"
    )

    entity_to_remove = {
        "person": person_zero_weight > 0,
        "benunit": benunit_zero_weight > 0,
        "household": hh_zero_weight > 0,
    }

    data = sim.dataset.load_dataset()
    for variable in data:
        entity = sim.tax_benefit_system.variables[variable].entity.key
        for time_period in data[variable]:
            if entity in entity_to_remove:
                data[variable][time_period] = data[variable][time_period][
                    ~entity_to_remove[entity]
                ]

    sim.dataset.save_dataset(data)


drop_zero_weight_households("enhanced_frs")
