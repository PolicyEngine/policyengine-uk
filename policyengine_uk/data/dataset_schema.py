import pandas as pd
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from policyengine_uk import Microsimulation

from pathlib import Path
import h5py


class UKSingleYearDataset:
    person: pd.DataFrame
    benunit: pd.DataFrame
    household: pd.DataFrame

    @staticmethod
    def validate_file_path(file_path: str, raise_exception: bool = True):
        if not file_path.endswith(".h5"):
            if raise_exception:
                raise ValueError(
                    "File path must end with '.h5' for UKDataset."
                )
            return False
        if not Path(file_path).exists():
            if raise_exception:
                raise FileNotFoundError(f"File not found: {file_path}")
            return False

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
                    if raise_exception:
                        raise ValueError(
                            f"Dataset '{dataset}' not found in the file: {file_path}"
                        )
                    else:
                        return False

        return True

    def __init__(
        self,
        file_path: str = None,
        person: pd.DataFrame = None,
        benunit: pd.DataFrame = None,
        household: pd.DataFrame = None,
        fiscal_year: int = 2025,
    ):
        file_path = str(file_path) if file_path else None
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
        self.table_names = ("person", "benunit", "household")

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
        return UKSingleYearDataset(
            person=self.person.copy(),
            benunit=self.benunit.copy(),
            household=self.household.copy(),
            fiscal_year=self.time_period,
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
            if len(input_variables) == 0:
                entity_dfs[entity] = pd.DataFrame()
            else:
                entity_dfs[entity] = simulation.calculate_dataframe(
                    input_variables, period=fiscal_year
                )

        return UKSingleYearDataset(
            person=entity_dfs["person"],
            benunit=entity_dfs["benunit"],
            household=entity_dfs["household"],
            fiscal_year=fiscal_year,
        )


class UKMultiYearDataset:
    def __init__(
        self,
        file_path: str = None,
        datasets: list[UKSingleYearDataset] | None = None,
    ):
        if datasets is not None:
            self.datasets = {}
            for dataset in datasets:
                if not isinstance(dataset, UKSingleYearDataset):
                    raise TypeError(
                        "All items in datasets must be of type UKSingleYearDataset."
                    )
                year = int(dataset.time_period[:4])
                self.datasets[year] = dataset

        if file_path is not None:
            UKMultiYearDataset.validate_file_path(file_path)
            with pd.HDFStore(file_path) as f:
                self.datasets = {}
                for year in f.keys():
                    if year.startswith("/person/"):
                        fiscal_year = int(year.split("/")[2])
                        person_df = f[year]
                        benunit_df = f[f"/benunit/{fiscal_year}"]
                        household_df = f[f"/household/{fiscal_year}"]
                        self.datasets[fiscal_year] = UKSingleYearDataset(
                            person=person_df,
                            benunit=benunit_df,
                            household=household_df,
                            fiscal_year=fiscal_year,
                        )

        self.data_format = "time_period_arrays"
        self.time_period = list(sorted(self.datasets.keys()))[0]

    def get_year(self, fiscal_year: int) -> UKSingleYearDataset:
        if fiscal_year in self.datasets:
            return self.datasets[fiscal_year]
        else:
            raise ValueError(f"No dataset found for year {fiscal_year}.")

    @property
    def years(self):
        return list(self.datasets.keys())

    def __getitem__(self, fiscal_year: int):
        return self.get_year(fiscal_year)

    def save(self, file_path: str):
        Path(file_path).unlink(
            missing_ok=True
        )  # Remove existing file if it exists
        with pd.HDFStore(file_path) as f:
            for year, dataset in self.datasets.items():
                f.put(
                    f"person/{year}",
                    dataset.person,
                    format="table",
                    data_columns=True,
                )
                f.put(
                    f"benunit/{year}",
                    dataset.benunit,
                    format="table",
                    data_columns=True,
                )
                f.put(
                    f"household/{year}",
                    dataset.household,
                    format="table",
                    data_columns=True,
                )
                f.put(
                    f"time_period/{year}",
                    pd.Series([year]),
                    format="table",
                    data_columns=True,
                )

    def copy(self):
        new_datasets = {
            year: dataset.copy() for year, dataset in self.datasets.items()
        }
        return UKMultiYearDataset(datasets=list(new_datasets.values()))

    @staticmethod
    def validate_file_path(file_path: str, raise_exception: bool = False):
        if not file_path.endswith(".h5"):
            if raise_exception:
                raise ValueError(
                    "File path must end with '.h5' for UKMultiYearDataset."
                )
            else:
                return False
        if not Path(file_path).exists():
            if raise_exception:
                raise FileNotFoundError(f"File not found: {file_path}")
            else:
                return False

        # Check if the file contains datasets for multiple years
        with h5py.File(file_path, "r") as f:
            for required_dataset in ["person", "benunit", "household"]:
                if not any(f"{required_dataset}" in key for key in f.keys()):
                    if raise_exception:
                        raise ValueError(
                            f"Dataset '{required_dataset}' not found in the file: {file_path}"
                        )
                    else:
                        return False

                # Check that there is at least one dataset year in the folder (keys include e.g. person/2025)

                # Check that there is at least one dataset year in the folder
                years_found = False
                for key in f.keys():
                    parts = key.split("/")
                    if len(parts) >= 2 and required_dataset == parts[0]:
                        years_found = True
                        break

                if not years_found:
                    if raise_exception:
                        raise ValueError(
                            f"No yearly data found for '{required_dataset}' in file: {file_path}"
                        )
                    else:
                        return False
        return True

    def load(self):
        data = {}
        for year, dataset in self.datasets.items():
            for df in (dataset.person, dataset.benunit, dataset.household):
                for col in df.columns:
                    if col not in data:
                        data[col] = {}
                    data[col][year] = df[col].values
        return data

    def reset_uprating(self):
        from policyengine_uk.data.economic_assumptions import reset_uprating

        reset_uprating(self)
