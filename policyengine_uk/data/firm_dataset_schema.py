import pandas as pd
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from policyengine_uk import Microsimulation

from pathlib import Path
import h5py


class UKFirmSingleYearDataset:
    firm: pd.DataFrame
    sector: pd.DataFrame
    business_group: pd.DataFrame

    @staticmethod
    def validate_file_path(file_path: str, raise_exception: bool = True):
        if not file_path.endswith(".h5"):
            if raise_exception:
                raise ValueError(
                    "File path must end with '.h5' for UKFirmDataset."
                )
            return False
        if not Path(file_path).exists():
            if raise_exception:
                raise FileNotFoundError(f"File not found: {file_path}")
            return False

        # Check if the file contains time_period, firm, sector, and business_group datasets
        with h5py.File(file_path, "r") as f:
            required_datasets = [
                "time_period",
                "firm",
                "sector",
                "business_group",
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
        firm: pd.DataFrame = None,
        sector: pd.DataFrame = None,
        business_group: pd.DataFrame = None,
        fiscal_year: int = 2025,
    ):
        file_path = str(file_path) if file_path else None
        if file_path is not None:
            self.validate_file_path(file_path)
            with pd.HDFStore(file_path) as f:
                self.firm = f["firm"]
                self.sector = f["sector"]
                self.business_group = f["business_group"]
                self.time_period = str(f["time_period"].iloc[0])
        else:
            if firm is None or sector is None or business_group is None:
                raise ValueError(
                    "Must provide either a file path or all three DataFrames (firm, sector, business_group)."
                )
            self.firm = firm
            self.sector = sector
            self.business_group = business_group
            self.time_period = str(fiscal_year)

        self.data_format = "arrays"
        self.tables = (self.firm, self.sector, self.business_group)
        self.table_names = ("firm", "sector", "business_group")

    def save(self, file_path: str):
        with pd.HDFStore(file_path) as f:
            f.put("firm", self.firm, format="table", data_columns=True)
            f.put("sector", self.sector, format="table", data_columns=True)
            f.put(
                "business_group",
                self.business_group,
                format="table",
                data_columns=True,
            )
            f.put("time_period", pd.Series([self.time_period]), format="table")

    def load(self):
        data = {}
        for df in (self.firm, self.sector, self.business_group):
            for col in df.columns:
                data[col] = df[col].values

        return data

    def copy(self):
        return UKFirmSingleYearDataset(
            firm=self.firm.copy(),
            sector=self.sector.copy(),
            business_group=self.business_group.copy(),
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

        for entity in ["firm", "sector", "business_group"]:
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

        return UKFirmSingleYearDataset(
            firm=entity_dfs["firm"],
            sector=entity_dfs["sector"],
            business_group=entity_dfs["business_group"],
            fiscal_year=fiscal_year,
        )
