import numpy as np


def stack_datasets(data_1, data_2):
    assert isinstance(
        data_1[list(data_1.keys())[0]], dict
    ), "Data must be in variable-time-period format."
    joined_data = {}

    for variable in data_1:
        joined_data[variable] = {}
        for time_period in data_1[variable]:
            if "_id" in variable:
                joined_data[variable][time_period] = np.concatenate(
                    [
                        data_1[variable][time_period],
                        data_2[variable][time_period]
                        + data_1[variable][time_period].max(),
                    ]
                )
            else:
                joined_data[variable][time_period] = np.concatenate(
                    [
                        data_1[variable][time_period],
                        data_2[variable][time_period],
                    ]
                )

    return joined_data
