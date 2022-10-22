from policyengine_uk.tools.simulation import Microsimulation
import pandas as pd
from policyengine_uk import BASELINE_VARIABLES


def formalise_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Exchanges column names for their labels if possible

    Args:
        df (pd.DataFrame): The dataframe containing variable names in columns.

    Returns:
        pd.DataFrame: The dataframe with columns renamed.
    """
    column_mapping = {}
    for i in range(len(df.columns)):
        name = df.columns[i]
        if "baseline_" in name or "reform_" in name:
            variable_name = (
                name.replace("baseline_", "")
                .replace("reform_", "")
                .replace("_deriv", "")
            )
            tag = {True: " (Baseline)", False: " (Reform)"}[
                "baseline_" in name
            ]
            if variable_name in BASELINE_VARIABLES:
                column_mapping[
                    name
                ] = f"{BASELINE_VARIABLES[variable_name].label}{tag}"
            else:
                column_mapping[name] = f"{variable_name}{tag}"
        elif name == "reform":
            column_mapping[name] = "Reform"
        elif name in BASELINE_VARIABLES:
            column_mapping[name] = BASELINE_VARIABLES[name].label
    df.columns = df.columns.map(column_mapping)
    return df, column_mapping


def net_cost(
    baseline_sim: Microsimulation,
    reform_sim: Microsimulation,
    invert: bool = False,
    variable: str = "net_income",
) -> float:
    if invert:
        multiplier = -1
    else:
        multiplier = 1
    return multiplier * (
        reform_sim.calc(variable).sum() - baseline_sim.calc(variable).sum()
    )


GREY, DARK_BLUE = ("#BDBDBD", "#0F4AA1")
COLORS = (GREY, DARK_BLUE)
