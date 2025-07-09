import pandas as pd
from policyengine_uk import Microsimulation


class UKDataset:
    person: pd.DataFrame
    benunit: pd.DataFrame
    household: pd.DataFrame

    def __init__(
        self,
        file_path: str = None,
        person: pd.DataFrame = None,
        benunit: pd.DataFrame = None,
        household: pd.DataFrame = None,
        fiscal_year: int = 2025,
    ):
        if file_path is not None:
            with pd.HDFStore(file_path) as f:
                self.person = f["person"]
                self.benunit = f["benunit"]
                self.household = f["household"]
                self.time_period = f["time_period"].iloc[0]
        else:
            if person is None or benunit is None or household is None:
                raise ValueError(
                    "Must provide either a file path or all three DataFrames (person, benunit, household)."
                )
            self.person = person
            self.benunit = benunit
            self.household = household

        self.data_format = "arrays"
        self.time_period = fiscal_year
        self.tables = (self.person, self.benunit, self.household)

    def save(self, file_path: str):
        with pd.HDFStore(file_path) as f:
            f.put("person", self.person, format="table", data_columns=True)
            f.put("benunit", self.benunit, format="table", data_columns=True)
            f.put(
                "household", self.household, format="table", data_columns=True
            )
            f.put("time_period", pd.Series([self.time_period]), format="table")

    def load(self):
        data = {}
        for df in (self.person, self.benunit, self.household):
            for col in df.columns:
                data[col] = df[col].values

        return data

    def copy(self):
        return UKDataset(
            person=self.person.copy(),
            benunit=self.benunit.copy(),
            household=self.household.copy(),
        )

    @staticmethod
    def from_simulation(simulation: Microsimulation, fiscal_year: int = 2025):
        entity_dfs = {}

        for entity in ["person", "benunit", "household"]:
            input_variables = [
                variable
                for variable in simulation.input_variables
                if simulation.tax_benefit_system.variables[variable].entity.key
                == entity
            ]
            entity_dfs[entity] = simulation.calculate_dataframe(
                input_variables, period=fiscal_year
            )

        return UKDataset(
            person=entity_dfs["person"],
            benunit=entity_dfs["benunit"],
            household=entity_dfs["household"],
            fiscal_year=fiscal_year,
        )
