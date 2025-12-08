import pandas as pd
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from policyengine_uk.simulation import Microsimulation


def compare_simulations(
    simulations: list["Microsimulation"],
    names: list[str],
    year: int,
    variables: list[str],
):
    dfs = [
        sim.calculate_dataframe(variables, year).rename(
            columns=lambda x: f"{x}_{name}"
        )
        for sim, name in zip(simulations, names)
    ]

    df = pd.concat(dfs, axis=1).reset_index().rename(columns={"index": "id"})

    # Sort columns by variable
    columns = []
    for var in variables:
        columns.extend([col for col in df.columns if col.startswith(var)])

    return df[columns]
