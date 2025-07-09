import pandas as pd
from pathlib import Path
from policyengine_uk.data.dataset_schema import UKDataset

START_YEAR = 2020
END_YEAR = 2034


def create_policyengine_uprating_factors_table():
    from policyengine_uk.system import system

    df = pd.DataFrame()

    variable_names = []
    years = []
    index_values = []

    parameter_by_variable = {}

    for variable in system.variables.values():
        if variable.uprating is not None:
            parameter = system.parameters.get_child(variable.uprating)
            parameter_by_variable[variable.name] = parameter.name
            start_value = parameter(START_YEAR)
            for year in range(START_YEAR, END_YEAR + 1):
                variable_names.append(variable.name)
                years.append(year)
                growth = parameter(year) / start_value
                index_values.append(round(growth, 3))

    df["Variable"] = variable_names
    df["Year"] = years
    df["Value"] = index_values

    # Convert to there is a column for each year
    df = df.pivot(index="Variable", columns="Year", values="Value")
    df = df.sort_values("Variable")

    # Create a table with growth factors by year

    df_growth = df.copy()
    for year in range(END_YEAR, START_YEAR, -1):
        df_growth[year] = round(df_growth[year] / df_growth[year - 1] - 1, 3)
    df_growth[START_YEAR] = 0

    file_path = Path(__file__).parent / "uprating_growth_factors.csv"
    df_growth["Parameter"] = df.index.map(parameter_by_variable)
    df_growth.to_csv(file_path)
    return pd.read_csv(file_path)


def apply_growth_factors(
    dataset: UKDataset,
    growth_factors: pd.DataFrame,
    start_year: int,
    end_year: int,
):
    dataset = dataset.copy()
    for i in range(len(growth_factors)):
        index = 1
        variable = growth_factors["Variable"].values[i]
        for year in range(start_year, end_year + 1):
            growth_factor = growth_factors[str(year)].values[i]
            index *= 1 + growth_factor

        for table in dataset.tables:
            if variable in table.columns:
                table[variable] *= index

    return dataset


BASELINE_GROWFACTORS = create_policyengine_uprating_factors_table()


if __name__ == "__main__":
    create_policyengine_uprating_factors_table()
