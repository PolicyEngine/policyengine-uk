import pandas as pd
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from policyengine_uk import Microsimulation

from pathlib import Path
import h5py


class UKDataset:
    person: pd.DataFrame
    benunit: pd.DataFrame
    household: pd.DataFrame

    @staticmethod
    def validate_file_path(file_path: str):
        if not file_path.endswith(".h5"):
            raise ValueError("File path must end with '.h5' for UKDataset.")
        if not Path(file_path).exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Check if the file contains time_period, person, benunit, and household datasets
        with h5py.File(file_path, "r") as f:
            required_datasets = [
                "time_period",
                "person",
                "benunit",
                "household",
            ]
            for dataset in required_datasets:
                if dataset not in f:
                    raise ValueError(
                        f"Dataset '{dataset}' not found in the file: {file_path}"
                    )

    def __init__(
        self,
        file_path: str = None,
        person: pd.DataFrame = None,
        benunit: pd.DataFrame = None,
        household: pd.DataFrame = None,
        fiscal_year: int = 2025,
    ):
        if file_path is not None:
            self.validate_file_path(file_path)
            with pd.HDFStore(file_path) as f:
                self.person = f["person"]
                self.benunit = f["benunit"]
                self.household = f["household"]
                self.time_period = str(f["time_period"].iloc[0])
        else:
            if person is None or benunit is None or household is None:
                raise ValueError(
                    "Must provide either a file path or all three DataFrames (person, benunit, household)."
                )
            self.person = person
            self.benunit = benunit
            self.household = household
            self.time_period = str(fiscal_year)

        self.data_format = "arrays"
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

    def validate(self):
        # Check for NaNs in the tables
        for df in self.tables:
            for col in df.columns:
                if df[col].isna().any():
                    raise ValueError(f"Column '{col}' contains NaN values.")

    @staticmethod
    def from_simulation(
        simulation: "Microsimulation", fiscal_year: int = 2025
    ):
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
